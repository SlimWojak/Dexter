"""End-to-end ingestion pipeline (Spec Sections 2.2, 3, 5).

Raw data -> validated bead -> HLC timestamped -> hash chained -> signed -> stored -> Merkle checked.

This is where every component proves it composes correctly.
"""

from collections import Counter
from datetime import datetime
from typing import Any

from pydantic import ValidationError
from uuid6 import uuid7

from bead_field.clock.hlc import HLC
from bead_field.integrity.chain import append_to_chain
from bead_field.integrity.hashing import compute_hash
from bead_field.integrity.merkle import BatchAnchor, AnchorConfig
from bead_field.integrity.signing import KeyPair, sign_hash
from bead_field.schema import BEAD_TYPE_MAP, parse_bead
from bead_field.schema.core import AttestationEnvelope, BeadCore, SourceRef
from bead_field.schema.enums import BeadType, TemporalClass
from bead_field.store.bitemporal import BeadStore


class IngestionError(Exception):
    pass


class IngestionResult:
    """Outcome of a single bead ingestion attempt."""

    def __init__(self, bead: BeadCore | None, batch_id: str | None, error: str | None):
        self.bead = bead
        self.batch_id = batch_id
        self.error = error

    @property
    def success(self) -> bool:
        return self.bead is not None and self.error is None


class IngestionPipeline:
    """Wires all Gate 1 components into a single ingestion path.

    Steps:
      1. Validate input against type-specific schema
      2. Assign bead_id (UUID v7)
      3. Set knowledge_time via HLC tick
      4. Compute hash_self (chain append)
      5. Sign (dual PQC + ECDSA)
      6. Insert into store
      7. Check Merkle trigger
    """

    def __init__(
        self,
        store: BeadStore,
        keys: KeyPair,
        hlc: HLC | None = None,
        anchor_config: AnchorConfig | None = None,
        air_node_id: str = "gate1-mini",
        code_hash: str = "dev",
    ) -> None:
        self.store = store
        self.keys = keys
        self.hlc = hlc or HLC()
        self.anchor = BatchAnchor(store, anchor_config)
        self._air_node_id = air_node_id
        self._code_hash = code_hash
        self._prev_bead: BeadCore | None = None

        self._counters: Counter = Counter()

    def ingest(
        self,
        bead_type: BeadType,
        content: dict[str, Any],
        temporal_class: TemporalClass,
        source_ref: SourceRef,
        world_time_valid_from: datetime | None = None,
        world_time_valid_to: datetime | None = None,
        lineage: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> IngestionResult:
        """Ingest raw data through the full pipeline."""
        self._counters["attempts"] += 1

        try:
            bead_cls = BEAD_TYPE_MAP.get(bead_type)
            if bead_cls is None:
                raise IngestionError(f"Unknown bead type: {bead_type}")

            kt = self.hlc.tick()

            raw_bead = bead_cls(
                bead_id=str(uuid7()),
                bead_type=bead_type,
                content=content,
                temporal_class=temporal_class,
                world_time_valid_from=world_time_valid_from,
                world_time_valid_to=world_time_valid_to,
                knowledge_time_recorded_at=kt,
                source_ref=source_ref,
                lineage=lineage or [],
                tags=tags or [],
                attestation=AttestationEnvelope(
                    air_node_id=self._air_node_id,
                    code_hash=self._code_hash,
                ),
            )
        except (ValidationError, IngestionError) as e:
            self._counters["rejected"] += 1
            self._counters[f"rejected:{bead_type.value}"] += 1
            return IngestionResult(bead=None, batch_id=None, error=str(e))

        linked = append_to_chain(raw_bead, self._prev_bead)

        ecdsa_sig, pqc_sig = sign_hash(linked.hash_self, self.keys)
        signed = linked.model_copy(
            update={"attestation": linked.attestation.model_copy(
                update={"ecdsa_sig": ecdsa_sig, "pqc_sig": pqc_sig}
            )}
        )

        try:
            self.store.insert(signed)
        except Exception as e:
            self._counters["rejected"] += 1
            return IngestionResult(bead=None, batch_id=None, error=str(e))

        self._prev_bead = signed

        batch_id = self.anchor.record(signed)

        self._counters["ingested"] += 1
        self._counters[f"ingested:{bead_type.value}"] += 1

        return IngestionResult(bead=signed, batch_id=batch_id, error=None)

    @property
    def stats(self) -> dict[str, int]:
        """Basic observability counters (beads ingested by type, rejections by reason)."""
        return dict(self._counters)
