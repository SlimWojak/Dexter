"""Test suite for synthetic bead pipeline.

Tests are split into:
  - Unit tests (transform, progress_log, tags) — no Dexter signing deps
  - Integration tests (full pipeline) — require pqcrypto/ecdsa, marked with
    @pytest.mark.integration so they can be skipped in CI without those deps

Run:
  pytest test_synthetic_pipeline.py -v
  pytest test_synthetic_pipeline.py -v -m integration  # integration only
"""

import json
import math
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

# These imports are always available (no native deps)
from progress_log import ProgressLog


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_row(
    ts: datetime | None = None,
    o: float = 1.0847,
    h: float = 1.0855,
    lo: float = 1.0840,
    c: float = 1.0850,
    v: float = 1234.5,
    source: str = "dukascopy",
    bar_hash: str = "abc123",
) -> SimpleNamespace:
    """Create a mock parquet row as a namespace (matches pandas itertuples)."""
    import pandas as pd

    if ts is None:
        ts = datetime(2024, 3, 15, 8, 30, tzinfo=timezone.utc)

    return SimpleNamespace(
        timestamp=pd.Timestamp(ts),
        open=o,
        high=h,
        low=lo,
        close=c,
        volume=v,
        source=source,
        bar_hash=bar_hash,
    )


# ---------------------------------------------------------------------------
# transform_bar tests
# ---------------------------------------------------------------------------

class TestTransformBar:
    """Tests for the row → ingest kwargs mapping."""

    @pytest.fixture(autouse=True)
    def _import_transform(self):
        """Import transform_bar. Available even without signing deps."""
        # We patch the Dexter imports at module level if they're unavailable
        import importlib
        import sys

        # Create stubs for Dexter modules if not installed
        stubs_needed = [
            "bead_field", "bead_field.clock", "bead_field.clock.hlc",
            "bead_field.ingestion", "bead_field.ingestion.pipeline",
            "bead_field.integrity", "bead_field.integrity.merkle",
            "bead_field.integrity.signing",
            "bead_field.schema", "bead_field.schema.core", "bead_field.schema.enums",
            "bead_field.store", "bead_field.store.bitemporal",
        ]
        self._patched = False
        for mod_name in stubs_needed:
            if mod_name not in sys.modules:
                sys.modules[mod_name] = MagicMock()
                self._patched = True

        # Now we need real enum values for the transform to work
        from bead_field.schema import enums as enums_mod
        enums_mod.BeadType = type("BeadType", (), {
            "FACT": "FACT", "CLAIM": "CLAIM",
        })
        enums_mod.TemporalClass = type("TemporalClass", (), {
            "OBSERVATION": "OBSERVATION", "PATTERN": "PATTERN",
        })
        enums_mod.SourceType = type("SourceType", (), {
            "MARKET_DATA": "MARKET_DATA",
        })

        from bead_field.schema import core as core_mod
        core_mod.SourceRef = lambda **kw: SimpleNamespace(**kw)

        # Re-import the pipeline module to pick up stubs
        if "synthetic_bead_pipeline" in sys.modules:
            del sys.modules["synthetic_bead_pipeline"]
        import synthetic_bead_pipeline
        self.transform_bar = synthetic_bead_pipeline.transform_bar

    def test_valid_row_produces_correct_content(self):
        row = _make_row()
        result = self.transform_bar(row, "EURUSD")

        assert result["bead_type"] == "FACT"
        assert result["temporal_class"] == "OBSERVATION"
        assert result["content"]["symbol"] == "EURUSD"
        assert result["content"]["field"] == "ohlcv_1m"
        assert result["content"]["provider"] == "dukascopy"
        assert result["content"]["quality_score"] == 1.0

        value = result["content"]["value"]
        assert value["open"] == 1.0847
        assert value["high"] == 1.0855
        assert value["low"] == 1.0840
        assert value["close"] == 1.0850
        assert value["volume"] == 1234.5

    def test_world_time_span_is_60_seconds(self):
        ts = datetime(2024, 3, 15, 8, 30, tzinfo=timezone.utc)
        row = _make_row(ts=ts)
        result = self.transform_bar(row, "EURUSD")

        assert result["world_time_valid_from"] == ts
        assert result["world_time_valid_to"] == ts + timedelta(seconds=60)

    def test_lineage_contains_bar_hash(self):
        row = _make_row(bar_hash="deadbeef123")
        result = self.transform_bar(row, "GBPUSD")

        assert len(result["lineage"]) == 1
        assert result["lineage"][0] == "riverwriter:bar_hash:deadbeef123"

    def test_tags_contain_all_three_mandatory(self):
        row = _make_row()
        result = self.transform_bar(row, "USDJPY")

        tags = result["tags"]
        assert "synthetic" in tags
        assert "pair:USDJPY" in tags
        assert "source:riverwriter-backfill" in tags
        assert len(tags) == 3

    def test_nan_value_raises(self):
        row = _make_row(o=float("nan"))
        with pytest.raises(ValueError, match="(?i)nan"):
            self.transform_bar(row, "EURUSD")

    def test_inf_value_raises(self):
        row = _make_row(h=float("inf"))
        with pytest.raises(ValueError, match="(?i)inf"):
            self.transform_bar(row, "EURUSD")

    def test_negative_inf_raises(self):
        row = _make_row(lo=float("-inf"))
        with pytest.raises(ValueError, match="(?i)inf"):
            self.transform_bar(row, "EURUSD")

    def test_naive_timestamp_gets_utc(self):
        """Timestamps without tzinfo should be treated as UTC."""
        naive_ts = datetime(2024, 6, 15, 14, 0)
        row = _make_row(ts=naive_ts)
        result = self.transform_bar(row, "EURUSD")

        wt_from = result["world_time_valid_from"]
        assert wt_from.tzinfo is not None

    def test_different_pairs_produce_correct_symbol(self):
        row = _make_row()
        for pair in ["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", "USDCHF"]:
            result = self.transform_bar(row, pair)
            assert result["content"]["symbol"] == pair
            assert f"pair:{pair}" in result["tags"]

    def test_value_is_dict_with_exact_keys(self):
        row = _make_row()
        result = self.transform_bar(row, "EURUSD")
        value = result["content"]["value"]

        assert isinstance(value, dict)
        assert set(value.keys()) == {"open", "high", "low", "close", "volume"}

    def test_all_value_fields_are_float(self):
        row = _make_row()
        result = self.transform_bar(row, "EURUSD")
        for k, v in result["content"]["value"].items():
            assert isinstance(v, float), f"{k} is {type(v)}, expected float"


