from pathlib import Path
from shutil import copy

from .agent import CodeAgent
from .command_runner import run_quality_commands
from .game_coupling import game_progress_from_ai
from .ports import JsonMap


async def self_program_once(agent: CodeAgent, allow_write: bool, instruction: str, max_files: int = 1, goal: str = "", target_path: str = "", patch_mode: bool = False) -> JsonMap:
    before = agent.validate_project()
    baseline_commands = await run_quality_commands()
    target = _target(agent.analyze_project(), max_files, target_path)
    items = await _program(agent, target, allow_write, goal, patch_mode)
    after = agent.validate_project()
    commands = await run_quality_commands()
    rolled_back = _rollback_if_needed(agent, allow_write, bool(baseline_commands["passed"]), bool(commands["passed"]), items)
    if rolled_back:
        after = agent.validate_project()
        commands = await run_quality_commands()
    return _payload(instruction, allow_write, before, baseline_commands, target, items, after, commands, rolled_back)


def _payload(
    instruction: str, allow_write: bool, before: JsonMap, baseline: JsonMap, target: list[JsonMap],
    items: list[JsonMap], after: JsonMap, commands: JsonMap, rolled_back: list[str],
) -> JsonMap:
    data = {"mode": "controlled_self_programming", "reply": _reply(allow_write, target, after, commands, rolled_back), "instruction": instruction, "before": before, "baseline_commands": baseline, "target": target, "items": items, "after": after, "commands": commands, "rolled_back": rolled_back, "guards": _guards()}
    data["game_project"] = game_progress_from_ai(instruction, {"target": target, "commands": commands})
    return data


def _target(analysis: JsonMap, max_files: int, target_path: str = "") -> list[JsonMap]:
    if target_path:
        return [{"path": target_path}]
    files = analysis.get("largest_files", [])
    if not isinstance(files, list):
        return []
    return [item for item in files[: max(1, max_files)] if isinstance(item, dict)]


async def _program(agent: CodeAgent, target: list[JsonMap], allow_write: bool, goal: str, patch_mode: bool) -> list[JsonMap]:
    items: list[JsonMap] = []
    for item in target:
        path = item.get("path")
        if not isinstance(path, str):
            continue
        try:
            items.append(await agent.improve(path, allow_write=allow_write, verify_commands=False, goal=goal, patch_mode=patch_mode))
        except Exception as exc:
            items.append({"path": path, "changed": False, "error": str(exc)})
    return items


def _rollback_if_needed(agent: CodeAgent, allow_write: bool, baseline_ok: bool, command_ok: bool, items: list[JsonMap]) -> list[str]:
    if not allow_write or not baseline_ok or command_ok:
        return []
    restored: list[str] = []
    for item in items:
        if item.get("changed") is not True or not isinstance(item.get("backup"), str):
            continue
        path = str(item.get("path", ""))
        copy(Path(str(item["backup"])), agent.tree.safe_path(path))
        restored.append(path)
    return restored


def _reply(allow_write: bool, target: list[JsonMap], after: JsonMap, commands: JsonMap, rolled_back: list[str]) -> str:
    names = ", ".join(str(item.get("path", "")) for item in target) or "\u672a\u9009\u5b9a\u6587\u4ef6"
    if rolled_back:
        state = "\u5199\u5165\u540e\u547d\u4ee4\u5931\u8d25\uff0c\u5df2\u56de\u6eda"
    elif allow_write and bool(after.get("passed")) and bool(commands.get("passed")):
        state = "\u5df2\u5199\u5165\u3001\u5df2\u6267\u884c\u547d\u4ee4\u3001\u9a8c\u8bc1\u901a\u8fc7"
    else:
        state = "\u5df2\u751f\u6210\u9884\u6848\u5e76\u6267\u884c\u547d\u4ee4\uff0c\u672a\u5199\u5165"
    verdict = "\u901a\u8fc7" if after.get("passed") and commands.get("passed") else "\u5931\u8d25"
    return f"\u53d7\u63a7\u81ea\u7f16\u7a0b\u5b8c\u6210\uff1a{state}\u3002\u76ee\u6807\uff1a{names}\u3002\u7efc\u5408\u9a8c\u8bc1\uff1a{verdict}\u3002"


def _guards() -> list[str]:
    return [
        "\u9879\u76ee\u76ee\u5f55\u9650\u5236",
        "\u9ed8\u8ba4 dry-run",
        "\u663e\u5f0f allow_write",
        "\u5199\u5165\u540e\u6267\u884c\u767d\u540d\u5355\u547d\u4ee4",
        "\u57fa\u7ebf\u901a\u8fc7\u4f46\u5199\u5165\u540e\u5931\u8d25\u5219\u56de\u6eda",
    ]
