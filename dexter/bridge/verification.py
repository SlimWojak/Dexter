"""
Verification whitelist — BRIDGE_SPEC_v0.2 Section 2.2.

Closed whitelist of permitted operations. Anything not listed is a spec violation.

Operations:
  SIG_VERIFY        — dispatch on algorithm field (CTO: ECDSA drops in later)
  HASH_VERIFY       — recompute hash_self, check hash_prev chain
  REPLAY_CHECK      — seq monotonic, gap semantics
  GT_MONOTONIC_CHECK — gt_timestamp never decreases per emitter
  VERSION_CHECK     — supported version set
  EVENT_TYPE_CHECK  — closed event type whitelist
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from bridge.types import (
    GOVERNANCE_EVENT_TYPES,
    SUPPORTED_VERSIONS,
    FailureStruct,
    FailureType,
    VerifyOutcome,
)

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Signature verification dispatch (CTO: dispatch on algorithm field)
# ---------------------------------------------------------------------------

SignatureVerifier = Callable[[bytes, str, str], bool]


def _verify_hmac_sha256(key: bytes, hash_hex: str, signature: str) -> bool:
    expected = hmac.new(key, hash_hex.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


_VERIFIERS: dict[str, SignatureVerifier] = {
    "hmac-sha256": _verify_hmac_sha256,
}


def register_verifier(algorithm: str, verifier: SignatureVerifier) -> None:
    """Register a new signature verifier (e.g. ecdsa-secp256r1 for future use)."""
    _VERIFIERS[algorithm] = verifier


def _available_algorithms() -> frozenset[str]:
    return frozenset(_VERIFIERS.keys())


# ---------------------------------------------------------------------------
# Canonical hashing (mirrors Phoenix governance_log.py)
# ---------------------------------------------------------------------------

def _canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def compute_entry_hash(entry: dict[str, Any]) -> str:
    """Recompute the hash of a governance log entry from its hashable fields."""
    hashable = {
        "seq": entry["seq"],
        "event_type": entry["event_type"],
        "payload": entry["payload"],
        "timestamp": entry["timestamp"],
        "hash_prev": entry["hash_prev"],
    }
    return _sha256_hex(_canonical_json(hashable))


# ---------------------------------------------------------------------------
# Individual verification operations
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _fail(
    ftype: FailureType,
    what: str,
    field: str,
    detail: str = "",
    snapshot: dict[str, Any] | None = None,
) -> FailureStruct:
    return FailureStruct(
        failure_type=ftype,
        what_failed=what,
        which_field=field,
        timestamp=_now_iso(),
        detail=detail,
        entry_snapshot=snapshot or {},
    )


def sig_verify(
    entry: dict[str, Any],
    phoenix_key: bytes,
) -> tuple[VerifyOutcome, FailureStruct | None]:
    """SIG_VERIFY: Verify Phoenix signature, dispatching on algorithm field."""
    sig_data = entry.get("source_signature", {})
    algorithm = sig_data.get("algorithm", "")
    signature = sig_data.get("sig", "")

    verifier = _VERIFIERS.get(algorithm)
    if verifier is None:
        return VerifyOutcome.FAIL, _fail(
            FailureType.ALGORITHM_UNKNOWN,
            "sig_verify",
            "source_signature.algorithm",
            f"Unknown algorithm '{algorithm}'. Registered: {sorted(_VERIFIERS)}",
            _safe_snapshot(entry),
        )

    computed_hash = compute_entry_hash(entry)

    if not verifier(phoenix_key, computed_hash, signature):
        return VerifyOutcome.FAIL, _fail(
            FailureType.SIG_INVALID,
            "sig_verify",
            "source_signature.sig",
            f"Signature verification failed for algorithm '{algorithm}'",
            _safe_snapshot(entry),
        )

    return VerifyOutcome.PASS, None


def hash_verify(
    entry: dict[str, Any],
    expected_hash_prev: str,
) -> tuple[VerifyOutcome, FailureStruct | None]:
    """HASH_VERIFY: Verify hash_self recomputes correctly and hash_prev links."""
    actual_prev = entry.get("hash_prev", "")
    if actual_prev != expected_hash_prev:
        return VerifyOutcome.FAIL, _fail(
            FailureType.HASH_CHAIN_BREAK,
            "hash_verify",
            "hash_prev",
            f"Expected {expected_hash_prev[:16]}..., got {actual_prev[:16]}...",
            _safe_snapshot(entry),
        )

    computed = compute_entry_hash(entry)
    athena_hash = entry.get("athena_hash", "")
    if computed != athena_hash:
        return VerifyOutcome.FAIL, _fail(
            FailureType.HASH_MISMATCH,
            "hash_verify",
            "athena_hash",
            f"Recomputed {computed[:16]}..., stored {athena_hash[:16]}...",
            _safe_snapshot(entry),
        )

    return VerifyOutcome.PASS, None


def replay_check(
    entry: dict[str, Any],
    last_seen_seq: int,
) -> tuple[VerifyOutcome, FailureStruct | None]:
    """REPLAY_CHECK: Verify seq is monotonically increasing.

    Pull-model semantics (BRIDGE_SPEC_v0.2 Section 2.2):
      seq == last_seen + 1: PASS (normal)
      seq <= last_seen: FAIL (replay/duplicate)
      seq == last_seen + 2: WARN (single-step gap — timing edge case)
      seq > last_seen + 2: HALT (missed events — log integrity concern)
    """
    seq = entry.get("seq", 0)

    if seq <= last_seen_seq:
        return VerifyOutcome.FAIL, _fail(
            FailureType.REPLAY_DUPLICATE,
            "replay_check",
            "seq",
            f"seq {seq} <= last_seen {last_seen_seq}",
            _safe_snapshot(entry),
        )

    gap = seq - last_seen_seq
    if gap == 1:
        return VerifyOutcome.PASS, None

    if gap == 2:
        log.warning("Replay check: single-step gap (seq %d, last_seen %d)", seq, last_seen_seq)
        return VerifyOutcome.WARN, _fail(
            FailureType.SEQ_GAP,
            "replay_check",
            "seq",
            f"Single-step gap: seq {seq}, last_seen {last_seen_seq}. Accepted with warning.",
            _safe_snapshot(entry),
        )

    return VerifyOutcome.HALT, _fail(
        FailureType.SEQ_GAP,
        "replay_check",
        "seq",
        f"Multi-step gap: seq {seq}, last_seen {last_seen_seq}. Log integrity concern.",
        _safe_snapshot(entry),
    )


def gt_monotonic_check(
    entry: dict[str, Any],
    last_seen_gt: str | None,
) -> tuple[VerifyOutcome, FailureStruct | None]:
    """GT_MONOTONIC_CHECK: gt_timestamp (= entry timestamp) must never decrease."""
    gt = entry.get("timestamp", "")

    if last_seen_gt is None or gt >= last_seen_gt:
        return VerifyOutcome.PASS, None

    return VerifyOutcome.FAIL, _fail(
        FailureType.GT_NON_MONOTONIC,
        "gt_monotonic_check",
        "timestamp",
        f"GT {gt} < last_seen {last_seen_gt}",
        _safe_snapshot(entry),
    )


def version_check(version: str) -> tuple[VerifyOutcome, FailureStruct | None]:
    """VERSION_CHECK: Reject unknown envelope versions."""
    if version in SUPPORTED_VERSIONS:
        return VerifyOutcome.PASS, None

    return VerifyOutcome.FAIL, _fail(
        FailureType.VERSION_UNKNOWN,
        "version_check",
        "version",
        f"Unknown version '{version}'. Supported: {sorted(SUPPORTED_VERSIONS)}",
    )


def event_type_check(event_type: str) -> tuple[VerifyOutcome, FailureStruct | None]:
    """EVENT_TYPE_CHECK: Reject event types not in closed whitelist."""
    if event_type in GOVERNANCE_EVENT_TYPES:
        return VerifyOutcome.PASS, None

    return VerifyOutcome.FAIL, _fail(
        FailureType.EVENT_TYPE_UNKNOWN,
        "event_type_check",
        "event_type",
        f"Unknown event_type '{event_type}'. Whitelist: {sorted(GOVERNANCE_EVENT_TYPES)}",
    )


# ---------------------------------------------------------------------------
# Full verification pipeline
# ---------------------------------------------------------------------------

def verify_entry(
    entry: dict[str, Any],
    phoenix_key: bytes,
    last_seen_seq: int,
    last_seen_gt: str | None,
    expected_hash_prev: str,
) -> tuple[VerifyOutcome, list[FailureStruct]]:
    """Run full verification whitelist on a governance log entry.

    Order: EVENT_TYPE_CHECK → SIG_VERIFY → HASH_VERIFY → REPLAY_CHECK → GT_MONOTONIC_CHECK
    Any FAIL or HALT → stop and return immediately.
    WARN → accumulate but continue.
    """
    failures: list[FailureStruct] = []
    worst = VerifyOutcome.PASS

    checks: list[tuple[str, tuple[VerifyOutcome, FailureStruct | None]]] = [
        ("event_type_check", event_type_check(entry.get("event_type", ""))),
        ("sig_verify", sig_verify(entry, phoenix_key)),
        ("hash_verify", hash_verify(entry, expected_hash_prev)),
        ("replay_check", replay_check(entry, last_seen_seq)),
        ("gt_monotonic_check", gt_monotonic_check(entry, last_seen_gt)),
    ]

    for name, (outcome, failure) in checks:
        if failure is not None:
            failures.append(failure)
            log.warning("Verification %s: %s (seq=%s)", name, outcome.value, entry.get("seq"))

        if outcome == VerifyOutcome.HALT:
            return VerifyOutcome.HALT, failures
        if outcome == VerifyOutcome.FAIL:
            return VerifyOutcome.FAIL, failures
        if outcome == VerifyOutcome.WARN and worst == VerifyOutcome.PASS:
            worst = VerifyOutcome.WARN

    return worst, failures


def _safe_snapshot(entry: dict[str, Any]) -> dict[str, Any]:
    """Snapshot of entry for failure struct — exclude large payload."""
    return {
        k: v for k, v in entry.items()
        if k != "payload"
    }
