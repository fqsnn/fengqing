from .agent_replies import EXPLAINERS
from .planner import direct_plan


def quick_reply(instruction: str) -> str | None:
    plan = direct_plan(instruction)
    if len(plan) != 1:
        return None
    action = str(plan[0].get("action", ""))
    params = plan[0].get("params", {})
    if action not in EXPLAINERS or not isinstance(params, dict):
        return None
    result = EXPLAINERS[action](**params)
    reply = result.get("reply")
    return reply if isinstance(reply, str) else None
