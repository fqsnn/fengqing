from .game_coupling import game_progress_from_ai
from .ports import JsonMap


def ai_core_push_reply() -> JsonMap:
    data = {"mode": "ai_core_concrete_push", "reply": _reply(), "layers": _layers(), "first_sprint": _first_sprint(), "acceptance": _acceptance()}
    data["game_project"] = game_progress_from_ai("推进 AI 核心", {"first_sprint": data["first_sprint"]})
    return data


def _reply() -> str:
    return "具体推进 AI 核心，先做四层：理解层、记忆层、决策层、表达层。第一轮不要贪大，先把“听懂你要什么”做稳。"


def _layers() -> list[JsonMap]:
    return [
        {"name": "理解层", "target": "识别用户真实意图、在意点和当前任务", "files": ["conversation_style.pyw", "planner.pyw"]},
        {"name": "记忆层", "target": "把长期有用的话写入上下文，并区分公开/私人", "files": ["context markdown", "private workspace notes"]},
        {"name": "决策层", "target": "决定回答、联网、智能体、自编程或雨城映射", "files": ["services.pyw", "orchestrator.pyw"]},
        {"name": "表达层", "target": "减少模板句，先接住人，再推进事", "files": ["conversation_style.pyw"]},
    ]


def _first_sprint() -> JsonMap:
    return {
        "name": "核心第一轮：理解层加固",
        "change": "新增 AI 核心推进入口，并把下一步固定为可验证的小任务",
        "verify": ["quality_gate", "compile_all", "smoke_test", "HTTP agent intent test"],
    }


def _acceptance() -> list[str]:
    return [
        "用户问“AI 核心怎么推”时，不再泛泛鼓励，而是给具体层级和文件",
        "每次核心推进都必须附带验证方式",
        "每次核心推进都必须同步给雨城一个映射产出",
    ]
