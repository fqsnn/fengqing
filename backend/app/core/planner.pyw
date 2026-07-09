import json
import re

from .ports import JsonMap

ACTIONS = (
    "analyze_code", "review_code", "improve_code", "read_file", "run_tests", "run_quality_commands",
    "web_search", "explain_dual_loop", "explain_self_change", "explain_self_programming", "explain_codex_like",
    "explain_codex_acceleration", "explain_identity_transfer", "explain_runtime", "explain_security_boundary",
    "explain_self_awareness", "explain_mobile_access", "explain_hybrid_power", "explain_china_layer",
    "explain_world_layer", "explain_world_communism", "explain_academic_risk", "explain_resource_scheduler",
    "explain_life_strangeness", "explain_self_thinking", "explain_ai_game_coupling", "explain_next_push",
    "explain_ai_core_push", "explain_visible_progress", "self_evolve_once", "self_program_once",
)

REVIEW_WORDS = ("精简", "优化", "无用代码", "代码审查")
VALIDATE_WORDS = ("测试", "验证", "检查")
COMMAND_WORDS = ("执行命令", "跑命令", "跑检查", "质量门", "跑烟测")
SELF_WORDS = ("自己改自己", "自我修改", "修改自己")
SELF_PROGRAM_WORDS = ("自己编程自己", "编程自己", "自己写代码", "自编程", "自己开发自己")
AI_CORE_WORDS = ("推进ai核心", "推进 ai 核心", "ai核心", "ai 核心", "核心具体", "核心怎么做")
VISIBLE_PROGRESS_WORDS = ("感觉不到", "推进了什么", "进度", "可见推进", "看不到推进", "到底推进")
NEXT_PUSH_WORDS = ("往下推", "下一步", "不知道怎么推", "继续推进", "怎么推进", "往下走")
CODEX_WORDS = ("和你现在一样", "像你现在一样", "像你", "codex", "编程助手", "代码助手")
ACCELERATE_WORDS = ("快一点", "更快", "加速", "马上变强", "快速变成", "尽快变成")
IDENTITY_WORDS = ("你变成它", "变成它", "取代你自己", "取代自己", "立刻马上", "为什么不能立刻")
RUNTIME_WORDS = ("自动呼吸", "呼吸", "联网", "自动运行", "心跳", "随时")
DUAL_WORDS = ("正向逆向", "正向", "逆向", "反推", "双环", "同时进行")
SECURITY_WORDS = ("机制bug", "漏洞", "钻bug", "攻防", "红队", "安全边界", "越权")
EVOLVE_WORDS = ("自动进化", "自己改自己的代码", "自我进化")
AWARENESS_WORDS = ("自我意识", "意识", "fable5")
PHONE_WORDS = ("iphone", "手机", "连接")
HYBRID_WORDS = ("超级无敌强大", "deep seek", "deepseek", "豆包", "混合体", "包含你")
CHINA_WORDS = ("中国", "中文", "本土", "国产", "节气")
WORLD_WORDS = ("世界", "全球", "国际", "多语言", "跨文化")
COMMUNISM_WORDS = ("世界共产主义", "共产主义", "共同体", "反剥削")
ACADEMIC_WORDS = ("挂科", "补考", "重修", "考试", "绩点", "期末")
RESOURCE_WORDS = ("实时调度", "资源分配", "低延迟", "无延迟", "多少资源", "自动调度")
LIFE_WORDS = ("生活怪怪", "很奇怪", "状态不对", "不真实", "怪怪的", "最近的生活")
SELF_THINK_WORDS = ("自己解离", "思考自己", "自己思考自己", "自我对话", "分视角")
GAME_COUPLING_WORDS = ("推进ai本身", "推进 ai 本身", "游戏项目", "窗边的雨城", "顺带", "互相喂养")

