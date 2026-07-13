import os
from pathlib import Path


def load_context(folder: Path) -> str:
    if not folder.exists():
        return ""
    chunks: list[str] = []
    for path in sorted(folder.glob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        if text:
            chunks.append(f"## {path.stem}\n{text}")
    return "\n\n".join(chunks)


def context_dir_from_env(name: str) -> Path | None:
    value = os.getenv(name, "").strip()
    return Path(value).expanduser() if value else None


def private_context_for_model(context: str, provider: str, allow_remote: bool) -> str:
    return context if provider.lower().strip() == "ollama" or allow_remote else ""
