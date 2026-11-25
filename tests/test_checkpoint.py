import tempfile
import unittest
from pathlib import Path
from app.checkpoint import Checkpoint

class CheckpointTests(unittest.TestCase):
    def test_save_load_and_no_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Checkpoint(Path(directory) / "state.json")
            store.save_completed("a")
            store.save_completed("a")
            store.save_completed("b")
            self.assertEqual(store.load(), ["a", "b"])

    def test_missing_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(Checkpoint(Path(directory) / "missing.json").load(), [])
