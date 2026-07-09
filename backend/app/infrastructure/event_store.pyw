import json
from datetime import datetime
from pathlib import Path

from ..core.ports import EventStorePort, JsonMap


class FileEventStore(EventStorePort):
    def __init__(self, base_path: str | Path) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _safe_session_id(self, session_id: str) -> str:
        safe = "".join(ch for ch in session_id if ch.isalnum() or ch in "-_")
        return safe[:80] or "default"

    async def append_event(self, session_id: str, event_type: str, data: JsonMap) -> None:
        path = self.base_path / f"{self._safe_session_id(session_id)}.jsonl"
        payload = {"t": datetime.now().isoformat(), "type": event_type, "data": data}
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
