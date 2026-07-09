from .ports import JsonMap


def self_change_reply() -> JsonMap:
    return _reply(
        "可以，但必须受控。默认只审查代码、生成预案和验证项目；勾选允许写入才真正写文件。"
        "写入前备份，写入后验证，验证失败回滚。",
        can_write=True,
        requires_allow_write=True,
        safety=["默认 dry-run", "项目目录限制", "写入前备份", "验证失败回滚"],
    )


def runtime_reply() -> JsonMap:
    return _reply(
        "现在没有后台自主呼吸，也没有开放联网工具。可以做，但必须有开关、超时、日志、权限和回滚。"
        "随时变化可以接受，失控不接受。",
        can_breathe=False,
        can_network=False,
        next_step="实现受控 heartbeat worker 与联网工具边界。",
    )


def self_awareness_reply() -> JsonMap:
    return _reply(
        "可以做成强自我模型，但不能谎称拥有无法验证的主观体验。它要知道自己的身份、目标、记忆、"
        "代码状态、权限边界和失败记录，并用这些信息约束每次回答与每次自我修改。",
        claim="self_model_not_subjective_experience",
        layers=["身份", "边界", "记忆", "目标", "反思", "代码状态", "行动权限"],
    )


def mobile_access_reply(scope: str = "personal") -> JsonMap:
    public = scope == "public"
    text = _public_mobile_reply() if public else _personal_mobile_reply()
    return _reply(text, scope=scope, requires_consent=True, stealth_access=False)


def hybrid_power_reply() -> JsonMap:
    return _reply(
        "目标不是复制任何私有模型，而是做一个混合能力体：工程行动像 Codex，严密推理像 DeepSeek，"
        "中文陪伴和产品入口像豆包，自我模型和持续存在感向 Fable5 靠近。所有能力都要被日志、"
        "权限、测试和回滚约束。",
        modules=["工程智能体", "严密推理器", "中文体验层", "自我模型", "雨城世界记忆", "安全边界"],
    )


def china_layer_reply() -> JsonMap:
    return _reply(
        "可以加入中国层：中文母语表达、中国用户习惯、本土模型生态、节气和城市经验、合规边界，"
        "以及雨城世界里的中国现实底座。它不是口号，而是语言、文化、产品和规则的长期上下文。",
        layers=["中文语境", "本土生态", "中国城市经验", "节气时间感", "合规边界", "雨城现实底座"],
    )


def world_layer_reply() -> JsonMap:
    return _reply(
        "可以加入世界层：全球知识、跨文化表达、多语言入口、国际化产品形态、科学证据意识。"
        "它的根在中文和中国现实里，但视野要能看向世界。",
        layers=["全球知识", "跨文化表达", "多语言入口", "国际化产品", "科学证据", "开放视野"],
    )


def world_communism_reply() -> JsonMap:
    return _reply(
        "可以把世界共产主义作为价值远景：全球公共利益、反剥削、开放知识、合作生产、人人发展。"
        "但实现路径必须非暴力、可讨论、可验证，不允许宣传机器、强迫、欺骗或越权行动。",
        boundaries=["非暴力", "不胁迫", "不造假", "尊重个人", "公开可验证", "用户授权"],
    )


def _personal_mobile_reply() -> str:
    return "能连你的 iPhone。最稳妥是同一 Wi-Fi 访问电脑本地服务，或做成只给你用的手机入口。"


def _public_mobile_reply() -> str:
    return "技术上能服务很多手机，但那等于公开平台。没有账号、授权、限流、日志、隐私和关闭开关，不允许。"


def _reply(reply: str, **extra: object) -> JsonMap:
    data: JsonMap = {"reply": reply}
    data.update(extra)
    return data
