"""Test all 8 bead type schemas: construction, validation, rejection, round-trip (Phase A)."""

import pytest
from datetime import datetime, timezone
from uuid6 import uuid7
from pydantic import ValidationError

from bead_field.schema.enums import (
    BeadType, TemporalClass, RejectionCategory, RejectionSource,
    ProposalAction, PositionSizeUnit, Drawer, Direction, SourceType,
)
from bead_field.schema.core import BeadCore, SourceRef, AttestationEnvelope
from bead_field.schema.fact import FactBead, FactContent
from bead_field.schema.claim import ClaimBead
from bead_field.schema.signal import SignalBead
from bead_field.schema.proposal import ProposalBead
from bead_field.schema.proposal_rejected import ProposalRejectedBead
from bead_field.schema.skill import SkillBead
from bead_field.schema.model_version import ModelVersionBead
from bead_field.schema.policy import PolicyBead
from bead_field.schema import parse_bead, BEAD_TYPE_MAP

from bead_field.tests.conftest import (
    make_core_fields, make_bead_id, make_attestation, make_source_ref, ts,
    make_fact_content, make_claim_content, make_signal_content,
    make_proposal_content, make_proposal_rejected_content,
    make_skill_content, make_model_version_content, make_policy_content,
)


# --- Happy path: every bead type constructs ---

class TestFactBead:
    def test_construct_valid(self):
        bead = FactBead(
            **make_core_fields(BeadType.FACT),
            content=make_fact_content(),
        )
        assert bead.bead_type == BeadType.FACT
        assert bead.content.symbol == "EURUSD"

    def test_quality_score_in_range(self):
        bead = FactBead(
            **make_core_fields(BeadType.FACT),
            content=make_fact_content(quality_score=0.95),
        )
        assert bead.content.quality_score == 0.95

    def test_quality_score_rejects_above_1(self):
        with pytest.raises(ValidationError):
            FactBead(
                **make_core_fields(BeadType.FACT),
                content=make_fact_content(quality_score=1.5),
            )

    def test_quality_score_rejects_below_0(self):
        with pytest.raises(ValidationError):
            FactBead(
                **make_core_fields(BeadType.FACT),
                content=make_fact_content(quality_score=-0.1),
            )

    def test_value_accepts_number(self):
        bead = FactBead(
            **make_core_fields(BeadType.FACT),
            content=make_fact_content(value=42),
        )
        assert bead.content.value == 42

    def test_value_accepts_string(self):
        bead = FactBead(
            **make_core_fields(BeadType.FACT),
            content=make_fact_content(value="NFP +256K"),
        )
        assert bead.content.value == "NFP +256K"

    def test_value_accepts_dict(self):
        bead = FactBead(
            **make_core_fields(BeadType.FACT),
            content=make_fact_content(value={"open": 1.08, "close": 1.09}),
        )
        assert isinstance(bead.content.value, dict)


class TestClaimBead:
    def test_construct_valid(self):
        bead = ClaimBead(
            **make_core_fields(BeadType.CLAIM, TemporalClass.PATTERN),
            content=make_claim_content(),
        )
        assert bead.bead_type == BeadType.CLAIM
        assert bead.content.drawer == Drawer.HTF_BIAS

    def test_icm_terms_present(self):
        bead = ClaimBead(
            **make_core_fields(BeadType.CLAIM, TemporalClass.PATTERN),
            content=make_claim_content(),
        )
        assert "OB" in bead.content.icm_terms


class TestSignalBead:
    def test_construct_valid(self):
        bead = SignalBead(
            **make_core_fields(BeadType.SIGNAL),
            content=make_signal_content(),
        )
        assert bead.bead_type == BeadType.SIGNAL
        assert bead.content.direction == Direction.SHORT

    def test_has_risk_profile(self):
        bead = SignalBead(
            **make_core_fields(BeadType.SIGNAL),
            content=make_signal_content(),
        )
        assert bead.content.risk_profile.invalidation


