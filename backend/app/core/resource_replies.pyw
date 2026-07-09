from .ports import JsonMap


def resource_scheduler_reply() -> JsonMap:
    return {
        "reply": (
            "可以做实时调度层，但不能承诺绝对零延迟。正确目标是低延迟：先规则直答，"
            "再本地快模型，再本地深度模型，最后才走可选 API；每一层都有超时、降级和日志。"
        ),
        "mode": "adaptive_resource_scheduler",
        "tiers": _tiers(),
        "boundary": "不后台失控抢资源，不绕过用户授权，不为低延迟牺牲验证和回滚。",
    }


def _tiers() -> list[JsonMap]:
    return [
        {"tier": "rule", "use": "固定能力和安全边界", "target_ms": 50},
        {"tier": "local_fast", "use": "短问答和轻推理", "target_ms": 1200},
        {"tier": "local_deep", "use": "复杂推理和长上下文", "target_ms": 8000},
        {"tier": "tool", "use": "代码、文件、测试、日志", "target_ms": 15000},
        {"tier": "api_optional", "use": "用户允许时的外部增强", "target_ms": 20000},
    ]
