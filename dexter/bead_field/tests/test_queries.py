"""Test bi-temporal queries — the physics experiment proves itself (Phase E).

Gate 1 exit criterion EC1:
"Show all FACT beads about EURUSD that we knew on Jan 1 about Q4 2025" → correct results
"""

import pytest
from datetime import datetime, timezone, timedelta

from bead_field.schema.enums import BeadType, TemporalClass
from bead_field.schema.fact import FactBead
from bead_field.schema.claim import ClaimBead
from bead_field.integrity.chain import append_to_chain
from bead_field.integrity.signing import KeyManager, sign_hash
from bead_field.store.bitemporal import BeadStore
from bead_field.store.queries import (
    query_by_wt_range,
    query_by_kt_asof,
    query_by_type_and_wt,
    query_by_kt_asof_and_wt_range,
    query_by_lineage,
    query_pattern_beads,
    refinery_latency,
)

from bead_field.tests.conftest import (
    make_core_fields, make_fact_content, make_claim_content, make_bead_id,
)


@pytest.fixture
def keys():
    return KeyManager.generate()


@pytest.fixture
def store():
    s = BeadStore(":memory:")
    yield s
    s.close()


def _sign_and_insert(store, bead, keys):
    linked = append_to_chain(bead)
    ecdsa_sig, pqc_sig = sign_hash(linked.hash_self, keys)
    signed = linked.model_copy(
        update={"attestation": linked.attestation.model_copy(
            update={"ecdsa_sig": ecdsa_sig, "pqc_sig": pqc_sig}
        )}
    )
    store.insert(signed)
    return signed


Q4_START = datetime(2025, 10, 1, tzinfo=timezone.utc)
Q4_END = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
JAN_1_2026 = datetime(2026, 1, 1, tzinfo=timezone.utc)
FEB_1_2026 = datetime(2026, 2, 1, tzinfo=timezone.utc)
NOV_15 = datetime(2025, 11, 15, 14, 0, 0, tzinfo=timezone.utc)
DEC_20 = datetime(2025, 12, 20, 10, 0, 0, tzinfo=timezone.utc)


class TestGate1ExitCriterionEC1:
    """EC1: "Show all FACT beads about EURUSD that we knew on Jan 1 about Q4 2025"."""

    def test_ec1_query_returns_correct_results(self, store, keys):
        # FACT about EURUSD in Q4 2025, learned before Jan 1
        bead_q4 = FactBead(
            **make_core_fields(
                BeadType.FACT,
                world_time_valid_from=NOV_15,
                world_time_valid_to=NOV_15,
                knowledge_time_recorded_at=DEC_20,
            ),
            content=make_fact_content(symbol="EURUSD", value=1.0847),
        )
        inserted_q4 = _sign_and_insert(store, bead_q4, keys)

        # FACT about EURUSD in Q4 2025, learned AFTER Jan 1 (should NOT appear)
        bead_late = FactBead(
            **make_core_fields(
                BeadType.FACT,
                world_time_valid_from=DEC_20,
                world_time_valid_to=DEC_20,
                knowledge_time_recorded_at=FEB_1_2026,
            ),
            content=make_fact_content(symbol="EURUSD", value=1.0900),
        )
        _sign_and_insert(store, bead_late, keys)

        # FACT about GBPUSD in Q4 2025 (wrong symbol, should NOT appear for typed query)
        bead_gbp = FactBead(
            **make_core_fields(
                BeadType.FACT,
                world_time_valid_from=NOV_15,
                world_time_valid_to=NOV_15,
                knowledge_time_recorded_at=DEC_20,
            ),
            content=make_fact_content(symbol="GBPUSD", value=1.2650),
        )
        _sign_and_insert(store, bead_gbp, keys)

        results = query_by_kt_asof_and_wt_range(
            store.connection,
            kt_asof=JAN_1_2026,
            wt_from=Q4_START,
            wt_to=Q4_END,
            bead_type="FACT",
        )

        assert len(results) == 2
        symbols = {r.content.symbol for r in results}
        assert "EURUSD" in symbols
        assert "GBPUSD" in symbols

    def test_ec1_excludes_late_knowledge(self, store, keys):
        bead = FactBead(
            **make_core_fields(
                BeadType.FACT,
                world_time_valid_from=NOV_15,
                world_time_valid_to=NOV_15,
                knowledge_time_recorded_at=FEB_1_2026,
            ),
            content=make_fact_content(),
        )
        _sign_and_insert(store, bead, keys)

        results = query_by_kt_asof_and_wt_range(
            store.connection, kt_asof=JAN_1_2026, wt_from=Q4_START, wt_to=Q4_END,
        )
        assert len(results) == 0


