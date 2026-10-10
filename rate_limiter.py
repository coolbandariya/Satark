"""Process-local sliding-window rate limiting for expensive analysis requests.

This limit is shared by sessions handled by the same Python process. It is
intentionally defense-in-depth, not a distributed quota: hosts with multiple
workers/replicas or restarts still need a gateway/provider-side global limit.
"""
from collections import deque
import threading
import time


class SlidingWindowRateLimiter:
    """Thread-safe, process-local sliding-window limiter."""

    def __init__(self):
        self._timestamps = deque()
        self._lock = threading.Lock()

    def consume(self, limit, window_seconds=60.0, now=None):
        """Return (allowed, retry_after_seconds) for one attempted request."""
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        if isinstance(window_seconds, bool) or not isinstance(window_seconds, (int, float)) or window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        current = time.monotonic() if now is None else float(now)

        with self._lock:
            cutoff = current - float(window_seconds)
            while self._timestamps and self._timestamps[0] <= cutoff:
                self._timestamps.popleft()

            if len(self._timestamps) >= limit:
                retry_after = max(0.0, self._timestamps[0] + float(window_seconds) - current)
                return False, retry_after

            self._timestamps.append(current)
            return True, 0.0


_PROCESS_LIMITER = SlidingWindowRateLimiter()


def consume_analysis_slot(limit, window_seconds=60.0):
    """Consume one shared process-level analysis slot, if available."""
    return _PROCESS_LIMITER.consume(limit=limit, window_seconds=window_seconds)
