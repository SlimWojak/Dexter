"""Bead integrity verification for the query layer.

verify_bead checks hash, chain linkage, Merkle proof, and optionally
signatures for a single bead. Uses the existing bead_field schema and
hashing infrastructure for exact format matching.
"""

import hashlib
import json
import sqlite3
from dataclasses import dataclass

from bead_field.integrity.hashing import compute_hash
from bead_field.schema import parse_bead


@dataclass
class VerificationResult:
    hash_valid: bool
    chain_valid: bool
    merkle_valid: bool | None
    sig_valid: bool | None
    proof_depth: int | None
    batch_id: str | None


def _merkle_hash_pair(left: str, right: str) -> str:
    """Replicate the exact Merkle hash construction from integrity/merkle.py.

    CRITICAL: concatenates hex strings as UTF-8, NOT raw bytes.
    """
    combined = (left + right).encode("utf-8")
    return hashlib.sha256(combined).hexdigest()


def _row_to_bead(row: sqlite3.Row):
    """Reconstruct a typed Bead from a database row using parse_bead."""
    data = {
        "bead_id": row["bead_id"],
        "bead_type": row["bead_type"],
        "content": json.loads(row["content"]),
        "world_time_valid_from": row["world_time_valid_from"],
        "world_time_valid_to": row["world_time_valid_to"],
        "knowledge_time_recorded_at": row["knowledge_time_recorded_at"],
        "temporal_class": row["temporal_class"],
        "source_ref": json.loads(row["source_ref"]),
        "lineage": json.loads(row["lineage"]),
        "hash_self": row["hash_self"],
        "hash_prev": row["hash_prev"],
        "merkle_batch_id": row["merkle_batch_id"],
        "attestation": json.loads(row["attestation"]),
        "status": row["status"],
        "superseded_by": row["superseded_by"],
        "retraction_reason": row["retraction_reason"],
        "tags": json.loads(row["tags"]),
    }
    return parse_bead(data)


def _verify_merkle(
    hash_self: str, batch_id: str, conn: sqlite3.Connection,
) -> tuple[bool, int | None]:
    """Verify a bead's Merkle proof by reconstructing the tree from its batch."""
    batch_row = conn.execute(
        "SELECT merkle_root, bead_count FROM merkle_batches WHERE batch_id = ?",
        (batch_id,),
    ).fetchone()
    if not batch_row:
        return False, None

    stored_root = batch_row[0]

    leaves_rows = conn.execute(
        "SELECT hash_self FROM beads WHERE merkle_batch_id = ? ORDER BY bead_id",
        (batch_id,),
    ).fetchall()
    leaves = [r[0] for r in leaves_rows]

    if not leaves:
        return False, None

    if hash_self not in leaves:
        return False, None

    current = list(leaves)
    depth = 0
    while len(current) > 1:
        next_layer = []
        for i in range(0, len(current), 2):
            left = current[i]
            right = current[i + 1] if i + 1 < len(current) else left
            next_layer.append(_merkle_hash_pair(left, right))
        current = next_layer
        depth += 1

    computed_root = current[0]
    return computed_root == stored_root, depth


def verify_bead(db_path: str, bead_id: str) -> VerificationResult:
    """Verify integrity of a single bead.

    Checks:
        hash_valid: hash_self matches recomputed hash from bead fields
        chain_valid: hash_prev matches predecessor's hash_self
        merkle_valid: Merkle proof reconstructed and verified against batch root
        sig_valid: None (requires key material not stored in DB)
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM beads WHERE bead_id = ?", (bead_id,)
        ).fetchone()
        if not row:
            raise ValueError(f"Bead {bead_id} not found")

        bead = _row_to_bead(row)
        computed_hash = compute_hash(bead)
        hash_valid = computed_hash == row["hash_self"]

        chain_valid = True
        if row["hash_prev"]:
            prev_row = conn.execute(
                "SELECT hash_self FROM beads WHERE hash_self = ?",
                (row["hash_prev"],),
            ).fetchone()
            chain_valid = prev_row is not None

        merkle_valid = None
        proof_depth = None
        batch_id = row["merkle_batch_id"]
        if batch_id:
            merkle_valid, proof_depth = _verify_merkle(
                row["hash_self"], batch_id, conn,
            )

        return VerificationResult(
            hash_valid=hash_valid,
            chain_valid=chain_valid,
            merkle_valid=merkle_valid,
            sig_valid=None,
            proof_depth=proof_depth,
            batch_id=batch_id,
        )
    finally:
        conn.close()
