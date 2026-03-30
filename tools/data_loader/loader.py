"""Core data loading and timeframe aggregation for RiverWriter parquet data.

RiverWriter stores 1-minute OHLCV bars as yearly parquet files:
    ~/lab/data/river/data/1m/{PAIR}/{YEAR}.parquet

Schema: timestamp(UTC), open, high, low, close, volume, source, knowledge_time, bar_hash

This module loads raw bars and aggregates them to standard ICT timeframes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

RIVER_DATA_DIR = Path.home() / "lab" / "data" / "river" / "data" / "1m"

SUPPORTED_TIMEFRAMES = {
    "1m": "1min",
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1h": "1h",
    "4h": "4h",
    "1d": "1D",
    "1w": "1W",
}

VALID_PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", "USDCHF"]


def list_pairs() -> list[str]:
    """Return pairs that have parquet data available."""
    if not RIVER_DATA_DIR.exists():
        return []
    return sorted(
        d.name for d in RIVER_DATA_DIR.iterdir()
        if d.is_dir() and any(d.glob("*.parquet"))
    )


def available_range(pair: str) -> dict:
    """Return metadata about available data for a pair.

    Returns dict with keys: pair, files, total_bars, earliest, latest
    """
    pair = pair.upper()
    pair_dir = RIVER_DATA_DIR / pair
    if not pair_dir.exists():
        return {"pair": pair, "files": 0, "total_bars": 0, "earliest": None, "latest": None}

    files = sorted(pair_dir.glob("*.parquet"))
    if not files:
        return {"pair": pair, "files": 0, "total_bars": 0, "earliest": None, "latest": None}

    df = _load_parquet_files(files)
    return {
        "pair": pair,
        "files": len(files),
        "total_bars": len(df),
        "earliest": str(df["timestamp"].min()),
        "latest": str(df["timestamp"].max()),
    }


def load_pair(
    pair: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> pd.DataFrame:
    """Load 1-minute bars for a pair, optionally filtered by date range.

    Args:
        pair: Currency pair (e.g. "EURUSD")
        start: Inclusive start date (e.g. "2024-01-01")
        end: Inclusive end date (e.g. "2024-12-31")

    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume
        Sorted by timestamp, deduplicated, timezone-aware (UTC).
    """
    pair = pair.upper()
    pair_dir = RIVER_DATA_DIR / pair
    if not pair_dir.exists():
        raise FileNotFoundError(f"No data directory for {pair} at {pair_dir}")

    files = sorted(pair_dir.glob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"No parquet files for {pair}")

    if start or end:
        files = _filter_files_by_year(files, start, end)

    df = _load_parquet_files(files)
    df = _filter_by_date(df, start, end)
    return df[["timestamp", "open", "high", "low", "close", "volume"]]


def load_pair_tf(
    pair: str,
    timeframe: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> pd.DataFrame:
    """Load bars aggregated to a higher timeframe.

    Args:
        pair: Currency pair
        timeframe: One of: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w
        start: Inclusive start date
        end: Inclusive end date

    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume
    """
    tf = timeframe.lower()
    if tf not in SUPPORTED_TIMEFRAMES:
        raise ValueError(f"Unsupported timeframe '{tf}'. Use one of: {list(SUPPORTED_TIMEFRAMES.keys())}")

    if tf == "1m":
        return load_pair(pair, start, end)

    df_1m = load_pair(pair, start, end)
    return _aggregate_ohlcv(df_1m, SUPPORTED_TIMEFRAMES[tf])


def _load_parquet_files(files: list[Path]) -> pd.DataFrame:
    """Load and concatenate parquet files, dedup by timestamp."""
    dfs = [pd.read_parquet(f) for f in files]
    if not dfs:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

    df = pd.concat(dfs, ignore_index=True)
    df = df.sort_values("timestamp").drop_duplicates(subset=["timestamp"], keep="last")
    df = df.reset_index(drop=True)
    return df


def _filter_files_by_year(
    files: list[Path],
    start: Optional[str],
    end: Optional[str],
) -> list[Path]:
    """Pre-filter parquet files by year to avoid loading unnecessary data."""
    start_year = int(start[:4]) if start else 0
    end_year = int(end[:4]) if end else 9999
    result = []
    for f in files:
        # Filename may be "2026.parquet" or "EURUSD_2026.parquet"
        year_str = f.stem.split("_")[-1] if "_" in f.stem else f.stem
        try:
            year = int(year_str)
            if start_year <= year <= end_year:
                result.append(f)
        except ValueError:
            result.append(f)
    return result


def _filter_by_date(
    df: pd.DataFrame,
    start: Optional[str],
    end: Optional[str],
) -> pd.DataFrame:
    """Filter DataFrame by date range."""
    if start:
        df = df[df["timestamp"] >= pd.Timestamp(start, tz="UTC")]
    if end:
        df = df[df["timestamp"] <= pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)]
    return df


def _aggregate_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Aggregate 1-minute OHLCV bars to a higher timeframe.

    Uses left-labeled, closed-left convention (standard for trading).
    """
    if df.empty:
        return df

    df = df.set_index("timestamp")

    agg = df.resample(rule, label="left", closed="left").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    })

    agg = agg.dropna(subset=["open"])
    agg = agg.reset_index()
    agg = agg.rename(columns={"timestamp": "timestamp"})
    return agg
