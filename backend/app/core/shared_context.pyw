from dataclasses import dataclass
from datetime import datetime


@dataclass
class SharedEntry:
    source: str
    content: str
    timestamp: datetime


class SharedContext:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self._items: list[SharedEntry] = []

    def add(self, source: str, content: str) -> None:
        clean = content.strip()
        if not clean:
            return
        self._items.append(SharedEntry(source=source, content=clean[:600], timestamp=datetime.now()))
        self._items = self._items[-self.limit :]

    def render(self, max_chars: int | None = None) -> str:
        if not self._items:
            return ""
        rows = [f"- {item.source}: {item.content}" for item in self._items]
        text = "共享运行上下文：\n" + "\n".join(rows)
        return text if max_chars is None else text[:max_chars]
