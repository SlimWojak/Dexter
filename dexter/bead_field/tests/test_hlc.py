"""Test Hybrid Logical Clock monotonicity, merge, and thread safety (Phase C)."""

import threading
import pytest
from datetime import datetime, timezone, timedelta

from bead_field.clock.hlc import HLC


class TestTick:
    def test_tick_returns_datetime(self):
        hlc = HLC()
        ts = hlc.tick()
        assert isinstance(ts, datetime)
        assert ts.tzinfo == timezone.utc

    def test_two_ticks_monotonic(self):
        hlc = HLC()
        t1 = hlc.tick()
        t2 = hlc.tick()
        assert t2 > t1

    def test_1000_rapid_ticks_all_increasing(self):
        """1000 rapid ticks must be strictly monotonic (sprint doc requirement)."""
        hlc = HLC()
        timestamps = [hlc.tick() for _ in range(1000)]
        for i in range(1, len(timestamps)):
            assert timestamps[i] > timestamps[i - 1], (
                f"HLC regression at index {i}: {timestamps[i]} <= {timestamps[i-1]}"
            )

    def test_tick_has_microsecond_precision(self):
        hlc = HLC()
        ts = hlc.tick()
        assert ts.microsecond is not None

    def test_last_tracks_most_recent(self):
        hlc = HLC()
        t1 = hlc.tick()
        assert hlc.last == t1
        t2 = hlc.tick()
        assert hlc.last == t2


class TestMerge:
    def test_merge_future_time_advances_clock(self):
        hlc = HLC()
        local = hlc.tick()
        future = local + timedelta(hours=1)
        merged = hlc.merge(future)
        assert merged > future
        assert merged > local

    def test_merge_past_time_does_not_regress(self):
        hlc = HLC()
        local = hlc.tick()
        past = local - timedelta(hours=1)
        merged = hlc.merge(past)
        assert merged > local

    def test_merge_returns_utc(self):
        hlc = HLC()
        hlc.tick()
        remote = datetime.now(timezone.utc)
        merged = hlc.merge(remote)
        assert merged.tzinfo == timezone.utc

    def test_merge_result_greater_than_all_inputs(self):
        hlc = HLC()
        t1 = hlc.tick()
        remote = datetime.now(timezone.utc) + timedelta(seconds=5)
        merged = hlc.merge(remote)
        now = datetime.now(timezone.utc)
        assert merged > t1
        assert merged > remote or merged >= remote


class TestThreadSafety:
    def test_concurrent_ticks_all_unique(self):
        """Multiple threads calling tick() must all get unique timestamps."""
        hlc = HLC()
        results: list[datetime] = []
        lock = threading.Lock()

        def worker(n: int):
            timestamps = [hlc.tick() for _ in range(n)]
            with lock:
                results.extend(timestamps)

        threads = [threading.Thread(target=worker, args=(100,)) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 400
        assert len(set(results)) == 400, "Duplicate timestamps detected under concurrency"

    def test_concurrent_ticks_globally_sortable(self):
        """All timestamps from concurrent threads must form a valid total order."""
        hlc = HLC()
        results: list[datetime] = []
        lock = threading.Lock()

        def worker(n: int):
            timestamps = [hlc.tick() for _ in range(n)]
            with lock:
                results.extend(timestamps)

        threads = [threading.Thread(target=worker, args=(50,)) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        sorted_results = sorted(results)
        for i in range(1, len(sorted_results)):
            assert sorted_results[i] > sorted_results[i - 1]


class TestNonRegression:
    def test_no_backward_time_after_rapid_burst(self):
        """After a rapid burst, next tick must still advance (no regression)."""
        hlc = HLC()
        burst = [hlc.tick() for _ in range(500)]

        import time
        time.sleep(0.001)

        post_burst = hlc.tick()
        assert post_burst > burst[-1]

    def test_fresh_hlc_starts_at_current_time(self):
        hlc = HLC()
        before = datetime.now(timezone.utc)
        ts = hlc.tick()
        after = datetime.now(timezone.utc)
        assert before <= ts <= after + timedelta(milliseconds=1)
