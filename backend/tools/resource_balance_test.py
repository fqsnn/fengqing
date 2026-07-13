import asyncio

from app.core.context_recall import LocalContextRecall
from app.core.command_runner import COMMANDS
from app.core.entities import Conversation, Reflection
from app.core.resource_balance import BalanceSettings, ResourceBalance, ResourceProfile
from app.core.services import AICoreService
from app.infrastructure.llm_adapter import OllamaAdapter


class MemoryStub:
    def __init__(self) -> None:
        self.items: dict[str, Conversation] = {}

    async def load(self, session_id: str) -> Conversation | None:
        return self.items.get(session_id)

    async def save(self, session_id: str, conversation: Conversation) -> None:
        self.items[session_id] = conversation


class LlmStub:
    def __init__(self) -> None:
        self.messages: list[dict[str, str]] = []
        self.output_limit: int | None = None

    async def generate_response(self, messages: list[dict[str, str]], max_output_tokens: int | None = None) -> str:
        self.messages = messages
        self.output_limit = max_output_tokens
        return "可验证回答。"

    async def generate_raw(self, prompt: str, max_output_tokens: int | None = None) -> str:
        return prompt


class ReflectionStub:
    def __init__(self) -> None:
        self.output_limit: int | None = None

    async def reflect(self, user_input: str, raw_response: str, history: list[dict[str, str]], max_output_tokens: int | None = None) -> Reflection:
        self.output_limit = max_output_tokens
        return Reflection(raw_response, raw_response, [], 1.0, "validated")


class EvolutionStub:
    async def mutate(self, reflections: list[Reflection]) -> str:
        return ""


class EventStub:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, object]]] = []

    async def append_event(self, session_id: str, event_type: str, data: dict[str, object]) -> None:
        self.events.append((event_type, data))


class PythonStub:
    async def run_heart(self) -> dict[str, object]:
        return {}


def _balance() -> ResourceBalance:
    profiles = {
        "light": ResourceProfile("light", 2, 20, 11, 12, 13),
        "focused": ResourceProfile("focused", 3, 30, 21, 22, 23),
        "deep": ResourceProfile("deep", 4, 80, 31, 32, 33),
        "guarded": ResourceProfile("guarded", 5, 90, 41, 42, 43),
    }
    settings = BalanceSettings(10, 20, 2, 30, 90, profiles)
    return ResourceBalance(settings)


async def _applies_deep_budget() -> bool:
    balance, llm, reflection, events = _balance(), LlmStub(), ReflectionStub(), EventStub()
    service = AICoreService(
        llm, MemoryStub(), reflection, EvolutionStub(), events, PythonStub(), balance,
        system_prompt="核心", public_context_recall=LocalContextRecall("- 资源均衡架构必须可验证。"),
        allow_private_model_context=False,
    )
    await service.process_user_input("balance", "请完整严谨地分析资源均衡架构。")
    public_context = any("公开创作上下文" in message["content"] for message in llm.messages)
    recorded = any(kind == "RESOURCE_BALANCE" and data.get("mode") == "deep" for kind, data in events.events)
    return llm.output_limit == 31 and reflection.output_limit == 32 and public_context and recorded


def _selects_modes() -> bool:
    balance = _balance()
    light = balance.decide("你好")
    focused = balance.decide("可以吗？")
    deep = balance.decide("请完整分析这个架构")
    guarded = balance.decide("修改代码", operation="agent_write", allow_write=True)
    command_coverage = any(name == "resource_balance_test" for name, _args in COMMANDS)
    return light.profile.name == "light" and focused.profile.name == "focused" and deep.profile.name == "deep" and guarded.profile.name == "guarded" and guarded.code_output_tokens(100) == 50 and command_coverage


def _forwards_ollama_limit() -> bool:
    adapter = object.__new__(OllamaAdapter)
    adapter.temperature = 0.7
    return adapter._options(31) == {"temperature": 0.7, "num_predict": 31} and adapter._options(None) == {"temperature": 0.7}


def main() -> int:
    passed = _selects_modes() and _forwards_ollama_limit() and asyncio.run(_applies_deep_budget())
    print(f"resource_balance_test={'pass' if passed else 'fail'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
