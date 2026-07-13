import os
from pathlib import Path


def load_context(folder: Path, recursive: bool = False) -> str:
    if not folder.exists():
        return ""
    chunks: list[str] = []
    paths = folder.rglob("*.md") if recursive else folder.glob("*.md")
    for path in sorted(paths):
        text = path.read_text(encoding="utf-8").strip()
        if text:
            name = path.relative_to(folder).with_suffix("").as_posix()
            chunks.append(f"## {name}\n{text}")
    return "\n\n".join(chunks)


def context_dir_from_env(name: str) -> Path | None:
    value = os.getenv(name, "").strip()
    return Path(value).expanduser() if value else None


def private_context_for_model(context: str, provider: str, allow_remote: bool) -> str:
    return context if provider.lower().strip() == "ollama" or allow_remote else ""
