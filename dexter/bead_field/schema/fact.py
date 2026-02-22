from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from .core import BeadCore
from .enums import BeadType, DataQuality


class FactContent(BaseModel):
    """FACT bead content — market data, events (Spec Section 3.2)."""
    symbol: str
    field: str
    value: int | float | str | dict
    as_of_world_time: datetime
    provider: str
    quality_score: float | None = Field(
        default=None, ge=0.0, le=1.0,
        description="Provider-reported data quality, NOT analytical judgment",
    )


class FactBead(BeadCore):
    bead_type: Literal[BeadType.FACT] = BeadType.FACT
    content: FactContent
