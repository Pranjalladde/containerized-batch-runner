import unittest
from app.retry import run_with_retries

class RetryTests(unittest.TestCase):
    def test_success(self):
        self.assertEqual(run_with_retries(lambda: "ok", 1)[0], "ok")

    def test_retry_then_success(self):
        calls = {"n": 0}
        def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise ValueError("temporary")
            return "done"
        result, attempts = run_with_retries(flaky, 3, 0, sleep=lambda _: None)
        self.assertEqual((result, attempts), ("done", 3))

    def test_exhaustion(self):
        with self.assertRaises(RuntimeError):
            run_with_retries(lambda: 1 / 0, 2, 0, sleep=lambda _: None)

    def test_invalid_attempt_count(self):
        with self.assertRaises(ValueError):
            run_with_retries(lambda: None, 0)
