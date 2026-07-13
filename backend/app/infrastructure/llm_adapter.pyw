import logging
import os

import httpx

from ..core.ports import LLMEnginePort, LlmMessage

logger = logging.getLogger(__name__)


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def build_llm_adapter() -> LLMEnginePort:
    provider = required_env("AI_PROVIDER").lower().strip()
    if provider == "openai":
        return OpenAIAdapter()
    if provider == "ollama":
        return OllamaAdapter()
    raise ValueError(f"Unsupported AI_PROVIDER: {provider}")


class OllamaAdapter(LLMEnginePort):
    def __init__(self) -> None:
        self.base_url = required_env("OLLAMA_BASE_URL").rstrip("/")
        self.model = required_env("OLLAMA_MODEL")
        self.temperature = float(required_env("OLLAMA_TEMPERATURE"))
        self.timeout = httpx.Timeout(float(required_env("LLM_TIMEOUT_SECONDS")))

    async def generate_response(self, messages: list[LlmMessage], max_output_tokens: int | None = None) -> str:
        payload = {"model": self.model, "messages": messages, "stream": False, "options": self._options(max_output_tokens)}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            return self._extract_chat(resp.json())

    async def generate_raw(self, prompt: str, max_output_tokens: int | None = None) -> str:
        payload = {"model": self.model, "prompt": prompt, "stream": False, "options": self._options(max_output_tokens)}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/api/generate", json=payload)
            resp.raise_for_status()
            return str(resp.json().get("response", ""))

    def _options(self, max_output_tokens: int | None) -> dict[str, float | int]:
        options: dict[str, float | int] = {"temperature": self.temperature}
        if max_output_tokens is not None:
            options["num_predict"] = _output_limit(max_output_tokens)
        return options

    def _extract_chat(self, data: dict[str, object]) -> str:
        message = data.get("message")
        if isinstance(message, dict) and isinstance(message.get("content"), str):
            return message["content"]
        response = data.get("response")
        if isinstance(response, str):
            return response
        logger.error("Unexpected Ollama response: %s", data)
        raise RuntimeError("Unexpected Ollama response shape")


class OpenAIAdapter(LLMEnginePort):
    def __init__(self) -> None:
        self.base_url = required_env("OPENAI_BASE_URL").rstrip("/")
        self.api_key = required_env("OPENAI_API_KEY")
        self.model = required_env("OPENAI_MODEL")
        self.temperature = float(required_env("OPENAI_TEMPERATURE"))
        self.timeout = httpx.Timeout(float(required_env("LLM_TIMEOUT_SECONDS")))

    async def generate_response(self, messages: list[LlmMessage], max_output_tokens: int | None = None) -> str:
        payload = {"model": self.model, "input": messages, "temperature": self.temperature}
        if max_output_tokens is not None:
            payload["max_output_tokens"] = _output_limit(max_output_tokens)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/responses", headers=self._headers(), json=payload)
            resp.raise_for_status()
            return self._extract_text(resp.json())

    async def generate_raw(self, prompt: str, max_output_tokens: int | None = None) -> str:
        return await self.generate_response([{"role": "user", "content": prompt}], max_output_tokens=max_output_tokens)

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _extract_text(self, data: dict[str, object]) -> str:
        text = data.get("output_text")
        if isinstance(text, str):
            return text
        logger.error("Unexpected OpenAI response: %s", data)
        raise RuntimeError("Unexpected OpenAI response shape")


def _output_limit(value: int) -> int:
    if value < 1:
        raise ValueError("max_output_tokens must be positive")
    return value
