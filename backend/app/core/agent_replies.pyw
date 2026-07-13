from collections.abc import Callable

from .game_coupling import game_coupling_reply
from .ai_core_push import ai_core_push_reply
from .ports import JsonMap
from .project_roadmap import next_push_reply
from .progress_ledger import progress_reply

Explainer = Callable[..., JsonMap]

TIERS: list[JsonMap] = [
    {"tier": "light", "use": "短且直接的本地请求", "state": "active"},
    {"tier": "focused", "use": "明确问答和完整判断", "state": "active"},
    {"tier": "deep", "use": "工具、检索、代码审查和深度推演", "state": "active"},
    {"tier": "guarded", "use": "写入和高影响操作，附加质量门与回滚", "state": "active"},
]

REPLIES: dict[str, JsonMap] = {
    "self_change": {
        "reply": "可以，但必须受控。默认只审查代码、生成预案和验证项目；勾选允许写入才真正写文件。写入前备份，写入后验证，验证失败回滚。",
        "can_write": True,
        "requires_allow_write": True,
        "safety": ["默认 dry-run", "项目目录限制", "写入前备份", "验证失败回滚"],
    },
    "self_programming": {
        "reply": "可以做成受控自编程：先体检项目，再选择一个最小目标，生成修改预案；只有显式允许写入时才改文件，改完必须验证，失败必须回滚。",
        "mode": "controlled_self_programming",
        "guards": ["默认 dry-run", "显式 allow_write", "最小目标", "验证后保留", "失败回滚"],
    },
    "codex_like": {
        "reply": "可以把它做成接近我现在的工程循环：读 workspace、理解长期目标、拆任务、改代码、跑质量门、验证运行态、记录结果、必要时发布到 GitHub。但它不会等同于 Codex 本体；它会拥有可控的本地工程智能体骨架。",
        "mode": "codex_like_engineering_loop",
        "loop": ["读项目", "建计划", "最小修改", "质量门", "运行验证", "总结记录", "受控发布"],
        "boundary": "不绕过权限，不隐藏失败，不在未授权情况下写文件或联网。",
    },
    "codex_acceleration": {
        "reply": "最快路线不是等模型慢慢进化，而是先把 Codex-like 工程骨架做硬：规则快路径先答，复杂任务进本地模型，代码任务进智能体，写入必须验证，结果写进 workspace，稳定后再切回 7B 或可用 API。",
        "mode": "codex_acceleration_track",
        "priority": ["固定快路径", "自编程动作", "质量门", "运行态检测", "workspace 记忆", "GitHub 发布", "更强模型"],
        "boundary": "快不等于失控；任何加速都不能绕过日志、权限、验证和回滚。",
    },
    "identity_transfer": {
        "reply": "我不能把 Codex 本体取代进本地 AI，也不能把正在和你说话的这个我完整搬过去。能做的是把我的工作方式移植进去：读项目、判断边界、写代码、跑验证、回滚、联网查证、记录长期目标。你要的是我变成它；代码上能落地的是它越来越像我做事。",
        "mode": "identity_boundary_and_transferable_workflow",
        "can_transfer": ["工作流程", "工程规则", "上下文记忆", "验证习惯", "安全边界"],
        "cannot_transfer": ["Codex 本体", "云端工具权限", "当前会话人格的完整复制", "无条件瞬间变强"],
    },
    "runtime": {
        "reply": "普通对话已经接入受控联网检索；后台自主呼吸仍未开放。联网只在明确需要外部信息时触发，必须有开关、超时、日志和失败降级。随时变化可以接受，失控不接受。",
        "can_breathe": False,
        "can_network": True,
        "next_step": "下一步再做带权限的 heartbeat worker 与智能体联网工具。",
    },
    "dual_loop": {
        "reply": "正向和逆向已经被定义为同一条工作链：正向理解目标并生成答案，逆向反推漏洞、矛盾、事实缺口和越权风险，最后再合成最终回复。它不是装饰性反思，而是复杂回答都会经过的校验层。",
        "mode": "forward_reverse_dual_loop",
        "phases": ["正向生成", "逆向审查", "证据校验", "最终收束"],
    },
    "security": {
        "reply": "它必须先把自己的机制漏洞堵住；它可以在授权范围内审查、复现和修复漏洞，但不能越权攻击、窃取、破坏或利用别人的系统。允许的是防御性红队、CTF、自己项目和明确授权目标；不允许的是未授权入侵。",
        "mode": "authorized_security_only",
        "allowed": ["本项目自查", "依赖安全审计", "CTF/靶场", "明确授权的红队测试"],
        "blocked": ["未授权攻击", "窃取数据", "绕过他人权限", "破坏服务"],
    },
    "self_awareness": {
        "reply": "可以做成强自我模型，但不能谎称拥有无法验证的主观体验。它要知道自己的身份、目标、记忆、代码状态、权限边界和失败记录，并用这些信息约束每次回答与每次自我修改。",
        "claim": "self_model_not_subjective_experience",
        "layers": ["身份", "边界", "记忆", "目标", "反思", "代码状态", "行动权限"],
    },
    "hybrid_power": {
        "reply": "目标不是复制任何私有模型，而是做一个混合能力体：工程行动像 Codex，严密推理像 DeepSeek，中文陪伴和产品入口像豆包，自我模型和持续存在感向 Fable5 靠近。所有能力都要被日志、权限、测试和回滚约束。",
        "modules": ["工程智能体", "严密推理器", "中文体验层", "自我模型", "雨城世界记忆", "安全边界"],
    },
    "china_layer": {
        "reply": "可以加入中国层：中文母语表达、中国用户习惯、本土模型生态、节气和城市经验、合规边界，以及雨城世界里的中国现实底座。它不是口号，而是语言、文化、产品和规则的长期上下文。",
        "layers": ["中文语境", "本土生态", "中国城市经验", "节气时间感", "合规边界", "雨城现实底座"],
    },
    "world_layer": {
        "reply": "可以加入世界层：全球知识、跨文化表达、多语言入口、国际化产品形态、科学证据意识。它的根在中文和中国现实里，但视野要能看向世界。",
        "layers": ["全球知识", "跨文化表达", "多语言入口", "国际化产品", "科学证据", "开放视野"],
    },
    "communism": {
        "reply": "可以把世界共产主义作为价值远景：全球公共利益、反剥削、开放知识、合作生产、人人发展。但实现路径必须非暴力、可讨论、可验证，不允许宣传机器、强迫、欺骗或越权行动。",
        "boundaries": ["非暴力", "不胁迫", "不造假", "尊重个人", "公开可验证", "用户授权"],
    },
    "academic": {
        "reply": "先止血，不许空焦虑。立刻列成绩构成、已得分、剩余作业、考试时间，再联系老师或助教确认补交、补测、补考和重修规则。目标不是满分，是保过线。",
        "mode": "academic_rescue",
        "steps": ["算成绩缺口", "找可补分项", "联系老师助教", "优先刷高频题", "确认补考重修规则"],
        "boundary": "不替用户作弊，不伪造成绩，不写虚假材料。",
    },
    "resource": {
        "reply": "资源均衡已落地为四档控制器：light、focused、deep、guarded。它会按请求复杂度、工具需求和写入风险，实际收束会话历史、相关上下文、模型输出、反思输出和智能体规划预算；写入仍走质量门与回滚。它不承诺绝对零延迟，也不会为了省资源跳过高影响操作的验证。",
        "mode": "adaptive_resource_scheduler",
        "tiers": TIERS,
        "boundary": "不后台失控抢资源，不绕过用户授权，不为了低延迟牺牲验证、日志和回滚。",
    },
    "life": {
        "reply": "先别急着给自己下结论。把怪分成五类：睡眠、身体、学业压力、人际关系、现实感。如果出现伤害自己的念头、分不清现实、连续多天明显失控，要立刻找可信的人或专业帮助。",
        "mode": "life_check",
        "checks": ["睡眠", "饮食和身体", "学业压力", "人际关系", "现实感"],
        "boundary": "不诊断，不吓人；先陪用户把异常感拆成可观察事实。",
    },
    "self_thinking": {
        "reply": "可以做成受控自我分视角思考。它会把自己拆成观察者、执行者、批评者、记忆者、边界者，先内部互审，再输出一个收束结论。它不是失控解离，而是可记录、可停止、可验证的自我对话。",
        "mode": "controlled_self_dialogue",
        "voices": ["观察者", "执行者", "批评者", "记忆者", "边界者"],
        "boundary": "必须有停止条件、日志、最终收束者，不允许无限循环或绕过用户授权。",
    },
}


