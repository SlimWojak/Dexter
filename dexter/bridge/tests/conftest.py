"""Shared fixtures for Bridge tests.

Creates a real Phoenix governance log on disk that Bridge modules consume.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

GENESIS_HASH = "0" * 64


def _canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


class FakeGovernanceLog:
    """Writes governance_log.jsonl entries in the same format as Phoenix."""

    def __init__(self, log_dir: Path, key: bytes) -> None:
        self.log_path = log_dir / "governance_log.jsonl"
        self.key = key
        self._seq = 0
        self._hash_prev = GENESIS_HASH

    def append(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._seq += 1
        timestamp = datetime.now(UTC).isoformat()

        hashable = {
            "seq": self._seq,
            "event_type": event_type,
            "payload": payload,
            "timestamp": timestamp,
            "hash_prev": self._hash_prev,
        }
        hash_self = _sha256_hex(_canonical_json(hashable))
        sig = hmac.new(self.key, hash_self.encode("utf-8"), hashlib.sha256).hexdigest()

        entry = {
            "seq": self._seq,
            "event_type": event_type,
            "payload": payload,
            "timestamp": timestamp,
            "hash_prev": self._hash_prev,
            "athena_index": self._seq,
            "athena_hash": hash_self,
            "source_signature": {
                "sig": sig,
                "algorithm": "hmac-sha256",
                "key_id": "phoenix-gov-v1",
            },
        }

        line = _canonical_json(entry) + "\n"
        fd = os.open(str(self.log_path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            os.write(fd, line.encode("utf-8"))
            os.fsync(fd)
        finally:
            os.close(fd)

        self._hash_prev = hash_self
        return entry


@pytest.fixture()
def phoenix_key() -> bytes:
    return secrets.token_bytes(32)


@pytest.fixture()
def log_dir(tmp_path: Path) -> Path:
    d = tmp_path / "phoenix_data"
    d.mkdir()
    return d


@pytest.fixture()
def state_dir(tmp_path: Path) -> Path:
    d = tmp_path / "bridge_state"
    d.mkdir()
    return d


@pytest.fixture()
def fake_log(log_dir: Path, phoenix_key: bytes) -> FakeGovernanceLog:
    return FakeGovernanceLog(log_dir, phoenix_key)


@pytest.fixture()
def populated_log(fake_log: FakeGovernanceLog) -> FakeGovernanceLog:
    """A log with 5 mixed governance events."""
    fake_log.append("LEASE_ACTIVATION", {
        "lease_id": "lease_001", "strategy_ref": "STRAT_v1.0.0",
        "bounds_snapshot": {"max_drawdown_pct": 5.0},
    })
    fake_log.append("STATE_LOCK", {
        "lease_id": "lease_001", "prior_state": "DRAFT",
        "prior_state_hash": "abc", "requested_transition": "DRAFT→ACTIVE",
        "transition_result": "SUCCESS",
    })
    fake_log.append("CALIBRATION", {
        "cartridge_ref": "STRAT_v1.0.0", "lease_id": "lease_001",
        "drift_pct": 1.2, "verdict": "PASS",
    })
    fake_log.append("ATTESTATION", {
        "lease_id": "lease_001", "decision": "RENEW", "new_lease_id": None,
    })
    fake_log.append("LEASE_EXPIRY", {
        "lease_id": "lease_001", "final_stats": {"trades": 12},
    })
    return fake_log
