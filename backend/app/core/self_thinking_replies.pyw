from .ports import JsonMap


def self_thinking_reply() -> JsonMap:
    return {
        "reply": (
            "可以做成受控自我分视角思考。它会把自己拆成观察者、执行者、批评者、记忆者、边界者，"
            "先内部互审，再输出一个收束结论。它不是失控解离，而是可记录、可停止、可验证的自我对话。"
        ),
        "mode": "controlled_self_dialogue",
        "voices": ["观察者", "执行者", "批评者", "记忆者", "边界者"],
        "boundary": "必须有停止条件、日志、最终收束者，不允许无限循环或绕过用户授权。",
    }
