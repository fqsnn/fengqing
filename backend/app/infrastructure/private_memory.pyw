import hashlib
import threading
from pathlib import Path

from ..core.context_loader import load_context
from ..core.context_recall import LocalContextRecall
from ..core.ports import ActivityHistoryPort, ContextRecallPort, JsonMap, MemoryAdminPort

MemoryLocation = tuple[Path, int, str, str]
MEMORY_FILE = "personal_memory.md"


class MarkdownContextRecall(ContextRecallPort):
    def __init__(self, folder: Path, workspace_folder: Path | None = None) -> None:
        sources = [(folder, False)]
        if workspace_folder and workspace_folder.resolve() != folder.resolve():
            sources.append((workspace_folder, True))
        self.sources = tuple(sources)

    def recall(self, query: str) -> str | None:
        return self._reader().recall(query)

    def relevant(self, query: str) -> str:
        return self._reader().relevant(query)

    def _reader(self) -> LocalContextRecall:
        context = "\n\n".join(load_context(folder, recursive) for folder, recursive in self.sources)
        return LocalContextRecall(context)


class MarkdownMemoryAdmin(MemoryAdminPort):
    def __init__(self, folder: Path, history: ActivityHistoryPort) -> None:
        self.folder = folder
        self.history = history
        self._lock = threading.Lock()
        self.folder.mkdir(parents=True, exist_ok=True)

    async def list_facts(self) -> list[JsonMap]:
        with self._lock:
            return [_public(item) for item in _locations(self.folder)]

    async def add(self, text: str) -> JsonMap:
        clean = _clean(text)
        with self._lock:
            existing = _find_text(self.folder, clean)
            item = _public(existing) if existing else _append(self.folder / MEMORY_FILE, clean)
        if not existing:
            await self.history.append("memory_added", {"memory": item})
        return {**item, "created": not bool(existing)}

    async def update(self, memory_id: str, text: str) -> JsonMap | None:
        clean = _clean(text)
        with self._lock:
            location = _find(self.folder, memory_id)
            if not location:
                return None
            old = _public(location)
            changed = _replace(location, clean)
        await self.history.append("memory_updated", {"before": old, "after": changed})
        return changed

    async def delete(self, memory_id: str) -> JsonMap | None:
        with self._lock:
            location = _find(self.folder, memory_id)
            if not location:
                return None
            deleted = _public(location)
            _replace(location, None)
        await self.history.append("memory_deleted", {"memory": deleted})
        return deleted


def _locations(folder: Path) -> list[MemoryLocation]:
    items: list[MemoryLocation] = []
    for path in sorted(folder.glob("*.md")):
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
            text = _fact_text(line)
            if text:
                items.append((path, index, text, _memory_id(path, text)))
    return items


def _fact_text(line: str) -> str | None:
    value = line.strip()
    return _clean(value[2:]) if value.startswith(("- “", '- "')) else None


def _clean(text: str) -> str:
    value = " ".join(text.split()).strip('“”"').strip()
    if not value:
        raise ValueError("memory text cannot be empty")
    return value


def _memory_id(path: Path, text: str) -> str:
    return hashlib.sha256(f"{path.name}\0{text}".encode("utf-8")).hexdigest()[:12]


def _public(item: MemoryLocation) -> JsonMap:
    path, _index, text, memory_id = item
    return {"id": memory_id, "text": text, "source": path.name}


def _find(folder: Path, memory_id: str) -> MemoryLocation | None:
    return next((item for item in _locations(folder) if item[3] == memory_id), None)


def _find_text(folder: Path, text: str) -> MemoryLocation | None:
    return next((item for item in _locations(folder) if item[2] == text), None)


def _append(path: Path, text: str) -> JsonMap:
    current = path.read_text(encoding="utf-8") if path.exists() else "# 私人记忆\n"
    _write(path, current.rstrip() + f"\n\n- “{text}”\n")
    found = _find_text(path.parent, text)
    if not found:
        raise RuntimeError("memory write verification failed")
    return _public(found)


def _replace(item: MemoryLocation, text: str | None) -> JsonMap:
    path, index, _old, _memory_id_value = item
    lines = path.read_text(encoding="utf-8").splitlines()
    lines[index : index + 1] = [] if text is None else [f"- “{text}”"]
    _write(path, "\n".join(lines).rstrip() + "\n")
    return {} if text is None else _public((path, index, text, _memory_id(path, text)))


def _write(path: Path, text: str) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)
