from typing import Literal, Self

from pydantic import BaseModel, model_validator

from .core import BeadCore
from .enums import (
    BeadType,
    PositionSizeUnit,
    ProposalAction,
    RejectionCategory,
    RejectionSource,
)
from .proposal import PositionSize


class ProposalRejectedContent(BaseModel):
    """PROPOSAL_REJECTED bead content (Spec Section 3.2).

    INV-SHADOW-RICH: Structurally identical to PROPOSAL plus rejection context.
    Never a lightweight stub. The Dream Cycle cannot learn from what it cannot trace.
    """
    # Full proposal snapshot (identical to ProposalContent)
    signal_ref: str
    action: ProposalAction
    instrument: str
    entry_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    position_size: PositionSize | None = None
    constraints: list[str] = []
    execution_venue: str
    simulation_refs: list[str] | None = None

    # Rejection context
    rejection_source: RejectionSource
    rejection_reason: str
    rejection_category: RejectionCategory
    rejection_policy_ref: str | None = None
    risk_metrics_at_rejection: dict = {}
    counterfactual_summary: str | None = None
    linked_skills: list[str] | None = None

    @model_validator(mode="after")
    def validate_risk_breach_policy_ref(self) -> Self:
        """INV-REJECTION-POLICY-REF: RISK_BREACH must reference active POLICY version."""
        if (
            self.rejection_category == RejectionCategory.RISK_BREACH
            and self.rejection_policy_ref is None
        ):
            raise ValueError(
                "RISK_BREACH rejection requires rejection_policy_ref "
                "(INV-REJECTION-POLICY-REF)"
            )
        return self


class ProposalRejectedBead(BeadCore):
    bead_type: Literal[BeadType.PROPOSAL_REJECTED] = BeadType.PROPOSAL_REJECTED
    content: ProposalRejectedContent
