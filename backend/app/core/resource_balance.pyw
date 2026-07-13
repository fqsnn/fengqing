import os
from dataclasses import dataclass

from .ports import JsonMap

DEEP_MARKERS = ("深入", "完整", "系统性", "严谨", "架构", "推演", "方案", "对比", "分析", "代码审查")
QUESTION_MARKERS = ("？", "?", "为什么", "如何", "怎么", "是否", "能否", "能不能")
DEEP_OPERATIONS = frozenset(("web", "agent_read", "code_review"))
GUARDED_OPERATIONS = frozenset(("agent_write", "code_write", "publish", "external_write"))


@dataclass(frozen=True)
class ResourceProfile:
    name: str
    history_messages: int
    context_chars: int
    output_tokens: int
    reflection_tokens: int
    planner_tokens: int


@dataclass(frozen=True)
class BalanceSettings:
    focused_input_chars: int
    deep_input_chars: int
    code_chars_per_token: int
    code_min_tokens: int
    code_max_tokens: int
    profiles: dict[str, ResourceProfile]


@dataclass(frozen=True)
class ResourceDecision:
    profile: ResourceProfile
    operation: str
    reasons: tuple[str, ...]
    settings: BalanceSettings

    def event(self) -> JsonMap:
        return {
            "mode": self.profile.name,
            "operation": self.operation,
            "reasons": list(self.reasons),
            "history_messages": self.profile.history_messages,
            "context_chars_per_source": self.profile.context_chars,
            "output_tokens": self.profile.output_tokens,
            "reflection_tokens": self.profile.reflection_tokens,
            "planner_tokens": self.profile.planner_tokens,
        }

    def visible(self) -> JsonMap:
        return {"mode": self.profile.name, "reasons": list(self.reasons)}

    def code_output_tokens(self, source_chars: int) -> int:
        estimated = (max(0, source_chars) + self.settings.code_chars_per_token - 1) // self.settings.code_chars_per_token
        return min(max(estimated, self.settings.code_min_tokens), self.settings.code_max_tokens)


class ResourceBalance:
    def __init__(self, settings: BalanceSettings) -> None:
        self.settings = settings

    def decide(self, text: str, operation: str = "chat", allow_write: bool = False) -> ResourceDecision:
        mode, reasons = self._mode(text, operation, allow_write)
        return ResourceDecision(self.settings.profiles[mode], operation, reasons, self.settings)

    def _mode(self, text: str, operation: str, allow_write: bool) -> tuple[str, tuple[str, ...]]:
        if allow_write or operation in GUARDED_OPERATIONS:
            return "guarded", ("涉及写入或高影响操作",)
        if operation in DEEP_OPERATIONS:
            return "deep", ("需要工具、检索或代码审查",)
        if len(text) >= self.settings.deep_input_chars or _contains(text, DEEP_MARKERS):
            return "deep", ("请求复杂或要求深度推演",)
        if len(text) >= self.settings.focused_input_chars or _contains(text, QUESTION_MARKERS):
            return "focused", ("需要完整回答或明确判断",)
        return "light", ("请求短且可直接处理",)


def build_resource_balance() -> ResourceBalance:
    settings = _settings()
    _validate(settings)
    return ResourceBalance(settings)


def _settings() -> BalanceSettings:
    return BalanceSettings(
        focused_input_chars=_positive_int("BALANCE_FOCUSED_INPUT_CHARS"),
        deep_input_chars=_positive_int("BALANCE_DEEP_INPUT_CHARS"),
        code_chars_per_token=_positive_int("BALANCE_CODE_CHARS_PER_TOKEN"),
        code_min_tokens=_positive_int("BALANCE_CODE_MIN_TOKENS"),
        code_max_tokens=_positive_int("BALANCE_CODE_MAX_TOKENS"),
        profiles=_profiles(),
    )


def _profiles() -> dict[str, ResourceProfile]:
    return {
        "light": _profile("BALANCE_LIGHT", "light"),
        "focused": _profile("BALANCE_FOCUSED", "focused"),
        "deep": _profile("BALANCE_DEEP", "deep"),
        "guarded": _profile("BALANCE_GUARDED", "guarded"),
    }


def _validate(settings: BalanceSettings) -> None:
    if settings.code_min_tokens > settings.code_max_tokens:
        raise RuntimeError("BALANCE_CODE_MIN_TOKENS cannot exceed BALANCE_CODE_MAX_TOKENS")


def _profile(prefix: str, name: str) -> ResourceProfile:
    return ResourceProfile(
        name=name,
        history_messages=_positive_int(f"{prefix}_HISTORY_MESSAGES"),
        context_chars=_positive_int(f"{prefix}_CONTEXT_CHARS"),
        output_tokens=_positive_int(f"{prefix}_OUTPUT_TOKENS"),
        reflection_tokens=_positive_int(f"{prefix}_REFLECTION_TOKENS"),
        planner_tokens=_positive_int(f"{prefix}_PLANNER_TOKENS"),
    )


def _positive_int(name: str) -> int:
    value = os.getenv(name, "").strip()
    try:
        number = int(value)
    except ValueError as exc:
        raise RuntimeError(f"Missing or invalid positive integer environment variable: {name}") from exc
    if number < 1:
        raise RuntimeError(f"Missing or invalid positive integer environment variable: {name}")
    return number


def _contains(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)
