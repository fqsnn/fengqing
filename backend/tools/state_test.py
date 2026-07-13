import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image

from app.core.agent import _apply_patch
from app.core.agent_gateway import agent_intent, delegated_instruction
from app.core.agent_progress import summarize_agent_progress
from app.core.orchestrator import _accepts_plan, _web_reply
from app.core.planner import direct_plan
from app.core.dual_loop import needs_web_search
from app.core.python_examples import heart_reply
from app.core.quick_replies import quick_reply
from app.infrastructure.activity_history import JsonlActivityHistory
from app.infrastructure.private_memory import MarkdownContextRecall, MarkdownMemoryAdmin
from app.infrastructure.python_example_runner import LocalPythonExampleRunner
from app.infrastructure.runtime_probe import ollama_status_from_payload
from app.infrastructure.task_ledger import JsonlTaskLedger


async def _create_memory(admin: MarkdownMemoryAdmin, recall: MarkdownContextRecall) -> dict[str, object] | None:
    created = await admin.add("我喜欢南京的一号线，\n因为它是蓝色的。")
    normalized = created.get("text") == "我喜欢南京的一号线， 因为它是蓝色的。"
    recalled = "蓝色" in str(recall.recall("我为什么喜欢南京一号线？"))
    return created if created.get("created") and normalized and recalled else None


async def _rejects_blank(admin: MarkdownMemoryAdmin, memory_id: str) -> bool:
    try:
        await admin.update(memory_id, " \n ")
    except ValueError:
        return True
    return False


async def _task_lifecycle(root: Path) -> bool:
    path = root / "tasks.jsonl"
    ledger = JsonlTaskLedger(path)
    task = await ledger.create("检查项目", [{"id": "check", "action": "run_tests", "params": {}}], False)
    try:
        await ledger.transition(str(task["id"]), "completed")
        return False
    except ValueError:
        pass
    running = await ledger.transition(str(task["id"]), "running")
    verified = await ledger.transition(str(task["id"]), "verified", {"passed": True})
    completed = await ledger.transition(str(task["id"]), "completed", {"passed": True})
    loaded = await JsonlTaskLedger(path).list_tasks()
    states = completed.get("states", []) if completed else []
    return bool(running and verified and completed and loaded) and completed.get("status") == "completed" and len(states) == 4


async def _task_failure(root: Path) -> bool:
    ledger = JsonlTaskLedger(root / "failed-tasks.jsonl")
    task = await ledger.create("失败任务", [], False)
    running = await ledger.transition(str(task["id"]), "running")
    failed = await ledger.transition(str(task["id"]), "failed", {"error": "test"})
    try:
        await ledger.transition(str(task["id"]), "running")
        return False
    except ValueError:
        return bool(running and failed) and failed.get("status") == "failed"


async def _code_example_route(runner: LocalPythonExampleRunner) -> bool:
    plan = direct_plan("写一个爱心代码")
    reply = await quick_reply("写一段 Python 爱心代码", runner) or ""
    payload = heart_reply(await runner.run_heart())
    execution = payload.get("execution", {})
    artifact = Path(str(execution.get("artifact_path", ""))) if isinstance(execution, dict) else Path()
    with Image.open(artifact) as image:
        visual = image.format == "PNG" and image.size == (360, 360)
    return bool(plan) and plan[0]["action"] == "generate_python_heart" and "本机 Python" in reply and visual and payload.get("writes_project") is False


def _project_push_route() -> bool:
    plan = direct_plan("继续推进你自己的项目")
    return bool(plan) and plan[0]["action"] == "self_program_once" and agent_intent("继续推进你自己的项目") == "write"


def _web_route() -> bool:
    plan = direct_plan("联网搜索南京天气")
    reply = _web_reply([{"title": "天气", "url": "example.test", "snippet": "晴"}])
    return bool(plan) and plan[0]["action"] == "web_search" and "example.test" in reply


def _resource_scheduler_route() -> bool:
    plan = direct_plan("实时调度资源分配")
    return bool(plan) and plan[0]["action"] == "explain_resource_scheduler" and not needs_web_search("实时调度资源分配")


def _empty_error_fails() -> bool:
    progress = summarize_agent_progress(
        [{"action": "test"}],
        [{"step": {"action": "test"}, "result": {"error": ""}}],
        False,
    )
    steps = progress.get("steps", [])
    return progress.get("passed") is False and isinstance(steps, list) and steps[0].get("status") == "failed"


def _visual_progress_is_honest() -> bool:
    plan = [{"action": "generate_python_heart"}]
    results = [{"step": plan[0], "result": {"passed": True, "reply": "image"}}]
    progress = summarize_agent_progress(plan, results, True)
    return "临时运行，不写入项目" in str(progress.get("summary")) and "项目源码未被修改" in str(progress.get("next"))


def _restored_write_needs_attention() -> bool:
    plan = [{"action": "improve_code"}]
    results = [{"step": plan[0], "result": {"restored": True, "reply": "恢复完成"}}]
    progress = summarize_agent_progress(plan, results, True)
    steps = progress.get("steps", [])
    return progress.get("passed") is False and isinstance(steps, list) and steps[0].get("status") == "needs_attention"


