from .ports import JsonMap

MILESTONES: list[JsonMap] = [
    {"name": "受控自编程", "proof": "能生成修改预案、执行质量命令、失败回滚"},
    {"name": "日常对话去模板化", "proof": "拌面对话不再复读套话，能接住具体生活细节"},
    {"name": "AI 与雨城共生", "proof": "AI 每次推进都会映射一个雨城产出方向"},
    {"name": "下一步推进器", "proof": "不知道怎么推时，返回每日推进回路"},
    {"name": "AI 核心推进入口", "proof": "核心被拆成理解、记忆、决策、表达四层"},
    {"name": "智能体执行进度", "proof": "每轮智能体结果会附带可读进度摘要"},
]

CURRENT = {
    "stage": "AI 核心第一轮",
    "focus": "让推进变得可见：状态、证据、下一步都能被用户看到",
    "next": "把真实执行进度沉淀成可查询历史记录",
}


def progress_snapshot() -> JsonMap:
    return {"mode": "visible_progress", "current": CURRENT, "milestones": MILESTONES, "reply": progress_text()}


def progress_reply() -> JsonMap:
    data = progress_snapshot()
    data["answer"] = "推进现在不只藏在代码里：状态、证据、下一步都会被显示出来。"
    return data


def progress_text() -> str:
    names = "、".join(str(item["name"]) for item in MILESTONES[-3:])
    return f"当前阶段：{CURRENT['stage']}。最近可见推进：{names}。下一步：{CURRENT['next']}。"
