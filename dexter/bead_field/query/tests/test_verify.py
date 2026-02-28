"""Tests for verify_bead — T4 gate."""

import os
import sqlite3

import pytest

from bead_field.query.verify import verify_bead, VerificationResult

EURUSD_DB = os.path.expanduser("~/dexter/tools/synthetic/synthetic_beads.db")
SKIP_SYNTHETIC = not os.path.exists(EURUSD_DB)
skip_no_db = pytest.mark.skipif(SKIP_SYNTHETIC, reason="Synthetic DB not available")


def _get_bead_id(offset: int = 1000) -> str:
    conn = sqlite3.connect(EURUSD_DB)
    cur = conn.cursor()
    cur.execute(
        f"SELECT bead_id FROM beads ORDER BY world_time_valid_from LIMIT 1 OFFSET {offset}"
    )
    bead_id = cur.fetchone()[0]
    conn.close()
    return bead_id


@skip_no_db
class TestVerifyBead:
    def test_valid_bead_all_true(self):
        """T4 gate: verify_bead(valid_bead) returns all True."""
        bead_id = _get_bead_id()
        result = verify_bead(EURUSD_DB, bead_id)
        assert isinstance(result, VerificationResult)
        assert result.hash_valid is True
        assert result.chain_valid is True
        assert result.merkle_valid is True
        assert result.sig_valid is None  # no key material available
        assert result.batch_id is not None

    def test_merkle_proof_depth_for_batch_500(self):
        """T4 gate: Merkle proof depth matches observation (depth=9 for batch_size=500)."""
        bead_id = _get_bead_id()
        result = verify_bead(EURUSD_DB, bead_id)
        assert result.proof_depth == 9  # ceil(log2(500)) = 9

    def test_multiple_beads_verify(self):
        """Spot-check 10 beads across the DB."""
        for offset in range(0, 100000, 10000):
            bead_id = _get_bead_id(offset=max(offset, 1))
            result = verify_bead(EURUSD_DB, bead_id)
            assert result.hash_valid, f"Hash invalid at offset {offset}"
            assert result.chain_valid, f"Chain invalid at offset {offset}"

    def test_first_bead_chain_valid(self):
        """First bead (hash_prev=NULL) should still be chain_valid."""
        conn = sqlite3.connect(EURUSD_DB)
        cur = conn.cursor()
        cur.execute("SELECT bead_id FROM beads WHERE hash_prev IS NULL LIMIT 1")
        first_id = cur.fetchone()[0]
        conn.close()

        result = verify_bead(EURUSD_DB, first_id)
        assert result.hash_valid is True
        assert result.chain_valid is True

    def test_nonexistent_bead_raises(self):
        with pytest.raises(ValueError, match="not found"):
            verify_bead(EURUSD_DB, "nonexistent-bead-id")
