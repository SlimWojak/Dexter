from typing import Literal

from pydantic import BaseModel

from .core import BeadCore
from .enums import BeadType, Direction


class RiskProfile(BaseModel):
    invalidation: str
    risk_reward_basis: str


class SignalContent(BaseModel):
    """SIGNAL bead content — tradeable thesis with derivation (Spec Section 3.2)."""
    expression: str
    direction: Direction
    instrument: str
    horizon: str
    session_context: str | None = None
    regime_tags: list[str] = []
    risk_profile: RiskProfile
    supporting_claims: list[str]
    supporting_facts: list[str]


class SignalBead(BeadCore):
    bead_type: Literal[BeadType.SIGNAL] = BeadType.SIGNAL
    content: SignalContent
