"""Tests supplied as synthetic source evidence; not a skill behavior score."""
from tempfile import TemporaryDirectory
import unittest

from runner import Store, run_task


class RunnerTests(unittest.TestCase):
    def test_success(self):
        with TemporaryDirectory() as directory:
            store = Store(directory)
            store.create("one", "double 3", [{"tool": "double", "args": {"n": 3}}])
            task = run_task(store, "one", {"double": lambda n: n * 2})
            self.assertEqual(task["results"], [6])
            self.assertEqual(store.read("one")["state"], "completed")

    def test_completed_task_is_not_repeated(self):
        with TemporaryDirectory() as directory:
            store = Store(directory)
            calls = []
            store.create("two", "note", [{"tool": "note", "args": {}}])
            tools = {"note": lambda: calls.append("called")}
            run_task(store, "two", tools)
            run_task(Store(directory), "two", tools)
            self.assertEqual(calls, ["called"])

    def test_unknown_tool_is_failed(self):
        with TemporaryDirectory() as directory:
            store = Store(directory)
            store.create("three", "unknown", [{"tool": "missing", "args": {}}])
            task = run_task(store, "three", {})
            self.assertEqual(task["state"], "failed")
            self.assertEqual(task["index"], 0)
            self.assertIn("unknown tool", task["error"])


if __name__ == "__main__":
    unittest.main()
