"""Runs each task in its own short-lived Docker container."""
import json
import subprocess

class DockerExecutor:
    def __init__(self, image, memory_limit="256m", cpus=0.5, timeout_seconds=300,
                 docker_binary="docker"):
        self.image = image
        self.memory_limit = memory_limit
        self.cpus = cpus
        self.timeout_seconds = timeout_seconds
        self.docker_binary = docker_binary

    def execute(self, task_id):
        command = [
            self.docker_binary, "run", "--rm",
            "--memory", str(self.memory_limit),
            "--cpus", str(self.cpus),
            self.image, "python", "-m", "app.worker", task_id,
        ]
        completed = subprocess.run(
            command, capture_output=True, text=True,
            timeout=self.timeout_seconds, check=False
        )
        output = completed.stdout.strip()
        if completed.returncode != 0:
            detail = output or completed.stderr.strip() or f"container exited {completed.returncode}"
            raise RuntimeError(detail)
        try:
            result = json.loads(output.splitlines()[-1])
        except (IndexError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Worker returned invalid JSON: {output!r}") from exc
        if not result.get("ok"):
            raise RuntimeError(result.get("error", "Task failed"))
        return result.get("result")
