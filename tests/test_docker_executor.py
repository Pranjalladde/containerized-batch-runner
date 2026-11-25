import json
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from app.docker_executor import DockerExecutor

class DockerExecutorTests(unittest.TestCase):
    @patch("app.docker_executor.subprocess.run")
    def test_builds_isolated_container_command(self, run):
        run.return_value = SimpleNamespace(returncode=0, stdout='{"ok": true, "result": "done"}\n', stderr="")
        executor = DockerExecutor("image:tag", memory_limit="128m", cpus=0.25)
        self.assertEqual(executor.execute("task_1"), "done")
        command = run.call_args.args[0]
        self.assertIn("--memory", command)
        self.assertIn("--cpus", command)
        self.assertIn("task_1", command)
