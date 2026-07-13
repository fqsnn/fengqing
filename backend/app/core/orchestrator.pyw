from collections.abc import Awaitable, Callable

from .agent import CodeAgent
from .agent_progress import summarize_agent_progress
from .agent_replies import EXPLAINERS
from .command_runner import run_quality_commands
from .dual_loop import format_search_context
from .evolution_flow import controlled_self_evolution
from .planner import ACTIONS, direct_plan, parse_plan
from .ports import ActivityHistoryPort, AgentRunnerPort, JsonMap, LLMEnginePort, PythonExampleRunnerPort, TaskLedgerPort, WebSearchPort
from .python_examples import heart_reply
from .self_programming import self_program_once
from .shared_context import SharedContext


class HybridOrchestrator(AgentRunnerPort):
    def __init__(self, llm: LLMEnginePort, code_agent: CodeAgent, python_runner: PythonExampleRunnerPort, web_search: WebSearchPort | None = None, shared_context: SharedContext | None = None, history: ActivityHistoryPort | None = None, tasks: TaskLedgerPort | None = None) -> None:
        self.llm = llm
        self.code_agent = code_agent
        self.python_runner = python_runner
        self.web_search = web_search
        self.shared_context = shared_context
        self.history = history
        self.tasks = tasks
        self.registry: dict[str, Callable[..., Awaitable[object]]] = {
            "analyze_code": self._analyze_code, "review_code": self._review_code,
            "improve_code": self._improve_code, "read_file": self._read_file,
            "run_tests": self._run_tests, "run_quality_commands": self._run_quality_commands,
            "web_search": self._web_search, "generate_python_heart": self._run_python_heart,
        }

    async def execute(self, instruction: str, allow_write: bool = False) -> JsonMap:
        plan = await self._plan(instruction)
        task = await self._start_task(instruction, plan, allow_write)
        results = await self._results(plan, allow_write)
        output = _output(plan, results, allow_write)
        task = await self._finish_task(task, output)
        if task:
            output["task"] = task
        await self._record_run(instruction, output)
        return output

    async def _results(self, plan: list[JsonMap], allow_write: bool) -> list[JsonMap]:
        return [{"step": step, "result": await self._safe_step(step, allow_write)} for step in plan]

    async def _safe_step(self, step: JsonMap, allow_write: bool) -> object:
        try:
            return await self._run_step(step, allow_write)
        except Exception as exc:
            return {"error": f"{type(exc).__name__}: {exc}", "action": str(step.get("action", "unknown"))}

    async def _start_task(self, instruction: str, plan: list[JsonMap], allow_write: bool) -> JsonMap | None:
        if not self.tasks:
            return None
        task = await self.tasks.create(instruction, plan, allow_write)
        await self._record_task(task)
        return await self._transition(task, "running")

    async def _finish_task(self, task: JsonMap | None, output: JsonMap) -> JsonMap | None:
        if not task:
            return None
        progress = output["visible_progress"] if isinstance(output.get("visible_progress"), dict) else {}
        status = _task_status(progress)
        task = await self._transition(task, status, progress)
        return await self._transition(task, "completed", progress) if status == "verified" else task

    async def _transition(self, task: JsonMap, status: str, progress: JsonMap | None = None) -> JsonMap:
        if not self.tasks:
            return task
        updated = await self.tasks.transition(str(task["id"]), status, progress)
        if not updated:
            return task
        await self._record_task(updated)
        return updated

    async def _record_task(self, task: JsonMap) -> None:
        if self.history:
            data = {key: task.get(key, "") for key in ("id", "status", "instruction", "updated_at")}
            await self.history.append("task_state", data)

    async def _record_run(self, instruction: str, output: JsonMap) -> None:
        if self.history:
            event = await self.history.append("agent_run", {"instruction": instruction, "progress": output["visible_progress"]})
            output["history_id"] = event.get("id", "")
        if self.shared_context:
            self.shared_context.add("agent", self._summary(instruction, output))

    async def _plan(self, instruction: str) -> list[JsonMap]:
        direct = direct_plan(instruction)
        if direct:
            return direct
        prompt = f"Allowed actions: {list(ACTIONS)}. Return JSON array only. User: {instruction}"
        try:
            response = await self.llm.generate_response([{"role": "user", "content": prompt}])
        except Exception:
            return _scope_step(instruction)
        plan = parse_plan(response)
        return plan if _accepts_plan(instruction, plan) else _scope_step(instruction)

    async def _run_step(self, step: JsonMap, allow_write: bool) -> object:
        action, params = str(step.get("action")), step.get("params", {})
        params = params if isinstance(params, dict) else {}
        if action == "improve_code":
            params["allow_write"] = allow_write
        return await self._execute_step(action, self._normalize_params(action, params), allow_write)

    async def _execute_step(self, action: str, params: JsonMap, allow_write: bool) -> object:
        if action in EXPLAINERS:
            return EXPLAINERS[action](**params)
        if action == "self_evolve_once":
            return await controlled_self_evolution(self.code_agent, allow_write, int(params.get("max_files", 1)))
        if action == "self_program_once":
            return await self_program_once(self.code_agent, allow_write, str(params.get("instruction", "")), int(params.get("max_files", 1)))
        if action not in self.registry:
            return {"error": f"Unknown action: {action}"}
        return await self.registry[action](**params)

    def _normalize_params(self, action: str, params: JsonMap) -> JsonMap:
        if action not in {"read_file", "improve_code"} or "path" in params:
            return params
        for alias in ("file_path", "filepath", "file"):
            if alias in params:
                params["path"] = params.pop(alias)
        return params

    def _summary(self, instruction: str, output: JsonMap) -> str:
        return f"\u4efb\u52a1\uff1a{instruction}\n\u7ed3\u679c\uff1a{str(output)[:800]}"

    async def _analyze_code(self) -> JsonMap:
        return self.code_agent.analyze_project()

    async def _review_code(self, max_files: int = 5) -> JsonMap:
        return await self.code_agent.review_project(max_files=max_files)

    async def _improve_code(self, path: str | None = None, allow_write: bool = False, max_files: int = 1) -> JsonMap:
        if path:
            return await self.code_agent.improve(path, allow_write=allow_write)
        items = await self.code_agent._run_self_improvement_cycle(allow_write=allow_write, max_files=max_files)
        return {"items": items}

    async def _read_file(self, path: str) -> JsonMap:
        return self.code_agent.read_file(path)

    async def _run_tests(self) -> JsonMap:
        return self.code_agent.validate_project()

    async def _run_quality_commands(self) -> JsonMap:
        return await run_quality_commands()

    async def _web_search(self, query: str) -> JsonMap:
        if not self.web_search:
            return {"reply": "联网检索未启用，当前不会假装已经联网。", "query": query, "passed": False}
        try:
            results = await self.web_search.search(query)
        except Exception as exc:
            return {"reply": f"联网检索失败：{exc}。", "query": query, "error": str(exc), "passed": False}
        return {"reply": _web_reply(results), "query": query, "results": results, "passed": True}

    async def _run_python_heart(self) -> JsonMap:
        return heart_reply(await self.python_runner.run_heart())


def _output(plan: list[JsonMap], results: list[JsonMap], allow_write: bool) -> JsonMap:
    output: JsonMap = {"plan": plan, "results": results, "allow_write": allow_write}
    output["visible_progress"] = summarize_agent_progress(plan, results, allow_write)
    return output


def _task_status(progress: JsonMap) -> str:
    if bool(progress.get("passed")):
        return "verified"
    steps = progress.get("steps", [])
    failed = any(isinstance(step, dict) and step.get("status") == "failed" for step in steps) if isinstance(steps, list) else False
    return "failed" if failed else "needs_attention"


def _accepts_plan(instruction: str, plan: list[JsonMap]) -> bool:
    if not plan:
        return False
    if len(plan) != 1 or plan[0].get("action") != "analyze_code":
        return True
    return any(word in instruction.lower() for word in ("代码", "项目", "文件", "测试", "检查", "审查", "分析"))


def _scope_step(instruction: str) -> list[JsonMap]:
    return [{"id": "clarify", "action": "explain_agent_scope", "params": {"instruction": instruction}}]


def _web_reply(results: list[JsonMap]) -> str:
    return "已联网检索，但没有找到结果。" if not results else "已联网检索：\n" + format_search_context(results)
