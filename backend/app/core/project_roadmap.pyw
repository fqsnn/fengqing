from .game_coupling import game_progress_from_ai
from .ports import JsonMap


def next_push_reply() -> JsonMap:
    data = {"mode": "next_push_roadmap", "reply": _reply(), "now": _now(), "tracks": _tracks(), "first_move": _first_move()}
    data["game_project"] = game_progress_from_ai("下一步推进 AI 本身", {"first_move": data["first_move"]})
    return data


def _reply() -> str:
    return "现在不要再堆概念了。下一步是把它做成每日会推进的系统：先稳住 AI 核心，再让雨城同步产出，再升级模型和工具。"


def _now() -> str:
    return "第一优先级：做任务推进器，让 AI 每轮都能给出一个可验证的小步，而不是只回答愿景。"


def _first_move() -> JsonMap:
    return {"name": "每日推进回路", "output": "下一步任务、验证命令、雨城映射、完成记录"}


def _tracks() -> list[JsonMap]:
    return [
        {"name": "AI 核心", "goal": "更自然地理解用户、记忆目标、选择下一步"},
        {"name": "智能体", "goal": "受控改代码、跑命令、记录结果、失败回滚"},
        {"name": "雨城", "goal": "把每次 AI 能力变化映射成场景、交互或机制"},
        {"name": "模型与工具", "goal": "保持本地可用，同时逐步接入更强模型和联网工具"},
    ]
