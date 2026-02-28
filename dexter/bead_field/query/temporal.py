"""Bi-temporal query helpers for the bead field query layer.

known_at implements the canonical bi-temporal query from
BEAD_FIELD_SPEC Section 4.4: "What did we know at KT about WT range?"
"""

import json
import sqlite3
from dataclasses import dataclass

from .timestamps import normalize_timestamp


@dataclass
class BeadRecord:
    """Lightweight bead representation for query results.

    Content is the parsed JSON dict, not a Pydantic model,
    for query-layer performance.
    """
    bead_id: str
    bead_type: str
    content: dict
    world_time_valid_from: str | None
    world_time_valid_to: str | None
    knowledge_time_recorded_at: str
    hash_self: str
    tags: list[str]


def known_at(
    kt_cutoff: str,
    wt_from: str,
    wt_to: str,
    db_path: str,
) -> list[BeadRecord]:
    """What did we know at time kt_cutoff about the world_time range?

    Returns all beads where:
        - knowledge_time_recorded_at <= kt_cutoff
        - world_time_valid_from >= wt_from
        - world_time_valid_from < wt_to

    All timestamps are normalized to canonical UTC form before query.

    Note on synthetic data: all KT values are near 2026-02-28 (ingestion
    date). KT predicate has ~0% selectivity on synthetic field. This is
    expected; real-time ingestion will produce meaningful KT spread.
    """
    kt_norm = normalize_timestamp(kt_cutoff)
    wt_from_norm = normalize_timestamp(wt_from)
    wt_to_norm = normalize_timestamp(wt_to)

    sql = """
    SELECT bead_id, bead_type, content,
           world_time_valid_from, world_time_valid_to,
           knowledge_time_recorded_at, hash_self, tags
    FROM beads
    WHERE world_time_valid_from >= ?
      AND world_time_valid_from < ?
      AND knowledge_time_recorded_at <= ?
    ORDER BY world_time_valid_from
    """

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(sql, (wt_from_norm, wt_to_norm, kt_norm))
        rows = cur.fetchall()

        return [
            BeadRecord(
                bead_id=r["bead_id"],
                bead_type=r["bead_type"],
                content=json.loads(r["content"]),
                world_time_valid_from=r["world_time_valid_from"],
                world_time_valid_to=r["world_time_valid_to"],
                knowledge_time_recorded_at=r["knowledge_time_recorded_at"],
                hash_self=r["hash_self"],
                tags=json.loads(r["tags"]),
            )
            for r in rows
        ]
    finally:
        conn.close()
