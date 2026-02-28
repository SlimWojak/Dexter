"""
Governance mapper — Dexter-side receiver for Bridge envelopes.

BRIDGE_SPEC_v0.2 Section 5.3.

Maps BridgeEnvelope → FACT bead content + tags, routes through standard
IngestionPipeline. The ONLY place where governance event semantics are
interpreted. Bridge doesn't interpret. Phoenix doesn't format for Dexter.

Tagging contract (DEC-SUBSTRATE-FREEZE compliant — no new enums):
  Required: ["src:governance", "gov_event:{EVENT_TYPE}"]
  Post-freeze (~2026-03-24): migrate to SourceType.GOVERNANCE enum.

Source type mapping (Amendment 13, deterministic):
  HUMAN: ATTESTATION, CEREMONY, LEASE_REVOCATION, STRATEGY_DEPRECATION, EMERGENCY_EJECT
  AGENT: everything else (CALIBRATION, LEASE_*, STATE_LOCK, MARGIN_CONTENTION, CARTRIDGE_*)

Provenance layers (INV-BRIDGE-PROVENANCE-LAYER):
  Phoenix layer: athena_ref preserved in bead content (pass-through, opaque)
  Bead field layer: source_ref, attestation, hash_self — computed by pipeline

HEARTBEAT: pre-mapper filter. Not a bead. Updates metric only.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from bead_field.ingestion.pipeline import IngestionPipeline, IngestionResult
from bead_field.schema.core import SourceRef
from bead_field.schema.enums import BeadType, SourceType, TemporalClass
from bridge.types import (
    BridgeEnvelope,
    PHOENIX_GOVERNANCE_EVENTS,
)

log = logging.getLogger(__name__)

BRIDGE_SOURCE_ID = "bridge-notary"

SOURCE_TYPE_MAP: dict[str, SourceType] = {
    "ATTESTATION": SourceType.HUMAN,
    "CEREMONY": SourceType.HUMAN,
    "LEASE_REVOCATION": SourceType.HUMAN,
    "STRATEGY_DEPRECATION": SourceType.HUMAN,
    "EMERGENCY_EJECT": SourceType.HUMAN,
    "CALIBRATION": SourceType.AGENT,
    "LEASE_ACTIVATION": SourceType.AGENT,
    "LEASE_EXPIRY": SourceType.AGENT,
    "LEASE_HALT": SourceType.AGENT,
    "STATE_LOCK": SourceType.AGENT,
    "MARGIN_CONTENTION": SourceType.AGENT,
    "CARTRIDGE_INSERTION": SourceType.AGENT,
    "CARTRIDGE_REMOVAL": SourceType.AGENT,
}


class GovernanceMapperError(Exception):
    """Mapping or validation failure — envelope rejected at boundary."""


class HeartbeatReceived:
    """Sentinel: HEARTBEAT handled, not a bead. Metric update only."""

    def __init__(self, gt_timestamp: str, replay_guard: int) -> None:
        self.gt_timestamp = gt_timestamp
        self.replay_guard = replay_guard


class GovernanceMapper:
    """Maps BridgeEnvelopes to FACT beads via the standard ingestion pipeline.

    Replay guard: tracks last ingested replay_guard to prevent duplicates.
    HEARTBEAT: filtered before mapping, returns HeartbeatReceived.
    """

    def __init__(
        self,
        pipeline: IngestionPipeline,
        state_path: Path | None = None,
    ) -> None:
        self._pipeline = pipeline
        self._state_path = state_path
        self._last_replay_guard: int = 0
        self._heartbeat_count: int = 0
        if state_path:
            self._load_state()

    def map_and_ingest(
        self, envelope: BridgeEnvelope,
    ) -> IngestionResult | HeartbeatReceived | None:
        """Map envelope to FACT bead and ingest.

        Returns:
          IngestionResult — on successful (or failed) ingestion attempt
          HeartbeatReceived — for HEARTBEAT envelopes (metric update, no bead)
          None — duplicate (replay guard)

        Raises GovernanceMapperError on unknown event_type or malformed input.
        """
        if envelope.event_type == "HEARTBEAT":
            self._heartbeat_count += 1
            log.debug("HEARTBEAT received (count=%d)", self._heartbeat_count)
            return HeartbeatReceived(envelope.gt_timestamp, envelope.replay_guard)

        if envelope.replay_guard <= self._last_replay_guard:
            log.info(
                "Duplicate envelope (replay_guard=%d <= %d), skipping",
                envelope.replay_guard, self._last_replay_guard,
            )
            return None

        if envelope.event_type not in PHOENIX_GOVERNANCE_EVENTS:
            raise GovernanceMapperError(
                f"Unknown event_type '{envelope.event_type}'. "
                f"Known: {sorted(PHOENIX_GOVERNANCE_EVENTS)}"
            )

        source_type = SOURCE_TYPE_MAP.get(envelope.event_type)
        if source_type is None:
            raise GovernanceMapperError(
                f"No SOURCE_TYPE_MAP entry for '{envelope.event_type}'"
            )

        gt = datetime.fromisoformat(envelope.gt_timestamp)

        content = self._build_fact_content(envelope, gt)
        tags = self._build_tags(envelope)
        source_ref = SourceRef(
            source_type=source_type,
            source_id=BRIDGE_SOURCE_ID,
            source_version=envelope.version,
        )
        lineage = [f"bridge:event_id:{envelope.event_id}"]

        result = self._pipeline.ingest(
            bead_type=BeadType.FACT,
            content=content,
            temporal_class=TemporalClass.OBSERVATION,
            source_ref=source_ref,
            world_time_valid_from=gt,
            world_time_valid_to=gt,
            lineage=lineage,
            tags=tags,
        )

        if result.success:
            self._last_replay_guard = envelope.replay_guard
            if self._state_path:
                self._save_state()

        return result

    @property
    def last_replay_guard(self) -> int:
        return self._last_replay_guard

    @property
    def heartbeat_count(self) -> int:
        return self._heartbeat_count

    @staticmethod
    def _build_fact_content(
        envelope: BridgeEnvelope, gt: datetime,
    ) -> dict[str, Any]:
        """Map envelope to FactContent-compatible dict.

        value field carries the full governance event + Phoenix provenance
        (athena_ref, gt_timestamp — INV-BRIDGE-PROVENANCE-LAYER).
        """
        return {
            "symbol": "GOVERNANCE",
            "field": envelope.event_type,
            "value": {
                "event_payload": envelope.payload,
                "athena_ref": envelope.athena_ref,
                "gt_timestamp": envelope.gt_timestamp,
                "event_id": envelope.event_id,
                "replay_guard": envelope.replay_guard,
            },
            "as_of_world_time": gt.isoformat(),
            "provider": "phoenix-governance",
        }

    @staticmethod
    def _build_tags(envelope: BridgeEnvelope) -> list[str]:
        """Build tag set per Section 5.1 tagging contract."""
        tags = [
            "src:governance",
            f"gov_event:{envelope.event_type}",
        ]

        payload = envelope.payload
        if isinstance(payload, dict):
            for key in ("lease_id", "cartridge_ref", "strategy_ref"):
                if key in payload:
                    tags.append(f"gov:{key}:{payload[key]}")

        return tags

    def _load_state(self) -> None:
        if self._state_path and self._state_path.exists():
            try:
                data = json.loads(self._state_path.read_text())
                self._last_replay_guard = data.get("last_replay_guard", 0)
            except (json.JSONDecodeError, OSError):
                log.warning("Corrupt mapper state, resetting to 0")
                self._last_replay_guard = 0

    def _save_state(self) -> None:
        if self._state_path:
            self._state_path.parent.mkdir(parents=True, exist_ok=True)
            self._state_path.write_text(
                json.dumps({"last_replay_guard": self._last_replay_guard})
            )
