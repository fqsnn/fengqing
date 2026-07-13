import os
import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)
load_dotenv(Path(__file__).resolve().parents[1] / ".env.local", override=True)

from .api.routes import get_router
from .core.agent import CodeAgent
from .core.context_loader import context_dir_from_env, load_context, private_context_for_model
from .core.orchestrator import HybridOrchestrator
from .core.services import AICoreService, DEFAULT_SYSTEM_PROMPT
from .core.shared_context import SharedContext
from .infrastructure.event_store import FileEventStore
from .infrastructure.activity_history import JsonlActivityHistory
from .infrastructure.evolution_adapter import EvolutionEngine
from .infrastructure.llm_adapter import build_llm_adapter
from .infrastructure.memory_adapter import InMemoryMemoryAdapter
from .infrastructure.private_memory import MarkdownContextRecall, MarkdownMemoryAdmin
from .infrastructure.python_example_runner import LocalPythonExampleRunner
from .infrastructure.reflection_adapter import SelfReflectionEngine
from .infrastructure.task_ledger import JsonlTaskLedger
from .infrastructure.web_search_adapter import build_web_search_adapter

logging.basicConfig(level=logging.INFO)

BASE_DIR = Path(__file__).resolve().parents[1]
CONTEXT_DIR = BASE_DIR / "context"
PRIVATE_CONTEXT_DIR = context_dir_from_env("PRIVATE_CONTEXT_DIR") or BASE_DIR / "private_context"
WORKSPACE_CONTEXT_DIR = context_dir_from_env("WORKSPACE_CONTEXT_DIR")
PUBLIC_CONTEXT = load_context(CONTEXT_DIR)
PRIVATE_REMOTE = os.getenv("PRIVATE_CONTEXT_ALLOW_REMOTE", "false").lower().strip() == "true"
PRIVATE_MODEL_ENABLED = bool(private_context_for_model("enabled", os.getenv("AI_PROVIDER", "ollama"), PRIVATE_REMOTE))
SYSTEM_PROMPT = "\n\n".join(part for part in [DEFAULT_SYSTEM_PROMPT, PUBLIC_CONTEXT] if part)

llm = build_llm_adapter()
memory = InMemoryMemoryAdapter()
reflection = SelfReflectionEngine(llm)
evolution = EvolutionEngine(SYSTEM_PROMPT)
event_store = FileEventStore(BASE_DIR / "event_logs")
activity_history = JsonlActivityHistory(BASE_DIR / "event_logs" / "activity.jsonl")
task_ledger = JsonlTaskLedger(BASE_DIR / "event_logs" / "tasks.jsonl")
shared_context = SharedContext(limit=8)
web_search = build_web_search_adapter()
context_recall = MarkdownContextRecall(PRIVATE_CONTEXT_DIR, WORKSPACE_CONTEXT_DIR)
memory_admin = MarkdownMemoryAdmin(PRIVATE_CONTEXT_DIR, activity_history)
python_runner = LocalPythonExampleRunner(artifact_dir=BASE_DIR / "runtime_artifacts")
code_agent = CodeAgent(llm, BASE_DIR)
orchestrator = HybridOrchestrator(llm, code_agent, python_runner, web_search=web_search, shared_context=shared_context, history=activity_history, tasks=task_ledger)

service = AICoreService(
    llm, memory, reflection, evolution, event_store, python_runner, system_prompt=SYSTEM_PROMPT,
    shared_context=shared_context, web_search=web_search, context_recall=context_recall,
    agent_runner=orchestrator, allow_private_model_context=PRIVATE_MODEL_ENABLED
)

app = FastAPI(title="风轻思念浓 AI")
app.include_router(get_router(service, orchestrator, activity_history, memory_admin, task_ledger))


@app.get("/")
async def index() -> dict[str, str]:
    return {"name": "风轻思念浓 AI", "entry": "native-client", "status": "ok"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
