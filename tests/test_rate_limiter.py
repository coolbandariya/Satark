"""Regression tests for the shared process-local analysis rate limiter."""
import threading
import unittest

from rate_limiter import SlidingWindowRateLimiter


class SlidingWindowRateLimiterTests(unittest.TestCase):
    def test_blocks_at_limit_and_reports_retry_after(self):
        limiter = SlidingWindowRateLimiter()
        self.assertEqual(limiter.consume(limit=2, window_seconds=10, now=0), (True, 0.0))
        self.assertEqual(limiter.consume(limit=2, window_seconds=10, now=1), (True, 0.0))
        allowed, retry_after = limiter.consume(limit=2, window_seconds=10, now=2)
        self.assertFalse(allowed)
        self.assertAlmostEqual(retry_after, 8.0)

    def test_expires_old_requests_at_window_boundary(self):
        limiter = SlidingWindowRateLimiter()
        limiter.consume(limit=1, window_seconds=10, now=0)
        self.assertFalse(limiter.consume(limit=1, window_seconds=10, now=9.999)[0])
        self.assertTrue(limiter.consume(limit=1, window_seconds=10, now=10)[0])

    def test_sliding_window_keeps_newer_requests(self):
        limiter = SlidingWindowRateLimiter()
        limiter.consume(limit=2, window_seconds=10, now=0)
        limiter.consume(limit=2, window_seconds=10, now=8)
        self.assertTrue(limiter.consume(limit=2, window_seconds=10, now=10)[0])
        self.assertFalse(limiter.consume(limit=2, window_seconds=10, now=17.9)[0])
        allowed, retry_after = limiter.consume(limit=2, window_seconds=10, now=18)
        self.assertTrue(allowed)
        self.assertEqual(retry_after, 0.0)

    def test_rejects_invalid_limits_and_windows(self):
        limiter = SlidingWindowRateLimiter()
        for invalid in (0, -1, True, 1.5):
            with self.subTest(limit=invalid):
                with self.assertRaises(ValueError):
                    limiter.consume(limit=invalid)
        for invalid in (0, -1, True):
            with self.subTest(window=invalid):
                with self.assertRaises(ValueError):
                    limiter.consume(limit=1, window_seconds=invalid)

    def test_concurrent_calls_cannot_exceed_limit(self):
        limiter = SlidingWindowRateLimiter()
        outcomes = []
        guard = threading.Lock()

        def attempt():
            result = limiter.consume(limit=5, window_seconds=60, now=1)[0]
            with guard:
                outcomes.append(result)

        threads = [threading.Thread(target=attempt) for _ in range(40)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(sum(outcomes), 5)
        self.assertEqual(len(outcomes), 40)


if __name__ == "__main__":
    unittest.main()
