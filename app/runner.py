import argparse
import json
import logging
import time
from pathlib import Path
from app.checkpoint import Checkpoint
from app.docker_executor import DockerExecutor
from app.logging_config import configure_logging
from app.retry import run_with_retries

def load_manifest(path):
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {"tasks", "image"}
    missing = required - manifest.keys()
    if missing:
        raise ValueError(f"Manifest missing required keys: {sorted(missing)}")
    if not isinstance(manifest["tasks"], list):
        raise ValueError("'tasks' must be a list")
    ids = [task.get("id") for task in manifest["tasks"]]
    if any(not item for item in ids) or len(ids) != len(set(ids)):
        raise ValueError("Every task must have a unique, non-empty id")
    return manifest

def run_batch(manifest, executor, checkpoint, logger=None):
    logger = logger or logging.getLogger("batch_runner")
    completed_ids = set(checkpoint.load())
    report = {"succeeded": [], "failed": [], "skipped": [], "started_at": time.time()}
    for task in manifest["tasks"]:
        task_id = task["id"]
        if task_id in completed_ids:
            report["skipped"].append(task_id)
            logger.info("Skipping checkpointed task", extra={"task_id": task_id})
            continue
        attempts = int(task.get("max_attempts", manifest.get("max_attempts", 3)))
        backoff = float(task.get("backoff_seconds", manifest.get("backoff_seconds", 1)))
        started = time.monotonic()
        try:
            result, used_attempts = run_with_retries(
                lambda: executor.execute(task_id), attempts, backoff
            )
            checkpoint.save_completed(task_id)
            report["succeeded"].append({
                "task_id": task_id, "attempts": used_attempts,
                "duration_seconds": round(time.monotonic() - started, 3),
                "result": result,
            })
            logger.info("Task succeeded", extra={"task_id": task_id})
        except Exception as exc:
            report["failed"].append({
                "task_id": task_id, "error": str(exc),
                "duration_seconds": round(time.monotonic() - started, 3),
            })
            logger.exception("Task failed", extra={"task_id": task_id})
            break
    report["finished_at"] = time.time()
    report["duration_seconds"] = round(report["finished_at"] - report["started_at"], 3)
    report["status"] = "failed" if report["failed"] else "success"
    return report

def main():
    parser = argparse.ArgumentParser(description="Containerized batch task runner")
    parser.add_argument("--manifest", default="config/manifest.json")
    parser.add_argument("--checkpoint", default="data/checkpoint.json")
    parser.add_argument("--report", default="data/batch-report.json")
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    logger = configure_logging(manifest.get("log_level", "INFO"))
    executor = DockerExecutor(
        image=manifest["image"],
        memory_limit=manifest.get("memory_limit", "256m"),
        cpus=manifest.get("cpus", 0.5),
        timeout_seconds=manifest.get("task_timeout_seconds", 300),
    )
    report = run_batch(manifest, executor, Checkpoint(args.checkpoint), logger)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    logger.info("Batch finished with status %s", report["status"])
    if report["status"] != "success":
        raise SystemExit(1)

if __name__ == "__main__":
    main()