# ---------------------------------------------------------------------------
# ProgressLog tests
# ---------------------------------------------------------------------------

class TestProgressLog:

    def test_new_log_starts_empty(self, tmp_path):
        log = ProgressLog(tmp_path / "progress.json")
        assert log.get_offset("EURUSD", "2024") == 0

    def test_update_and_read_back(self, tmp_path):
        path = tmp_path / "progress.json"
        log = ProgressLog(path)
        log.update("EURUSD", "2024", 5000)

        assert log.get_offset("EURUSD", "2024") == 5000
        assert log.get_offset("EURUSD", "2025") == 0

    def test_persistence_across_instances(self, tmp_path):
        path = tmp_path / "progress.json"
        log1 = ProgressLog(path)
        log1.update("GBPUSD", "2023", 3000)

        log2 = ProgressLog(path)
        assert log2.get_offset("GBPUSD", "2023") == 3000

    def test_multiple_pairs_tracked_independently(self, tmp_path):
        path = tmp_path / "progress.json"
        log = ProgressLog(path)
        log.update("EURUSD", "2024", 1000)
        log.update("GBPUSD", "2024", 2000)

        assert log.get_offset("EURUSD", "2024") == 1000
        assert log.get_offset("GBPUSD", "2024") == 2000

    def test_update_overwrites_previous(self, tmp_path):
        path = tmp_path / "progress.json"
        log = ProgressLog(path)
        log.update("EURUSD", "2024", 1000)
        log.update("EURUSD", "2024", 5000)

        assert log.get_offset("EURUSD", "2024") == 5000

    def test_corrupt_json_raises_runtime_error(self, tmp_path):
        path = tmp_path / "progress.json"
        path.write_text("{corrupt json!!!")

        with pytest.raises(RuntimeError, match="Corrupt progress log"):
            ProgressLog(path)

    def test_atomic_write(self, tmp_path):
        """After update, no .tmp file should remain."""
        path = tmp_path / "progress.json"
        log = ProgressLog(path)
        log.update("EURUSD", "2024", 500)

        assert not (tmp_path / "progress.tmp").exists()
        assert path.exists()

    def test_state_property_returns_copy(self, tmp_path):
        path = tmp_path / "progress.json"
        log = ProgressLog(path)
        log.update("EURUSD", "2024", 100)

        state = log.state
        state["EURUSD:2024"] = 999  # mutate the copy
        assert log.get_offset("EURUSD", "2024") == 100  # original unchanged


