"""
Bridge orchestrator — the poll-verify-seal-project loop.

BRIDGE_SPEC_v0.2 Section 3.

Ties together: reader → envelope constructor → governance mapper.
Pull-based: caller invokes cycle() on cadence.
Checkpoint AFTER mapper confirms bead written (INV-BRIDGE-CHECKPOINT-AFTER-WRITE).
Fail-closed: any step failure raises BridgeHalt (INV-BRIDGE-FAIL-CLOSED).

No silent drops: every entry produces a bead, a HeartbeatReceived,
or a FailureStruct (INV-BRIDGE-NO-SILENT-DROP).
"""

from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from bead_field.ingestion.governance_mapper import (
    GovernanceMapper,
    HeartbeatReceived,
)
from bead_field.ingestion.pipeline import IngestionPipeline
from bridge.envelope import EnvelopeConstructor, load_or_create_bridge_key
from bridge.reader import BridgeHalt, GovernanceLogReader
from bridge.types import BridgeEnvelope

log = logging.getLogger(__name__)


@dataclass
class CycleResult:
    """Result of a single poll-verify-seal-project cycle."""

    entries_read: int = 0
    envelopes_sealed: int = 0
    beads_written: int = 0
    heartbeats: int = 0
    duplicates_skipped: int = 0


class BridgeOrchestrator:
    """Pull-based orchestrator: poll → verify → seal → project → checkpoint.

    INV-BRIDGE-CHECKPOINT-AFTER-WRITE: Checkpoint only after mapper confirms.
    INV-BRIDGE-FAIL-CLOSED: Any failure → BridgeHalt.
    INV-BRIDGE-NO-SILENT-DROP: Every entry produces bead or failure.
    """

    def __init__(
        self,
        reader: GovernanceLogReader,
        constructor: EnvelopeConstructor,
        mapper: GovernanceMapper,
    ) -> None:
        self._reader = reader
        self._constructor = constructor
        self._mapper = mapper

    @classmethod
    def build(
        cls,
        log_path: Path,
        state_dir: Path,
        phoenix_key: bytes,
        pipeline: IngestionPipeline,
        bridge_key: bytes | None = None,
        bridge_key_id: str = "bridge-notary-v1",
        mapper_state_path: Path | None = None,
    ) -> BridgeOrchestrator:
        """Convenience factory: construct full Bridge from config."""
        reader = GovernanceLogReader(
            log_path=log_path,
            state_dir=state_dir,
            phoenix_key=phoenix_key,
        )
        bk = bridge_key or secrets.token_bytes(32)
        constructor = EnvelopeConstructor(bridge_key=bk, bridge_key_id=bridge_key_id)
        mapper = GovernanceMapper(pipeline=pipeline, state_path=mapper_state_path)
        return cls(reader=reader, constructor=constructor, mapper=mapper)

    def cycle(self) -> CycleResult:
        """Execute one poll-verify-seal-project cycle.

        Returns CycleResult on success. Raises BridgeHalt on any failure.
        """
        result = CycleResult()

        poll_result = self._reader.poll()
        result.entries_read = len(poll_result.entries)

        if not poll_result.entries:
            return result

        envelopes: list[BridgeEnvelope] = []
        for entry in poll_result.entries:
            envelope = self._constructor.seal(entry)
            envelopes.append(envelope)
        result.envelopes_sealed = len(envelopes)

        for envelope in envelopes:
            ingest_result = self._mapper.map_and_ingest(envelope)

            if isinstance(ingest_result, HeartbeatReceived):
                result.heartbeats += 1
                continue

            if ingest_result is None:
                result.duplicates_skipped += 1
                continue

            if not ingest_result.success:
                raise BridgeHalt(
                    f"Mapper rejected envelope event_id={envelope.event_id}: "
                    f"{ingest_result.error}"
                )

            result.beads_written += 1

        self._reader.checkpoint()

        log.info(
            "Bridge cycle: read=%d sealed=%d written=%d heartbeats=%d skipped=%d",
            result.entries_read,
            result.envelopes_sealed,
            result.beads_written,
            result.heartbeats,
            result.duplicates_skipped,
        )

        return result

    @property
    def reader(self) -> GovernanceLogReader:
        return self._reader

    @property
    def constructor(self) -> EnvelopeConstructor:
        return self._constructor

    @property
    def mapper(self) -> GovernanceMapper:
        return self._mapper