def _runtime_probe_states() -> bool:
    checked_at = "2026-07-13T00:00:00+00:00"
    ready = ollama_status_from_payload("qwen2.5:0.5b", {"models": [{"name": "qwen2.5:0.5b"}]}, checked_at)
    missing = ollama_status_from_payload("qwen2.5:7b", {"models": [{"name": "qwen2.5:0.5b"}]}, checked_at)
    invalid = ollama_status_from_payload("qwen2.5:0.5b", {}, checked_at)
    return ready.get("state") == "ready" and missing.get("state") == "model_missing" and missing.get("available_models") == ["qwen2.5:0.5b"] and invalid.get("state") == "invalid_response"


async def _ui_question_route(runner: LocalPythonExampleRunner) -> bool:
    plan = direct_plan("你可以改一下你自己的 UI 吗")
    reply = await quick_reply("你可以改一下你自己的 UI 吗", runner) or ""
    return bool(plan) and plan[0]["action"] == "explain_ui_change" and "不会擅自改界面" in reply


def _ui_self_optimization_route() -> bool:
    plan = direct_plan("自己优化自己的 UI 页面")
    return bool(plan) and plan[0]["action"] == "improve_ui" and plan[0]["params"].get("instruction") == "自己优化自己的 UI 页面"


def _unique_ui_patch_guard() -> bool:
    candidates = [("padx=22", 22)]
    changed = _apply_patch("box = Frame(root, padx=22)\n", '{"id":1,"value":24}', candidates) == "box = Frame(root, padx=24)\n"
    try:
        _apply_patch("box = Frame(root, padx=22)\n", '{"id":1,"value":22}', candidates)
    except ValueError:
        return changed
    return False


async def _ai_creation_route(runner: LocalPythonExampleRunner) -> bool:
    plan = direct_plan("你可以自己创造 AI 吗")
    reply = await quick_reply("你可以自己创造 AI 吗", runner) or ""
    fallback = [{"id": "analyze", "action": "analyze_code", "params": {}}]
    return bool(plan) and plan[0]["action"] == "explain_ai_creation" and "受控的本地 AI 系统" in reply and not _accepts_plan("你可以自己创造 AI 吗", fallback)


async def _computer_control_route(runner: LocalPythonExampleRunner) -> bool:
    plan = direct_plan("你可以自动操作电脑吗")
    reply = await quick_reply("你可以自动操作电脑吗", runner) or ""
    return bool(plan) and plan[0]["action"] == "explain_computer_control" and "不会暗中点击" in reply


async def _quick_routes() -> bool:
    with TemporaryDirectory() as artifact_dir:
        runner = LocalPythonExampleRunner(artifact_dir=Path(artifact_dir))
        checks = [await _code_example_route(runner), await _ui_question_route(runner), await _ai_creation_route(runner), await _computer_control_route(runner)]
        return all(checks)


def _workspace_sync(root: Path) -> bool:
    workspace = root / "workspace"
    note = workspace / "nested" / "balance.md"
    note.parent.mkdir(parents=True)
    note.write_text("# 均衡\n\n> 我要在均衡里该强的时候强，该弱的时候弱。\n", encoding="utf-8")
    recall = MarkdownContextRecall(root / "private", workspace)
    first = "该强的时候强" in recall.relevant("我想在均衡里怎样调整强弱？")
    note.write_text("# 均衡\n\n> 我要在均衡里该快的时候快，该慢的时候慢。\n", encoding="utf-8")
    second = recall.relevant("我想在均衡里该快还是该慢？")
    return first and "该快的时候快" in second and "该强的时候强" not in second


async def _exercise(root: Path) -> bool:
    history = JsonlActivityHistory(root / "activity.jsonl")
    folder = root / "private"
    admin = MarkdownMemoryAdmin(folder, history)
    recall = MarkdownContextRecall(folder)
    created = await _create_memory(admin, recall)
    if not created or not await _rejects_blank(admin, str(created["id"])):
        return False
    updated = await admin.update(str(created["id"]), "我喜欢南京的一号线，因为它是天空蓝。")
    if not updated or "天空蓝" not in str(recall.recall("我为什么喜欢南京一号线？")):
        return False
    deleted = await admin.delete(str(updated["id"]))
    events = await history.list_events(limit=10)
    return bool(deleted) and not await admin.list_facts() and [item["kind"] for item in events] == ["memory_deleted", "memory_updated", "memory_added"]


def _checks() -> bool:
    return all((
        asyncio.run(_quick_routes()), _project_push_route(), _web_route(), _resource_scheduler_route(), _empty_error_fails(),
        _visual_progress_is_honest(), _restored_write_needs_attention(), _runtime_probe_states(), _ui_self_optimization_route(), _unique_ui_patch_guard(),
        agent_intent("写一段 Python 爱心代码") is None, agent_intent("修改项目代码") == "write",
        agent_intent("请运行测试") == "read", delegated_instruction("继续推进AI项目", "write").startswith("自己编程自己"),
    ))


def main() -> int:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        local = asyncio.run(_exercise(root)) and asyncio.run(_task_lifecycle(root)) and asyncio.run(_task_failure(root)) and _workspace_sync(root)
    passed = local and _checks()
    print(f"state_test={'pass' if passed else 'fail'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
