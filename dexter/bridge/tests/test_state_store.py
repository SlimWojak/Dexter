"""
Tests for Bridge state store — BRIDGE_SPEC_v0.2 Section 4.

Covers:
  - Bootstrap mode (first start, no checkpoint)
  - Checkpoint save/load round-trip
  - Cursor tracking (last_read_seq resumes)
  - Corruption detection (HALT)
  - Pointer ahead detection (HALT)
  - Log rotation detection (inode change → HALT)
  - Replay counter and GT tracker persistence
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bridge.state_store import GENESIS_HASH, BridgeStateError, BridgeStateStore
from bridge.tests.conftest import FakeGovernanceLog


class TestBootstrap:
    def test_first_start_is_bootstrap(
        self, state_dir: Path, log_dir: Path, fake_log: FakeGovernanceLog
    ) -> None:
        store = BridgeStateStore(state_dir, fake_log.log_path)
        assert store.is_bootstrap
        assert store.last_read_seq == 0
        assert store.last_event_hash == GENESIS_HASH

    def test_bootstrap_with_no_log_file(
        self, state_dir: Path, tmp_path: Path
    ) -> None:
        missing_log = tmp_path / "nonexistent" / "governance_log.jsonl"
        store = BridgeStateStore(state_dir, missing_log)
        assert store.is_bootstrap

    def test_bootstrap_distinct_from_corruption(
        self, state_dir: Path, fake_log: FakeGovernanceLog
    ) -> None:
        """First start = bootstrap. Second start with corrupt checkpoint = error."""
        store = BridgeStateStore(state_dir, fake_log.log_path)
        store.advance(seq=1, event_hash="abc", gt_timestamp="2026-01-01T00:00:00")
        store.save()

        checkpoint = state_dir / "bridge_checkpoint.json"
        checkpoint.write_text("{corrupt")

        with pytest.raises(BridgeStateError, match="cannot parse"):
            BridgeStateStore(state_dir, fake_log.log_path)


class TestCheckpointRoundTrip:
    def test_save_and_load(
        self, state_dir: Path, fake_log: FakeGovernanceLog
    ) -> None:
        store1 = BridgeStateStore(state_dir, fake_log.log_path)
        store1.advance(seq=3, event_hash="hash_3", gt_timestamp="2026-02-28T12:00:00")
        store1.save()

        store2 = BridgeStateStore(state_dir, fake_log.log_path)
        assert store2.last_read_seq == 3
        assert store2.last_event_hash == "hash_3"
        assert not store2.is_bootstrap

    def test_replay_counter_persists(
        self, state_dir: Path, fake_log: FakeGovernanceLog
    ) -> None:
        store1 = BridgeStateStore(state_dir, fake_log.log_path)
        store1.advance(seq=5, event_hash="h5", gt_timestamp="2026-02-28T12:00:00")
        store1.save()

        store2 = BridgeStateStore(state_dir, fake_log.log_path)
        assert store2.get_replay_counter("phoenix") == 5

    def test_gt_tracker_persists(
        self, state_dir: Path, fake_log: FakeGovernanceLog
    ) -> None:
        store1 = BridgeStateStore(state_dir, fake_log.log_path)
        store1.advance(
            seq=2, event_hash="h2", gt_timestamp="2026-02-28T15:30:00"
        )
        store1.save()

        store2 = BridgeStateStore(state_dir, fake_log.log_path)
        assert store2.get_last_gt("phoenix") == "2026-02-28T15:30:00"

    def test_multiple_advances_then_save(
        self, state_dir: Path, fake_log: FakeGovernanceLog
    ) -> None:
        store = BridgeStateStore(state_dir, fake_log.log_path)
        store.advance(seq=1, event_hash="h1", gt_timestamp="2026-01-01T00:00:00")
        store.advance(seq=2, event_hash="h2", gt_timestamp="2026-01-01T00:01:00")
        store.advance(seq=3, event_hash="h3", gt_timestamp="2026-01-01T00:02:00")
        store.save()

        store2 = BridgeStateStore(state_dir, fake_log.log_path)
        assert store2.last_read_seq == 3
        assert store2.last_event_hash == "h3"


class TestCorruptionDetection:
    def test_corrupt_json_halts(
        self, state_dir: Path, fake_log: FakeGovernanceLog
    ) -> None:
        store = BridgeStateStore(state_dir, fake_log.log_path)
        store.advance(seq=1, event_hash="h1", gt_timestamp="t1")
        store.save()

        checkpoint = state_dir / "bridge_checkpoint.json"
        checkpoint.write_text("{invalid json")

        with pytest.raises(BridgeStateError, match="cannot parse"):
            BridgeStateStore(state_dir, fake_log.log_path)

    def test_tampered_checkpoint_hash_halts(
        self, state_dir: Path, fake_log: FakeGovernanceLog
    ) -> None:
        store = BridgeStateStore(state_dir, fake_log.log_path)
        store.advance(seq=1, event_hash="h1", gt_timestamp="t1")
        store.save()

        checkpoint = state_dir / "bridge_checkpoint.json"
        data = json.loads(checkpoint.read_text())
        data["last_read_seq"] = 999
        checkpoint.write_text(json.dumps(data))

        with pytest.raises(BridgeStateError, match="hash mismatch"):
            BridgeStateStore(state_dir, fake_log.log_path)


class TestPointerAhead:
    def test_pointer_ahead_of_log_halts(
        self, state_dir: Path, fake_log: FakeGovernanceLog
    ) -> None:
        store = BridgeStateStore(state_dir, fake_log.log_path)
        store.advance(seq=10, event_hash="h10", gt_timestamp="t10")
        with pytest.raises(BridgeStateError, match="Pointer ahead"):
            store.verify_pointer(log_length=5)

    def test_pointer_at_log_length_ok(
        self, state_dir: Path, fake_log: FakeGovernanceLog
    ) -> None:
        store = BridgeStateStore(state_dir, fake_log.log_path)
        store.advance(seq=3, event_hash="h3", gt_timestamp="t3")
        store.verify_pointer(log_length=5)


class TestLogRotationDetection:
    def test_inode_change_halts(
        self, state_dir: Path, log_dir: Path, phoenix_key: bytes
    ) -> None:
        log1 = FakeGovernanceLog(log_dir, phoenix_key)
        log1.append("LEASE_ACTIVATION", {"lease_id": "l1"})

        store = BridgeStateStore(state_dir, log1.log_path)
        store.advance(seq=1, event_hash="h1", gt_timestamp="t1")
        store.save()

        log1.log_path.unlink()
        log1.log_path.write_text('{"seq":1}\n')

        with pytest.raises(BridgeStateError, match="identity changed"):
            BridgeStateStore(state_dir, log1.log_path)
