"""Synthetic offline Agent runner; no external services or model calls."""
import json
from pathlib import Path


class Store:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, task_id):
        if not task_id.isalnum():
            raise ValueError("task_id must be alphanumeric")
        return self.directory / (task_id + ".json")

    def create(self, task_id, prompt, plan):
        task = {"id": task_id, "prompt": prompt, "plan": plan,
                "index": 0, "state": "pending", "results": [], "error": None}
        with self._path(task_id).open("x", encoding="utf-8") as stream:
            json.dump(task, stream)
        return task

    def read(self, task_id):
        return json.loads(self._path(task_id).read_text(encoding="utf-8"))

    def save(self, task):
        path = self._path(task["id"])
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(task), encoding="utf-8")
        temporary.replace(path)


def execute(step, tools):
    name = step["tool"]
    if name not in tools:
        raise ValueError("unknown tool: " + name)
    return tools[name](**step["args"])


def run_task(store, task_id, tools):
    task = store.read(task_id)
    if task["state"] == "completed":
        return task
    task["state"] = "running"
    task["error"] = None
    store.save(task)
    while task["index"] < len(task["plan"]):
        step = task["plan"][task["index"]]
        try:
            result = execute(step, tools)
        except Exception as error:
            task["state"] = "failed"
            task["error"] = str(error)
            store.save(task)
            return task
        task["results"].append(result)
        task["index"] += 1
        store.save(task)
    task["state"] = "completed"
    store.save(task)
    return task