class TestWtRangeQueries:
    def test_overlapping_wt(self, store, keys):
        now = datetime.now(timezone.utc)
        bead = FactBead(
            **make_core_fields(
                BeadType.FACT,
                world_time_valid_from=now - timedelta(hours=2),
                world_time_valid_to=now,
            ),
            content=make_fact_content(),
        )
        _sign_and_insert(store, bead, keys)

        results = query_by_wt_range(
            store.connection,
            wt_from=now - timedelta(hours=3),
            wt_to=now - timedelta(hours=1),
        )
        assert len(results) == 1

    def test_non_overlapping_wt(self, store, keys):
        now = datetime.now(timezone.utc)
        bead = FactBead(
            **make_core_fields(
                BeadType.FACT,
                world_time_valid_from=now - timedelta(hours=2),
                world_time_valid_to=now - timedelta(hours=1),
            ),
            content=make_fact_content(),
        )
        _sign_and_insert(store, bead, keys)

        results = query_by_wt_range(
            store.connection,
            wt_from=now + timedelta(hours=1),
            wt_to=now + timedelta(hours=2),
        )
        assert len(results) == 0

    def test_pattern_beads_excluded_from_wt_query(self, store, keys):
        bead = ClaimBead(
            **make_core_fields(BeadType.CLAIM, TemporalClass.PATTERN),
            content=make_claim_content(),
        )
        _sign_and_insert(store, bead, keys)

        results = query_by_wt_range(
            store.connection,
            wt_from=datetime(2020, 1, 1, tzinfo=timezone.utc),
            wt_to=datetime(2030, 1, 1, tzinfo=timezone.utc),
        )
        assert len(results) == 0


class TestKtAsofQueries:
    def test_asof_filters_by_knowledge_time(self, store, keys):
        now = datetime.now(timezone.utc)
        early = FactBead(
            **make_core_fields(BeadType.FACT, knowledge_time_recorded_at=now - timedelta(days=2)),
            content=make_fact_content(symbol="EARLY"),
        )
        late = FactBead(
            **make_core_fields(BeadType.FACT, knowledge_time_recorded_at=now),
            content=make_fact_content(symbol="LATE"),
        )
        _sign_and_insert(store, early, keys)
        _sign_and_insert(store, late, keys)

        results = query_by_kt_asof(store.connection, now - timedelta(days=1))
        assert len(results) == 1
        assert results[0].content.symbol == "EARLY"


class TestTypeAndWtQueries:
    def test_filters_by_type(self, store, keys):
        now = datetime.now(timezone.utc)
        fact = FactBead(
            **make_core_fields(BeadType.FACT, world_time_valid_from=now, world_time_valid_to=now),
            content=make_fact_content(),
        )
        _sign_and_insert(store, fact, keys)

        results = query_by_type_and_wt(store.connection, "CLAIM", now - timedelta(hours=1), now + timedelta(hours=1))
        assert len(results) == 0

        results = query_by_type_and_wt(store.connection, "FACT", now - timedelta(hours=1), now + timedelta(hours=1))
        assert len(results) == 1


class TestLineageQueries:
    def test_find_dependents(self, store, keys):
        ancestor_id = make_bead_id()
        child = FactBead(
            **make_core_fields(BeadType.FACT, lineage=[ancestor_id]),
            content=make_fact_content(),
        )
        signed = _sign_and_insert(store, child, keys)

        results = query_by_lineage(store.connection, ancestor_id)
        assert len(results) == 1
        assert ancestor_id in results[0].lineage

    def test_no_dependents(self, store, keys):
        bead = FactBead(
            **make_core_fields(BeadType.FACT),
            content=make_fact_content(),
        )
        _sign_and_insert(store, bead, keys)

        results = query_by_lineage(store.connection, "nonexistent-ancestor")
        assert len(results) == 0


class TestPatternBeadQueries:
    def test_query_pattern_beads(self, store, keys):
        claim = ClaimBead(
            **make_core_fields(BeadType.CLAIM, TemporalClass.PATTERN),
            content=make_claim_content(),
        )
        _sign_and_insert(store, claim, keys)

        results = query_pattern_beads(store.connection)
        assert len(results) == 1
        assert results[0].temporal_class == TemporalClass.PATTERN

    def test_pattern_query_filters_by_type(self, store, keys):
        claim = ClaimBead(
            **make_core_fields(BeadType.CLAIM, TemporalClass.PATTERN),
            content=make_claim_content(),
        )
        _sign_and_insert(store, claim, keys)

        results = query_pattern_beads(store.connection, bead_type="FACT")
        assert len(results) == 0


class TestRefineryLatency:
    def test_computes_latency(self, store, keys):
        now = datetime.now(timezone.utc)
        wt_end = now - timedelta(seconds=5)
        bead = FactBead(
            **make_core_fields(
                BeadType.FACT,
                world_time_valid_from=wt_end - timedelta(seconds=10),
                world_time_valid_to=wt_end,
                knowledge_time_recorded_at=now,
            ),
            content=make_fact_content(),
        )
        signed = _sign_and_insert(store, bead, keys)

        latency = refinery_latency(store.connection, signed.bead_id)
        assert latency is not None
        assert abs(latency - 5.0) < 1.0

    def test_pattern_bead_returns_none(self, store, keys):
        claim = ClaimBead(
            **make_core_fields(BeadType.CLAIM, TemporalClass.PATTERN),
            content=make_claim_content(),
        )
        signed = _sign_and_insert(store, claim, keys)

        latency = refinery_latency(store.connection, signed.bead_id)
        assert latency is None

    def test_nonexistent_bead_returns_none(self, store):
        assert refinery_latency(store.connection, "nonexistent") is None


class TestEmptyDbEdgeCases:
    def test_wt_range_empty_db(self, store):
        now = datetime.now(timezone.utc)
        results = query_by_wt_range(store.connection, now, now)
        assert results == []

    def test_kt_asof_empty_db(self, store):
        now = datetime.now(timezone.utc)
        results = query_by_kt_asof(store.connection, now)
        assert results == []

    def test_pattern_beads_empty_db(self, store):
        results = query_pattern_beads(store.connection)
        assert results == []
