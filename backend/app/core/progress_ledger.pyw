from .ports import JsonMap

MILESTONES: list[JsonMap] = [
    {"name": "受控自编程", "proof": "能生成修改预案、执行质量命令、失败回滚"},
    {"name": "日常对话去模板化", "proof": "拌面对话不再复读套话，能接住具体生活细节"},
    {"name": "AI 与雨城共生", "proof": "AI 每次推进都会映射一个雨城产出方向"},
    {"name": "下一步推进器", "proof": "不知道怎么推时，返回每日推进回路"},
    {"name": "AI 核心推进入口", "proof": "核心被拆成理解、记忆、决策、表达四层"},
]

CURRENT = {
    "stage": "AI 核心第一轮",
    "focus": "让推进变得可见：状态、证据、下一步都能被用户看到",
    "next": "把每次智能体执行结果显示成可读进度，而不是只显示一句回答",
}


def progress_snapshot() -> JsonMap:
    return {"mode": "visible_progress", "current": CURRENT, "milestones": MILESTONES, "reply": progress_text()}


def progress_reply() -> JsonMap:
    data = progress_snapshot()
    data["answer"] = "你感觉不到推进，是因为系统没有把推进显性化。现在要把进度变成界面和接口里能看见的东西。"
    return data


def progress_text() -> str:
    names = "、".join(str(item["name"]) for item in MILESTONES[-3:])
    return f"当前阶段：{CURRENT['stage']}。最近可见推进：{names}。下一步：{CURRENT['next']}。"
