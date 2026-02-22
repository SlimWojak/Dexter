from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from .core import BeadCore
from .enums import BeadType, DeploymentStatus


class DeploymentHistoryEntry(BaseModel):
    status: str
    changed_at: datetime
    changed_by: str


class ModelVersionContent(BaseModel):
    """MODEL_VERSION bead content — model metadata (Spec Section 3.2)."""
    model_name: str
    version_hash: str
    training_data_refs: list[str]
    eval_metrics: dict
    deployment_status: DeploymentStatus
    deployment_history: list[DeploymentHistoryEntry] = []


class ModelVersionBead(BeadCore):
    bead_type: Literal[BeadType.MODEL_VERSION] = BeadType.MODEL_VERSION
    content: ModelVersionContent
