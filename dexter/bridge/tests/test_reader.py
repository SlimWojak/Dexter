"""
Tests for Bridge governance log reader — BRIDGE_SPEC_v0.2 Section 3.1.

Covers:
  - Pull-based reading (poll returns new entries since cursor)
  - Cursor tracking across polls (checkpoint resumes)
  - Fail-closed on invalid signature (BridgeHalt)
  - Fail-closed on corrupt log (BridgeHalt)
  - Bootstrap (empty log, no prior state)
  - End-to-end: write events → poll → verify → checkpoint → poll again
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bridge.reader import BridgeHalt, GovernanceLogReader
from bridge.tests.conftest import FakeGovernanceLog
from bridge.types import FailureType


class TestPollBasics:
    def test_poll_empty_log_returns_nothing(
        self, log_dir: Path, state_dir: Path, phoenix_key: bytes, fake_log: FakeGovernanceLog
    ) -> None:
        reader = GovernanceLogReader(fake_log.log_path, state_dir, phoenix_key)
        result = reader.poll()
        assert result.entries == []
        assert result.entries_read == 0
        assert not result.halted

    def test_poll_returns_new_entries(
        self, log_dir: Path, state_dir: Path, phoenix_key: bytes,
        populated_log: FakeGovernanceLog,
    ) -> None:
        reader = GovernanceLogReader(populated_log.log_path, state_dir, phoenix_key)
        result = reader.poll()
        assert len(result.entries) == 5
        assert result.entries[0].event_type == "LEASE_ACTIVATION"
        assert result.entries[4].event_type == "LEASE_EXPIRY"

    def test_poll_entries_have_correct_fields(
        self, log_dir: Path, state_dir: Path, phoenix_key: bytes,
        fake_log: FakeGovernanceLog,
    ) -> None:
        fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1", "strategy_ref": "S_v1.0.0", "bounds_snapshot": {}})
        reader = GovernanceLogReader(fake_log.log_path, state_dir, phoenix_key)
        result = reader.poll()

        entry = result.entries[0]
        assert entry.seq == 1
        assert entry.event_type == "LEASE_ACTIVATION"
        assert entry.payload["lease_id"] == "l1"
        assert entry.athena_index == 1
        assert len(entry.athena_hash) == 64
        assert entry.source_signature["algorithm"] == "hmac-sha256"


class TestCursorTracking:
    def test_checkpoint_advances_cursor(
        self, log_dir: Path, state_dir: Path, phoenix_key: bytes,
        fake_log: FakeGovernanceLog,
    ) -> None:
        fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})
        fake_log.append("LEASE_EXPIRY", {"lease_id": "l1", "final_stats": {}})

        reader = GovernanceLogReader(fake_log.log_path, state_dir, phoenix_key)
        result = reader.poll()
        assert len(result.entries) == 2
        reader.checkpoint()

        assert reader.state.last_read_seq == 2

    def test_second_poll_only_returns_new(
        self, log_dir: Path, state_dir: Path, phoenix_key: bytes,
        fake_log: FakeGovernanceLog,
    ) -> None:
        fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})
        fake_log.append("LEASE_EXPIRY", {"lease_id": "l1", "final_stats": {}})

        reader = GovernanceLogReader(fake_log.log_path, state_dir, phoenix_key)
        reader.poll()
        reader.checkpoint()

        fake_log.append("ATTESTATION", {"lease_id": "l1", "decision": "RENEW", "new_lease_id": None})

        result2 = reader.poll()
        assert len(result2.entries) == 1
        assert result2.entries[0].event_type == "ATTESTATION"
        assert result2.entries[0].seq == 3

    def test_cursor_survives_restart(
        self, log_dir: Path, state_dir: Path, phoenix_key: bytes,
        fake_log: FakeGovernanceLog,
    ) -> None:
        fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})
        fake_log.append("LEASE_EXPIRY", {"lease_id": "l1", "final_stats": {}})

        reader1 = GovernanceLogReader(fake_log.log_path, state_dir, phoenix_key)
        reader1.poll()
        reader1.checkpoint()

        fake_log.append("ATTESTATION", {"lease_id": "l2", "decision": "RENEW", "new_lease_id": None})

        reader2 = GovernanceLogReader(fake_log.log_path, state_dir, phoenix_key)
        result = reader2.poll()
        assert len(result.entries) == 1
        assert result.entries[0].seq == 3

    def test_no_checkpoint_rereads_all(
        self, log_dir: Path, state_dir: Path, phoenix_key: bytes,
        fake_log: FakeGovernanceLog,
    ) -> None:
        """Without checkpoint, second poll re-verifies everything."""
        fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})

        reader = GovernanceLogReader(fake_log.log_path, state_dir, phoenix_key)
        r1 = reader.poll()
        assert len(r1.entries) == 1

        reader2 = GovernanceLogReader(fake_log.log_path, state_dir, phoenix_key)
        r2 = reader2.poll()
        assert len(r2.entries) == 1


class TestFailClosed:
    def test_invalid_signature_halts(
        self, log_dir: Path, state_dir: Path, fake_log: FakeGovernanceLog,
    ) -> None:
        fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})
        reader = GovernanceLogReader(fake_log.log_path, state_dir, b"wrong_key")

        with pytest.raises(BridgeHalt, match="BRIDGE HALT"):
            reader.poll()

    def test_corrupt_log_entry_halts(
        self, log_dir: Path, state_dir: Path, phoenix_key: bytes,
        fake_log: FakeGovernanceLog,
    ) -> None:
        fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})

        with open(fake_log.log_path, "a") as f:
            f.write("{not valid json\n")

        reader = GovernanceLogReader(fake_log.log_path, state_dir, phoenix_key)
        with pytest.raises(BridgeHalt, match="Corrupt"):
            reader.poll()

    def test_tampered_entry_halts(
        self, log_dir: Path, state_dir: Path, phoenix_key: bytes,
        fake_log: FakeGovernanceLog,
    ) -> None:
        fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})
        fake_log.append("LEASE_EXPIRY", {"lease_id": "l1", "final_stats": {}})

        lines = fake_log.log_path.read_text().strip().split("\n")
        entry = json.loads(lines[1])
        entry["payload"]["lease_id"] = "TAMPERED"
        lines[1] = json.dumps(entry, sort_keys=True, separators=(",", ":"))
        fake_log.log_path.write_text("\n".join(lines) + "\n")

        reader = GovernanceLogReader(fake_log.log_path, state_dir, phoenix_key)
        with pytest.raises(BridgeHalt):
            reader.poll()

    def test_missing_log_after_bootstrap_halts(
        self, log_dir: Path, state_dir: Path, phoenix_key: bytes,
        fake_log: FakeGovernanceLog,
    ) -> None:
        fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})

        reader = GovernanceLogReader(fake_log.log_path, state_dir, phoenix_key)
        reader.poll()
        reader.checkpoint()

        fake_log.log_path.unlink()

        reader2 = GovernanceLogReader(fake_log.log_path, state_dir, phoenix_key)
        with pytest.raises(BridgeHalt, match="missing"):
            reader2.poll()


class TestEndToEnd:
    def test_write_poll_checkpoint_poll_cycle(
        self, log_dir: Path, state_dir: Path, phoenix_key: bytes,
        fake_log: FakeGovernanceLog,
    ) -> None:
        """Full cycle: write → poll → checkpoint → write more → poll → checkpoint."""
        fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})
        fake_log.append("STATE_LOCK", {"lease_id": "l1", "prior_state": "DRAFT", "prior_state_hash": "x", "requested_transition": "t", "transition_result": "SUCCESS"})

        reader = GovernanceLogReader(fake_log.log_path, state_dir, phoenix_key)

        r1 = reader.poll()
        assert len(r1.entries) == 2
        assert r1.entries_read == 2
        reader.checkpoint()

        fake_log.append("CALIBRATION", {"cartridge_ref": "S_v1.0.0", "lease_id": "l1", "drift_pct": 0.5, "verdict": "PASS"})
        fake_log.append("LEASE_EXPIRY", {"lease_id": "l1", "final_stats": {}})

        r2 = reader.poll()
        assert len(r2.entries) == 2
        assert r2.entries[0].seq == 3
        assert r2.entries[1].seq == 4
        reader.checkpoint()

        assert reader.state.last_read_seq == 4

        r3 = reader.poll()
        assert len(r3.entries) == 0

    def test_five_events_all_verified(
        self, log_dir: Path, state_dir: Path, phoenix_key: bytes,
        populated_log: FakeGovernanceLog,
    ) -> None:
        reader = GovernanceLogReader(populated_log.log_path, state_dir, phoenix_key)
        result = reader.poll()

        assert len(result.entries) == 5
        assert result.failures == []
        assert not result.halted

        seqs = [e.seq for e in result.entries]
        assert seqs == [1, 2, 3, 4, 5]

        types = [e.event_type for e in result.entries]
        assert types == [
            "LEASE_ACTIVATION", "STATE_LOCK", "CALIBRATION",
            "ATTESTATION", "LEASE_EXPIRY",
        ]
