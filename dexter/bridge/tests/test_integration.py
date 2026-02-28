"""
End-to-end integration test — the S62 capstone.

Phoenix governance_log.py (emitter)
  → bridge/reader.py (poll + verify)
  → bridge/envelope.py (seal into BridgeEnvelope)
  → governance_mapper.py (map to FACT bead)
  → bead field store

Plus: all 7 banked Bridge invariants and kill chain.
"""

from __future__ import annotations

import json
import secrets
from pathlib import Path

import pytest

from bead_field.ingestion.governance_mapper import GovernanceMapper, SOURCE_TYPE_MAP
from bead_field.ingestion.pipeline import IngestionPipeline
from bead_field.integrity.signing import KeyManager
from bead_field.schema.enums import BeadType, SourceType, TemporalClass
from bead_field.store.bitemporal import BeadStore
from bridge.envelope import EnvelopeConstructor
from bridge.orchestrator import BridgeOrchestrator, CycleResult
from bridge.reader import BridgeHalt, GovernanceLogReader
from bridge.tests.conftest import FakeGovernanceLog
from bridge.types import PHOENIX_GOVERNANCE_EVENTS


# --- Fixtures ---

@pytest.fixture()
def phoenix_key() -> bytes:
    return secrets.token_bytes(32)


@pytest.fixture()
def bridge_key() -> bytes:
    return secrets.token_bytes(32)


@pytest.fixture()
def log_dir(tmp_path: Path) -> Path:
    d = tmp_path / "phoenix_data"
    d.mkdir()
    return d


@pytest.fixture()
def state_dir(tmp_path: Path) -> Path:
    d = tmp_path / "bridge_state"
    d.mkdir()
    return d


@pytest.fixture()
def fake_log(log_dir: Path, phoenix_key: bytes) -> FakeGovernanceLog:
    return FakeGovernanceLog(log_dir, phoenix_key)


@pytest.fixture()
def bead_keys():
    return KeyManager.generate()


@pytest.fixture()
def store():
    s = BeadStore(":memory:")
    yield s
    s.close()


@pytest.fixture()
def pipeline(store, bead_keys):
    return IngestionPipeline(store, bead_keys)


@pytest.fixture()
def bridge(
    fake_log: FakeGovernanceLog,
    state_dir: Path,
    phoenix_key: bytes,
    bridge_key: bytes,
    pipeline: IngestionPipeline,
) -> BridgeOrchestrator:
    reader = GovernanceLogReader(fake_log.log_path, state_dir, phoenix_key)
    constructor = EnvelopeConstructor(bridge_key=bridge_key)
    mapper = GovernanceMapper(pipeline=pipeline)
    return BridgeOrchestrator(reader=reader, constructor=constructor, mapper=mapper)


def _populate_governance_log(fake_log: FakeGovernanceLog) -> int:
    """Write a realistic sequence of governance events. Returns count."""
    fake_log.append("CARTRIDGE_INSERTION", {
        "cartridge_ref": "STRAT_v1.0.0", "hash": "abc123", "linter_result": "PASS",
    })
    fake_log.append("LEASE_ACTIVATION", {
        "lease_id": "lease_001", "strategy_ref": "STRAT_v1.0.0",
        "bounds_snapshot": {"max_drawdown_pct": 5.0},
    })
    fake_log.append("STATE_LOCK", {
        "lease_id": "lease_001", "prior_state": "DRAFT",
        "prior_state_hash": "def456", "requested_transition": "DRAFT→ACTIVE",
        "transition_result": "SUCCESS",
    })
    fake_log.append("CALIBRATION", {
        "cartridge_ref": "STRAT_v1.0.0", "lease_id": "lease_001",
        "drift_pct": 1.2, "verdict": "PASS",
    })
    fake_log.append("ATTESTATION", {
        "lease_id": "lease_001", "decision": "RENEW", "new_lease_id": None,
    })
    fake_log.append("LEASE_EXPIRY", {
        "lease_id": "lease_001", "final_stats": {"trades": 12, "pnl": 150.0},
    })
    fake_log.append("CARTRIDGE_REMOVAL", {
        "cartridge_ref": "STRAT_v1.0.0", "removed_by": "G", "reason": "end_of_life",
    })
    return 7


# ===================================================================
# End-to-end: Phoenix → Bridge → FACT bead in Dexter store
# ===================================================================

