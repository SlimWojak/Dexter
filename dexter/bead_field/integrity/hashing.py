"""Deterministic SHA-256 hashing over canonical JSON (Spec Section 5.1).

Hash input: ALL fields EXCEPT hash_self, merkle_batch_id, and signature bytes.
Signatures are computed FROM the hash, so including them would be circular.
Attestation metadata (air_node_id, code_hash, model_hash, container_hash) IS included.
Canonical JSON: sorted keys, no whitespace, UTF-8.
Same inputs MUST produce same hash.
"""

import hashlib
import json

from bead_field.schema.core import BeadCore

EXCLUDED_FROM_HASH = frozenset({"hash_self", "merkle_batch_id"})
EXCLUDED_ATTESTATION_FIELDS = frozenset({"ecdsa_sig", "pqc_sig", "signing_cert_chain"})


def canonical_json(bead: BeadCore) -> str:
    """Produce canonical JSON string for hash computation.

    Uses model_dump(mode='json') for consistent serialization of
    datetimes, enums, and nested models, then strips excluded fields.
    Attestation signature bytes excluded (they're computed from this hash).
    """
    data = bead.model_dump(mode="json")
    for key in EXCLUDED_FROM_HASH:
        data.pop(key, None)
    if "attestation" in data:
        for sig_field in EXCLUDED_ATTESTATION_FIELDS:
            data["attestation"].pop(sig_field, None)
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_hash(bead: BeadCore) -> str:
    """Compute hex-encoded SHA-256 of a bead's canonical JSON."""
    return hashlib.sha256(canonical_json(bead).encode("utf-8")).hexdigest()
