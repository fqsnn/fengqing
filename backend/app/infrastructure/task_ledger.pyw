import json
import os
import threading
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from ..core.ports import JsonMap, TaskLedgerPort

TASK_STATES = frozenset({"planned", "running", "verified", "completed", "needs_attention", "failed"})
TRANSITIONS = {
    "planned": frozenset({"running", "failed"}), "running": frozenset({"verified", "needs_attention", "failed"}),
    "verified": frozenset({"completed", "needs_attention", "failed"}), "needs_attention": frozenset({"running", "failed"}),
    "completed": frozenset(), "failed": frozenset(),
}


class JsonlTaskLedger(TaskLedgerPort):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    async def create(self, instruction: str, plan: list[JsonMap], allow_write: bool) -> JsonMap:
        task = _new_task(instruction, plan, allow_write)
        with self._lock:
            self._append(task)
        return task

    async def transition(self, task_id: str, status: str, progress: JsonMap | None = None) -> JsonMap | None:
        with self._lock:
            task = self._latest().get(task_id)
            if not task:
                return None
            if not _allowed(str(task.get("status", "")), status):
                raise ValueError(f"invalid task transition: {task.get('status')} -> {status}")
            updated = _updated(task, status, progress)
            self._append(updated)
        return updated

    async def list_tasks(self, limit: int = 20) -> list[JsonMap]:
        with self._lock:
            tasks = list(self._latest().values())
        size = max(1, min(limit, 100))
        return sorted(tasks, key=lambda task: str(task.get("updated_at", "")), reverse=True)[:size]

    def _append(self, task: JsonMap) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(task, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def _latest(self) -> dict[str, JsonMap]:
        latest: dict[str, JsonMap] = {}
        if not self.path.exists():
            return latest
        with self.path.open("r", encoding="utf-8") as handle:
            for number, line in enumerate(handle, 1):
                task = _decode(line, number)
                latest[str(task["id"])] = task
        return latest


def _new_task(instruction: str, plan: list[JsonMap], allow_write: bool) -> JsonMap:
    now = _now()
    return {"id": uuid4().hex, "instruction": instruction, "plan": plan, "allow_write": allow_write,
            "status": "planned", "created_at": now, "updated_at": now, "states": [{"status": "planned", "time": now}]}


def _updated(task: JsonMap, status: str, progress: JsonMap | None) -> JsonMap:
    now = _now()
    states = _states(task) + [{"status": status, "time": now}]
    updated: JsonMap = {**task, "status": status, "updated_at": now, "states": states}
    if progress is not None:
        updated["progress"] = progress
    return updated


def _states(task: JsonMap) -> list[JsonMap]:
    value = task.get("states", [])
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _allowed(current: str, target: str) -> bool:
    return target in TASK_STATES and target in TRANSITIONS.get(current, frozenset())


def _decode(line: str, number: int) -> JsonMap:
    try:
        task = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid task ledger line {number}") from exc
    if not isinstance(task, dict) or not isinstance(task.get("id"), str):
        raise ValueError(f"invalid task ledger object at line {number}")
    return task


def _now() -> str:
    return datetime.now().isoformat(timespec="milliseconds")
