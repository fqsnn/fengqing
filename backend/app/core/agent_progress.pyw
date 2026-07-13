from .ports import JsonMap


def summarize_agent_progress(plan: list[JsonMap], results: list[JsonMap], allow_write: bool) -> JsonMap:
    steps = [_step(item) for item in results]
    passed = _passed(results)
    temporary_visual = _temporary_visual(plan)
    return {
        "mode": "agent_execution_progress",
        "summary": _summary(steps, passed, allow_write, temporary_visual),
        "steps": steps,
        "passed": passed,
        "next": _next(passed, allow_write, temporary_visual),
    }


def _step(item: JsonMap) -> JsonMap:
    step = item.get("step", {})
    result = item.get("result", {})
    action = step.get("action", "unknown") if isinstance(step, dict) else "unknown"
    return {"action": action, "status": _status(result), "evidence": _evidence(result)}


def _status(result: object) -> str:
    if not isinstance(result, dict):
        return "done"
    if "error" in result:
        return "failed"
    if result.get("passed") is False or result.get("rolled_back"):
        return "needs_attention"
    return "passed" if result.get("passed") is True or result.get("reply") else "done"


def _evidence(result: object) -> str:
    if not isinstance(result, dict):
        return str(result)[:120]
    if result.get("reply"):
        return str(result["reply"])[:180]
    if isinstance(result.get("commands"), list):
        return f"{len(result['commands'])} commands"
    return str({k: result[k] for k in list(result)[:3]})[:180]


def _passed(results: list[JsonMap]) -> bool:
    return all(_status(item.get("result", {})) not in {"failed", "needs_attention"} for item in results)


def _temporary_visual(plan: list[JsonMap]) -> bool:
    return len(plan) == 1 and plan[0].get("action") == "generate_python_heart"


def _summary(steps: list[JsonMap], passed: bool, allow_write: bool, temporary_visual: bool) -> str:
    write = "临时运行，不写入项目" if temporary_visual else ("允许写入" if allow_write else "未写入")
    return f"本轮智能体执行 {len(steps)} 步，状态：{'通过' if passed else '需要处理'}，模式：{write}。"


def _next(passed: bool, allow_write: bool, temporary_visual: bool) -> str:
    if not passed:
        return "先处理失败步骤，再继续推进。"
    if temporary_visual:
        return "图像已在本地生成，项目源码未被修改。"
    return "下一步可以授权写入，或选择更小目标继续推进。" if not allow_write else "写入后继续观察验证结果。"
