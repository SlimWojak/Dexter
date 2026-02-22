"""Hybrid Logical Clock for knowledge_time ordering (Spec Section 3.1 + 4.1).

Single-node simplified HLC for Gate 1 (Mac Mini).
Full distributed HLC with cross-node merge when M3 Ultra arrives.

Guarantees:
- Monotonically increasing: each tick() > previous tick()
- Microsecond precision ISO 8601
- Thread-safe (Lock-protected)
- merge(remote) advances clock without regression
"""

import threading
from datetime import datetime, timedelta, timezone


class HLC:
    """Hybrid Logical Clock.

    Combines wall clock with a logical counter to guarantee
    monotonicity even when wall clock hasn't advanced between calls.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._last_ts: datetime = datetime.min.replace(tzinfo=timezone.utc)

    def tick(self) -> datetime:
        """Return a timestamp guaranteed greater than all previous ticks.

        If wall clock has advanced past last timestamp: use wall clock.
        If wall clock hasn't advanced: increment by 1 microsecond.
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            if now > self._last_ts:
                self._last_ts = now
            else:
                self._last_ts = self._last_ts + timedelta(microseconds=1)
            return self._last_ts

    def merge(self, remote_time: datetime) -> datetime:
        """Merge a remote timestamp into the clock, advancing if needed.

        Used for future multi-node coordination (DGX <-> M3 Ultra).
        Result is always > max(local, remote).
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            max_ts = max(now, self._last_ts, remote_time)
            self._last_ts = max_ts + timedelta(microseconds=1)
            return self._last_ts

    @property
    def last(self) -> datetime:
        """Most recent timestamp issued by this clock."""
        with self._lock:
            return self._last_ts
