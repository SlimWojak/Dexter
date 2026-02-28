"""Tests for walk_chain — T3 gate."""

import os
import time
import statistics

import pytest

from bead_field.query.chain import walk_chain, ChainIntegrityError, ChainEntry

EURUSD_DB = os.path.expanduser("~/dexter/tools/synthetic/synthetic_beads.db")
SKIP_SYNTHETIC = not os.path.exists(EURUSD_DB)
skip_no_db = pytest.mark.skipif(SKIP_SYNTHETIC, reason="Synthetic DB not available")


def _get_mid_bead_id() -> str:
    import sqlite3
    conn = sqlite3.connect(EURUSD_DB)
    cur = conn.cursor()
    cur.execute(
        "SELECT bead_id FROM beads ORDER BY world_time_valid_from LIMIT 1 OFFSET 500000"
    )
    bead_id = cur.fetchone()[0]
    conn.close()
    return bead_id


@skip_no_db
class TestWalkChain:
    def test_walk_10_steps(self):
        bead_id = _get_mid_bead_id()
        entries = walk_chain(EURUSD_DB, bead_id, steps=10)
        assert len(entries) == 11  # start + 10 steps
        assert entries[0].bead_id == bead_id
        assert all(isinstance(e, ChainEntry) for e in entries)

    def test_walk_10000_under_1s(self):
        """T3 gate: walk_chain(any_bead, 10_000) completes < 1s."""
        bead_id = _get_mid_bead_id()
        times = []
        for _ in range(3):
            t0 = time.monotonic()
            entries = walk_chain(EURUSD_DB, bead_id, steps=10_000)
            t1 = time.monotonic()
            times.append((t1 - t0) * 1000)
        median_ms = statistics.median(times)
        assert len(entries) > 1000
        assert median_ms < 1000, f"10K walk took {median_ms:.1f}ms, gate is <1000ms"

    def test_chain_linkage_verified(self):
        bead_id = _get_mid_bead_id()
        entries = walk_chain(EURUSD_DB, bead_id, steps=100, verify=True)
        for i in range(1, len(entries)):
            assert entries[i].hash_self == entries[i - 1].hash_prev

    def test_walk_beyond_chain_returns_partial(self):
        """When steps > available chain, return what exists."""
        import sqlite3
        conn = sqlite3.connect(EURUSD_DB)
        cur = conn.cursor()
        cur.execute(
            "SELECT bead_id FROM beads WHERE hash_prev IS NULL LIMIT 1"
        )
        first_bead = cur.fetchone()[0]
        conn.close()

        entries = walk_chain(EURUSD_DB, first_bead, steps=100)
        assert len(entries) == 1  # first bead has no predecessor

    def test_forward_raises_not_implemented(self):
        bead_id = _get_mid_bead_id()
        with pytest.raises(NotImplementedError, match="Forward chain traversal"):
            walk_chain(EURUSD_DB, bead_id, steps=10, direction="forward")

    def test_invalid_bead_id_raises(self):
        with pytest.raises(ValueError, match="not found"):
            walk_chain(EURUSD_DB, "nonexistent-bead-id", steps=10)

    def test_entries_have_world_time(self):
        bead_id = _get_mid_bead_id()
        entries = walk_chain(EURUSD_DB, bead_id, steps=5)
        for e in entries:
            assert e.world_time_valid_from is not None
