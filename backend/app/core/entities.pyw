from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Message:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Conversation:
    session_id: str
    messages: list[Message] = field(default_factory=list)

    def add_message(self, role: str, content: str) -> None:
        self.messages.append(Message(role=role, content=content))

    def to_llm_format(self) -> list[dict[str, str]]:
        return [{"role": item.role, "content": item.content} for item in self.messages]


@dataclass
class Reflection:
    original_response: str
    revised_response: str
    contradictions: list[str]
    confidence: float
    inner_monologue: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EvolutionMutation:
    old_system_prompt: str
    new_system_prompt: str
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)
