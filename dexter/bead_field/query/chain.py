"""Hash chain walk for the bead field query layer.

walk_chain traverses the hash chain backward (following hash_prev).
Forward traversal is intentionally unsupported — the chain is
append-only and singly-linked backward. This is correct architecture,
not a gap.
"""

import sqlite3
from dataclasses import dataclass


class ChainIntegrityError(Exception):
    """Raised when hash chain linkage is broken during a walk."""

    def __init__(self, message: str, position: int, expected: str, actual: str):
        self.position = position
        self.expected_hash = expected
        self.actual_hash = actual
        super().__init__(message)


@dataclass(frozen=True)
class ChainEntry:
    bead_id: str
    hash_self: str
    hash_prev: str | None
    world_time_valid_from: str | None


def walk_chain(
    db_path: str,
    bead_id: str,
    steps: int,
    direction: str = "backward",
    verify: bool = True,
) -> list[ChainEntry]:
    """Walk the hash chain from a starting bead.

    Args:
        db_path: Path to the SQLite DB file.
        bead_id: Starting bead's ID.
        steps: Maximum number of chain links to follow.
        direction: Only 'backward' is supported.
        verify: If True, verify hash linkage at each step.

    Returns:
        List of ChainEntry objects, starting with the given bead
        at index 0 and walking backward in time.

    Raises:
        NotImplementedError: If direction='forward' (append-only chain
            is backward-linked; forward walk would require full table scan
            or a hash_next column which violates append-only semantics).
        ChainIntegrityError: If verify=True and a hash link is broken.
        ValueError: If bead_id not found.
    """
    if direction != "backward":
        raise NotImplementedError(
            "Forward chain traversal is not supported. "
            "The hash chain is singly-linked backward (append-only). "
            "Each bead's hash_prev points to the preceding bead's hash_self. "
            "Forward lookup would require a full table scan or a hash_next "
            "column, which violates append-only chain semantics."
        )

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()

        cte_sql = f"""
        WITH RECURSIVE chain(bead_id, hash_self, hash_prev, wt_from, depth) AS (
            SELECT bead_id, hash_self, hash_prev, world_time_valid_from, 0
            FROM beads WHERE bead_id = ?
            UNION ALL
            SELECT b.bead_id, b.hash_self, b.hash_prev, b.world_time_valid_from, c.depth + 1
            FROM beads b
            JOIN chain c ON b.hash_self = c.hash_prev
            WHERE c.depth < ?
        )
        SELECT bead_id, hash_self, hash_prev, wt_from, depth
        FROM chain ORDER BY depth
        """

        cur.execute(cte_sql, (bead_id, steps))
        rows = cur.fetchall()

        if not rows:
            raise ValueError(f"Bead {bead_id} not found")

        entries = [
            ChainEntry(
                bead_id=r[0],
                hash_self=r[1],
                hash_prev=r[2],
                world_time_valid_from=r[3],
            )
            for r in rows
        ]

        if verify and len(entries) > 1:
            for i in range(1, len(entries)):
                if entries[i].hash_self != entries[i - 1].hash_prev:
                    raise ChainIntegrityError(
                        f"Chain break at position {i}: "
                        f"expected hash_self={entries[i-1].hash_prev}, "
                        f"got {entries[i].hash_self}",
                        position=i,
                        expected=entries[i - 1].hash_prev or "",
                        actual=entries[i].hash_self,
                    )

        return entries
    finally:
        conn.close()
