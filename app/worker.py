"""Container entry point: executes exactly one registered task."""
import json
import sys
from tasks.sample_tasks import TASKS

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"ok": False, "error": "Usage: python -m app.worker TASK_ID"}))
        return 2
    task_id = sys.argv[1]
    if task_id not in TASKS:
        print(json.dumps({"ok": False, "error": f"Unknown task: {task_id}"}))
        return 2
    try:
        result = TASKS[task_id]()
        print(json.dumps({"ok": True, "task_id": task_id, "result": result}))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "task_id": task_id, "error": str(exc)}))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
