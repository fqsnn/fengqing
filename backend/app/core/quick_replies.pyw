from .agent_replies import EXPLAINERS
from .planner import direct_plan
from .ports import PythonExampleRunnerPort
from .python_examples import heart_reply


async def quick_reply(instruction: str, python_runner: PythonExampleRunnerPort) -> str | None:
    plan = direct_plan(instruction)
    if len(plan) != 1:
        return None
    action = str(plan[0].get("action", ""))
    if action == "generate_python_heart":
        return str(heart_reply(await python_runner.run_heart())["reply"])
    params = plan[0].get("params", {})
    if action not in EXPLAINERS or not isinstance(params, dict):
        return None
    result = EXPLAINERS[action](**params)
    reply = result.get("reply")
    return reply if isinstance(reply, str) else None
