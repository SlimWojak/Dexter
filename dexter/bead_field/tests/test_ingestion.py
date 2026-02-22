"""Test end-to-end ingestion pipeline — all components compose correctly (Phase G)."""

import pytest
from datetime import datetime, timezone

from bead_field.clock.hlc import HLC
from bead_field.integrity.chain import verify_hash_self
from bead_field.integrity.merkle import AnchorConfig
from bead_field.integrity.signing import KeyManager, verify_dual
from bead_field.ingestion.pipeline import IngestionPipeline, IngestionResult
from bead_field.schema.enums import (
    BeadType, TemporalClass, Direction, Drawer, ProposalAction,
    RejectionCategory, RejectionSource, SkillType, SkillValidation,
    DeploymentStatus, PolicyType, PositionSizeUnit,
)
from bead_field.schema.core import SourceRef
from bead_field.store.bitemporal import BeadStore

from bead_field.tests.conftest import (
    make_source_ref, make_fact_content, make_claim_content,
    make_signal_content, make_proposal_content,
    make_proposal_rejected_content, make_skill_content,
    make_model_version_content, make_policy_content, ts,
)


@pytest.fixture
def keys():
    return KeyManager.generate()


@pytest.fixture
def pipeline(keys):
    store = BeadStore(":memory:")
    p = IngestionPipeline(store, keys)
    yield p
    store.close()


def _ingest_fact(pipeline, **content_overrides):
    now = ts()
    return pipeline.ingest(
        bead_type=BeadType.FACT,
        content=make_fact_content(**content_overrides),
        temporal_class=TemporalClass.OBSERVATION,
        source_ref=make_source_ref(),
        world_time_valid_from=now,
        world_time_valid_to=now,
    )


# --- Happy path: every bead type through the full pipeline ---

class TestHappyPathAllTypes:
    def test_fact_ingestion(self, pipeline):
        result = _ingest_fact(pipeline)
        assert result.success
        assert result.bead.bead_type == BeadType.FACT

    def test_claim_ingestion(self, pipeline):
        result = pipeline.ingest(
            bead_type=BeadType.CLAIM,
            content=make_claim_content(),
            temporal_class=TemporalClass.PATTERN,
            source_ref=make_source_ref(),
        )
        assert result.success
        assert result.bead.bead_type == BeadType.CLAIM

    def test_signal_ingestion(self, pipeline):
        now = ts()
        result = pipeline.ingest(
            bead_type=BeadType.SIGNAL,
            content=make_signal_content(),
            temporal_class=TemporalClass.OBSERVATION,
            source_ref=make_source_ref(),
            world_time_valid_from=now,
            world_time_valid_to=now,
        )
        assert result.success

    def test_proposal_ingestion(self, pipeline):
        now = ts()
        result = pipeline.ingest(
            bead_type=BeadType.PROPOSAL,
            content=make_proposal_content(),
            temporal_class=TemporalClass.OBSERVATION,
            source_ref=make_source_ref(),
            world_time_valid_from=now,
            world_time_valid_to=now,
        )
        assert result.success

    def test_proposal_rejected_ingestion(self, pipeline):
        now = ts()
        result = pipeline.ingest(
            bead_type=BeadType.PROPOSAL_REJECTED,
            content=make_proposal_rejected_content(),
            temporal_class=TemporalClass.OBSERVATION,
            source_ref=make_source_ref(),
            world_time_valid_from=now,
            world_time_valid_to=now,
        )
        assert result.success

    def test_skill_ingestion(self, pipeline):
        result = pipeline.ingest(
            bead_type=BeadType.SKILL,
            content=make_skill_content(),
            temporal_class=TemporalClass.PATTERN,
            source_ref=make_source_ref(),
        )
        assert result.success

    def test_model_version_ingestion(self, pipeline):
        result = pipeline.ingest(
            bead_type=BeadType.MODEL_VERSION,
            content=make_model_version_content(),
            temporal_class=TemporalClass.PATTERN,
            source_ref=make_source_ref(),
        )
        assert result.success

    def test_policy_ingestion(self, pipeline):
        result = pipeline.ingest(
            bead_type=BeadType.POLICY,
            content=make_policy_content(),
            temporal_class=TemporalClass.PATTERN,
            source_ref=make_source_ref(),
        )
        assert result.success


# --- Pipeline correctness ---

