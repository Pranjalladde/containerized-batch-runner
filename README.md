# Containerized Batch Runner with Retries and Checkpointed Recovery

A Python and Docker project that orchestrates batch tasks as separate, short-lived containers. It provides retry handling, checkpoint-based restart, resource limits, structured logs, batch reports, and CI automation.

## Architecture

```text
                    manifest.json
                          |
                          v
                  Batch Orchestrator
                          |
             +------------+------------+
             |            |            |
             v            v            v
         Docker run   Docker run   Docker run
          Task 1       Task 2       Task 3
             |            |            |
             +------------+------------+
                          |
                  Retry on failure
                          |
                   Checkpoint store
                          |
                  Batch JSON report
```

## Features

- **One container per task:** the orchestrator launches a separate Docker container for each task.
- **Resource isolation:** each worker receives configured memory and CPU limits.
- **Retry with exponential backoff:** transient task failures are retried with increasing delays.
- **Checkpoint recovery:** successful task IDs are persisted atomically; a restarted batch skips completed tasks.
- **Structured logs:** JSON log records include timestamps, severity and task identifiers.
- **Batch report:** records successes, failures, skipped tasks, attempts and durations.
- **Manifest-driven execution:** task list and runtime settings are configured in JSON.
- **Automated CI:** GitHub Actions runs unit tests and builds the Docker image.

## Requirements

- Python 3.12+
- Docker Engine or Docker Desktop
- Docker Compose v2
- Git

## Quick start

Build the worker image:

```bash
docker build -t containerized-batch-runner:1.0.0 .
```

Run the orchestrator (Linux/macOS with Docker CLI available):

```bash
python -m app.runner
```

The orchestrator invokes the Docker CLI to start one worker container per task. The Docker daemon must be running and accessible to the user.

Run the test suite:

```bash
python -m unittest discover -s tests -v
```

## Run the orchestrator in Docker Compose

The Compose setup mounts the Docker socket so the orchestrator container can launch worker containers:

```bash
docker compose up --build
```

Stop it:

```bash
docker compose down
```

**Security note:** access to `/var/run/docker.sock` is effectively privileged access to the Docker host. Use this configuration only in a trusted local development environment. For shared or production environments, use a restricted remote execution service or dedicated worker architecture instead.

## Configuration

Edit `config/manifest.json`:

```json
{
  "image": "containerized-batch-runner:1.0.0",
  "tasks": [
    {"id": "task_1"},
    {"id": "task_2", "max_attempts": 5, "backoff_seconds": 2}
  ],
  "max_attempts": 3,
  "backoff_seconds": 1,
  "memory_limit": "256m",
  "cpus": 0.5,
  "task_timeout_seconds": 300,
  "log_level": "INFO"
}
```

Every task ID must be unique and must be registered in `tasks/sample_tasks.py`. Task functions should be idempotent because retries can execute a task more than once.

## Recovery behavior

1. The orchestrator reads the manifest and checkpoint.
2. Tasks already in the checkpoint are skipped.
3. Each remaining task starts in its own container.
4. A failed task is retried according to its retry policy.
5. On success, its ID is atomically added to the checkpoint.
6. If all attempts fail, the batch stops and writes a failure report.
7. Restarting the orchestrator resumes from the last completed task.

Checkpoint and report files are written under `data/`, which is excluded from Git.

## Project layout

```text
app/                   Orchestration, Docker execution, retry, checkpoint, worker
tasks/                 Example task implementations
config/manifest.json   Batch configuration
tests/                 Unit tests
.github/workflows/     GitHub Actions CI
Dockerfile             Worker image
docker-compose.yml     Local orchestrator deployment
```

## Tests

The unit tests cover retry success and exhaustion, checkpoint persistence, batch resume behavior, manifest validation, and Docker command construction. The CI workflow runs these tests and builds the Docker image on pushes and pull requests to `main`.

## Limitations and operational considerations

- The included task registry and task functions are examples; replace them with real workload logic.
- The Docker executor requires a reachable Docker daemon and a locally available image tag.
- The current checkpoint is a single-process JSON store; it is not a distributed coordination system for concurrent orchestrators.
- Task timeout is enforced by the Docker subprocess call; hard termination and cleanup should be validated in the target operating system.
- Worker containers have CPU and memory limits but do not yet implement a full network/filesystem sandbox.
- Exactly-once execution is not guaranteed. Design tasks to be idempotent and make external side effects safe to repeat.

## License

MIT
