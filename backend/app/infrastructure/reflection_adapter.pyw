import json
import re

from ..core.entities import Reflection
from ..core.ports import LLMEnginePort, LlmMessage


class SelfReflectionEngine:
    def __init__(self, llm: LLMEnginePort) -> None:
        self.llm = llm

    async def reflect(self, user_input: str, raw_response: str, history: list[LlmMessage], max_output_tokens: int | None = None) -> Reflection:
        result = await self.llm.generate_raw(self._prompt(user_input, raw_response, history), max_output_tokens=max_output_tokens)
        data = self._parse_json(result, raw_response)
        return Reflection(
            original_response=raw_response,
            revised_response=str(data.get("revised_response", raw_response)),
            contradictions=self._as_list(data.get("contradictions", [])),
            confidence=self._confidence(data.get("confidence", 0.5)),
            inner_monologue=str(data.get("inner_monologue", "")),
        )

    def _prompt(self, user_input: str, raw_response: str, history: list[LlmMessage]) -> str:
        payload = json.dumps(history, ensure_ascii=False)
        return (
            "你是严格的自我审查器。只输出 JSON。"
            f"\n用户输入：{user_input}"
            f"\n原始回答：{raw_response}"
            f"\n最近上下文：{payload}"
            '\n格式：{"contradictions":[],"confidence":0.9,"inner_monologue":"","revised_response":""}'
        )

    def _parse_json(self, text: str, raw_response: str) -> dict[str, object]:
        cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start >= 0 and end > start:
            cleaned = cleaned[start : end + 1]
        try:
            data = json.loads(cleaned)
            return data if isinstance(data, dict) else self._fallback(raw_response)
        except json.JSONDecodeError:
            return self._fallback(raw_response)

    def _fallback(self, raw_response: str) -> dict[str, object]:
        return {"contradictions": [], "confidence": 0.5, "inner_monologue": "反思 JSON 解析失败", "revised_response": raw_response}

    def _confidence(self, value: object) -> float:
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return 0.5

    def _as_list(self, value: object) -> list[str]:
        if isinstance(value, list):
            return [str(item) for item in value]
        return [str(value)] if value else []
