import os

from .ports import JsonMap


def runtime_status() -> JsonMap:
    provider = os.getenv("AI_PROVIDER", "ollama").lower().strip()
    key = "OPENAI_MODEL" if provider == "openai" else "OLLAMA_MODEL"
    return {
        "provider": provider,
        "model": os.getenv(key, "unknown"),
        "fast_path": True,
        "agent": True,
    }