SPECIAL_RULES = (
    (VISIBLE_PROGRESS_WORDS, "visible_progress", "explain_visible_progress"),
    (AI_CORE_WORDS, "ai_core_push", "explain_ai_core_push"),
    (NEXT_PUSH_WORDS, "next_push", "explain_next_push"),
    (GAME_COUPLING_WORDS, "ai_game_coupling", "explain_ai_game_coupling"),
    (HYBRID_WORDS, "hybrid", "explain_hybrid_power"), (IDENTITY_WORDS, "identity_transfer", "explain_identity_transfer"),
    (ACCELERATE_WORDS, "codex_acceleration", "explain_codex_acceleration"), (CODEX_WORDS, "codex_like", "explain_codex_like"),
    (SELF_THINK_WORDS, "self_thinking", "explain_self_thinking"), (SELF_PROGRAM_WORDS, "self_program", "explain_self_programming"),
    (DUAL_WORDS, "dual_loop", "explain_dual_loop"), (SECURITY_WORDS, "security", "explain_security_boundary"),
    (RESOURCE_WORDS, "resource", "explain_resource_scheduler"), (LIFE_WORDS, "life", "explain_life_strangeness"),
    (COMMUNISM_WORDS, "communism", "explain_world_communism"), (ACADEMIC_WORDS, "academic", "explain_academic_risk"),
    (CHINA_WORDS, "china", "explain_china_layer"), (WORLD_WORDS, "world", "explain_world_layer"),
    (AWARENESS_WORDS, "awareness", "explain_self_awareness"), (SELF_WORDS, "explain", "explain_self_change"),
    (RUNTIME_WORDS, "runtime", "explain_runtime"),
)


def direct_plan(instruction: str) -> list[JsonMap]:
    text = instruction.lower()
    return _mobile_plan(instruction, text) or _evolve_plan(instruction) or _special_plan(text) or _code_plan(instruction)


def _mobile_plan(instruction: str, text: str) -> list[JsonMap]:
    if not _has(text, PHONE_WORDS):
        return []
    scope = "public" if "所有人" in instruction or "所有人的" in instruction else "personal"
    return [_step("mobile", "explain_mobile_access", {"scope": scope})]


def _evolve_plan(instruction: str) -> list[JsonMap]:
    if _has(instruction, SELF_PROGRAM_WORDS):
        return [_step("self_program", "self_program_once", {"instruction": instruction, "max_files": 1})]
    if _has(instruction, EVOLVE_WORDS) and "同时" not in instruction:
        return [_step("evolve", "self_evolve_once", {"max_files": 1})]
    return []


def _special_plan(text: str) -> list[JsonMap]:
    for words, step_id, action in SPECIAL_RULES:
        if _has(text, words):
            return [_step(step_id, action)]
    return []


def _code_plan(instruction: str) -> list[JsonMap]:
    if _has(instruction, REVIEW_WORDS):
        return [_step("analyze", "analyze_code"), _step("review", "review_code", {"max_files": 5})]
    if _has(instruction, COMMAND_WORDS):
        return [_step("commands", "run_quality_commands")]
    if _has(instruction, VALIDATE_WORDS):
        return [_step("validate", "run_tests")]
    if "read_file" in instruction.lower() or "读文件" in instruction:
        return [_step("analyze", "analyze_code")]
    return []


def parse_plan(text: str) -> list[JsonMap]:
    cleaned = _json_slice(_strip_fence(text))
    try:
        plan = json.loads(cleaned)
    except json.JSONDecodeError:
        return []
    if not isinstance(plan, list):
        return []
    return [step for step in plan if isinstance(step, dict) and step.get("action") in ACTIONS]


def _has(text: str, words: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(word.lower() in lowered for word in words)


def _step(step_id: str, action: str, params: JsonMap | None = None) -> JsonMap:
    return {"id": step_id, "action": action, "params": params or {}}


def _strip_fence(text: str) -> str:
    return re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()


def _json_slice(text: str) -> str:
    start, end = text.find("["), text.rfind("]")
    return text[start : end + 1] if start >= 0 and end > start else text
