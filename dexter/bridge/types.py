"""
Bridge types — envelope schema, failure structs, verification results.

BRIDGE_SPEC_v0.2 Sections 2.1, 2.2.

All data structures the Bridge operates on. No logic here — just shapes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

BRIDGE_VERSION = "0.1.0"
SUPPORTED_VERSIONS = frozenset({"0.1.0"})

GOVERNANCE_EVENT_TYPES = frozenset({
    "CARTRIDGE_INSERTION",
    "CARTRIDGE_REMOVAL",
    "CALIBRATION",
    "STRATEGY_DEPRECATION",
    "LEASE_ACTIVATION",
    "LEASE_EXPIRY",
    "LEASE_REVOCATION",
    "LEASE_HALT",
    "ATTESTATION",
    "CEREMONY",
    "STATE_LOCK",
    "MARGIN_CONTENTION",
    "EMERGENCY_EJECT",
    "HEARTBEAT",
})

PHOENIX_GOVERNANCE_EVENTS = GOVERNANCE_EVENT_TYPES - {"HEARTBEAT"}


class FailureType(str, Enum):
    """INV-BRIDGE-NO-SILENT-DROP: Every rejection carries one of these."""

    SIG_INVALID = "SIG_INVALID"
    HASH_MISMATCH = "HASH_MISMATCH"
    HASH_CHAIN_BREAK = "HASH_CHAIN_BREAK"
    REPLAY_DUPLICATE = "REPLAY_DUPLICATE"
    SEQ_GAP = "SEQ_GAP"
    VERSION_UNKNOWN = "VERSION_UNKNOWN"
    EVENT_TYPE_UNKNOWN = "EVENT_TYPE_UNKNOWN"
    GT_NON_MONOTONIC = "GT_NON_MONOTONIC"
    ALGORITHM_UNKNOWN = "ALGORITHM_UNKNOWN"
    LOG_CORRUPT = "LOG_CORRUPT"
    CHECKPOINT_CORRUPT = "CHECKPOINT_CORRUPT"
    POINTER_AHEAD = "POINTER_AHEAD"
    LOG_IDENTITY_CHANGED = "LOG_IDENTITY_CHANGED"


class VerifyOutcome(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    HALT = "HALT"


class MerkleStatus(str, Enum):
    PRESENT = "PRESENT"
    DEFERRED = "DEFERRED"


@dataclass(frozen=True)
class FailureStruct:
    """INV-BRIDGE-NO-SILENT-DROP: Structured failure record for every rejection."""

    failure_type: FailureType
    what_failed: str
    which_field: str
    timestamp: str
    detail: str = ""
    entry_snapshot: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VerifiedEntry:
    """A governance log entry that passed all verification checks."""

    seq: int
    event_type: str
    payload: dict[str, Any]
    timestamp: str
    hash_prev: str
    athena_index: int
    athena_hash: str
    source_signature: dict[str, str]


@dataclass
class BridgeEnvelope:
    """Notary envelope per BRIDGE_SPEC_v0.2 Section 2.1."""

    version: str
    event_id: str
    event_type: str
    payload: dict[str, Any]
    gt_timestamp: str
    athena_ref: dict[str, Any]
    source_signature: dict[str, str]
    hash_chain_proof: dict[str, Any]
    replay_guard: int
    bridge_seal: dict[str, str]


@dataclass
class BridgeCheckpoint:
    """Serializable bridge state for durable checkpoint."""

    last_read_seq: int
    last_event_hash: str
    updated_at: str
    replay_counters: dict[str, int]
    gt_tracker: dict[str, str]
    log_inode: int | None
    log_path: str
    checkpoint_hash: str = ""
