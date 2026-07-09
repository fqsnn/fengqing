import os

from .ports import JsonMap
from .progress_ledger import CURRENT


def runtime_status() -> JsonMap:
    provider = os.getenv("AI_PROVIDER", "ollama").lower().strip()
    key = "OPENAI_MODEL" if provider == "openai" else "OLLAMA_MODEL"
    return {
        "provider": provider,
        "model": os.getenv(key, "unknown"),
        "fast_path": True,
        "agent": True,
        "dual_loop": True,
        "web_search": os.getenv("WEB_SEARCH_ENABLED", "false").lower().strip() == "true",
        "progress_stage": CURRENT["stage"],
        "latest_progress": CURRENT["focus"],
    }
