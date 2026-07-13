from .ports import JsonMap

MILESTONES: list[JsonMap] = [
    {"name": "受控自编程", "proof": "能生成修改预案、执行质量命令、失败回滚"},
    {"name": "日常对话去模板化", "proof": "拌面对话不再复读套话，能接住具体生活细节"},
    {"name": "AI 与雨城共生", "proof": "AI 每次推进都会映射一个雨城产出方向"},
    {"name": "下一步推进器", "proof": "不知道怎么推时，返回每日推进回路"},
    {"name": "AI 核心推进入口", "proof": "核心被拆成理解、记忆、决策、表达四层"},
    {"name": "智能体执行进度", "proof": "每轮智能体结果会附带可读进度摘要"},
    {"name": "南京私人记忆", "proof": "公开语境与本机私人事实分层，明确问题可从原话准确召回"},
    {"name": "可管理私人记忆", "proof": "原生界面可查看、新增、修正和删除，变更立即进入本机审计"},
    {"name": "AI 自行调用智能体", "proof": "普通对话可自动委派检查、测试和代码预案，写入仍需明确授权"},
    {"name": "统一活动历史", "proof": "智能体执行与记忆变更可持久化查询，重启后仍保留"},
    {"name": "Workspace 实时同步", "proof": "本机 Markdown 在下一轮请求动态重载，不复制进仓库，也不默认发送给远程模型"},
]

CURRENT = {
    "stage": "AI 核心第三轮：行动",
    "focus": "让私人 workspace 与 AI 动态同步，同时保持本机边界、权限与可追溯性",
    "next": "把意图路由升级为结构化工具选择与任务状态机，并用真实任务评测能力",
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
