import asyncio
import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory, gettempdir
from uuid import uuid4

from ..core.ports import JsonMap, PythonExampleRunnerPort
from ..core.python_examples import PYTHON_HEART_SOURCE

MAX_ARTIFACTS = 12
MAX_OUTPUT_CHARS = 2400


class LocalPythonExampleRunner(PythonExampleRunnerPort):
    def __init__(self, timeout_seconds: float = 5.0, artifact_dir: Path | None = None) -> None:
        self.python = sys.executable
        self.timeout_seconds = timeout_seconds
        self.artifact_dir = artifact_dir or Path(gettempdir()) / "fengqing-python-artifacts"

    async def run_heart(self) -> JsonMap:
        artifact = await asyncio.to_thread(_next_artifact, self.artifact_dir)
        with TemporaryDirectory(prefix="fengqing-python-") as folder:
            script = Path(folder) / "heart.py"
            await asyncio.to_thread(script.write_text, PYTHON_HEART_SOURCE, encoding="utf-8")
            return await self._execute(script, artifact)

    async def _execute(self, script: Path, artifact: Path) -> JsonMap:
        started = time.perf_counter()
        args = (self.python, "-I", "-B", str(script), str(artifact))
        code, stdout, stderr, timed_out = await asyncio.to_thread(_run, args, str(script.parent), self.timeout_seconds)
        return _result(code, stdout, stderr, started, timed_out, artifact)


def _next_artifact(folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    old = sorted(folder.glob("heart-*.png"), key=lambda path: path.stat().st_mtime)
    for path in old[: max(0, len(old) - MAX_ARTIFACTS + 1)]:
        try:
            path.unlink()
        except OSError:
            continue
    return folder / f"heart-{uuid4().hex}.png"


def _run(args: tuple[str, ...], cwd: str, timeout: float) -> tuple[int, bytes, bytes, bool]:
    try:
        result = subprocess.run(args, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        return 124, _bytes(exc.stdout), _bytes(exc.stderr), True
    except OSError as exc:
        return 127, b"", str(exc).encode(), False
    return int(result.returncode), result.stdout, result.stderr, False


def _result(code: int, stdout: bytes, stderr: bytes, started: float, timed_out: bool, artifact: Path) -> JsonMap:
    created = artifact.is_file()
    artifact_error = "" if created or code != 0 else "Python exited successfully but did not create the expected PNG artifact."
    return {
        "passed": code == 0 and not timed_out and created,
        "executed": not timed_out,
        "timed_out": timed_out,
        "exit_code": code,
        "duration_ms": int((time.perf_counter() - started) * 1000),
        "stdout": _tail(stdout),
        "stderr": _tail(stderr),
        "artifact_path": str(artifact) if created else "",
        "artifact_created": created,
        "artifact_error": artifact_error,
        "scope": "temporary_directory",
    }


def _tail(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")[-MAX_OUTPUT_CHARS:].rstrip()


def _bytes(data: bytes | str | None) -> bytes:
    return data if isinstance(data, bytes) else str(data or "").encode()
