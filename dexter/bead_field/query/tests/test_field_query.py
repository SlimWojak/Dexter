"""Tests for FieldQuery — T6 gate."""

import os
import time

import pytest

from bead_field.query.field_query import FieldQuery, FieldQueryResult

DB_DIR = os.path.expanduser("~/dexter/tools/synthetic")
SKIP_SYNTHETIC = not os.path.exists(os.path.join(DB_DIR, "synthetic_beads.db"))
skip_no_db = pytest.mark.skipif(SKIP_SYNTHETIC, reason="Synthetic DBs not available")


@skip_no_db
class TestFieldQuery:
    def test_from_data_dir_discovers_all_pairs(self):
        fq = FieldQuery.from_data_dir(DB_DIR)
        assert len(fq.pairs) == 6
        assert "EURUSD" in fq.pairs
        assert "USDJPY" in fq.pairs

    def test_execute_returns_results_from_all_dbs(self):
        """T6 gate: returns results from all 6 DBs."""
        fq = FieldQuery.from_data_dir(DB_DIR)
        result = fq.execute(
            "SELECT bead_id, content FROM beads WHERE world_time_valid_from = ?",
            ("2024-01-15T14:30:00",),
        )
        assert isinstance(result, FieldQueryResult)
        assert len(result.results) == 6
        assert result.total_rows == 6
        for qr in result.results:
            assert qr.row_count == 1

    def test_parallel_produces_same_results_as_sequential(self):
        """T6 gate: parallel and sequential produce identical results."""
        fq = FieldQuery.from_data_dir(DB_DIR)
        sql = """SELECT bead_id FROM beads
                 WHERE world_time_valid_from >= ?
                   AND world_time_valid_from < ?"""
        params = ("2023-06-01T00:00:00", "2023-07-01T00:00:00")

        seq = fq.execute(sql, params, parallel=False)
        par = fq.execute(sql, params, parallel=True)

        assert par.total_rows == seq.total_rows
        seq_ids = {r.pair: sorted(row["bead_id"] for row in r.rows) for r in seq.results}
        par_ids = {r.pair: sorted(row["bead_id"] for row in r.rows) for r in par.results}
        assert seq_ids == par_ids

    def test_timestamps_normalized_automatically(self):
        """T6 gate: normalizes timestamps in params."""
        fq = FieldQuery.from_data_dir(DB_DIR)

        result_bare = fq.execute(
            "SELECT COUNT(*) as cnt FROM beads WHERE world_time_valid_from = ?",
            ("2024-01-15T14:30:00",),
        )
        result_tz = fq.execute(
            "SELECT COUNT(*) as cnt FROM beads WHERE world_time_valid_from = ?",
            ("2024-01-15T14:30:00+00:00",),
        )
        bare_total = sum(r.rows[0]["cnt"] for r in result_bare.results)
        tz_total = sum(r.rows[0]["cnt"] for r in result_tz.results)
        assert bare_total == tz_total == 6

    def test_invalid_db_path_raises(self):
        """T6 gate: invalid DB path raises clear error."""
        with pytest.raises(FileNotFoundError):
            FieldQuery({"EURUSD": "/nonexistent/path.db"})

    def test_empty_db_paths_raises(self):
        with pytest.raises(ValueError, match="empty"):
            FieldQuery({})

    def test_nonexistent_dir_raises(self):
        with pytest.raises(FileNotFoundError):
            FieldQuery.from_data_dir("/nonexistent/directory")

    def test_all_rows_have_pair_label(self):
        fq = FieldQuery.from_data_dir(DB_DIR)
        result = fq.execute(
            "SELECT bead_id FROM beads WHERE world_time_valid_from = ?",
            ("2024-01-15T14:30:00",),
        )
        all_rows = result.all_rows
        assert len(all_rows) == 6
        pairs_seen = {r["_pair"] for r in all_rows}
        assert len(pairs_seen) == 6

    def test_no_attach_used(self):
        """T6 gate: implementation uses no ATTACH."""
        import inspect
        source = inspect.getsource(FieldQuery)
        assert "ATTACH" not in source
