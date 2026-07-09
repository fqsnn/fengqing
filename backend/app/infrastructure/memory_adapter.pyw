from ..core.entities import Conversation, Message
from ..core.ports import ShortTermMemoryPort


class InMemoryMemoryAdapter(ShortTermMemoryPort):
    def __init__(self) -> None:
        self._storage: dict[str, list[dict[str, str]]] = {}

    async def save(self, session_id: str, conversation: Conversation) -> None:
        limited = conversation.messages[-20:]
        self._storage[session_id] = [{"role": item.role, "content": item.content} for item in limited]

    async def load(self, session_id: str) -> Conversation | None:
        raw = self._storage.get(session_id)
        if not raw:
            return None
        conv = Conversation(session_id=session_id)
        for item in raw:
            conv.messages.append(Message(role=item["role"], content=item["content"]))
        return conv
