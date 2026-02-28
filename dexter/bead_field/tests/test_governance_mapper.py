"""
Tests for governance mapper — BRIDGE_SPEC_v0.2 Section 5.

Covers:
  - Envelope → FACT bead mapping (all 13 event types)
  - Field preservation (payload, athena_ref in content.value)
  - Tag contract (src:governance, gov_event:{type}, gov:lease_id, etc.)
  - Source type mapping (HUMAN vs AGENT deterministic)
  - Provenance layer separation (Athena pass-through vs bead field native)
  - Duplicate detection (replay guard on Dexter side)
  - HEARTBEAT pre-filter (not a bead)
  - Invalid envelope rejection (fail-closed)
  - Tag-based governance identification (query path)
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from bead_field.ingestion.governance_mapper import (
    BRIDGE_SOURCE_ID,
    SOURCE_TYPE_MAP,
    GovernanceMapper,
    GovernanceMapperError,
    HeartbeatReceived,
)
from bead_field.ingestion.pipeline import IngestionPipeline
from bead_field.integrity.signing import KeyManager
from bead_field.schema.enums import BeadType, SourceType, TemporalClass
from bead_field.store.bitemporal import BeadStore
from bridge.types import BridgeEnvelope, PHOENIX_GOVERNANCE_EVENTS


# --- Fixtures ---

@pytest.fixture()
def keys():
    return KeyManager.generate()


@pytest.fixture()
def store():
    s = BeadStore(":memory:")
    yield s
    s.close()


@pytest.fixture()
def pipeline(store, keys):
    return IngestionPipeline(store, keys)


@pytest.fixture()
def mapper(pipeline):
    return GovernanceMapper(pipeline)


def _make_envelope(
    event_type: str = "LEASE_ACTIVATION",
    payload: dict[str, Any] | None = None,
    replay_guard: int = 1,
    gt_timestamp: str | None = None,
) -> BridgeEnvelope:
    if payload is None:
        payload = {"lease_id": "lease_001", "strategy_ref": "STRAT_v1.0.0", "bounds_snapshot": {}}
    return BridgeEnvelope(
        version="0.1.0",
        event_id="evt_" + event_type.lower() + f"_{replay_guard}",
        event_type=event_type,
        payload=payload,
        gt_timestamp=gt_timestamp or datetime.now(UTC).isoformat(),
        athena_ref={"athena_hash": "a" * 64, "athena_index": replay_guard},
        source_signature={"sig": "test_sig", "algorithm": "hmac-sha256", "key_id": "phoenix-gov-v1"},
        hash_chain_proof={"hash_self": "b" * 64, "hash_prev": "c" * 64, "merkle_proof": None, "merkle_status": "DEFERRED"},
        replay_guard=replay_guard,
        bridge_seal={"bridge_sig": "d" * 64, "bridge_key_id": "bridge-v1", "sealed_at": datetime.now(UTC).isoformat(), "bridge_version": "0.1.0"},
    )


# --- Mapping tests for all 13 event types ---

class TestEventTypeMapping:
    """All 13 governance events should map to FACT beads."""

    @pytest.mark.parametrize("event_type", sorted(PHOENIX_GOVERNANCE_EVENTS))
    def test_all_governance_events_ingest(self, mapper: GovernanceMapper, event_type: str) -> None:
        envelope = _make_envelope(event_type=event_type, replay_guard=1)
        result = mapper.map_and_ingest(envelope)
        assert result is not None
        assert not isinstance(result, HeartbeatReceived)
        assert result.success, f"Failed for {event_type}: {result.error}"
        assert result.bead.bead_type == BeadType.FACT

    def test_event_count_is_13(self) -> None:
        assert len(PHOENIX_GOVERNANCE_EVENTS) == 13


class TestFieldPreservation:
    """Payload, athena_ref, gt_timestamp preserved in FACT bead content."""

    def test_payload_preserved_in_value(self, mapper: GovernanceMapper) -> None:
        payload = {"lease_id": "l99", "strategy_ref": "S_v2.0.0", "bounds_snapshot": {"max_dd": 5.0}}
        envelope = _make_envelope(payload=payload)
        result = mapper.map_and_ingest(envelope)
        assert result.success

        content = result.bead.content
        assert content.field == "LEASE_ACTIVATION"
        assert content.symbol == "GOVERNANCE"
        assert content.value["event_payload"] == payload

    def test_athena_ref_in_value(self, mapper: GovernanceMapper) -> None:
        envelope = _make_envelope()
        result = mapper.map_and_ingest(envelope)

        value = result.bead.content.value
        assert "athena_ref" in value
        assert value["athena_ref"]["athena_hash"] == "a" * 64
        assert value["athena_ref"]["athena_index"] == 1

    def test_gt_timestamp_in_value(self, mapper: GovernanceMapper) -> None:
        ts = "2026-02-28T14:30:00+00:00"
        envelope = _make_envelope(gt_timestamp=ts)
        result = mapper.map_and_ingest(envelope)

        value = result.bead.content.value
        assert value["gt_timestamp"] == ts

    def test_event_id_in_value(self, mapper: GovernanceMapper) -> None:
        envelope = _make_envelope()
        result = mapper.map_and_ingest(envelope)

        value = result.bead.content.value
        assert value["event_id"] == envelope.event_id

    def test_replay_guard_in_value(self, mapper: GovernanceMapper) -> None:
        envelope = _make_envelope(replay_guard=42)
        result = mapper.map_and_ingest(envelope)

        value = result.bead.content.value
        assert value["replay_guard"] == 42


class TestTagContract:
    """Section 5.1 tagging contract: src:governance + gov_event:{TYPE}."""

    def test_required_tags_present(self, mapper: GovernanceMapper) -> None:
        envelope = _make_envelope(event_type="CALIBRATION")
        result = mapper.map_and_ingest(envelope)

        tags = result.bead.tags
        assert "src:governance" in tags
        assert "gov_event:CALIBRATION" in tags

    def test_lease_id_tag_extracted(self, mapper: GovernanceMapper) -> None:
        envelope = _make_envelope(payload={"lease_id": "lease_007"})
        result = mapper.map_and_ingest(envelope)

        assert "gov:lease_id:lease_007" in result.bead.tags

    def test_cartridge_ref_tag_extracted(self, mapper: GovernanceMapper) -> None:
        envelope = _make_envelope(
            event_type="CARTRIDGE_INSERTION",
            payload={"cartridge_ref": "STRAT_v3.0.0", "hash": "xyz", "linter_result": "PASS"},
        )
        result = mapper.map_and_ingest(envelope)

        assert "gov:cartridge_ref:STRAT_v3.0.0" in result.bead.tags

    def test_strategy_ref_tag_extracted(self, mapper: GovernanceMapper) -> None:
        envelope = _make_envelope(payload={"lease_id": "l1", "strategy_ref": "S_v1.0.0", "bounds_snapshot": {}})
        result = mapper.map_and_ingest(envelope)

        assert "gov:strategy_ref:S_v1.0.0" in result.bead.tags

    def test_no_extra_tags_for_minimal_payload(self, mapper: GovernanceMapper) -> None:
        envelope = _make_envelope(
            event_type="CEREMONY",
            payload={"participants": ["Olya"], "summary": "renewal", "decisions": []},
        )
        result = mapper.map_and_ingest(envelope)

        tags = result.bead.tags
        gov_specific = [t for t in tags if t.startswith("gov:")]
        assert gov_specific == []


class TestSourceTypeMapping:
    """Amendment 13: deterministic HUMAN/AGENT per event type."""

    HUMAN_EVENTS = {"ATTESTATION", "CEREMONY", "LEASE_REVOCATION", "STRATEGY_DEPRECATION", "EMERGENCY_EJECT"}
    AGENT_EVENTS = PHOENIX_GOVERNANCE_EVENTS - HUMAN_EVENTS

    @pytest.mark.parametrize("event_type", sorted(HUMAN_EVENTS))
    def test_human_events(self, mapper: GovernanceMapper, event_type: str) -> None:
        envelope = _make_envelope(event_type=event_type)
        result = mapper.map_and_ingest(envelope)
        assert result.success
        assert result.bead.source_ref.source_type == SourceType.HUMAN

    @pytest.mark.parametrize("event_type", sorted(AGENT_EVENTS))
    def test_agent_events(self, mapper: GovernanceMapper, event_type: str) -> None:
        envelope = _make_envelope(event_type=event_type)
        result = mapper.map_and_ingest(envelope)
        assert result.success
        assert result.bead.source_ref.source_type == SourceType.AGENT

    def test_source_type_map_exhaustive(self) -> None:
        """Every governance event has exactly one source_type mapping."""
        for et in PHOENIX_GOVERNANCE_EVENTS:
            assert et in SOURCE_TYPE_MAP, f"Missing SOURCE_TYPE_MAP entry: {et}"

    def test_source_id_is_bridge_notary(self, mapper: GovernanceMapper) -> None:
        envelope = _make_envelope()
        result = mapper.map_and_ingest(envelope)
        assert result.bead.source_ref.source_id == BRIDGE_SOURCE_ID

    def test_source_version_from_envelope(self, mapper: GovernanceMapper) -> None:
        envelope = _make_envelope()
        result = mapper.map_and_ingest(envelope)
        assert result.bead.source_ref.source_version == "0.1.0"


class TestProvenanceLayerSeparation:
    """INV-BRIDGE-PROVENANCE-LAYER: Athena pass-through vs bead field native."""

    def test_athena_ref_not_in_bead_metadata(self, mapper: GovernanceMapper) -> None:
        """Athena ref lives in content.value, NOT in bead-level fields."""
        envelope = _make_envelope()
        result = mapper.map_and_ingest(envelope)
        bead = result.bead

        assert bead.content.value["athena_ref"]["athena_hash"] == "a" * 64
        assert bead.hash_self != "a" * 64

    def test_bead_has_own_hash_chain(self, mapper: GovernanceMapper) -> None:
        """Bead field provenance: hash_self, hash_prev computed by pipeline."""
        e1 = _make_envelope(event_type="LEASE_ACTIVATION", replay_guard=1)
        e2 = _make_envelope(event_type="LEASE_EXPIRY", replay_guard=2,
                            payload={"lease_id": "l1", "final_stats": {}})

        r1 = mapper.map_and_ingest(e1)
        r2 = mapper.map_and_ingest(e2)

        assert r1.bead.hash_self != ""
        assert r2.bead.hash_self != ""
        assert r2.bead.hash_prev == r1.bead.hash_self

    def test_lineage_traces_to_bridge(self, mapper: GovernanceMapper) -> None:
        envelope = _make_envelope()
        result = mapper.map_and_ingest(envelope)

        assert any("bridge:event_id:" in lin for lin in result.bead.lineage)

    def test_temporal_class_is_observation(self, mapper: GovernanceMapper) -> None:
        envelope = _make_envelope()
        result = mapper.map_and_ingest(envelope)
        assert result.bead.temporal_class == TemporalClass.OBSERVATION


class TestReplayGuard:
    """Duplicate detection via replay_guard on Dexter side."""

    def test_duplicate_returns_none(self, mapper: GovernanceMapper) -> None:
        e1 = _make_envelope(replay_guard=1)
        e2 = _make_envelope(replay_guard=1)

        r1 = mapper.map_and_ingest(e1)
        r2 = mapper.map_and_ingest(e2)

        assert r1 is not None and r1.success
        assert r2 is None

    def test_old_replay_guard_returns_none(self, mapper: GovernanceMapper) -> None:
        e1 = _make_envelope(replay_guard=5)
        e2 = _make_envelope(replay_guard=3)

        mapper.map_and_ingest(e1)
        result = mapper.map_and_ingest(e2)
        assert result is None

    def test_increasing_replay_guard_ingests(self, mapper: GovernanceMapper) -> None:
        for i in range(1, 6):
            envelope = _make_envelope(replay_guard=i)
            result = mapper.map_and_ingest(envelope)
            assert result is not None and result.success

        assert mapper.last_replay_guard == 5

    def test_state_persists_to_file(self, pipeline: IngestionPipeline, tmp_path: Path) -> None:
        state_path = tmp_path / "mapper_state.json"
        mapper = GovernanceMapper(pipeline, state_path=state_path)

        mapper.map_and_ingest(_make_envelope(replay_guard=7))
        assert state_path.exists()

        data = json.loads(state_path.read_text())
        assert data["last_replay_guard"] == 7

    def test_state_survives_restart(self, pipeline: IngestionPipeline, tmp_path: Path) -> None:
        state_path = tmp_path / "mapper_state.json"

        m1 = GovernanceMapper(pipeline, state_path=state_path)
        m1.map_and_ingest(_make_envelope(replay_guard=3))

        m2 = GovernanceMapper(pipeline, state_path=state_path)
        assert m2.last_replay_guard == 3

        result = m2.map_and_ingest(_make_envelope(replay_guard=3))
        assert result is None


class TestHeartbeatFilter:
    """HEARTBEAT: pre-mapper filter, metric update only, never a bead."""

    def test_heartbeat_returns_sentinel(self, mapper: GovernanceMapper) -> None:
        envelope = _make_envelope(event_type="HEARTBEAT", payload={})
        result = mapper.map_and_ingest(envelope)
        assert isinstance(result, HeartbeatReceived)

    def test_heartbeat_does_not_create_bead(self, mapper: GovernanceMapper, store: BeadStore) -> None:
        envelope = _make_envelope(event_type="HEARTBEAT", payload={})
        mapper.map_and_ingest(envelope)
        assert store.count() == 0

    def test_heartbeat_count_tracked(self, mapper: GovernanceMapper) -> None:
        for i in range(3):
            mapper.map_and_ingest(_make_envelope(event_type="HEARTBEAT", payload={}, replay_guard=i + 1))
        assert mapper.heartbeat_count == 3

    def test_heartbeat_carries_gt(self, mapper: GovernanceMapper) -> None:
        ts = "2026-02-28T12:00:00+00:00"
        envelope = _make_envelope(event_type="HEARTBEAT", payload={}, gt_timestamp=ts)
        result = mapper.map_and_ingest(envelope)
        assert result.gt_timestamp == ts


class TestRejection:
    """Invalid envelopes rejected at boundary."""

    def test_unknown_event_type_raises(self, mapper: GovernanceMapper) -> None:
        envelope = _make_envelope(event_type="INVENTED_EVENT")
        with pytest.raises(GovernanceMapperError, match="Unknown event_type"):
            mapper.map_and_ingest(envelope)

    def test_unknown_event_does_not_create_bead(self, mapper: GovernanceMapper, store: BeadStore) -> None:
        try:
            mapper.map_and_ingest(_make_envelope(event_type="INVENTED_EVENT"))
        except GovernanceMapperError:
            pass
        assert store.count() == 0


class TestTagQuery:
    """Tag-based governance identification for post-freeze enum migration."""

    def test_governance_beads_identifiable_by_tag(self, mapper: GovernanceMapper, store: BeadStore) -> None:
        mapper.map_and_ingest(_make_envelope(event_type="LEASE_ACTIVATION", replay_guard=1))
        mapper.map_and_ingest(_make_envelope(event_type="ATTESTATION", replay_guard=2))

        conn = store.connection
        rows = conn.execute(
            "SELECT tags FROM beads WHERE tags LIKE ?", ('%src:governance%',)
        ).fetchall()
        assert len(rows) == 2

    def test_filter_by_event_type_tag(self, mapper: GovernanceMapper, store: BeadStore) -> None:
        mapper.map_and_ingest(_make_envelope(event_type="LEASE_ACTIVATION", replay_guard=1))
        mapper.map_and_ingest(_make_envelope(event_type="CALIBRATION", replay_guard=2,
                                             payload={"cartridge_ref": "S_v1", "lease_id": "l1", "drift_pct": 1.0, "verdict": "PASS"}))
        mapper.map_and_ingest(_make_envelope(event_type="LEASE_EXPIRY", replay_guard=3,
                                             payload={"lease_id": "l1", "final_stats": {}}))

        conn = store.connection
        lease_rows = conn.execute(
            "SELECT tags FROM beads WHERE tags LIKE ?", ('%gov_event:LEASE_%',)
        ).fetchall()
        assert len(lease_rows) == 2

    def test_filter_by_lease_id_tag(self, mapper: GovernanceMapper, store: BeadStore) -> None:
        mapper.map_and_ingest(_make_envelope(replay_guard=1, payload={"lease_id": "l_alpha"}))
        mapper.map_and_ingest(_make_envelope(replay_guard=2, payload={"lease_id": "l_beta"}))

        conn = store.connection
        rows = conn.execute(
            "SELECT tags FROM beads WHERE tags LIKE ?", ('%gov:lease_id:l_alpha%',)
        ).fetchall()
        assert len(rows) == 1
