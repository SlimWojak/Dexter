"""
Bridge state store — BRIDGE_SPEC_v0.2 Section 4.

Tracks where Bridge last read in the Phoenix governance log.
This is the ONLY state Bridge maintains. Minimal and durable.

State:
  last_read_seq      — Sequence number of last processed entry
  last_event_hash    — Hash of last processed entry (integrity check on resume)
  replay_counters    — map<emitter_id, last_seen_seq> (single emitter for now)
  gt_tracker         — map<emitter_id, last_seen_gt> (INV-BRIDGE-GT-MONOTONIC)
  log_inode          — File identity for rotation detection (OWL RF-2)

Failure modes:
  No checkpoint     → BOOTSTRAP (position 0, expected exactly once)
  Corrupt checkpoint → GovernanceLogError (HALT)
  Pointer ahead     → GovernanceLogError (HALT)
  Inode changed     → GovernanceLogError (HALT — log rotation)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bridge.types import BridgeCheckpoint

log = logging.getLogger(__name__)

GENESIS_HASH = "0" * 64


class BridgeStateError(Exception):
    """State store integrity failure — caller should HALT Bridge."""


class BridgeStateStore:
    """Durable Bridge state with checkpoint file.

    Checkpoint format: single JSON file with self-hash for corruption detection.
    """

    def __init__(self, state_dir: Path, log_path: Path) -> None:
        self._state_dir = state_dir
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._checkpoint_path = state_dir / "bridge_checkpoint.json"
        self._log_path = log_path
        self._state = self._load_or_bootstrap()

    def _load_or_bootstrap(self) -> BridgeCheckpoint:
        if not self._checkpoint_path.exists():
            log.info("BOOTSTRAP: No checkpoint found. First-ever Bridge start.")
            return self._bootstrap()

        try:
            raw = json.loads(self._checkpoint_path.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            raise BridgeStateError(
                f"Corrupt checkpoint file — cannot parse: {exc}"
            ) from exc

        stored_hash = raw.get("checkpoint_hash", "")
        computed_hash = self._compute_checkpoint_hash(raw)
        if stored_hash != computed_hash:
            raise BridgeStateError(
                f"Checkpoint hash mismatch — expected {computed_hash[:16]}..., "
                f"stored {stored_hash[:16]}... . Manual recovery required."
            )

        checkpoint = BridgeCheckpoint(
            last_read_seq=raw["last_read_seq"],
            last_event_hash=raw["last_event_hash"],
            updated_at=raw["updated_at"],
            replay_counters=raw.get("replay_counters", {}),
            gt_tracker=raw.get("gt_tracker", {}),
            log_inode=raw.get("log_inode"),
            log_path=raw.get("log_path", ""),
            checkpoint_hash=stored_hash,
        )

        if checkpoint.log_inode is not None and self._log_path.exists():
            current_inode = self._get_inode(self._log_path)
            if current_inode != checkpoint.log_inode:
                raise BridgeStateError(
                    f"Log file identity changed (inode {checkpoint.log_inode} → "
                    f"{current_inode}). Log rotation detected. HALT."
                )

        log.info(
            "Checkpoint loaded: last_read_seq=%d, last_hash=%s",
            checkpoint.last_read_seq,
            checkpoint.last_event_hash[:16],
        )
        return checkpoint

    def _bootstrap(self) -> BridgeCheckpoint:
        return BridgeCheckpoint(
            last_read_seq=0,
            last_event_hash=GENESIS_HASH,
            updated_at=datetime.now(UTC).isoformat(),
            replay_counters={},
            gt_tracker={},
            log_inode=self._get_inode(self._log_path) if self._log_path.exists() else None,
            log_path=str(self._log_path),
        )

    @property
    def last_read_seq(self) -> int:
        return self._state.last_read_seq

    @property
    def last_event_hash(self) -> str:
        return self._state.last_event_hash

    @property
    def is_bootstrap(self) -> bool:
        return self._state.last_read_seq == 0 and self._state.last_event_hash == GENESIS_HASH

    def get_replay_counter(self, emitter: str = "phoenix") -> int:
        return self._state.replay_counters.get(emitter, 0)

    def get_last_gt(self, emitter: str = "phoenix") -> str | None:
        return self._state.gt_tracker.get(emitter)

    def advance(
        self,
        seq: int,
        event_hash: str,
        gt_timestamp: str,
        emitter: str = "phoenix",
    ) -> None:
        """Advance state after successfully processing an entry."""
        self._state.last_read_seq = seq
        self._state.last_event_hash = event_hash
        self._state.updated_at = datetime.now(UTC).isoformat()
        self._state.replay_counters[emitter] = seq
        self._state.gt_tracker[emitter] = gt_timestamp
        if self._log_path.exists():
            self._state.log_inode = self._get_inode(self._log_path)

    def save(self) -> None:
        """Persist checkpoint to disk with self-hash."""
        data: dict[str, Any] = {
            "last_read_seq": self._state.last_read_seq,
            "last_event_hash": self._state.last_event_hash,
            "updated_at": self._state.updated_at,
            "replay_counters": self._state.replay_counters,
            "gt_tracker": self._state.gt_tracker,
            "log_inode": self._state.log_inode,
            "log_path": str(self._log_path),
        }
        data["checkpoint_hash"] = self._compute_checkpoint_hash(data)

        tmp_path = self._checkpoint_path.with_suffix(".tmp")
        fd = os.open(str(tmp_path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
        try:
            content = json.dumps(data, sort_keys=True, indent=2) + "\n"
            os.write(fd, content.encode("utf-8"))
            os.fsync(fd)
        finally:
            os.close(fd)

        os.replace(str(tmp_path), str(self._checkpoint_path))

    def verify_pointer(self, log_length: int) -> None:
        """Verify pointer is not ahead of log. Raises BridgeStateError if so."""
        if self._state.last_read_seq > log_length:
            raise BridgeStateError(
                f"Pointer ahead of log: last_read_seq={self._state.last_read_seq}, "
                f"log_length={log_length}. Log truncated or rolled. HALT."
            )

    @staticmethod
    def _compute_checkpoint_hash(data: dict[str, Any]) -> str:
        hashable = {k: v for k, v in data.items() if k != "checkpoint_hash"}
        canonical = json.dumps(hashable, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _get_inode(path: Path) -> int | None:
        try:
            return os.stat(str(path)).st_ino
        except OSError:
            return None
