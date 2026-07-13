import json
import os
import threading
from collections import deque
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from ..core.ports import ActivityHistoryPort, JsonMap


class JsonlActivityHistory(ActivityHistoryPort):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    async def append(self, kind: str, data: JsonMap) -> JsonMap:
        entry: JsonMap = {"id": uuid4().hex, "time": datetime.now().isoformat(timespec="seconds"), "kind": kind, "data": data}
        line = json.dumps(entry, ensure_ascii=False)
        with self._lock, self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return entry

    async def list_events(self, kind: str | None = None, limit: int = 20) -> list[JsonMap]:
        size = max(1, min(limit, 100))
        items: deque[JsonMap] = deque(maxlen=size)
        if not self.path.exists():
            return []
        with self._lock, self.path.open("r", encoding="utf-8") as handle:
            for number, line in enumerate(handle, 1):
                entry = _decode(line, number)
                if not kind or entry.get("kind") == kind:
                    items.append(entry)
        return list(reversed(items))


def _decode(line: str, number: int) -> JsonMap:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid activity history line {number}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"invalid activity history object at line {number}")
    return payload
