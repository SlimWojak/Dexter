"""Bi-temporal query helpers (Spec Section 4.4).

These implement the physics experiment queries:
- WT range: "What was happening in the world during period X?"
- KT as-of: "What did we know at time Y?"
- Combined: "What did we know at Y about period X?" (Gate 1 exit criterion)
- Lineage: "What depends on this bead?"
- Refinery latency: "How fast did we learn?" (WT-KT delta)
"""

import json
import sqlite3
from datetime import datetime

from bead_field.schema.core import BeadCore
from bead_field.schema import parse_bead


def _rows_to_beads(cursor: sqlite3.Cursor) -> list[BeadCore]:
    rows = cursor.fetchall()
    beads = []
    for row in rows:
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
        beads.append(parse_bead(data))
    return beads


def query_by_wt_range(
    conn: sqlite3.Connection,
    wt_from: datetime,
    wt_to: datetime,
) -> list[BeadCore]:
    """Beads with world_time overlapping the given range."""
    cursor = conn.execute(
        """SELECT * FROM beads
           WHERE world_time_valid_from IS NOT NULL
             AND world_time_valid_to IS NOT NULL
             AND world_time_valid_from <= ?
             AND world_time_valid_to >= ?
           ORDER BY knowledge_time_recorded_at""",
        (wt_to.isoformat(), wt_from.isoformat()),
    )
    return _rows_to_beads(cursor)


def query_by_kt_asof(
    conn: sqlite3.Connection,
    asof_time: datetime,
) -> list[BeadCore]:
    """Beads known at or before the given knowledge time."""
    cursor = conn.execute(
        """SELECT * FROM beads
           WHERE knowledge_time_recorded_at <= ?
           ORDER BY knowledge_time_recorded_at""",
        (asof_time.isoformat(),),
    )
    return _rows_to_beads(cursor)


def query_by_type_and_wt(
    conn: sqlite3.Connection,
    bead_type: str,
    wt_from: datetime,
    wt_to: datetime,
) -> list[BeadCore]:
    """Beads of a specific type with world_time overlapping the range."""
    cursor = conn.execute(
        """SELECT * FROM beads
           WHERE bead_type = ?
             AND world_time_valid_from IS NOT NULL
             AND world_time_valid_to IS NOT NULL
             AND world_time_valid_from <= ?
             AND world_time_valid_to >= ?
           ORDER BY knowledge_time_recorded_at""",
        (bead_type, wt_to.isoformat(), wt_from.isoformat()),
    )
    return _rows_to_beads(cursor)


def query_by_kt_asof_and_wt_range(
    conn: sqlite3.Connection,
    kt_asof: datetime,
    wt_from: datetime,
    wt_to: datetime,
    bead_type: str | None = None,
) -> list[BeadCore]:
    """The canonical bi-temporal query: "What did we know at kt_asof about period [wt_from, wt_to]?"

    This is Gate 1 exit criterion EC1.
    """
    sql = """SELECT * FROM beads
             WHERE knowledge_time_recorded_at <= ?
               AND world_time_valid_from IS NOT NULL
               AND world_time_valid_to IS NOT NULL
               AND world_time_valid_from >= ?
               AND world_time_valid_to <= ?"""
    params: list = [kt_asof.isoformat(), wt_from.isoformat(), wt_to.isoformat()]

    if bead_type:
        sql += " AND bead_type = ?"
        params.append(bead_type)

    sql += " ORDER BY knowledge_time_recorded_at"
    cursor = conn.execute(sql, params)
    return _rows_to_beads(cursor)


def query_by_lineage(
    conn: sqlite3.Connection,
    bead_id: str,
) -> list[BeadCore]:
    """All beads that reference the given bead_id in their lineage."""
    cursor = conn.execute(
        """SELECT * FROM beads
           WHERE lineage LIKE ?
           ORDER BY knowledge_time_recorded_at""",
        (f'%"{bead_id}"%',),
    )
    return _rows_to_beads(cursor)


def query_pattern_beads(
    conn: sqlite3.Connection,
    bead_type: str | None = None,
) -> list[BeadCore]:
    """All PATTERN-class beads (timeless methodology). Used for Genesis queries."""
    sql = "SELECT * FROM beads WHERE temporal_class = 'PATTERN'"
    params: list = []
    if bead_type:
        sql += " AND bead_type = ?"
        params.append(bead_type)
    sql += " ORDER BY knowledge_time_recorded_at"
    cursor = conn.execute(sql, params)
    return _rows_to_beads(cursor)


def refinery_latency(
    conn: sqlite3.Connection,
    bead_id: str,
) -> float | None:
    """WT-KT delta in seconds for a specific bead (Spec Section 4.3).

    Returns None if bead not found or has no world_time.
    Near-zero = anomaly (hallucination detector).
    """
    row = conn.execute(
        """SELECT world_time_valid_to, knowledge_time_recorded_at
           FROM beads WHERE bead_id = ?""",
        (bead_id,),
    ).fetchone()

    if row is None or row["world_time_valid_to"] is None:
        return None

    wt_end = datetime.fromisoformat(row["world_time_valid_to"])
    kt = datetime.fromisoformat(row["knowledge_time_recorded_at"])
    return (kt - wt_end).total_seconds()
