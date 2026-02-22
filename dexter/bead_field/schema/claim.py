from typing import Literal

from pydantic import BaseModel

from .core import BeadCore
from .enums import BeadType, Drawer


class ClaimContent(BaseModel):
    """CLAIM bead content — agent inference with reasoning trace (Spec Section 3.2)."""
    conclusion: str
    reasoning_trace: str
    premises_ref: list[str]
    confidence_basis: str
    drawer: Drawer
    icm_terms: list[str]


class ClaimBead(BeadCore):
    bead_type: Literal[BeadType.CLAIM] = BeadType.CLAIM
    content: ClaimContent
