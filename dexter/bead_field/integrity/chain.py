"""Per-stream hash chain for tamper detection (Spec Section 5.1).

Each bead in a stream links to the previous via hash_prev.
hash_prev is INCLUDED in the hash input, so tampering with any
field (including linkage) causes hash_self to mismatch.
"""

from bead_field.schema.core import BeadCore
from .hashing import compute_hash


class HashChainError(Exception):
    """Raised when hash chain integrity is violated."""

    def __init__(self, message: str, bead_index: int, bead_id: str):
        self.bead_index = bead_index
        self.bead_id = bead_id
        super().__init__(message)


def verify_hash_self(bead: BeadCore) -> bool:
    """Verify that a bead's stored hash_self matches its computed hash."""
    return bead.hash_self == compute_hash(bead)


def verify_chain(beads: list[BeadCore]) -> bool:
    """Verify hash chain integrity for an ordered sequence of beads.

    Beads must be in chronological order (oldest first).
    Raises HashChainError on first integrity violation found.
    Returns True if chain is intact.
    """
    if not beads:
        return True

    for i, bead in enumerate(beads):
        computed = compute_hash(bead)
        if bead.hash_self != computed:
            raise HashChainError(
                f"Hash mismatch at index {i}: stored={bead.hash_self} "
                f"computed={computed}",
                bead_index=i,
                bead_id=bead.bead_id,
            )

        if i == 0:
            continue

        expected_prev = beads[i - 1].hash_self
        if bead.hash_prev != expected_prev:
            raise HashChainError(
                f"Chain break at index {i}: hash_prev={bead.hash_prev} "
                f"expected={expected_prev}",
                bead_index=i,
                bead_id=bead.bead_id,
            )

    return True


def append_to_chain(
    bead: BeadCore, prev_bead: BeadCore | None = None
) -> BeadCore:
    """Link a bead into the chain by computing hash_prev and hash_self.

    1. Set hash_prev from prev_bead (or None for first in stream)
    2. Compute hash_self over all fields (hash_prev included, hash_self excluded)
    3. Return new bead instance with both fields set
    """
    hash_prev = prev_bead.hash_self if prev_bead else None

    linked = bead.model_copy(update={"hash_prev": hash_prev, "hash_self": ""})
    hash_self = compute_hash(linked)
    return linked.model_copy(update={"hash_self": hash_self})