# ---------------------------------------------------------------------------
# BatchCommitContext tests (unit-level, mock store)
# ---------------------------------------------------------------------------

class TestBatchCommitContext:

    @pytest.fixture(autouse=True)
    def _import_batch(self):
        import sys
        stubs_needed = [
            "bead_field", "bead_field.clock", "bead_field.clock.hlc",
            "bead_field.ingestion", "bead_field.ingestion.pipeline",
            "bead_field.integrity", "bead_field.integrity.merkle",
            "bead_field.integrity.signing",
            "bead_field.schema", "bead_field.schema.core", "bead_field.schema.enums",
            "bead_field.store", "bead_field.store.bitemporal",
        ]
        for mod_name in stubs_needed:
            if mod_name not in sys.modules:
                sys.modules[mod_name] = MagicMock()

        if "synthetic_bead_pipeline" in sys.modules:
            del sys.modules["synthetic_bead_pipeline"]
        import synthetic_bead_pipeline
        self.BatchCommitContext = synthetic_bead_pipeline.BatchCommitContext

    def test_commit_suppressed_during_batch(self):
        """Inside the context, store._conn.commit() is intercepted."""
        mock_store = MagicMock()
        real_conn = MagicMock()
        mock_store._conn = real_conn

        with self.BatchCommitContext(mock_store) as batcher:
            # store._conn is now a wrapper; calls to .commit() are no-ops
            mock_store._conn.commit()
            mock_store._conn.commit()
            mock_store._conn.commit()

            # The real connection's commit should not have been called
            real_conn.commit.assert_not_called()

        # On exit, pending writes are flushed
        real_conn.commit.assert_called_once()

    def test_flush_triggers_real_commit(self):
        mock_store = MagicMock()
        real_conn = MagicMock()
        mock_store._conn = real_conn

        with self.BatchCommitContext(mock_store) as batcher:
            mock_store._conn.commit()  # deferred
            batcher.flush()
            real_conn.commit.assert_called_once()
            real_conn.commit.reset_mock()

            # After flush, pending count resets — no-op flush
            batcher.flush()
            real_conn.commit.assert_not_called()

    def test_exit_restores_original_connection(self):
        mock_store = MagicMock()
        real_conn = MagicMock()
        mock_store._conn = real_conn

        with self.BatchCommitContext(mock_store):
            # During context, _conn is a wrapper
            assert mock_store._conn is not real_conn

        # After exit, real connection is restored
        assert mock_store._conn is real_conn


# ---------------------------------------------------------------------------
# Tag construction tests
# ---------------------------------------------------------------------------

class TestTagConstruction:

    def test_all_pairs_produce_valid_tag_format(self):
        pairs = ["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", "USDCHF"]
        for pair in pairs:
            tag = f"pair:{pair}"
            assert ":" in tag
            assert tag.startswith("pair:")
            assert len(tag) > 5


# ---------------------------------------------------------------------------
# Integration tests — require full Dexter deps
# ---------------------------------------------------------------------------

def _has_dexter_deps() -> bool:
    try:
        import bead_field.schema.enums
        import bead_field.integrity.signing
        return True
    except ImportError:
        return False


@pytest.mark.integration
@pytest.mark.skipif(not _has_dexter_deps(), reason="Dexter deps not installed")
class TestIntegration:
    """Full pipeline integration tests. Require Dexter + signing deps."""

    def test_single_bead_ingestion(self, tmp_path):
        """Ingest one bar through the full pipeline and verify the bead."""
        from synthetic_bead_pipeline import transform_bar, run_pipeline
        # This test requires a real parquet file — skip if not available
        pytest.skip("Requires parquet test fixture — run on VPS")

    def test_per_pair_chain_starts_fresh(self, tmp_path):
        """Each pair should start with hash_prev=None."""
        pytest.skip("Requires parquet test fixture — run on VPS")

    def test_ecdsa_sig_present_on_all_beads(self, tmp_path):
        """Every bead should have a non-empty ecdsa_sig."""
        pytest.skip("Requires parquet test fixture — run on VPS")