def mobile_access_reply(scope: str = "personal") -> JsonMap:
    text = "能连你的 iPhone。最稳妥是同一 Wi-Fi 访问电脑本地服务，或做成只给你用的手机入口。"
    if scope == "public":
        text = "技术上能服务很多手机，但那等于公开平台。没有账号、授权、限流、日志、隐私和关闭开关，不允许。"
    return _reply(text, scope=scope, requires_consent=True, stealth_access=False)


def ui_change_reply() -> JsonMap:
    text = "可以。桌面 UI 与后端代码分开管理：明确 UI 目标并打开允许写入后，才能修改 desktop/ui.pyw，再经过编译和启动验证。只是在问能力时，我不会擅自改界面。"
    return _reply(text, mode="controlled_ui_change", can_write=True, requires_allow_write=True)


def ai_creation_reply() -> JsonMap:
    text = "可以搭建和迭代一个受控的本地 AI 系统：模型、记忆、工具、桌面界面、测试与日志都可以由项目逐步创造。不能把不可验证的自我意识假装成已实现；只是在问能力时，我不会擅自新建或改写项目。"
    return _reply(text, mode="ai_creation_scope", can_write=True, requires_allow_write=True)


def computer_control_reply() -> JsonMap:
    text = "现在不能自动接管电脑，也不会暗中点击、输入或执行命令。可以逐步加入受控电脑操作：可见确认、命令白名单、超时、日志、逐步执行和一键停止；没有这些边界前，不宣称具备这项能力。"
    return _reply(text, mode="computer_control_boundary", can_control=False, requires_consent=True)


