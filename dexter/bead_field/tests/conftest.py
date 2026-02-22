"""Shared test fixtures for Bead Field Gate 1."""

from datetime import datetime, timezone

from uuid6 import uuid7

from bead_field.schema.enums import (
    BeadType,
    Direction,
    Drawer,
    PolicyType,
    PositionSizeUnit,
    ProposalAction,
    RejectionCategory,
    RejectionSource,
    SkillType,
    SkillValidation,
    DeploymentStatus,
    SourceType,
    TemporalClass,
)
from bead_field.schema.core import AttestationEnvelope, SourceRef
from bead_field.schema.fact import FactContent
from bead_field.schema.claim import ClaimContent
from bead_field.schema.signal import SignalContent, RiskProfile
from bead_field.schema.proposal import ProposalContent, PositionSize
from bead_field.schema.proposal_rejected import ProposalRejectedContent
from bead_field.schema.skill import SkillContent, SkillConditions
from bead_field.schema.model_version import ModelVersionContent
from bead_field.schema.policy import PolicyContent


def make_bead_id() -> str:
    return str(uuid7())


def make_source_ref(**overrides) -> SourceRef:
    defaults = dict(
        source_type=SourceType.AGENT,
        source_id="test-agent-001",
        source_version="v0.1.0",
    )
    defaults.update(overrides)
    return SourceRef(**defaults)


def make_attestation(**overrides) -> AttestationEnvelope:
    defaults = dict(
        air_node_id="test-node-mini",
        code_hash="abc123def456",
        ecdsa_sig="test_ecdsa_sig",
        pqc_sig="test_pqc_sig",
    )
    defaults.update(overrides)
    return AttestationEnvelope(**defaults)


def ts() -> datetime:
    """Current UTC timestamp."""
    return datetime.now(timezone.utc)


def make_core_fields(
    bead_type: BeadType,
    temporal_class: TemporalClass = TemporalClass.OBSERVATION,
    **overrides,
) -> dict:
    """Build the universal BeadCore fields dict."""
    now = ts()
    defaults = dict(
        bead_id=make_bead_id(),
        bead_type=bead_type,
        knowledge_time_recorded_at=now,
        temporal_class=temporal_class,
        source_ref=make_source_ref(),
        attestation=make_attestation(),
    )
    if temporal_class == TemporalClass.OBSERVATION:
        defaults["world_time_valid_from"] = now
        defaults["world_time_valid_to"] = now
    defaults.update(overrides)
    return defaults


# --- Content factories ---

def make_fact_content(**overrides) -> dict:
    defaults = dict(
        symbol="EURUSD",
        field="close",
        value=1.0847,
        as_of_world_time=ts(),
        provider="IBKR",
    )
    defaults.update(overrides)
    return defaults


def make_claim_content(**overrides) -> dict:
    defaults = dict(
        conclusion="HTF bias is bearish based on weekly OB rejection",
        reasoning_trace="Weekly candle rejected from bearish OB at 1.0920",
        premises_ref=[make_bead_id()],
        confidence_basis="Strong rejection with volume confirmation",
        drawer=Drawer.HTF_BIAS,
        icm_terms=["OB", "HTF", "MSS"],
    )
    defaults.update(overrides)
    return defaults


def make_signal_content(**overrides) -> dict:
    defaults = dict(
        expression="Short EURUSD at OTE within bearish FVG",
        direction=Direction.SHORT,
        instrument="EURUSD",
        horizon="intraday",
        session_context="London",
        risk_profile=dict(
            invalidation="Break above 1.0920 OB",
            risk_reward_basis="3:1 to daily low target",
        ),
        supporting_claims=[make_bead_id()],
        supporting_facts=[make_bead_id()],
    )
    defaults.update(overrides)
    return defaults


def make_proposal_content(**overrides) -> dict:
    defaults = dict(
        signal_ref=make_bead_id(),
        action=ProposalAction.ENTER_SHORT,
        instrument="EURUSD",
        entry_price=1.0855,
        stop_loss=1.0880,
        take_profit=1.0790,
        position_size=dict(method="fixed_fractional", value=0.01, unit=PositionSizeUnit.LOTS),
        execution_venue="IBKR_PAPER",
    )
    defaults.update(overrides)
    return defaults


def make_proposal_rejected_content(**overrides) -> dict:
    base = make_proposal_content()
    base.update(
        rejection_source=RejectionSource.RISK_ENGINE,
        rejection_reason="Daily loss limit would be exceeded",
        rejection_category=RejectionCategory.RISK_BREACH,
        rejection_policy_ref=make_bead_id(),
    )
    base.update(overrides)
    return base


def make_skill_content(**overrides) -> dict:
    defaults = dict(
        skill_name="avoid_high_leverage_low_liquidity",
        skill_type=SkillType.AVOIDANCE,
        description="Avoid entering positions during low-liquidity windows with high leverage",
        failure_trajectory_refs=[make_bead_id()],
        conditions=dict(
            if_conditions=["spread > 2x normal", "leverage > 10x"],
            then_action="skip entry, wait for liquidity return",
            confidence_basis="3 failure trajectories showed same pattern",
        ),
        distillation_method="Dream_Cycle_v1",
        validation_status=SkillValidation.CANDIDATE,
    )
    defaults.update(overrides)
    return defaults


def make_model_version_content(**overrides) -> dict:
    defaults = dict(
        model_name="cso_gate_evaluator",
        version_hash="sha256:abc123",
        training_data_refs=[make_bead_id()],
        eval_metrics={"accuracy": 0.87, "f1": 0.82},
        deployment_status=DeploymentStatus.STAGING,
    )
    defaults.update(overrides)
    return defaults


def make_policy_content(**overrides) -> dict:
    defaults = dict(
        policy_name="max_daily_loss",
        policy_type=PolicyType.RISK,
        rules={"max_loss_pct": 2.0, "max_loss_usd": 1000},
        effective_from=ts(),
        authority="G",
    )
    defaults.update(overrides)
    return defaults
