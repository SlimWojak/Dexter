"""Quick smoke tests for data_loader."""

import sys
sys.path.insert(0, "/home/playground/lab")

from tools.data_loader import list_pairs, available_range, load_pair, load_pair_tf, SUPPORTED_TIMEFRAMES


def test_list_pairs():
    pairs = list_pairs()
    assert isinstance(pairs, list)
    print(f"PASS: list_pairs returned {len(pairs)} pairs: {pairs}")


def test_available_range():
    pairs = list_pairs()
    if not pairs:
        print("SKIP: no data available")
        return
    info = available_range(pairs[0])
    assert info["total_bars"] > 0
    assert info["earliest"] is not None
    print(f"PASS: {pairs[0]} has {info['total_bars']} bars, {info['earliest']} to {info['latest']}")


def test_load_pair():
    pairs = list_pairs()
    if not pairs:
        print("SKIP: no data available")
        return
    df = load_pair(pairs[0])
    assert len(df) > 0
    assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
    assert df["timestamp"].is_monotonic_increasing
    print(f"PASS: loaded {len(df)} bars for {pairs[0]}")


def test_aggregation():
    pairs = list_pairs()
    if not pairs:
        print("SKIP: no data available")
        return
    pair = pairs[0]
    df_1m = load_pair(pair)
    prev_len = len(df_1m)
    for tf in ["5m", "15m", "1h", "4h", "1d"]:
        df_tf = load_pair_tf(pair, tf)
        assert len(df_tf) < prev_len or tf == "1d", f"{tf} should have fewer bars than previous"
        assert list(df_tf.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
        print(f"  {tf}: {len(df_tf)} bars")
        prev_len = len(df_tf)
    print(f"PASS: all timeframes aggregate correctly for {pair}")


if __name__ == "__main__":
    test_list_pairs()
    test_available_range()
    test_load_pair()
    test_aggregation()
    print("\nAll data_loader tests passed.")
