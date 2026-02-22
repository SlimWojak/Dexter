from datetime import datetime
from typing import Self

from pydantic import BaseModel, Field, model_validator

from .enums import BeadStatus, BeadType, SourceType, TemporalClass


class SourceRef(BaseModel):
    """What produced this bead."""
    source_type: SourceType
    source_id: str
    source_version: str | None = None


class AttestationEnvelope(BaseModel):
    """Proof of HOW a structural bead was produced (Layer 3)."""
    air_node_id: str
    code_hash: str
    model_hash: str | None = None
    container_hash: str | None = None
    ecdsa_sig: str = ""
    pqc_sig: str = ""
    signing_cert_chain: list[str] = Field(default_factory=list)


class BeadCore(BaseModel):
    """Universal fields shared by all structural beads (Spec Section 3.1).

    All 8 bead types inherit from this and add a typed `content` field.
    """
    bead_id: str = Field(description="UUID v7, time-ordered")
    bead_type: BeadType

    # Bi-temporal
    world_time_valid_from: datetime | None = None
    world_time_valid_to: datetime | None = None
    knowledge_time_recorded_at: datetime
    temporal_class: TemporalClass

    # Provenance
    source_ref: SourceRef
    lineage: list[str] = Field(default_factory=list)

    # Integrity (hash_self computed after all fields set; sigs added by signing pipeline)
    hash_self: str = ""
    hash_prev: str | None = None
    merkle_batch_id: str | None = None

    # Attestation (Layer 3)
    attestation: AttestationEnvelope

    # Operational
    status: BeadStatus = BeadStatus.ACTIVE
    superseded_by: str | None = None
    retraction_reason: str | None = None
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_temporal_class(self) -> Self:
        if self.temporal_class == TemporalClass.OBSERVATION:
            if self.world_time_valid_from is None or self.world_time_valid_to is None:
                raise ValueError(
                    "OBSERVATION temporal class requires both "
                    "world_time_valid_from and world_time_valid_to"
                )
        elif self.temporal_class == TemporalClass.PATTERN:
            if self.world_time_valid_from is not None or self.world_time_valid_to is not None:
                raise ValueError(
                    "PATTERN temporal class requires null world_time fields"
                )
        return self
