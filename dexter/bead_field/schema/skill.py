from typing import Literal

from pydantic import BaseModel

from .core import BeadCore
from .enums import BeadType, SkillType, SkillValidation


class SkillConditions(BaseModel):
    if_conditions: list[str]
    then_action: str
    confidence_basis: str


class SkillContent(BaseModel):
    """SKILL bead content — distilled lesson from Dream Cycle (Spec Section 3.2)."""
    skill_name: str
    skill_type: SkillType
    description: str
    failure_trajectory_refs: list[str]
    success_trajectory_refs: list[str] | None = None
    conditions: SkillConditions
    distillation_method: str
    validation_status: SkillValidation
    validated_by: str | None = None


class SkillBead(BeadCore):
    bead_type: Literal[BeadType.SKILL] = BeadType.SKILL
    content: SkillContent
