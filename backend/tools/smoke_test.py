import logging

from fastapi.testclient import TestClient

from app.core.context_loader import private_context_for_model
from app.core.context_recall import LocalContextRecall
from app.core.conversation_style import natural_reply
from app.core.entities import Conversation
from app.main import PUBLIC_CONTEXT, SYSTEM_PROMPT, app


def _system_topic_is_ignored() -> bool:
    conv = Conversation(session_id="smoke")
    conv.add_message("system", "拌面")
    conv.add_message("user", "我为什么喜欢南京一号线？")
    return natural_reply(conv.messages[-1].content, conv) is None


def _core_behavior_works() -> bool:
    context = '- “我喜欢南京的一号线，因为它是蓝色的。”'
    recall = LocalContextRecall(context).recall("我为什么喜欢南京一号线？")
    remote_safe = private_context_for_model("private", "openai", False) == ""
    public_context_is_dynamic = "南京：被生活过的城市" in PUBLIC_CONTEXT and "南京：被生活过的城市" not in SYSTEM_PROMPT
    return public_context_is_dynamic and _system_topic_is_ignored() and remote_safe and recall == "因为它是蓝色的。这是你之前亲口告诉我的。"


def main() -> int:
    logging.getLogger("httpx").setLevel(logging.WARNING)
    client = TestClient(app)
    for path in ("/", "/health", "/api/v1/status", "/api/v1/history?limit=1", "/api/v1/tasks?limit=1", "/api/v1/memories"):
        response = client.get(path)
        if response.status_code != 200:
            print(f"smoke failed: {path} -> {response.status_code}")
            return 1
    if not _core_behavior_works():
        print("smoke failed: context or recall behavior")
        return 1
    print("smoke=pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
