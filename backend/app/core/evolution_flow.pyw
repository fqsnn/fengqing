from .agent import CodeAgent
from .ports import JsonMap
from .self_programming import self_program_once


async def controlled_self_evolution(agent: CodeAgent, allow_write: bool, max_files: int) -> JsonMap:
    analysis = agent.analyze_project()
    return await _write(agent, analysis, max_files) if allow_write else await _preview(agent, analysis, max_files)


async def _write(agent: CodeAgent, analysis: JsonMap, max_files: int) -> JsonMap:
    result = await self_program_once(agent, True, "受控自我进化", max_files)
    result["mode"] = "controlled_self_evolution"
    result["phases"] = _phases(analysis, result["before"], result["after"])
    return result


async def _preview(agent: CodeAgent, analysis: JsonMap, max_files: int) -> JsonMap:
    before = agent.validate_project()
    items = await agent._run_self_improvement_cycle(allow_write=False, max_files=max_files)
    after = agent.validate_project()
    return _payload(analysis, before, items, after)


def _payload(analysis: JsonMap, before: JsonMap, items: list[dict[str, object]], after: JsonMap) -> JsonMap:
    return {"mode": "controlled_self_evolution", "reply": _reply(False, items, after), "phases": _phases(analysis, before, after), "before": before, "items": items, "after": after}


def _reply(allow_write: bool, items: list[dict[str, object]], after: JsonMap) -> str:
    target = str(items[0].get("path", "未选定目标")) if items else "未选定目标"
    state = "已写入并验证" if allow_write and bool(after.get("passed")) else "已生成预案，未写入"
    verdict = "通过" if after.get("passed") else "失败"
    return f"受控自我进化完成：{state}。目标：{target}。验证：{verdict}。"


def _phases(analysis: JsonMap, before: JsonMap, after: JsonMap) -> list[JsonMap]:
    return [
        {"role": "实", "work": "扫描项目并验证当前代码", "result": before},
        {"role": "虚", "work": "生成一个最小修改预案", "result": {"file_count": analysis.get("file_count", 0)}},
        {"role": "间", "work": "复验结果并决定保留或回滚", "result": after},
    ]
