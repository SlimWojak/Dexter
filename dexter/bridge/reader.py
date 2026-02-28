"""
Phoenix governance log reader — pull-based, fail-closed.

BRIDGE_SPEC_v0.2 Section 3.1 Steps 2-3.

Architecture:
  Bridge calls reader.poll() on cadence (default 5s) or trigger.
  Reader opens governance_log.jsonl, seeks to last-read position,
  reads new entries, verifies each, yields VerifiedEntry objects.
  State store tracks cursor. Checkpoint persists across restarts.

Fail-closed:
  - Unverifiable entry → FailureStruct logged, HALT returned
  - Corrupt log → BridgeStateError, HALT
  - Pointer ahead → BridgeStateError, HALT
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from bridge.state_store import BridgeStateError, BridgeStateStore
from bridge.types import (
    FailureStruct,
    FailureType,
    VerifiedEntry,
    VerifyOutcome,
)
from bridge.verification import compute_entry_hash, verify_entry

log = logging.getLogger(__name__)


class BridgeHalt(Exception):
    """Bridge must halt — security event or integrity concern."""

    def __init__(self, reason: str, failures: list[FailureStruct] | None = None):
        self.reason = reason
        self.failures = failures or []
        super().__init__(f"BRIDGE HALT: {reason}")


@dataclass
class PollResult:
    """Result of a single poll cycle."""

    entries: list[VerifiedEntry] = field(default_factory=list)
    failures: list[FailureStruct] = field(default_factory=list)
    halted: bool = False
    halt_reason: str = ""
    entries_read: int = 0


class GovernanceLogReader:
    """Pull-based reader for Phoenix governance log.

    Usage:
        reader = GovernanceLogReader(log_path, state_dir, phoenix_key)
        result = reader.poll()
        for entry in result.entries:
            # process entry -> build envelope -> deliver
        reader.checkpoint()
    """

    def __init__(
        self,
        log_path: Path,
        state_dir: Path,
        phoenix_key: bytes,
    ) -> None:
        self._log_path = log_path
        self._phoenix_key = phoenix_key
        self._state = BridgeStateStore(state_dir=state_dir, log_path=log_path)
        self._pending_entries: list[VerifiedEntry] = []

    @property
    def state(self) -> BridgeStateStore:
        return self._state

    def poll(self) -> PollResult:
        """Read and verify new entries since last checkpoint.

        Returns PollResult with verified entries and/or failures.
        On HALT-level failure, raises BridgeHalt.
        """
        result = PollResult()

        if not self._log_path.exists():
            if self._state.is_bootstrap:
                return result
            raise BridgeHalt("Governance log missing after bootstrap")

        raw_entries = self._read_new_entries()

        try:
            self._state.verify_pointer(
                self._state.last_read_seq + len(raw_entries)
            )
        except BridgeStateError as exc:
            raise BridgeHalt(str(exc)) from exc

        last_hash = self._state.last_event_hash

        for raw in raw_entries:
            last_seq = self._state.last_read_seq + len(result.entries)
            last_gt = self._state.get_last_gt()
            if result.entries:
                last_seq = result.entries[-1].seq
                last_gt = result.entries[-1].timestamp
                last_hash = result.entries[-1].athena_hash

            outcome, failures = verify_entry(
                entry=raw,
                phoenix_key=self._phoenix_key,
                last_seen_seq=last_seq,
                last_seen_gt=last_gt,
                expected_hash_prev=last_hash,
            )

            result.failures.extend(failures)
            result.entries_read += 1

            if outcome == VerifyOutcome.HALT:
                result.halted = True
                result.halt_reason = (
                    f"HALT at seq {raw.get('seq')}: {failures[-1].detail}"
                    if failures
                    else f"HALT at seq {raw.get('seq')}"
                )
                raise BridgeHalt(result.halt_reason, failures)

            if outcome == VerifyOutcome.FAIL:
                result.halted = True
                result.halt_reason = (
                    f"Verification failed at seq {raw.get('seq')}: "
                    f"{failures[-1].failure_type.value}"
                    if failures
                    else f"Verification failed at seq {raw.get('seq')}"
                )
                raise BridgeHalt(result.halt_reason, failures)

            entry_hash = compute_entry_hash(raw)
            verified = VerifiedEntry(
                seq=raw["seq"],
                event_type=raw["event_type"],
                payload=raw["payload"],
                timestamp=raw["timestamp"],
                hash_prev=raw["hash_prev"],
                athena_index=raw["athena_index"],
                athena_hash=entry_hash,
                source_signature=raw["source_signature"],
            )
            result.entries.append(verified)
            last_hash = entry_hash

        self._pending_entries = list(result.entries)
        return result

    def checkpoint(self) -> None:
        """Persist state to disk after successful processing of pending entries."""
        for entry in self._pending_entries:
            self._state.advance(
                seq=entry.seq,
                event_hash=entry.athena_hash,
                gt_timestamp=entry.timestamp,
            )
        self._state.save()
        self._pending_entries.clear()

    def _read_new_entries(self) -> list[dict[str, Any]]:
        """Read governance log entries after last_read_seq."""
        entries: list[dict[str, Any]] = []
        target_seq = self._state.last_read_seq

        try:
            with open(self._log_path) as f:
                for line_num, raw_line in enumerate(f, 1):
                    stripped = raw_line.strip()
                    if not stripped:
                        continue
                    try:
                        entry = json.loads(stripped)
                    except json.JSONDecodeError as exc:
                        raise BridgeHalt(
                            f"Corrupt governance log at line {line_num}: {exc}",
                            [FailureStruct(
                                failure_type=FailureType.LOG_CORRUPT,
                                what_failed="read",
                                which_field=f"line_{line_num}",
                                timestamp="",
                                detail=str(exc),
                            )],
                        ) from exc

                    seq = entry.get("seq", 0)
                    if seq > target_seq:
                        entries.append(entry)
        except OSError as exc:
            raise BridgeHalt(f"Cannot read governance log: {exc}") from exc

        return entries
