from pydantic import BaseModel, Field

from ..core.ports import JsonMap


class ChatRequest(BaseModel):
    session_id: str
    message: str
    allow_agent_write: bool = False


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    status: str = "success"


class AgentRequest(BaseModel):
    instruction: str = Field(..., min_length=1)
    allow_write: bool = False


class AgentResponse(BaseModel):
    result: JsonMap
    status: str = "success"


class MemoryRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
