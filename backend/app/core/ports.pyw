from abc import ABC, abstractmethod

from .entities import Conversation, Reflection

JsonMap = dict[str, object]
LlmMessage = dict[str, str]


class LLMEnginePort(ABC):
    @abstractmethod
    async def generate_response(self, messages: list[LlmMessage]) -> str:
        raise NotImplementedError

    @abstractmethod
    async def generate_raw(self, prompt: str) -> str:
        raise NotImplementedError


class ShortTermMemoryPort(ABC):
    @abstractmethod
    async def save(self, session_id: str, conversation: Conversation) -> None:
        raise NotImplementedError

    @abstractmethod
    async def load(self, session_id: str) -> Conversation | None:
        raise NotImplementedError


class ReflectionEnginePort(ABC):
    @abstractmethod
    async def reflect(self, user_input: str, raw_response: str, history: list[LlmMessage]) -> Reflection:
        raise NotImplementedError


class EvolutionEnginePort(ABC):
    @abstractmethod
    async def mutate(self, reflections: list[Reflection]) -> str:
        raise NotImplementedError


class WebSearchPort(ABC):
    @abstractmethod
    async def search(self, query: str) -> list[JsonMap]:
        raise NotImplementedError


class EventStorePort(ABC):
    @abstractmethod
    async def append_event(self, session_id: str, event_type: str, data: JsonMap) -> None:
        raise NotImplementedError
