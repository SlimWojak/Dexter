from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from .core import BeadCore
from .enums import BeadType, PolicyType


class PolicyContent(BaseModel):
    """POLICY bead content — risk rules, position limits, regime definitions (Spec Section 3.2)."""
    policy_name: str
    policy_type: PolicyType
    rules: dict
    effective_from: datetime
    effective_to: datetime | None = None
    supersedes: str | None = None
    authority: str


class PolicyBead(BeadCore):
    bead_type: Literal[BeadType.POLICY] = BeadType.POLICY
    content: PolicyContent
