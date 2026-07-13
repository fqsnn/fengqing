from datetime import datetime, timezone

import httpx

from ..core.ports import JsonMap, RuntimeProbePort
from .llm_adapter import required_env


def build_runtime_probe() -> RuntimeProbePort:
    provider = required_env("AI_PROVIDER").lower().strip()
    model_key = "OPENAI_MODEL" if provider == "openai" else "OLLAMA_MODEL"
    if provider == "ollama":
        return OllamaRuntimeProbe(
            required_env("OLLAMA_BASE_URL"),
            required_env(model_key),
            float(required_env("RUNTIME_DIAGNOSTIC_TIMEOUT_SECONDS")),
        )
    return ConfiguredRemoteRuntimeProbe(provider, required_env(model_key))


class OllamaRuntimeProbe(RuntimeProbePort):
    def __init__(self, base_url: str, model: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = httpx.Timeout(timeout_seconds)

    async def model_status(self) -> JsonMap:
        checked_at = _checked_at()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
            return ollama_status_from_payload(self.model, response.json(), checked_at)
        except httpx.HTTPStatusError as exc:
            return _status("service_error", self.model, checked_at, "Ollama 返回了 HTTP 错误。", http_status=exc.response.status_code)
        except httpx.HTTPError:
            return _status("unreachable", self.model, checked_at, "无法连接 Ollama。")
        except ValueError:
            return _status("invalid_response", self.model, checked_at, "Ollama 返回的模型列表无效。")


class ConfiguredRemoteRuntimeProbe(RuntimeProbePort):
    def __init__(self, provider: str, model: str) -> None:
        self.provider = provider
        self.model = model

    async def model_status(self) -> JsonMap:
        return {
            "state": "configured_remote",
            "provider": self.provider,
            "model": self.model,
            "checked_at": _checked_at(),
            "detail": "远程模型是否可用会在真实请求时验证。",
        }


def ollama_status_from_payload(model: str, payload: object, checked_at: str) -> JsonMap:
    if not isinstance(payload, dict) or not isinstance(payload.get("models"), list):
        return _status("invalid_response", model, checked_at, "Ollama 返回的模型列表无效。")
    records = payload["models"]
    available = [str(item["name"]) for item in records if isinstance(item, dict) and isinstance(item.get("name"), str)]
    state = "ready" if model in available else "model_missing"
    detail = "本地配置模型已就绪。" if state == "ready" else "已连接 Ollama，但配置的模型未下载。"
    return _status(state, model, checked_at, detail, available_models=available[:12])


def _status(state: str, model: str, checked_at: str, detail: str, **extra: object) -> JsonMap:
    return {"state": state, "provider": "ollama", "model": model, "checked_at": checked_at, "detail": detail, **extra}


def _checked_at() -> str:
    return datetime.now(timezone.utc).isoformat()
