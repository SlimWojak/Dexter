"""
Envelope constructor — seals verified entries into BridgeEnvelopes.

BRIDGE_SPEC_v0.2 Section 2.1.

Takes VerifiedEntry (from reader), constructs BridgeEnvelope with:
  - Temporal snapshot (GT frozen at construction time)
  - Provenance layering (Athena pass-through, Bridge provenance added)
  - Notary seal (Bridge's own HMAC-SHA256 over envelope hash)

Two-key chain (INV-BRIDGE-SIG-CHAIN):
  Phoenix signs the log entry → source_signature (pass-through)
  Bridge signs the envelope → bridge_seal (added here)

INV-BRIDGE-KEY-ISOLATION: Bridge key ≠ Phoenix key.
INV-BRIDGE-ENVELOPE-COMPLETE: All fields populated or reject.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bridge.types import (
    BRIDGE_VERSION,
    BridgeEnvelope,
    MerkleStatus,
    VerifiedEntry,
)

log = logging.getLogger(__name__)

DEFAULT_BRIDGE_KEY_DIR = Path.home() / "dexter" / "data" / "bridge_keys"


def _canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _hmac_sign(key: bytes, data: str) -> str:
    return hmac.new(key, data.encode("utf-8"), hashlib.sha256).hexdigest()


def load_or_create_bridge_key(
    key_dir: Path | None = None,
    key_id: str = "bridge-notary-v1",
) -> bytes:
    """Load Bridge signing key from disk, or generate and persist a new one."""
    kd = key_dir or DEFAULT_BRIDGE_KEY_DIR
    kd.mkdir(parents=True, exist_ok=True)
    key_path = kd / f"{key_id}.key"
    if key_path.exists():
        return key_path.read_bytes()
    key = secrets.token_bytes(32)
    fd = os.open(str(key_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(fd, key)
    finally:
        os.close(fd)
    log.info("Generated bridge signing key: %s", key_path)
    return key


class EnvelopeConstructor:
    """Wraps VerifiedEntry into sealed BridgeEnvelope.

    INV-BRIDGE-ENVELOPE-COMPLETE: All fields populated.
    INV-BRIDGE-SIG-CHAIN: Phoenix sig preserved, Bridge sig added.
    """

    def __init__(
        self,
        bridge_key: bytes,
        bridge_key_id: str = "bridge-notary-v1",
    ) -> None:
        self._key = bridge_key
        self._key_id = bridge_key_id

    def seal(self, entry: VerifiedEntry) -> BridgeEnvelope:
        """Construct and seal a BridgeEnvelope from a verified entry."""
        event_id = _sha256_hex(_canonical_json(entry.payload))

        athena_ref = {
            "athena_hash": entry.athena_hash,
            "athena_index": entry.athena_index,
        }

        hash_chain_proof = {
            "hash_self": entry.athena_hash,
            "hash_prev": entry.hash_prev,
            "merkle_proof": None,
            "merkle_status": MerkleStatus.DEFERRED.value,
        }

        sealed_at = datetime.now(UTC).isoformat()

        envelope_hashable = {
            "version": BRIDGE_VERSION,
            "event_id": event_id,
            "event_type": entry.event_type,
            "payload": entry.payload,
            "gt_timestamp": entry.timestamp,
            "athena_ref": athena_ref,
            "hash_chain_proof": hash_chain_proof,
            "replay_guard": entry.seq,
            "sealed_at": sealed_at,
        }
        envelope_hash = _sha256_hex(_canonical_json(envelope_hashable))

        bridge_seal = {
            "bridge_sig": _hmac_sign(self._key, envelope_hash),
            "bridge_key_id": self._key_id,
            "sealed_at": sealed_at,
            "bridge_version": BRIDGE_VERSION,
        }

        return BridgeEnvelope(
            version=BRIDGE_VERSION,
            event_id=event_id,
            event_type=entry.event_type,
            payload=entry.payload,
            gt_timestamp=entry.timestamp,
            athena_ref=athena_ref,
            source_signature=entry.source_signature,
            hash_chain_proof=hash_chain_proof,
            replay_guard=entry.seq,
            bridge_seal=bridge_seal,
        )

    def verify_seal(self, envelope: BridgeEnvelope) -> bool:
        """Verify Bridge's own seal on an envelope."""
        envelope_hashable = {
            "version": envelope.version,
            "event_id": envelope.event_id,
            "event_type": envelope.event_type,
            "payload": envelope.payload,
            "gt_timestamp": envelope.gt_timestamp,
            "athena_ref": envelope.athena_ref,
            "hash_chain_proof": envelope.hash_chain_proof,
            "replay_guard": envelope.replay_guard,
            "sealed_at": envelope.bridge_seal.get("sealed_at", ""),
        }
        envelope_hash = _sha256_hex(_canonical_json(envelope_hashable))
        expected_sig = _hmac_sign(self._key, envelope_hash)
        return hmac.compare_digest(
            expected_sig, envelope.bridge_seal.get("bridge_sig", "")
        )

    @property
    def key_id(self) -> str:
        return self._key_id
