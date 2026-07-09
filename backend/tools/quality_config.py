from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE_SUFFIXES = {".py", ".pyw", ".html", ".css", ".js"}
SKIP_DIRS = {".git", ".venv", "__pycache__", ".backup", "event_logs"}


def config_path() -> Path:
    return ROOT / "config.yaml"


def read_limits(path: Path) -> dict[str, int]:
    limits: dict[str, int] = {}
    for raw in _lines(path):
        key, value = _pair(raw)
        if key and value.isdigit():
            limits[key] = int(value)
    return limits


def read_list(path: Path, section_name: str) -> list[str]:
    values: list[str] = []
    section = ""
    for raw in _lines(path):
        line = raw.strip()
        section = line[:-1] if line.endswith(":") and not line.startswith("-") else section
        if section == section_name and line.startswith("- "):
            values.append(line[2:].strip())
    return values


def code_files(roots: list[str]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        base = (ROOT / root).resolve()
        files += [p for p in base.rglob("*") if _is_code(p)]
    return sorted(files)


def effective_lines(path: Path) -> int:
    lines = path.read_text(encoding="utf-8").splitlines()
    return sum(1 for line in lines if line.strip() and not line.lstrip().startswith("#"))


def _is_code(path: Path) -> bool:
    return path.is_file() and path.suffix in CODE_SUFFIXES and not _is_skipped(path)


def _is_skipped(path: Path) -> bool:
    return any(part in SKIP_DIRS or part.startswith(".venv") for part in path.parts)


def _lines(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"missing config: {path}")
    return path.read_text(encoding="utf-8").splitlines()


def _pair(raw: str) -> tuple[str, str]:
    line = raw.strip()
    if not line or line.startswith("#") or ":" not in line:
        return "", ""
    key, value = line.split(":", 1)
    return key.strip(), value.strip()
