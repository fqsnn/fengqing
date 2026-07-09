from fastapi import APIRouter, HTTPException

from ..core.orchestrator import HybridOrchestrator
from ..core.ports import JsonMap
from ..core.runtime_status import runtime_status
from ..core.services import AICoreService
from .schemas import AgentRequest, AgentResponse, ChatRequest, ChatResponse


class ChatEndpoint:
    def __init__(self, service: AICoreService) -> None:
        self.service = service

    async def __call__(self, req: ChatRequest) -> ChatResponse:
        try:
            reply = await self.service.process_user_input(req.session_id, req.message)
            return ChatResponse(session_id=req.session_id, reply=reply)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc


class AgentEndpoint:
    def __init__(self, orchestrator: HybridOrchestrator) -> None:
        self.orchestrator = orchestrator

    async def __call__(self, req: AgentRequest) -> AgentResponse:
        try:
            result = await self.orchestrator.execute(req.instruction, allow_write=req.allow_write)
            return AgentResponse(result=result)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc


def get_router(service: AICoreService, orchestrator: HybridOrchestrator | None = None) -> APIRouter:
    router = APIRouter(prefix="/api/v1")
    router.add_api_route("/status", status_endpoint, methods=["GET"])
    router.add_api_route("/chat", ChatEndpoint(service).__call__, methods=["POST"], response_model=ChatResponse)
    if orchestrator:
        endpoint = AgentEndpoint(orchestrator).__call__
        router.add_api_route("/agent", endpoint, methods=["POST"], response_model=AgentResponse)
    return router


async def status_endpoint() -> JsonMap:
    return runtime_status()
