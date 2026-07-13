import asyncio
import sys
import time
from pathlib import Path

from .ports import JsonMap

BACKEND_ROOT = Path(__file__).resolve().parents[2]
TAIL_CHARS = 2400

COMPILE_SCRIPT = """
from pathlib import Path
files = list(Path("app").rglob("*.pyw")) + list(Path("tools").rglob("*.py"))
for path in files:
    compile(path.read_text(encoding="utf-8"), str(path), "exec")
print(f"compile=pass checked={len(files)}")
""".strip()

COMMANDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("quality_gate", ("tools/quality_gate.py",)),
    ("compile_all", ("-c", COMPILE_SCRIPT)),
    ("smoke_test", ("-m", "tools.smoke_test")),
    ("state_test", ("-m", "tools.state_test")),
    ("resource_balance_test", ("-m", "tools.resource_balance_test")),
)


async def run_quality_commands(timeout: float = 18.0) -> JsonMap:
    results: list[JsonMap] = []
    for name, args in COMMANDS:
        result = await _run(name, (sys.executable, *args), timeout)
        results.append(result)
        if int(result["exit_code"]) != 0:
            break
    return {"passed": all(int(item["exit_code"]) == 0 for item in results), "commands": results}


async def _run(name: str, args: tuple[str, ...], timeout: float) -> JsonMap:
    start = time.perf_counter()
    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            cwd=BACKEND_ROOT,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return _result(name, args, int(proc.returncode or 0), stdout, stderr, start)
    except TimeoutError:
        return _result(name, args, 124, b"", f"timeout after {timeout}s".encode(), start)
    except OSError as exc:
        return _result(name, args, 127, b"", str(exc).encode(), start)


def _result(name: str, args: tuple[str, ...], code: int, stdout: bytes, stderr: bytes, start: float) -> JsonMap:
    return {
        "name": name,
        "args": _public_args(args),
        "exit_code": code,
        "duration_ms": int((time.perf_counter() - start) * 1000),
        "stdout": _tail(stdout),
        "stderr": _tail(stderr),
    }


def _public_args(args: tuple[str, ...]) -> list[str]:
    return ["python" if item == sys.executable else item for item in args]


def _tail(data: bytes) -> str:
    text = data.decode("utf-8", errors="replace").strip()
    return text[-TAIL_CHARS:]
