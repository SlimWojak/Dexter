from .enums import (
    BeadType, TemporalClass, BeadStatus, SourceType, Direction,
    ProposalAction, RejectionSource, RejectionCategory,
    SkillType, SkillValidation, DeploymentStatus, PolicyType,
    Drawer, PositionSizeUnit, DataQuality,
)
from .core import BeadCore, SourceRef, AttestationEnvelope
from .fact import FactContent, FactBead
from .claim import ClaimContent, ClaimBead
from .signal import SignalContent, SignalBead, RiskProfile
from .proposal import ProposalContent, ProposalBead, PositionSize
from .proposal_rejected import ProposalRejectedContent, ProposalRejectedBead
from .skill import SkillContent, SkillBead, SkillConditions
from .model_version import ModelVersionContent, ModelVersionBead, DeploymentHistoryEntry
from .policy import PolicyContent, PolicyBead

BEAD_TYPE_MAP: dict[BeadType, type[BeadCore]] = {
    BeadType.FACT: FactBead,
    BeadType.CLAIM: ClaimBead,
    BeadType.SIGNAL: SignalBead,
    BeadType.PROPOSAL: ProposalBead,
    BeadType.PROPOSAL_REJECTED: ProposalRejectedBead,
    BeadType.SKILL: SkillBead,
    BeadType.MODEL_VERSION: ModelVersionBead,
    BeadType.POLICY: PolicyBead,
}


def parse_bead(data: dict) -> BeadCore:
    """Parse a dict into the appropriate typed Bead model."""
    raw_type = data.get("bead_type")
    bead_type = raw_type if isinstance(raw_type, BeadType) else BeadType(raw_type)
    cls = BEAD_TYPE_MAP.get(bead_type)
    if cls is None:
        raise ValueError(f"Unknown bead type: {raw_type}")
    return cls.model_validate(data)


__all__ = [
    "BeadType", "TemporalClass", "BeadStatus", "SourceType", "Direction",
    "ProposalAction", "RejectionSource", "RejectionCategory",
    "SkillType", "SkillValidation", "DeploymentStatus", "PolicyType",
    "Drawer", "PositionSizeUnit", "DataQuality",
    "BeadCore", "SourceRef", "AttestationEnvelope",
    "FactContent", "FactBead",
    "ClaimContent", "ClaimBead",
    "SignalContent", "SignalBead", "RiskProfile",
    "ProposalContent", "ProposalBead", "PositionSize",
    "ProposalRejectedContent", "ProposalRejectedBead",
    "SkillContent", "SkillBead", "SkillConditions",
    "ModelVersionContent", "ModelVersionBead", "DeploymentHistoryEntry",
    "PolicyContent", "PolicyBead",
    "BEAD_TYPE_MAP", "parse_bead",
]
