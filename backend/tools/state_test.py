import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from app.core.agent_gateway import agent_intent, delegated_instruction
from app.infrastructure.activity_history import JsonlActivityHistory
from app.infrastructure.private_memory import MarkdownContextRecall, MarkdownMemoryAdmin


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


def _workspace_sync(root: Path) -> bool:
    workspace = root / "workspace"
    workspace.mkdir()
    note = workspace / "balance.md"
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


def main() -> int:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        passed = asyncio.run(_exercise(root)) and _workspace_sync(root)
    passed = passed and agent_intent("请运行测试") == "read"
    passed = passed and delegated_instruction("继续推进AI项目", "write").startswith("自己编程自己")
    print(f"state_test={'pass' if passed else 'fail'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
