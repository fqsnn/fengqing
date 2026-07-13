from .ports import JsonMap

DUAL_LOOP_SYSTEM = (
    "工作必须同时包含正向与逆向：正向负责理解目标、生成答案和行动方案；"
    "逆向负责挑错、找矛盾、查边界、验证证据和安全性。"
    "最终回复必须吸收逆向检查结果，不隐藏失败，不假装确定。"
)
WEB_HINT_WORDS = ("联网查", "联网搜索", "搜索", "查一下", "查一查", "最新", "今天", "新闻", "价格", "天气", "现任", "官网")


def needs_web_search(text: str) -> bool:
    lowered = text.lower()
    return any(word.lower() in lowered for word in WEB_HINT_WORDS)


def format_search_context(results: list[JsonMap]) -> str:
    if not results:
        return ""
    rows = [_format_row(index, item) for index, item in enumerate(results, 1)]
    return "联网检索证据：\n" + "\n".join(rows)


def _format_row(index: int, item: JsonMap) -> str:
    title, url = str(item.get("title", "")), str(item.get("url", ""))
    snippet = str(item.get("snippet", ""))
    return f"{index}. {title}\n   {url}\n   {snippet}".strip()
