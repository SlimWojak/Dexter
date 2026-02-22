from typing import Literal

from pydantic import BaseModel

from .core import BeadCore
from .enums import BeadType, PositionSizeUnit, ProposalAction


class PositionSize(BaseModel):
    method: str
    value: float
    unit: PositionSizeUnit


class ProposalContent(BaseModel):
    """PROPOSAL bead content — trade intent that passed all gates (Spec Section 3.2)."""
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


class ProposalBead(BeadCore):
    bead_type: Literal[BeadType.PROPOSAL] = BeadType.PROPOSAL
    content: ProposalContent