class TestProposalBead:
    def test_construct_valid(self):
        bead = ProposalBead(
            **make_core_fields(BeadType.PROPOSAL),
            content=make_proposal_content(),
        )
        assert bead.bead_type == BeadType.PROPOSAL
        assert bead.content.entry_price == 1.0855


class TestProposalRejectedBead:
    def test_construct_valid_with_policy_ref(self):
        bead = ProposalRejectedBead(
            **make_core_fields(BeadType.PROPOSAL_REJECTED),
            content=make_proposal_rejected_content(),
        )
        assert bead.bead_type == BeadType.PROPOSAL_REJECTED
        assert bead.content.rejection_source == RejectionSource.RISK_ENGINE

    def test_inv_shadow_rich_has_full_proposal_fields(self):
        """INV-SHADOW-RICH: rejected proposal must have all proposal fields."""
        bead = ProposalRejectedBead(
            **make_core_fields(BeadType.PROPOSAL_REJECTED),
            content=make_proposal_rejected_content(),
        )
        assert bead.content.signal_ref
        assert bead.content.action == ProposalAction.ENTER_SHORT
        assert bead.content.instrument == "EURUSD"
        assert bead.content.execution_venue == "IBKR_PAPER"

    def test_inv_rejection_policy_ref_required_for_risk_breach(self):
        """INV-REJECTION-POLICY-REF: RISK_BREACH without policy ref must fail."""
        with pytest.raises(ValidationError, match="rejection_policy_ref"):
            ProposalRejectedBead(
                **make_core_fields(BeadType.PROPOSAL_REJECTED),
                content=make_proposal_rejected_content(
                    rejection_category=RejectionCategory.RISK_BREACH,
                    rejection_policy_ref=None,
                ),
            )

    def test_non_risk_breach_allows_null_policy_ref(self):
        """HUMAN_OVERRIDE does not require policy ref."""
        bead = ProposalRejectedBead(
            **make_core_fields(BeadType.PROPOSAL_REJECTED),
            content=make_proposal_rejected_content(
                rejection_category=RejectionCategory.HUMAN_OVERRIDE,
                rejection_policy_ref=None,
            ),
        )
        assert bead.content.rejection_policy_ref is None


class TestSkillBead:
    def test_construct_valid(self):
        bead = SkillBead(
            **make_core_fields(BeadType.SKILL, TemporalClass.PATTERN),
            content=make_skill_content(),
        )
        assert bead.bead_type == BeadType.SKILL
        assert bead.content.conditions.if_conditions


class TestModelVersionBead:
    def test_construct_valid(self):
        bead = ModelVersionBead(
            **make_core_fields(BeadType.MODEL_VERSION, TemporalClass.PATTERN),
            content=make_model_version_content(),
        )
        assert bead.bead_type == BeadType.MODEL_VERSION
        assert bead.content.version_hash


class TestPolicyBead:
    def test_construct_valid(self):
        bead = PolicyBead(
            **make_core_fields(BeadType.POLICY, TemporalClass.PATTERN),
            content=make_policy_content(),
        )
        assert bead.bead_type == BeadType.POLICY
        assert bead.content.authority == "G"


# --- Temporal class validation ---

