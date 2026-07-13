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


class AgentRunnerPort(ABC):
    @abstractmethod
    async def execute(self, instruction: str, allow_write: bool = False) -> JsonMap:
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


class ContextRecallPort(ABC):
    @abstractmethod
    def recall(self, query: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def relevant(self, query: str) -> str:
        raise NotImplementedError


class ActivityHistoryPort(ABC):
    @abstractmethod
    async def append(self, kind: str, data: JsonMap) -> JsonMap:
        raise NotImplementedError

    @abstractmethod
    async def list_events(self, kind: str | None = None, limit: int = 20) -> list[JsonMap]:
        raise NotImplementedError


class TaskLedgerPort(ABC):
    @abstractmethod
    async def create(self, instruction: str, plan: list[JsonMap], allow_write: bool) -> JsonMap:
        raise NotImplementedError

    @abstractmethod
    async def transition(self, task_id: str, status: str, progress: JsonMap | None = None) -> JsonMap | None:
        raise NotImplementedError

    @abstractmethod
    async def list_tasks(self, limit: int = 20) -> list[JsonMap]:
        raise NotImplementedError


class MemoryAdminPort(ABC):
    @abstractmethod
    async def list_facts(self) -> list[JsonMap]:
        raise NotImplementedError

    @abstractmethod
    async def add(self, text: str) -> JsonMap:
        raise NotImplementedError

    @abstractmethod
    async def update(self, memory_id: str, text: str) -> JsonMap | None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, memory_id: str) -> JsonMap | None:
        raise NotImplementedError


class EventStorePort(ABC):
    @abstractmethod
    async def append_event(self, session_id: str, event_type: str, data: JsonMap) -> None:
        raise NotImplementedError
