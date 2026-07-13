import os

from .ports import JsonMap
from .progress_ledger import CURRENT


def runtime_status() -> JsonMap:
    provider = os.getenv("AI_PROVIDER", "ollama").lower().strip()
    key = "OPENAI_MODEL" if provider == "openai" else "OLLAMA_MODEL"
    return {"provider": provider, "model": os.getenv(key, "unknown"), **_capabilities(),
            "progress_stage": CURRENT["stage"], "latest_progress": CURRENT["focus"]}


def _capabilities() -> JsonMap:
    return {
        "fast_path": True,
        "agent": True,
        "agent_self_use": True,
        "task_state_machine": True,
        "private_memory": True,
        "workspace_sync": bool(os.getenv("WORKSPACE_CONTEXT_DIR", "").strip()),
        "dual_loop": True,
        "python_execution": True,
        "web_search": os.getenv("WEB_SEARCH_ENABLED", "false").lower().strip() == "true",
    }
