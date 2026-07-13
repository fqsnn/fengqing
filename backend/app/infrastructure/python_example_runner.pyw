import asyncio
import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from ..core.ports import JsonMap, PythonExampleRunnerPort
from ..core.python_examples import PYTHON_HEART_SOURCE

MAX_OUTPUT_CHARS = 2400


class LocalPythonExampleRunner(PythonExampleRunnerPort):
    def __init__(self, timeout_seconds: float = 5.0) -> None:
        self.python = sys.executable
        self.timeout_seconds = timeout_seconds

    async def run_heart(self) -> JsonMap:
        with TemporaryDirectory(prefix="fengqing-python-") as folder:
            script = Path(folder) / "heart.py"
            await asyncio.to_thread(script.write_text, PYTHON_HEART_SOURCE, encoding="utf-8")
            return await self._execute(script)

    async def _execute(self, script: Path) -> JsonMap:
        started = time.perf_counter()
        args = (self.python, "-I", "-B", str(script))
        code, stdout, stderr, timed_out = await asyncio.to_thread(_run, args, str(script.parent), self.timeout_seconds)
        return _result(code, stdout, stderr, started, timed_out)


def _run(args: tuple[str, ...], cwd: str, timeout: float) -> tuple[int, bytes, bytes, bool]:
    try:
        result = subprocess.run(args, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        return 124, _bytes(exc.stdout), _bytes(exc.stderr), True
    except OSError as exc:
        return 127, b"", str(exc).encode(), False
    return int(result.returncode), result.stdout, result.stderr, False


def _result(code: int, stdout: bytes, stderr: bytes, started: float, timed_out: bool) -> JsonMap:
    return {
        "passed": code == 0 and not timed_out,
        "executed": not timed_out,
        "timed_out": timed_out,
        "exit_code": code,
        "duration_ms": int((time.perf_counter() - started) * 1000),
        "stdout": _tail(stdout),
        "stderr": _tail(stderr),
        "scope": "temporary_directory",
    }


def _tail(data: bytes) -> str:
    return data.decode("utf-8", errors="replace").strip()[-MAX_OUTPUT_CHARS:]


def _bytes(data: bytes | str | None) -> bytes:
    return data if isinstance(data, bytes) else str(data or "").encode()