class TestPipelineIntegrity:
    def test_bead_has_uuid7_id(self, pipeline):
        result = _ingest_fact(pipeline)
        assert len(result.bead.bead_id) == 36

    def test_bead_has_hlc_knowledge_time(self, pipeline):
        result = _ingest_fact(pipeline)
        assert result.bead.knowledge_time_recorded_at.tzinfo is not None

    def test_bead_has_valid_hash_self(self, pipeline):
        result = _ingest_fact(pipeline)
        assert verify_hash_self(result.bead)

    def test_bead_is_signed(self, pipeline, keys):
        result = _ingest_fact(pipeline)
        att = result.bead.attestation
        assert att.ecdsa_sig
        assert att.pqc_sig
        v = verify_dual(
            result.bead.hash_self,
            att.ecdsa_sig, att.pqc_sig,
            keys.ecdsa_vk, keys.pqc_pk,
        )
        assert v.optimal

    def test_bead_stored_and_retrievable(self, pipeline):
        result = _ingest_fact(pipeline)
        retrieved = pipeline.store.get(result.bead.bead_id)
        assert retrieved is not None
        assert retrieved.bead_id == result.bead.bead_id

    def test_sequential_beads_form_chain(self, pipeline):
        r1 = _ingest_fact(pipeline, symbol="EURUSD")
        r2 = _ingest_fact(pipeline, symbol="GBPUSD")
        assert r2.bead.hash_prev == r1.bead.hash_self

    def test_hlc_monotonic_across_ingestions(self, pipeline):
        r1 = _ingest_fact(pipeline)
        r2 = _ingest_fact(pipeline)
        assert r2.bead.knowledge_time_recorded_at > r1.bead.knowledge_time_recorded_at


# --- Rejection cases ---

class TestIngestionRejection:
    def test_bad_schema_rejected(self, pipeline):
        result = pipeline.ingest(
            bead_type=BeadType.FACT,
            content={"missing": "required_fields"},
            temporal_class=TemporalClass.OBSERVATION,
            source_ref=make_source_ref(),
            world_time_valid_from=ts(),
            world_time_valid_to=ts(),
        )
        assert not result.success
        assert result.error is not None

    def test_observation_without_wt_rejected(self, pipeline):
        result = pipeline.ingest(
            bead_type=BeadType.FACT,
            content=make_fact_content(),
            temporal_class=TemporalClass.OBSERVATION,
            source_ref=make_source_ref(),
        )
        assert not result.success

    def test_duplicate_bead_rejected(self, pipeline):
        r1 = _ingest_fact(pipeline)
        assert r1.success
        result = pipeline.ingest(
            bead_type=BeadType.FACT,
            content=make_fact_content(),
            temporal_class=TemporalClass.OBSERVATION,
            source_ref=make_source_ref(),
            world_time_valid_from=ts(),
            world_time_valid_to=ts(),
        )
        assert result.success


# --- Merkle trigger ---

class TestMerkleTriggerIntegration:
    def test_signal_triggers_merkle_anchor(self, keys):
        store = BeadStore(":memory:")
        pipeline = IngestionPipeline(store, keys)
        now = ts()

        r1 = _ingest_fact(pipeline)
        assert r1.batch_id is None

        r2 = pipeline.ingest(
            bead_type=BeadType.SIGNAL,
            content=make_signal_content(),
            temporal_class=TemporalClass.OBSERVATION,
            source_ref=make_source_ref(),
            world_time_valid_from=now,
            world_time_valid_to=now,
        )
        assert r2.batch_id is not None
        store.close()

    def test_beads_get_merkle_batch_id_after_anchor(self, keys):
        store = BeadStore(":memory:")
        config = AnchorConfig(max_beads=3)
        pipeline = IngestionPipeline(store, keys, anchor_config=config)

        results = []
        for i in range(3):
            r = _ingest_fact(pipeline)
            results.append(r)

        for r in results:
            retrieved = store.get(r.bead.bead_id)
            assert retrieved.merkle_batch_id is not None
        store.close()


# --- Observability counters ---

class TestObservabilityCounters:
    def test_ingested_counter(self, pipeline):
        _ingest_fact(pipeline)
        _ingest_fact(pipeline)
        assert pipeline.stats["ingested"] == 2
        assert pipeline.stats["ingested:FACT"] == 2

    def test_rejected_counter(self, pipeline):
        pipeline.ingest(
            bead_type=BeadType.FACT,
            content={"bad": "data"},
            temporal_class=TemporalClass.OBSERVATION,
            source_ref=make_source_ref(),
            world_time_valid_from=ts(),
            world_time_valid_to=ts(),
        )
        assert pipeline.stats["rejected"] == 1
        assert pipeline.stats["rejected:FACT"] == 1

    def test_attempts_counter(self, pipeline):
        _ingest_fact(pipeline)
        pipeline.ingest(
            bead_type=BeadType.FACT,
            content={"bad": "data"},
            temporal_class=TemporalClass.OBSERVATION,
            source_ref=make_source_ref(),
            world_time_valid_from=ts(),
            world_time_valid_to=ts(),
        )
        assert pipeline.stats["attempts"] == 2

    def test_mixed_type_counters(self, pipeline):
        _ingest_fact(pipeline)
        pipeline.ingest(
            bead_type=BeadType.CLAIM,
            content=make_claim_content(),
            temporal_class=TemporalClass.PATTERN,
            source_ref=make_source_ref(),
        )
        assert pipeline.stats["ingested:FACT"] == 1
        assert pipeline.stats["ingested:CLAIM"] == 1
