from .ports import JsonMap


def game_progress_from_ai(instruction: str, ai_result: JsonMap) -> JsonMap:
    theme = _theme(instruction)
    return {
        "mode": "ai_game_coevolution",
        "reply": _reply(theme),
        "principle": "\u63a8\u8fdb AI \u672c\u8eab\u65f6\uff0c\u5fc5\u987b\u540c\u6b65\u4ea7\u51fa\u4e00\u4e2a\u300a\u7a97\u8fb9\u7684\u96e8\u57ce\u300b\u4e0b\u4e00\u6b65\u3002",
        "theme": theme,
        "source": ai_result,
        "next_steps": _steps(theme),
    }


def game_coupling_reply() -> JsonMap:
    result = game_progress_from_ai("\u63a8\u8fdb AI \u672c\u8eab\uff0c\u987a\u5e26\u63a8\u8fdb\u6e38\u620f\u9879\u76ee", {})
    result["reply"] = "\u5bf9\uff0c\u8fd9\u8981\u505a\u6210\u4e00\u4e2a\u5171\u751f\u5faa\u73af\uff1aAI \u6bcf\u53d8\u5f3a\u4e00\u6b65\uff0c\u96e8\u57ce\u4e5f\u8981\u524d\u8fdb\u4e00\u6b65\u3002"
    return result


def _theme(instruction: str) -> str:
    if "核心" in instruction:
        return "AI 核心"
    if "\u5728\u610f" in instruction:
        return "\u5728\u610f\u672c\u8eab"
    if "\u4ee3\u7801" in instruction or "\u7f16\u7a0b" in instruction:
        return "\u81ea\u7f16\u7a0b"
    return "\u5171\u751f\u63a8\u8fdb"


def _reply(theme: str) -> str:
    return f"\u5df2\u628a\u8fd9\u6b21 AI \u63a8\u8fdb\u6620\u5c04\u5230\u96e8\u57ce\uff1a{theme}\u3002"


def _steps(theme: str) -> list[str]:
    return [
        f"\u628a\u201c{theme}\u201d\u53d8\u6210\u96e8\u57ce\u7684\u4e00\u4e2a\u53ef\u73a9\u4e92\u52a8\u5355\u5143",
        "\u8bb0\u5f55\u5b83\u5bf9 AI \u6027\u683c\u3001UI \u548c\u667a\u80fd\u4f53\u884c\u4e3a\u7684\u5f71\u54cd",
        "\u4e0b\u4e00\u8f6e\u81ea\u7f16\u7a0b\u65f6\u68c0\u67e5\u8fd9\u4e2a\u6e38\u620f\u5355\u5143\u662f\u5426\u6709\u4ee3\u7801\u843d\u70b9",
    ]
