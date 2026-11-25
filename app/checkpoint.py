import json
import os
import tempfile
from pathlib import Path
from threading import Lock

class Checkpoint:
    """Atomic JSON checkpoint store for completed task IDs."""
    def __init__(self, path="data/checkpoint.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def load(self):
        with self._lock:
            if not self.path.exists():
                return []
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                if not isinstance(data, list):
                    raise ValueError("Checkpoint must contain a JSON list")
                return data
            except (json.JSONDecodeError, OSError) as exc:
                raise RuntimeError(f"Cannot read checkpoint {self.path}: {exc}") from exc

    def save_completed(self, task_id):
        with self._lock:
            completed = self.load_unlocked()
            if task_id not in completed:
                completed.append(task_id)
            self._atomic_write(completed)

    def load_unlocked(self):
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("Checkpoint must contain a JSON list")
        return data

    def _atomic_write(self, data):
        fd, temp_name = tempfile.mkstemp(prefix=".checkpoint-", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