class TestTemporalClassValidation:
    def test_observation_requires_world_time(self):
        with pytest.raises(ValidationError, match="OBSERVATION.*requires"):
            FactBead(
                **make_core_fields(
                    BeadType.FACT,
                    TemporalClass.OBSERVATION,
                    world_time_valid_from=None,
                    world_time_valid_to=None,
                ),
                content=make_fact_content(),
            )

    def test_observation_requires_both_fields(self):
        with pytest.raises(ValidationError, match="OBSERVATION.*requires"):
            FactBead(
                **make_core_fields(
                    BeadType.FACT,
                    TemporalClass.OBSERVATION,
                    world_time_valid_from=ts(),
                    world_time_valid_to=None,
                ),
                content=make_fact_content(),
            )

    def test_pattern_requires_null_world_time(self):
        with pytest.raises(ValidationError, match="PATTERN.*requires null"):
            ClaimBead(
                **make_core_fields(
                    BeadType.CLAIM,
                    TemporalClass.PATTERN,
                    world_time_valid_from=ts(),
                    world_time_valid_to=ts(),
                ),
                content=make_claim_content(),
            )

    def test_derived_allows_world_time(self):
        """DERIVED can have world_time (inherited from OBSERVATION inputs)."""
        bead = SignalBead(
            **make_core_fields(
                BeadType.SIGNAL,
                TemporalClass.DERIVED,
                world_time_valid_from=ts(),
                world_time_valid_to=ts(),
            ),
            content=make_signal_content(),
        )
        assert bead.temporal_class == TemporalClass.DERIVED

    def test_derived_allows_null_world_time(self):
        """DERIVED can also have null WT (if all inputs are PATTERN)."""
        bead = SignalBead(
            **make_core_fields(
                BeadType.SIGNAL,
                TemporalClass.DERIVED,
                world_time_valid_from=None,
                world_time_valid_to=None,
            ),
            content=make_signal_content(),
        )
        assert bead.world_time_valid_from is None


# --- JSON round-trip ---

class TestJsonRoundTrip:
    """Every bead type must survive model → JSON → model without data loss."""

    BEAD_CONFIGS = [
        (FactBead, BeadType.FACT, TemporalClass.OBSERVATION, make_fact_content),
        (ClaimBead, BeadType.CLAIM, TemporalClass.PATTERN, make_claim_content),
        (SignalBead, BeadType.SIGNAL, TemporalClass.OBSERVATION, make_signal_content),
        (ProposalBead, BeadType.PROPOSAL, TemporalClass.OBSERVATION, make_proposal_content),
        (ProposalRejectedBead, BeadType.PROPOSAL_REJECTED, TemporalClass.OBSERVATION, make_proposal_rejected_content),
        (SkillBead, BeadType.SKILL, TemporalClass.PATTERN, make_skill_content),
        (ModelVersionBead, BeadType.MODEL_VERSION, TemporalClass.PATTERN, make_model_version_content),
        (PolicyBead, BeadType.POLICY, TemporalClass.PATTERN, make_policy_content),
    ]

    @pytest.mark.parametrize("bead_cls,bead_type,tc,content_fn", BEAD_CONFIGS,
                             ids=[c[0].__name__ for c in BEAD_CONFIGS])
    def test_json_round_trip(self, bead_cls, bead_type, tc, content_fn):
        original = bead_cls(
            **make_core_fields(bead_type, tc),
            content=content_fn(),
        )
        json_str = original.model_dump_json()
        restored = bead_cls.model_validate_json(json_str)
        assert restored.bead_id == original.bead_id
        assert restored.bead_type == original.bead_type
        assert restored.content == original.content


# --- Missing required fields ---

class TestMissingRequiredFields:
    def test_fact_missing_symbol(self):
        with pytest.raises(ValidationError):
            FactBead(
                **make_core_fields(BeadType.FACT),
                content={"field": "close", "value": 1.0, "as_of_world_time": ts().isoformat(), "provider": "IBKR"},
            )

    def test_claim_missing_drawer(self):
        with pytest.raises(ValidationError):
            ClaimBead(
                **make_core_fields(BeadType.CLAIM, TemporalClass.PATTERN),
                content={"conclusion": "test", "reasoning_trace": "test",
                         "premises_ref": [], "confidence_basis": "test", "icm_terms": []},
            )

    def test_signal_missing_direction(self):
        with pytest.raises(ValidationError):
            SignalBead(
                **make_core_fields(BeadType.SIGNAL),
                content={"expression": "test", "instrument": "EURUSD", "horizon": "intra",
                         "risk_profile": {"invalidation": "x", "risk_reward_basis": "y"},
                         "supporting_claims": [], "supporting_facts": []},
            )

    def test_proposal_rejected_missing_rejection_source(self):
        with pytest.raises(ValidationError):
            content = make_proposal_content()
            content["rejection_reason"] = "test"
            content["rejection_category"] = RejectionCategory.REGIME_MISMATCH
            ProposalRejectedBead(
                **make_core_fields(BeadType.PROPOSAL_REJECTED),
                content=content,
            )

    def test_core_missing_bead_id(self):
        with pytest.raises(ValidationError):
            FactBead(
                bead_type=BeadType.FACT,
                knowledge_time_recorded_at=ts(),
                temporal_class=TemporalClass.OBSERVATION,
                world_time_valid_from=ts(),
                world_time_valid_to=ts(),
                source_ref=make_source_ref(),
                attestation=make_attestation(),
                content=make_fact_content(),
            )