class TestEndToEnd:
    def test_full_pipeline_seven_events(
        self, fake_log: FakeGovernanceLog, bridge: BridgeOrchestrator, store: BeadStore,
    ) -> None:
        count = _populate_governance_log(fake_log)
        result = bridge.cycle()

        assert result.entries_read == count
        assert result.envelopes_sealed == count
        assert result.beads_written == count
        assert store.count() == count

    def test_beads_are_fact_type(
        self, fake_log: FakeGovernanceLog, bridge: BridgeOrchestrator, store: BeadStore,
    ) -> None:
        _populate_governance_log(fake_log)
        bridge.cycle()

        conn = store.connection
        rows = conn.execute("SELECT bead_type FROM beads").fetchall()
        assert all(r["bead_type"] == "FACT" for r in rows)

    def test_beads_queryable_by_governance_tag(
        self, fake_log: FakeGovernanceLog, bridge: BridgeOrchestrator, store: BeadStore,
    ) -> None:
        _populate_governance_log(fake_log)
        bridge.cycle()

        conn = store.connection
        rows = conn.execute(
            "SELECT tags FROM beads WHERE tags LIKE ?", ('%src:governance%',)
        ).fetchall()
        assert len(rows) == 7

    def test_beads_queryable_by_event_type_tag(
        self, fake_log: FakeGovernanceLog, bridge: BridgeOrchestrator, store: BeadStore,
    ) -> None:
        _populate_governance_log(fake_log)
        bridge.cycle()

        conn = store.connection
        rows = conn.execute(
            "SELECT tags FROM beads WHERE tags LIKE ?",
            ('%gov_event:LEASE_ACTIVATION%',),
        ).fetchall()
        assert len(rows) == 1

    def test_beads_queryable_by_lease_id_tag(
        self, fake_log: FakeGovernanceLog, bridge: BridgeOrchestrator, store: BeadStore,
    ) -> None:
        _populate_governance_log(fake_log)
        bridge.cycle()

        conn = store.connection
        rows = conn.execute(
            "SELECT tags FROM beads WHERE tags LIKE ?",
            ('%gov:lease_id:lease_001%',),
        ).fetchall()
        assert len(rows) == 5

    def test_multi_cycle_incremental(
        self, fake_log: FakeGovernanceLog, bridge: BridgeOrchestrator, store: BeadStore,
    ) -> None:
        fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1", "strategy_ref": "S_v1", "bounds_snapshot": {}})
        fake_log.append("LEASE_EXPIRY", {"lease_id": "l1", "final_stats": {}})

        r1 = bridge.cycle()
        assert r1.beads_written == 2
        assert store.count() == 2

        fake_log.append("ATTESTATION", {"lease_id": "l2", "decision": "RENEW", "new_lease_id": None})

        r2 = bridge.cycle()
        assert r2.beads_written == 1
        assert store.count() == 3

    def test_empty_cycle_returns_zero(
        self, bridge: BridgeOrchestrator,
    ) -> None:
        result = bridge.cycle()
        assert result.entries_read == 0
        assert result.beads_written == 0

    def test_payload_preserved_end_to_end(
        self, fake_log: FakeGovernanceLog, bridge: BridgeOrchestrator, store: BeadStore,
    ) -> None:
        original_payload = {
            "lease_id": "lease_999", "strategy_ref": "S_vX.Y.Z",
            "bounds_snapshot": {"max_drawdown_pct": 3.14},
        }
        fake_log.append("LEASE_ACTIVATION", original_payload)
        bridge.cycle()

        conn = store.connection
        row = conn.execute("SELECT content FROM beads").fetchone()
        content = json.loads(row["content"])
        assert content["value"]["event_payload"] == original_payload


# ===================================================================
# 7 Banked Bridge Invariants
# ===================================================================

