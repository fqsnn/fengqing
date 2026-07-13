from .ports import JsonMap

READ_WORDS = ("检查代码", "审查代码", "分析代码", "分析项目", "检查项目", "运行测试", "跑测试", "质量门", "跑检查", "读文件")
WRITE_WORDS = ("修改代码", "修复代码", "优化代码", "实现功能", "写代码", "推进ai项目", "推进 ai 项目", "自己改自己", "自己编程自己")


def agent_intent(text: str) -> str | None:
    lowered = text.lower()
    if any(word in lowered for word in WRITE_WORDS):
        return "write"
    return "read" if any(word in lowered for word in READ_WORDS) else None


def delegated_instruction(text: str, intent: str) -> str:
    if intent != "write" or "自己编程自己" in text:
        return text
    return f"自己编程自己：{text}"


def delegated_reply(result: JsonMap, allow_write: bool) -> str:
    visible = result.get("visible_progress", {})
    if not isinstance(visible, dict):
        return "我已调用智能体，但它没有返回可读进度。"
    permission = "已获写入权限" if allow_write else "只读或预案模式"
    summary = str(visible.get("summary", "智能体已执行。"))
    next_step = str(visible.get("next", ""))
    return f"我已自行调用智能体（{permission}）。{summary}\n下一步：{next_step}"
