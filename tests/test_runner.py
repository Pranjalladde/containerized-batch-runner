import tempfile
import unittest
from pathlib import Path
from app.checkpoint import Checkpoint
from app.runner import run_batch, load_manifest

class FakeExecutor:
    def __init__(self):
        self.calls = {}
    def execute(self, task_id):
        self.calls[task_id] = self.calls.get(task_id, 0) + 1
        if task_id == "retry" and self.calls[task_id] == 1:
            raise RuntimeError("temporary")
        if task_id == "fail":
            raise RuntimeError("permanent")
        return {"task": task_id}

class RunnerTests(unittest.TestCase):
    def test_success_retry_and_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            cp = Checkpoint(Path(directory) / "state.json")
            executor = FakeExecutor()
            manifest = {"tasks": [{"id":"first"}, {"id":"retry"}], "max_attempts": 2, "backoff_seconds": 0}
            report = run_batch(manifest, executor, cp)
            self.assertEqual(report["status"], "success")
            self.assertEqual(executor.calls["retry"], 2)
            report2 = run_batch(manifest, executor, cp)
            self.assertEqual(len(report2["skipped"]), 2)
            self.assertEqual(executor.calls["first"], 1)

    def test_failure_stops_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            report = run_batch(
                {"tasks": [{"id":"fail"}, {"id":"later"}], "max_attempts": 1},
                FakeExecutor(), Checkpoint(Path(directory) / "state.json")
            )
            self.assertEqual(report["status"], "failed")
            self.assertEqual(len(report["failed"]), 1)

    def test_manifest_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text('{"image":"x","tasks":[{"id":"a"},{"id":"a"}]}')
            with self.assertRaises(ValueError):
                load_manifest(path)
