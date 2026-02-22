"""Merkle tree + batch anchoring with hybrid trigger (Spec Section 5.2).

Trigger precedence (first wins):
  1. DECISION_BOUNDARY: SIGNAL or PROPOSAL committed
  2. MAX_BEADS: 500 beads since last anchor (configurable)
  3. MAX_TIME: 1 hour since last anchor (configurable)

Proof: given a leaf, produce path to root. Verify membership without full tree.
"""

import hashlib
import math
from datetime import datetime, timedelta, timezone
from uuid6 import uuid7

from bead_field.schema.core import BeadCore
from bead_field.schema.enums import BeadType
from bead_field.store.bitemporal import BeadStore


def _hash_pair(left: str, right: str) -> str:
    combined = (left + right).encode("utf-8")
    return hashlib.sha256(combined).hexdigest()


class MerkleTree:
    """Binary Merkle tree over a list of leaf hashes."""

    def __init__(self, leaves: list[str]) -> None:
        if not leaves:
            raise ValueError("Cannot build Merkle tree from empty leaf set")

        self.leaves = list(leaves)
        self._layers: list[list[str]] = [self.leaves[:]]
        self._build()

    def _build(self) -> None:
        current = self._layers[0]
        while len(current) > 1:
            next_layer = []
            for i in range(0, len(current), 2):
                left = current[i]
                right = current[i + 1] if i + 1 < len(current) else left
                next_layer.append(_hash_pair(left, right))
            self._layers.append(next_layer)
            current = next_layer

    @property
    def root(self) -> str:
        return self._layers[-1][0]

    @property
    def leaf_count(self) -> int:
        return len(self.leaves)

    def proof(self, leaf_index: int) -> list[tuple[str, str]]:
        """Generate inclusion proof for a leaf.

        Returns list of (sibling_hash, side) where side is 'L' or 'R'
        indicating which side the sibling is on.
        """
        if leaf_index < 0 or leaf_index >= len(self.leaves):
            raise IndexError(f"Leaf index {leaf_index} out of range [0, {len(self.leaves)})")

        proof_path = []
        idx = leaf_index
        for layer in self._layers[:-1]:
            if idx % 2 == 0:
                sibling_idx = idx + 1
                side = "R"
            else:
                sibling_idx = idx - 1
                side = "L"

            if sibling_idx < len(layer):
                proof_path.append((layer[sibling_idx], side))
            else:
                proof_path.append((layer[idx], side))

            idx //= 2

        return proof_path

    @staticmethod
    def verify_proof(leaf_hash: str, proof_path: list[tuple[str, str]], root: str) -> bool:
        """Verify a Merkle inclusion proof against a known root."""
        current = leaf_hash
        for sibling, side in proof_path:
            if side == "R":
                current = _hash_pair(current, sibling)
            else:
                current = _hash_pair(sibling, current)
        return current == root


class AnchorConfig:
    """Configurable trigger thresholds for Merkle batch anchoring."""

    def __init__(
        self,
        max_beads: int = 500,
        max_time_seconds: int = 3600,
    ) -> None:
        self.max_beads = max_beads
        self.max_time = timedelta(seconds=max_time_seconds)


DECISION_BOUNDARY_TYPES = frozenset({BeadType.SIGNAL, BeadType.PROPOSAL})


class BatchAnchor:
    """Manages Merkle batch anchoring with hybrid trigger logic."""

    def __init__(self, store: BeadStore, config: AnchorConfig | None = None) -> None:
        self.store = store
        self.config = config or AnchorConfig()
        self._pending_beads: list[BeadCore] = []
        self._last_anchor_time: datetime = datetime.now(timezone.utc)

    def record(self, bead: BeadCore) -> str | None:
        """Record a bead and check if anchoring should trigger.

        Returns batch_id if anchor fired, None otherwise.
        """
        self._pending_beads.append(bead)

        if self._should_anchor(bead):
            return self._anchor(trigger_bead=bead)
        return None

    def check_time_trigger(self) -> str | None:
        """Check time-based fallback trigger. Call periodically."""
        if not self._pending_beads:
            return None
        elapsed = datetime.now(timezone.utc) - self._last_anchor_time
        if elapsed >= self.config.max_time:
            return self._anchor(trigger_bead=None)
        return None

    @property
    def pending_count(self) -> int:
        return len(self._pending_beads)

    def _should_anchor(self, bead: BeadCore) -> bool:
        if bead.bead_type in DECISION_BOUNDARY_TYPES:
            return True
        if len(self._pending_beads) >= self.config.max_beads:
            return True
        return False

    def _anchor(self, trigger_bead: BeadCore | None) -> str:
        """Build Merkle tree, store batch, backfill bead_ids."""
        leaves = [b.hash_self for b in self._pending_beads]
        tree = MerkleTree(leaves)
        batch_id = str(uuid7())

        self.store.connection.execute(
            """INSERT INTO merkle_batches
               (batch_id, merkle_root, bead_count, timestamp, trigger_bead_id)
               VALUES (?, ?, ?, ?, ?)""",
            (
                batch_id,
                tree.root,
                tree.leaf_count,
                datetime.now(timezone.utc).isoformat(),
                trigger_bead.bead_id if trigger_bead else None,
            ),
        )

        for bead in self._pending_beads:
            self.store.set_merkle_batch_id(bead.bead_id, batch_id)

        self.store.connection.commit()
        self._pending_beads.clear()
        self._last_anchor_time = datetime.now(timezone.utc)

        return batch_id

    def get_batch(self, batch_id: str) -> dict | None:
        """Retrieve a Merkle batch record."""
        row = self.store.connection.execute(
            "SELECT * FROM merkle_batches WHERE batch_id = ?", (batch_id,)
        ).fetchone()
        if row is None:
            return None
        return dict(row)
