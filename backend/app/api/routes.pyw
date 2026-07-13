from fastapi import APIRouter, HTTPException

from ..core.orchestrator import HybridOrchestrator
from ..core.ports import ActivityHistoryPort, JsonMap, MemoryAdminPort, RuntimeProbePort, TaskLedgerPort
from ..core.progress_ledger import progress_snapshot
from ..core.runtime_status import runtime_status
from ..core.services import AICoreService
from .schemas import AgentRequest, AgentResponse, ChatRequest, ChatResponse, MemoryRequest


class ChatEndpoint:
    def __init__(self, service: AICoreService) -> None:
        self.service = service

    async def __call__(self, req: ChatRequest) -> ChatResponse:
        try:
            reply = await self.service.process_user_input(req.session_id, req.message, req.allow_agent_write)
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


class StatusEndpoint:
    def __init__(self, probe: RuntimeProbePort) -> None:
        self.probe = probe

    async def __call__(self) -> JsonMap:
        return await runtime_status(self.probe)


class HistoryEndpoint:
    def __init__(self, history: ActivityHistoryPort) -> None:
        self.history = history

    async def __call__(self, kind: str | None = None, limit: int = 20) -> JsonMap:
        items = await self.history.list_events(kind=kind, limit=limit)
        return {"items": items, "count": len(items)}


class TasksEndpoint:
    def __init__(self, tasks: TaskLedgerPort) -> None:
        self.tasks = tasks

    async def __call__(self, limit: int = 20) -> JsonMap:
        items = await self.tasks.list_tasks(limit=limit)
        return {"items": items, "count": len(items)}


class MemoryCollectionEndpoint:
    def __init__(self, memories: MemoryAdminPort) -> None:
        self.memories = memories

    async def list_items(self) -> JsonMap:
        items = await self.memories.list_facts()
        return {"items": items, "count": len(items)}

    async def create(self, req: MemoryRequest) -> JsonMap:
        try:
            return await self.memories.add(req.text)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc


class MemoryItemEndpoint:
    def __init__(self, memories: MemoryAdminPort) -> None:
        self.memories = memories

    async def update(self, memory_id: str, req: MemoryRequest) -> JsonMap:
        try:
            item = await self.memories.update(memory_id, req.text)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if not item:
            raise HTTPException(status_code=404, detail="memory not found")
        return item

    async def delete(self, memory_id: str) -> JsonMap:
        item = await self.memories.delete(memory_id)
        if not item:
            raise HTTPException(status_code=404, detail="memory not found")
        return item


def get_router(service: AICoreService, runtime_probe: RuntimeProbePort, orchestrator: HybridOrchestrator | None = None, history: ActivityHistoryPort | None = None, memories: MemoryAdminPort | None = None, tasks: TaskLedgerPort | None = None) -> APIRouter:
    router = APIRouter(prefix="/api/v1")
    router.add_api_route("/status", StatusEndpoint(runtime_probe).__call__, methods=["GET"])
    router.add_api_route("/progress", progress_endpoint, methods=["GET"])
    router.add_api_route("/chat", ChatEndpoint(service).__call__, methods=["POST"], response_model=ChatResponse)
    if orchestrator:
        endpoint = AgentEndpoint(orchestrator).__call__
        router.add_api_route("/agent", endpoint, methods=["POST"], response_model=AgentResponse)
    _register_state_routes(router, history, memories, tasks)
    return router


def _register_state_routes(router: APIRouter, history: ActivityHistoryPort | None, memories: MemoryAdminPort | None, tasks: TaskLedgerPort | None) -> None:
    if history:
        router.add_api_route("/history", HistoryEndpoint(history).__call__, methods=["GET"])
    if tasks:
        router.add_api_route("/tasks", TasksEndpoint(tasks).__call__, methods=["GET"])
    if memories:
        collection, item = MemoryCollectionEndpoint(memories), MemoryItemEndpoint(memories)
        router.add_api_route("/memories", collection.list_items, methods=["GET"])
        router.add_api_route("/memories", collection.create, methods=["POST"])
        router.add_api_route("/memories/{memory_id}", item.update, methods=["PATCH"])
        router.add_api_route("/memories/{memory_id}", item.delete, methods=["DELETE"])


async def progress_endpoint() -> JsonMap:
    return progress_snapshot()
