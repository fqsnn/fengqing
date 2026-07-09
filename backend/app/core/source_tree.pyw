from pathlib import Path


class SourceTree:
    SOURCE_SUFFIXES = {".py", ".pyw"}
    IGNORE_DIRS = {".git", "__pycache__", ".backup", "event_logs", "resources", "locales"}

    def __init__(self, target_dir: str | Path) -> None:
        self.target_dir = Path(target_dir).resolve()
        self.backup_dir = self.target_dir / ".backup"
        self.backup_dir.mkdir(exist_ok=True)

    def is_ignored(self, path: Path) -> bool:
        parts = path.relative_to(self.target_dir).parts
        return any(part in self.IGNORE_DIRS or part.startswith(".venv") for part in parts)

    def source_files(self) -> list[Path]:
        files: list[Path] = []
        for path in self.target_dir.rglob("*"):
            if self._is_source(path):
                files.append(path)
        return sorted(files)

    def safe_path(self, path: str | Path) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.target_dir / candidate
        return self._checked(candidate.resolve())

    def backup_path(self, file_path: Path, stamp: int) -> Path:
        return self.backup_dir / f"{file_path.name}.{stamp}.bak"

    def _is_source(self, path: Path) -> bool:
        return path.is_file() and path.suffix.lower() in self.SOURCE_SUFFIXES and not self.is_ignored(path)

    def _checked(self, path: Path) -> Path:
        if self.target_dir not in path.parents and path != self.target_dir:
            raise ValueError("path is outside target_dir")
        if self.is_ignored(path):
            raise ValueError("path is ignored")
        if path.suffix.lower() not in self.SOURCE_SUFFIXES:
            raise ValueError("only Python source files can be modified")
        return path
