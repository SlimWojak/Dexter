"""Deterministic SHA-256 hashing over canonical JSON (Spec Section 5.1).

Hash input: ALL fields EXCEPT hash_self and merkle_batch_id.
Canonical JSON: sorted keys, no whitespace, UTF-8.
Same inputs MUST produce same hash.
"""

import hashlib
import json

from bead_field.schema.core import BeadCore

EXCLUDED_FROM_HASH = frozenset({"hash_self", "merkle_batch_id"})


def canonical_json(bead: BeadCore) -> str:
    """Produce canonical JSON string for hash computation.

    Uses model_dump(mode='json') for consistent serialization of
    datetimes, enums, and nested models, then strips excluded fields.
    """
    data = bead.model_dump(mode="json")
    for key in EXCLUDED_FROM_HASH:
        data.pop(key, None)
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_hash(bead: BeadCore) -> str:
    """Compute hex-encoded SHA-256 of a bead's canonical JSON."""
    return hashlib.sha256(canonical_json(bead).encode("utf-8")).hexdigest()
