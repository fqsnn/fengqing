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
