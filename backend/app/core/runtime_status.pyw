import os

from .ports import JsonMap, RuntimeProbePort
from .progress_ledger import CURRENT


async def runtime_status(probe: RuntimeProbePort) -> JsonMap:
    provider = os.getenv("AI_PROVIDER", "ollama").lower().strip()
    key = "OPENAI_MODEL" if provider == "openai" else "OLLAMA_MODEL"
    return {"provider": provider, "model": os.getenv(key, "unknown"), "model_runtime": await _probe_status(probe), **_capabilities(),
            "progress_stage": CURRENT["stage"], "latest_progress": CURRENT["focus"]}


async def _probe_status(probe: RuntimeProbePort) -> JsonMap:
    try:
        return await probe.model_status()
    except Exception as exc:
        return {"state": "diagnostic_failed", "detail": "模型诊断未完成。", "error_type": type(exc).__name__}


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
        "visual_python_execution": True,
        "web_search": os.getenv("WEB_SEARCH_ENABLED", "false").lower().strip() == "true",
        "resource_balance": True,
    }