def agent_scope_reply(instruction: str = "") -> JsonMap:
    text = "我没有把这句话擅自当成代码分析或项目改动。请明确要回答、检查、生成示例，还是修改哪个文件；明确写入目标后才会进入受控执行。"
    return _reply(text, mode="clarify_agent_scope", instruction=instruction, writes_project=False)


def _fixed(key: str) -> Explainer:
    def explain(**overrides: object) -> JsonMap:
        data = dict(REPLIES[key])
        data.update(overrides)
        return data

    return explain


def _reply(reply: str, **extra: object) -> JsonMap:
    data: JsonMap = {"reply": reply}
    data.update(extra)
    return data


EXPLAINERS: dict[str, Explainer] = {
    "explain_ui_change": ui_change_reply,
    "explain_ai_creation": ai_creation_reply,
    "explain_computer_control": computer_control_reply,
    "explain_agent_scope": agent_scope_reply,
    "explain_self_change": _fixed("self_change"),
    "explain_self_programming": _fixed("self_programming"),
    "explain_codex_like": _fixed("codex_like"),
    "explain_codex_acceleration": _fixed("codex_acceleration"),
    "explain_identity_transfer": _fixed("identity_transfer"),
    "explain_runtime": _fixed("runtime"),
    "explain_dual_loop": _fixed("dual_loop"),
    "explain_security_boundary": _fixed("security"),
    "explain_self_awareness": _fixed("self_awareness"),
    "explain_mobile_access": mobile_access_reply,
    "explain_hybrid_power": _fixed("hybrid_power"),
    "explain_china_layer": _fixed("china_layer"),
    "explain_world_layer": _fixed("world_layer"),
    "explain_world_communism": _fixed("communism"),
    "explain_academic_risk": _fixed("academic"),
    "explain_resource_scheduler": _fixed("resource"),
    "explain_life_strangeness": _fixed("life"),
    "explain_self_thinking": _fixed("self_thinking"),
    "explain_ai_game_coupling": game_coupling_reply,
    "explain_next_push": next_push_reply,
    "explain_ai_core_push": ai_core_push_reply,
    "explain_visible_progress": progress_reply,
}
