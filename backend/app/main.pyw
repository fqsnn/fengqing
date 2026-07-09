import logging
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from .api.routes import get_router
from .api.schemas import AgentRequest
from .core.agent import CodeAgent
from .core.context_loader import load_context
from .core.orchestrator import HybridOrchestrator
from .core.services import AICoreService, DEFAULT_SYSTEM_PROMPT
from .core.shared_context import SharedContext
from .infrastructure.event_store import FileEventStore
from .infrastructure.evolution_adapter import EvolutionEngine
from .infrastructure.llm_adapter import build_llm_adapter
from .infrastructure.memory_adapter import InMemoryMemoryAdapter
from .infrastructure.reflection_adapter import SelfReflectionEngine

logging.basicConfig(level=logging.INFO)

BASE_DIR = Path(__file__).resolve().parents[1]
CONTEXT_DIR = BASE_DIR / "context"
SYSTEM_PROMPT = "\n\n".join(part for part in [DEFAULT_SYSTEM_PROMPT, load_context(CONTEXT_DIR)] if part)

llm = build_llm_adapter()
memory = InMemoryMemoryAdapter()
reflection = SelfReflectionEngine(llm)
evolution = EvolutionEngine(SYSTEM_PROMPT)
event_store = FileEventStore(BASE_DIR / "event_logs")
shared_context = SharedContext(limit=8)

service = AICoreService(llm, memory, reflection, evolution, event_store, system_prompt=SYSTEM_PROMPT, shared_context=shared_context)
code_agent = CodeAgent(llm, BASE_DIR)
orchestrator = HybridOrchestrator(llm, code_agent, shared_context=shared_context)

app = FastAPI(title="风轻思念浓 AI")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(get_router(service, orchestrator))


@app.get("/")
async def index() -> dict[str, str]:
    return {"name": "风轻思念浓 AI", "entry": "native-client", "status": "ok"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/agent")
async def run_agent(req: Optional[AgentRequest] = Body(default=None), instruction: Optional[str] = None) -> dict[str, object]:
    text = req.instruction if req else instruction
    if not text:
        raise HTTPException(status_code=400, detail="instruction is required")
    result = await orchestrator.execute(text, allow_write=req.allow_write if req else False)
    return {"result": result}
