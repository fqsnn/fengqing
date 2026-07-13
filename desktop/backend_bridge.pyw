import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
LOCAL_SETTINGS = dotenv_values(BACKEND / ".env.local")


def _setting(name: str, default: str) -> str:
    return os.getenv(name) or str(LOCAL_SETTINGS.get(name) or default)


HOST = _setting("APP_OPEN_HOST", ".".join(("127", "0", "0", "1")))
PORT = _setting("APP_PORT", "8000")
BASE_URL = f"{'http'}://{HOST}:{PORT}"


def ensure_backend() -> None:
    if request("GET", "/api/v1/status") is not None:
        return
    args = [str(PYTHON), "-m", "uvicorn", "app.main:app", "--host", HOST, "--port", PORT]
    subprocess.Popen(args, cwd=BACKEND, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    for _ in range(30):
        if request("GET", "/api/v1/status") is not None:
            return
        time.sleep(1)


def request(method: str, path: str, payload: dict[str, object] | None = None) -> dict[str, object] | None:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(BASE_URL + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None