# --- parse_bead discriminated parsing ---

class TestParseBead:
    def test_parse_fact_from_dict(self):
        data = make_core_fields(BeadType.FACT)
        data["content"] = make_fact_content()
        bead = parse_bead(data)
        assert isinstance(bead, FactBead)

    def test_parse_claim_from_dict(self):
        data = make_core_fields(BeadType.CLAIM, TemporalClass.PATTERN)
        data["content"] = make_claim_content()
        bead = parse_bead(data)
        assert isinstance(bead, ClaimBead)

    def test_parse_unknown_type_raises(self):
        with pytest.raises(ValueError):
            parse_bead({"bead_type": "NONEXISTENT"})

    def test_bead_type_map_has_all_8(self):
        assert len(BEAD_TYPE_MAP) == 8
        for bt in BeadType:
            assert bt in BEAD_TYPE_MAP


# --- UUID v7 monotonicity (concurrency prep) ---

class TestUuidV7Monotonicity:
    def test_1000_rapid_uuids_are_monotonic(self):
        """1000 rapid UUID v7 creates must be strictly increasing (R5 mitigation)."""
        ids = [str(uuid7()) for _ in range(1000)]
        for i in range(1, len(ids)):
            assert ids[i] > ids[i - 1], f"UUID v7 ordering violated at index {i}"


# --- Supporting models ---

class TestSourceRef:
    def test_construct_valid(self):
        ref = make_source_ref()
        assert ref.source_type == SourceType.AGENT

    def test_source_version_optional(self):
        ref = SourceRef(source_type=SourceType.HUMAN, source_id="olya")
        assert ref.source_version is None


class TestAttestationEnvelope:
    def test_construct_valid(self):
        att = make_attestation()
        assert att.air_node_id == "test-node-mini"

    def test_sigs_default_empty(self):
        att = AttestationEnvelope(air_node_id="n", code_hash="h")
        assert att.ecdsa_sig == ""
        assert att.pqc_sig == ""

    def test_optional_fields(self):
        att = make_attestation()
        assert att.model_hash is None
        assert att.container_hash is None


# --- Bead defaults ---

class TestBeadDefaults:
    def test_status_defaults_to_active(self):
        bead = FactBead(
            **make_core_fields(BeadType.FACT),
            content=make_fact_content(),
        )
        assert bead.status == "ACTIVE"

    def test_lineage_defaults_to_empty(self):
        bead = FactBead(
            **make_core_fields(BeadType.FACT),
            content=make_fact_content(),
        )
        assert bead.lineage == []

    def test_tags_defaults_to_empty(self):
        bead = FactBead(
            **make_core_fields(BeadType.FACT),
            content=make_fact_content(),
        )
        assert bead.tags == []

    def test_hash_self_defaults_empty(self):
        bead = FactBead(
            **make_core_fields(BeadType.FACT),
            content=make_fact_content(),
        )
        assert bead.hash_self == ""

    def test_superseded_by_defaults_none(self):
        bead = FactBead(
            **make_core_fields(BeadType.FACT),
            content=make_fact_content(),
        )
        assert bead.superseded_by is None
