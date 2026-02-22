"""SQLite bi-temporal bead store (Spec Section 4 + Gate 1 exit criteria).

INV-BEAD-IMMUTABLE: INSERT only on bead content. No UPDATE on content after INSERT.
UPDATE allowed only on: status, superseded_by, retraction_reason, merkle_batch_id.
Unsigned beads rejected at insert. Duplicate bead_id rejected.
"""

import json
import sqlite3
from pathlib import Path

from bead_field.schema.core import BeadCore
from bead_field.schema import parse_bead
from .migrations import apply_migrations


class BeadStoreError(Exception):
    pass


class ImmutabilityViolation(BeadStoreError):
    pass


class UnsignedBeadError(BeadStoreError):
    pass


class DuplicateBeadError(BeadStoreError):
    pass


class BeadStore:
    """Bi-temporal SQLite store for structural beads.

    SQLite is the Gate 1 proxy. Swappable to XTDB on M3 Ultra.
    """

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        apply_migrations(self._conn)

    @property
    def connection(self) -> sqlite3.Connection:
        return self._conn

    def insert(self, bead: BeadCore) -> None:
        """Insert a signed bead. Rejects unsigned or duplicate beads."""
        att = bead.attestation
        if not att.ecdsa_sig and not att.pqc_sig:
            raise UnsignedBeadError(
                f"Bead {bead.bead_id} has no signatures (INV-BEAD-SIGNED)"
            )

        wt_from = bead.world_time_valid_from.isoformat() if bead.world_time_valid_from else None
        wt_to = bead.world_time_valid_to.isoformat() if bead.world_time_valid_to else None

        try:
            self._conn.execute(
                """INSERT INTO beads (
                    bead_id, bead_type, content,
                    world_time_valid_from, world_time_valid_to,
                    knowledge_time_recorded_at, temporal_class,
                    source_ref, lineage,
                    hash_self, hash_prev, merkle_batch_id,
                    attestation, status, superseded_by, retraction_reason, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    bead.bead_id,
                    bead.bead_type.value if hasattr(bead.bead_type, "value") else bead.bead_type,
                    json.dumps(bead.content.model_dump(mode="json"), sort_keys=True),
                    wt_from,
                    wt_to,
                    bead.knowledge_time_recorded_at.isoformat(),
                    bead.temporal_class.value if hasattr(bead.temporal_class, "value") else bead.temporal_class,
                    json.dumps(bead.source_ref.model_dump(mode="json"), sort_keys=True),
                    json.dumps(bead.lineage),
                    bead.hash_self,
                    bead.hash_prev,
                    bead.merkle_batch_id,
                    json.dumps(bead.attestation.model_dump(mode="json"), sort_keys=True),
                    bead.status.value if hasattr(bead.status, "value") else bead.status,
                    bead.superseded_by,
                    bead.retraction_reason,
                    json.dumps(bead.tags),
                ),
            )
            self._conn.commit()
        except sqlite3.IntegrityError as e:
            if "UNIQUE" in str(e) or "PRIMARY KEY" in str(e):
                raise DuplicateBeadError(
                    f"Bead {bead.bead_id} already exists"
                ) from e
            raise

    def get(self, bead_id: str) -> BeadCore | None:
        """Retrieve a single bead by ID."""
        row = self._conn.execute(
            "SELECT * FROM beads WHERE bead_id = ?", (bead_id,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_bead(row)

    def update_status(
        self,
        bead_id: str,
        status: str,
        superseded_by: str | None = None,
        retraction_reason: str | None = None,
    ) -> None:
        """Update operational fields only (INV-BEAD-IMMUTABLE safe)."""
        self._conn.execute(
            """UPDATE beads SET status = ?, superseded_by = ?, retraction_reason = ?
               WHERE bead_id = ?""",
            (status, superseded_by, retraction_reason, bead_id),
        )
        self._conn.commit()

    def set_merkle_batch_id(self, bead_id: str, batch_id: str) -> None:
        """Backfill merkle_batch_id after Merkle anchoring."""
        self._conn.execute(
            "UPDATE beads SET merkle_batch_id = ? WHERE bead_id = ?",
            (batch_id, bead_id),
        )
        self._conn.commit()

    def count(self, bead_type: str | None = None) -> int:
        if bead_type:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM beads WHERE bead_type = ?", (bead_type,)
            ).fetchone()
        else:
            row = self._conn.execute("SELECT COUNT(*) FROM beads").fetchone()
        return row[0]

    def _row_to_bead(self, row: sqlite3.Row) -> BeadCore:
        """Reconstruct a typed Bead from a database row."""
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

    def close(self) -> None:
        self._conn.close()
