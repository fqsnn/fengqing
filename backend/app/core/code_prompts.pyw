from pathlib import Path

REVIEW_RULES = (
    "你是代码审查智能体。请指出下面文件中最值得精简、修复或验证的地方。",
    "要求：",
    "- 不要输出完整代码。",
    "- 优先指出高价值问题。",
    "- 保留现有功能。",
    "- 如果没有明显问题，就明确说没有发现高风险问题。",
)

IMPROVE_RULES = (
    "你是代码优化智能体。请在不丢失功能的前提下精简下面代码。",
    "要求：",
    "- 只输出优化后的完整代码。",
    "- 不要解释。",
    "- 不要删除公共接口。",
    "- 不要引入无关依赖。",
)


def review_prompt(path: str, content: str) -> str:
    return "\n".join((*REVIEW_RULES, f"文件：{path}", "", f"代码：\n{content}"))


def improve_prompt(path: str, content: str) -> str:
    return "\n".join((*IMPROVE_RULES, f"文件：{path}", "", f"代码：\n{content}"))


def extract_code(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped + "\n"
    return "\n".join(_strip_fence(stripped.splitlines())).strip() + "\n"


def static_review(text: str, error: Exception) -> str:
    issues = _static_issues(text, error)
    if len(issues) == 1:
        issues.append("静态检查未发现明显高风险冗余。")
    return "\n".join(f"- {item}" for item in issues)


def file_stats(path: Path, root: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    return {"path": str(path.relative_to(root)), "lines": text.count("\n") + 1, "chars": len(text)}


def _strip_fence(lines: list[str]) -> list[str]:
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return lines


def _static_issues(text: str, error: Exception) -> list[str]:
    issues = [f"LLM 不可用，已改用静态检查：{error}"]
    checks = (
        ("except:" in text, "发现裸 except，建议改成明确异常类型。"),
        ("print(" in text, "发现 print 调试输出，服务代码里建议改用 logging。"),
        (_looks_like_local_path(text), "发现硬编码项目路径，建议改为项目根目录或环境变量。"),
        ("json.loads" in text and "JSONDecodeError" not in text, "发现 JSON 解析，建议补容错解析。"),
        (text.count("\n") > 180, "文件偏长，建议按职责逐步拆小。"),
    )
    issues.extend(message for failed, message in checks if failed)
    return issues


def _looks_like_local_path(text: str) -> bool:
    return "myapp" in text and (":/" in text or ":\\" in text)
