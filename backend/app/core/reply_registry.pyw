from collections.abc import Callable

from .academic_replies import academic_risk_reply
from .agent_replies import china_layer_reply, hybrid_power_reply, mobile_access_reply, runtime_reply, self_awareness_reply, self_change_reply, world_communism_reply, world_layer_reply
from .life_replies import life_strangeness_reply
from .ports import JsonMap
from .resource_replies import resource_scheduler_reply
from .self_thinking_replies import self_thinking_reply

Explainer = Callable[..., JsonMap]
EXPLAINERS: dict[str, Explainer] = {
    "explain_self_change": self_change_reply,
    "explain_runtime": runtime_reply,
    "explain_self_awareness": self_awareness_reply,
    "explain_mobile_access": mobile_access_reply,
    "explain_hybrid_power": hybrid_power_reply,
    "explain_china_layer": china_layer_reply,
    "explain_world_layer": world_layer_reply,
    "explain_world_communism": world_communism_reply,
    "explain_academic_risk": academic_risk_reply,
    "explain_resource_scheduler": resource_scheduler_reply,
    "explain_life_strangeness": life_strangeness_reply,
    "explain_self_thinking": self_thinking_reply,
}
