"""Tests for known_at — T5 gate."""

import os

import pytest

from bead_field.query.temporal import known_at, BeadRecord

EURUSD_DB = os.path.expanduser("~/dexter/tools/synthetic/synthetic_beads.db")
SKIP_SYNTHETIC = not os.path.exists(EURUSD_DB)
skip_no_db = pytest.mark.skipif(SKIP_SYNTHETIC, reason="Synthetic DB not available")


@skip_no_db
class TestKnownAt:
    def test_wt_range_returns_beads(self):
        """T5 gate: known_at with WT range returns correct beads."""
        results = known_at(
            kt_cutoff="2026-12-31T00:00:00",
            wt_from="2023-06-15T00:00:00",
            wt_to="2023-06-16T00:00:00",
            db_path=EURUSD_DB,
        )
        assert len(results) > 0
        assert all(isinstance(r, BeadRecord) for r in results)
        for r in results:
            assert r.world_time_valid_from >= "2023-06-15"
            assert r.world_time_valid_from < "2023-06-16"

    def test_kt_before_ingestion_returns_empty(self):
        """T5 gate: KT cutoff before all ingestion returns empty set."""
        results = known_at(
            kt_cutoff="2020-01-01T00:00:00",
            wt_from="2023-06-15T00:00:00",
            wt_to="2023-06-16T00:00:00",
            db_path=EURUSD_DB,
        )
        assert len(results) == 0

    def test_kt_after_ingestion_same_as_wt_only(self):
        """T5 gate: KT cutoff after all ingestion returns same as WT-only query."""
        far_future = known_at(
            kt_cutoff="2099-01-01T00:00:00",
            wt_from="2023-06-15T00:00:00",
            wt_to="2023-06-16T00:00:00",
            db_path=EURUSD_DB,
        )
        just_after = known_at(
            kt_cutoff="2026-12-31T00:00:00",
            wt_from="2023-06-15T00:00:00",
            wt_to="2023-06-16T00:00:00",
            db_path=EURUSD_DB,
        )
        assert len(far_future) == len(just_after)

    def test_bare_timestamps_normalized(self):
        """T5 gate: bare ISO input works correctly (normalizer handles it)."""
        result_bare = known_at(
            kt_cutoff="2026-12-31T00:00:00",
            wt_from="2023-06-15T00:00:00",
            wt_to="2023-06-16T00:00:00",
            db_path=EURUSD_DB,
        )
        result_tz = known_at(
            kt_cutoff="2026-12-31T00:00:00+00:00",
            wt_from="2023-06-15T00:00:00+00:00",
            wt_to="2023-06-16T00:00:00+00:00",
            db_path=EURUSD_DB,
        )
        assert len(result_bare) == len(result_tz)

    def test_z_suffix_works(self):
        results = known_at(
            kt_cutoff="2026-12-31T00:00:00Z",
            wt_from="2023-06-15T00:00:00Z",
            wt_to="2023-06-16T00:00:00Z",
            db_path=EURUSD_DB,
        )
        assert len(results) > 0

    def test_content_has_ohlcv(self):
        results = known_at(
            kt_cutoff="2026-12-31T00:00:00",
            wt_from="2023-06-15T14:30:00",
            wt_to="2023-06-15T14:31:00",
            db_path=EURUSD_DB,
        )
        assert len(results) == 1
        content = results[0].content
        assert "value" in content
        assert "open" in content["value"]
        assert "high" in content["value"]
        assert "low" in content["value"]
        assert "close" in content["value"]
        assert "volume" in content["value"]