class TestBankedInvariants:
    """All 7 banked invariants from BRIDGE_SPEC_v0.2."""

    def test_INV_BRIDGE_ONE_WAY(
        self, fake_log: FakeGovernanceLog, bridge: BridgeOrchestrator,
    ) -> None:
        """Economy 2 → Economy 1 projection only. Bridge cannot modify Phoenix state."""
        fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})
        bridge.cycle()

        with open(fake_log.log_path) as f:
            lines = [l.strip() for l in f if l.strip()]
        assert len(lines) == 1, "Bridge must not write to Phoenix governance log"
        entry = json.loads(lines[0])
        assert entry["seq"] == 1
        assert entry["event_type"] == "LEASE_ACTIVATION"

    def test_INV_BRIDGE_PULL_NOT_PUSH(
        self, fake_log: FakeGovernanceLog, bridge: BridgeOrchestrator, store: BeadStore,
    ) -> None:
        """Bridge polls Phoenix log. Phoenix never pushes to Bridge."""
        assert store.count() == 0

        fake_log.append("CALIBRATION", {
            "cartridge_ref": "S_v1", "lease_id": "l1", "drift_pct": 0.5, "verdict": "PASS",
        })
        assert store.count() == 0

        bridge.cycle()
        assert store.count() == 1

    def test_INV_BRIDGE_NOT_CONTROL_PLANE(
        self, fake_log: FakeGovernanceLog, bridge: BridgeOrchestrator, store: BeadStore,
    ) -> None:
        """Bridge notarizes. It does not route, filter, or modify."""
        original = {"lease_id": "l1", "strategy_ref": "S_v1", "bounds_snapshot": {"x": 1}}
        fake_log.append("LEASE_ACTIVATION", original)
        bridge.cycle()

        conn = store.connection
        row = conn.execute("SELECT content FROM beads").fetchone()
        content = json.loads(row["content"])
        assert content["value"]["event_payload"] == original

    def test_INV_BRIDGE_IDEMPOTENT_INGESTION(
        self, fake_log: FakeGovernanceLog, state_dir: Path, phoenix_key: bytes,
        bridge_key: bytes, pipeline: IngestionPipeline, store: BeadStore,
    ) -> None:
        """Re-projecting the same event produces no duplicate bead."""
        fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})

        reader = GovernanceLogReader(fake_log.log_path, state_dir, phoenix_key)
        constructor = EnvelopeConstructor(bridge_key=bridge_key)
        mapper = GovernanceMapper(pipeline=pipeline)
        orch = BridgeOrchestrator(reader, constructor, mapper)

        r1 = orch.cycle()
        assert r1.beads_written == 1
        assert store.count() == 1

        reader2 = GovernanceLogReader(fake_log.log_path, state_dir, phoenix_key)
        orch2 = BridgeOrchestrator(reader2, constructor, mapper)
        r2 = orch2.cycle()
        assert r2.duplicates_skipped == 0
        assert r2.entries_read == 0
        assert store.count() == 1

    def test_INV_BRIDGE_GT_MONOTONIC(
        self, fake_log: FakeGovernanceLog, bridge: BridgeOrchestrator, store: BeadStore,
    ) -> None:
        """GT timestamps within a single Bridge stream never decrease."""
        fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})
        fake_log.append("LEASE_EXPIRY", {"lease_id": "l1", "final_stats": {}})
        fake_log.append("ATTESTATION", {"lease_id": "l2", "decision": "RENEW", "new_lease_id": None})

        bridge.cycle()

        conn = store.connection
        rows = conn.execute(
            "SELECT content FROM beads ORDER BY bead_id"
        ).fetchall()

        gt_values = []
        for row in rows:
            content = json.loads(row["content"])
            gt_values.append(content["value"]["gt_timestamp"])

        for i in range(1, len(gt_values)):
            assert gt_values[i] >= gt_values[i - 1], (
                f"GT non-monotonic at index {i}: {gt_values[i]} < {gt_values[i-1]}"
            )

    def test_INV_BRIDGE_NO_SILENT_DROP(
        self, fake_log: FakeGovernanceLog, bridge: BridgeOrchestrator, store: BeadStore,
    ) -> None:
        """Every envelope processed produces either a FACT bead or a FailureStruct."""
        count = _populate_governance_log(fake_log)
        result = bridge.cycle()

        total_outcomes = (
            result.beads_written
            + result.heartbeats
            + result.duplicates_skipped
        )
        assert total_outcomes == count, (
            f"Silent drop: {count} envelopes but only {total_outcomes} outcomes"
        )

    def test_INV_BRIDGE_PROVENANCE_LAYER(
        self, fake_log: FakeGovernanceLog, bridge: BridgeOrchestrator, store: BeadStore,
    ) -> None:
        """Athena provenance and Bead Field provenance are never conflated."""
        fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})
        bridge.cycle()

        bead = store.get(
            store.connection.execute("SELECT bead_id FROM beads").fetchone()["bead_id"]
        )

        content_value = bead.content.value
        assert "athena_ref" in content_value
        athena_hash = content_value["athena_ref"]["athena_hash"]

        assert bead.hash_self != athena_hash, (
            "Bead hash_self must NOT equal Athena hash — different provenance layers"
        )
        assert bead.source_ref.source_id == "bridge-notary"


# ===================================================================
# Kill Chain: corrupt mid-stream → HALT, no partial projection
# ===================================================================

