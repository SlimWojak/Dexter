"""Version-tracked schema migrations (ChadBoar learning #2).

Numbered migrations with up/down. No CREATE IF NOT EXISTS.
Migration table tracks applied versions. Tested before Genesis load (Owl advisory).
"""

import sqlite3
from datetime import datetime, timezone
from typing import Callable

Migration = tuple[str, Callable[[sqlite3.Connection], None], Callable[[sqlite3.Connection], None]]

MIGRATIONS: list[Migration] = [
    (
        "001_initial_schema",
        lambda conn: conn.executescript("""
            CREATE TABLE beads (
                bead_id TEXT PRIMARY KEY,
                bead_type TEXT NOT NULL,
                content TEXT NOT NULL,
                world_time_valid_from TEXT,
                world_time_valid_to TEXT,
                knowledge_time_recorded_at TEXT NOT NULL,
                temporal_class TEXT NOT NULL,
                source_ref TEXT NOT NULL,
                lineage TEXT NOT NULL,
                hash_self TEXT NOT NULL,
                hash_prev TEXT,
                merkle_batch_id TEXT,
                attestation TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                superseded_by TEXT,
                retraction_reason TEXT,
                tags TEXT NOT NULL
            );

            CREATE TABLE merkle_batches (
                batch_id TEXT PRIMARY KEY,
                merkle_root TEXT NOT NULL,
                bead_count INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                trigger_bead_id TEXT
            );

            CREATE INDEX idx_beads_type ON beads(bead_type);
            CREATE INDEX idx_beads_wt_from ON beads(world_time_valid_from);
            CREATE INDEX idx_beads_wt_to ON beads(world_time_valid_to);
            CREATE INDEX idx_beads_kt ON beads(knowledge_time_recorded_at);
            CREATE INDEX idx_beads_temporal_class ON beads(temporal_class);
            CREATE INDEX idx_beads_status ON beads(status);
            CREATE INDEX idx_beads_merkle ON beads(merkle_batch_id);

            -- INV-BEAD-IMMUTABLE: block UPDATE on content and integrity fields
            CREATE TRIGGER trg_bead_immutable
            BEFORE UPDATE ON beads
            WHEN OLD.content != NEW.content
              OR OLD.bead_type != NEW.bead_type
              OR OLD.temporal_class != NEW.temporal_class
              OR OLD.source_ref != NEW.source_ref
              OR OLD.lineage != NEW.lineage
              OR OLD.hash_self != NEW.hash_self
              OR OLD.hash_prev != NEW.hash_prev
              OR OLD.knowledge_time_recorded_at != NEW.knowledge_time_recorded_at
              OR OLD.world_time_valid_from IS NOT NEW.world_time_valid_from
              OR OLD.world_time_valid_to IS NOT NEW.world_time_valid_to
              OR OLD.attestation != NEW.attestation
            BEGIN
              SELECT RAISE(ABORT, 'INV-BEAD-IMMUTABLE: cannot modify structural bead fields');
            END;
        """),
        lambda conn: conn.executescript("""
            DROP TRIGGER IF EXISTS trg_bead_immutable;
            DROP INDEX IF EXISTS idx_beads_merkle;
            DROP INDEX IF EXISTS idx_beads_status;
            DROP INDEX IF EXISTS idx_beads_temporal_class;
            DROP INDEX IF EXISTS idx_beads_kt;
            DROP INDEX IF EXISTS idx_beads_wt_to;
            DROP INDEX IF EXISTS idx_beads_wt_from;
            DROP INDEX IF EXISTS idx_beads_type;
            DROP TABLE IF EXISTS merkle_batches;
            DROP TABLE IF EXISTS beads;
        """),
    ),
]


def _ensure_migration_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )
    """)


def get_current_version(conn: sqlite3.Connection) -> int:
    _ensure_migration_table(conn)
    row = conn.execute("SELECT MAX(version) FROM migrations").fetchone()
    return row[0] if row[0] is not None else 0


def apply_migrations(conn: sqlite3.Connection) -> int:
    """Apply all pending migrations. Returns number applied."""
    _ensure_migration_table(conn)
    current = get_current_version(conn)
    applied = 0

    for i, (name, up, _down) in enumerate(MIGRATIONS, start=1):
        if i > current:
            up(conn)
            conn.execute(
                "INSERT INTO migrations (version, name, applied_at) VALUES (?, ?, ?)",
                (i, name, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
            applied += 1

    return applied


def rollback_last(conn: sqlite3.Connection) -> int:
    """Roll back the most recent migration. Returns new version."""
    current = get_current_version(conn)
    if current == 0:
        return 0

    _name, _up, down = MIGRATIONS[current - 1]
    down(conn)
    conn.execute("DELETE FROM migrations WHERE version = ?", (current,))
    conn.commit()
    return current - 1