class TestKillChain:
    def test_corrupt_entry_halts_no_partial_write(
        self, log_dir: Path, state_dir: Path, phoenix_key: bytes,
        bridge_key: bytes, pipeline: IngestionPipeline, store: BeadStore,
    ) -> None:
        """Corrupt mid-stream → HALT, no partial projection."""
        fake_log = FakeGovernanceLog(log_dir, phoenix_key)
        fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})
        fake_log.append("STATE_LOCK", {"lease_id": "l1", "prior_state": "DRAFT",
                                       "prior_state_hash": "x", "requested_transition": "t",
                                       "transition_result": "SUCCESS"})

        lines = fake_log.log_path.read_text().strip().split("\n")
        entry2 = json.loads(lines[1])
        entry2["payload"]["lease_id"] = "TAMPERED"
        lines[1] = json.dumps(entry2, sort_keys=True, separators=(",", ":"))
        fake_log.log_path.write_text("\n".join(lines) + "\n")

        reader = GovernanceLogReader(fake_log.log_path, state_dir, phoenix_key)
        constructor = EnvelopeConstructor(bridge_key=bridge_key)
        mapper = GovernanceMapper(pipeline=pipeline)
        orch = BridgeOrchestrator(reader, constructor, mapper)

        with pytest.raises(BridgeHalt):
            orch.cycle()

        assert store.count() == 0, "No beads should be written on HALT"

    def test_corrupt_checkpoint_halts(
        self, fake_log: FakeGovernanceLog, state_dir: Path,
        phoenix_key: bytes, bridge_key: bytes,
        pipeline: IngestionPipeline, store: BeadStore,
    ) -> None:
        """Corrupt checkpoint → HALT on next cycle."""
        fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})

        reader = GovernanceLogReader(fake_log.log_path, state_dir, phoenix_key)
        constructor = EnvelopeConstructor(bridge_key=bridge_key)
        mapper = GovernanceMapper(pipeline=pipeline)
        orch = BridgeOrchestrator(reader, constructor, mapper)

        orch.cycle()
        assert store.count() == 1

        checkpoint = state_dir / "bridge_checkpoint.json"
        data = json.loads(checkpoint.read_text())
        data["last_read_seq"] = 999
        checkpoint.write_text(json.dumps(data))

        from bridge.state_store import BridgeStateError

        with pytest.raises(BridgeStateError, match="hash mismatch"):
            GovernanceLogReader(fake_log.log_path, state_dir, phoenix_key)

    def test_wrong_phoenix_key_halts(
        self, fake_log: FakeGovernanceLog, state_dir: Path,
        bridge_key: bytes, pipeline: IngestionPipeline,
    ) -> None:
        """Wrong Phoenix key → signature verification fails → HALT."""
        fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})

        wrong_key = secrets.token_bytes(32)
        reader = GovernanceLogReader(fake_log.log_path, state_dir, wrong_key)
        constructor = EnvelopeConstructor(bridge_key=bridge_key)
        mapper = GovernanceMapper(pipeline=pipeline)
        orch = BridgeOrchestrator(reader, constructor, mapper)

        with pytest.raises(BridgeHalt):
            orch.cycle()

        assert pipeline.store.count() == 0


# ===================================================================
# Checkpoint ordering — the critical property
# ===================================================================

class TestCheckpointOrdering:
    """INV-BRIDGE-CHECKPOINT-AFTER-WRITE"""

    def test_checkpoint_after_write_not_after_read(
        self, fake_log: FakeGovernanceLog, bridge: BridgeOrchestrator,
    ) -> None:
        """Verify checkpoint only advances after mapper confirms."""
        fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})
        fake_log.append("LEASE_EXPIRY", {"lease_id": "l1", "final_stats": {}})

        assert bridge.reader.state.last_read_seq == 0

        bridge.cycle()

        assert bridge.reader.state.last_read_seq == 2

    def test_crash_between_read_and_write_replays(
        self, log_dir: Path, state_dir: Path, phoenix_key: bytes,
        bridge_key: bytes, bead_keys, store: BeadStore,
    ) -> None:
        """If crash after read but before checkpoint, restart replays."""
        fake_log = FakeGovernanceLog(log_dir, phoenix_key)
        fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})
        fake_log.append("LEASE_EXPIRY", {"lease_id": "l1", "final_stats": {}})

        reader = GovernanceLogReader(fake_log.log_path, state_dir, phoenix_key)
        poll_result = reader.poll()
        assert len(poll_result.entries) == 2

        reader2 = GovernanceLogReader(fake_log.log_path, state_dir, phoenix_key)
        poll_result2 = reader2.poll()
        assert len(poll_result2.entries) == 2, "Without checkpoint, restart replays"

        pipeline = IngestionPipeline(store, bead_keys)
        constructor = EnvelopeConstructor(bridge_key=bridge_key)
        mapper = GovernanceMapper(pipeline=pipeline)
        orch = BridgeOrchestrator(reader2, constructor, mapper)
        orch.cycle()

        assert store.count() == 2
        assert orch.reader.state.last_read_seq == 2
