from .entities import Conversation

ROBOTIC_PHRASES = (
    "探索和讨论这个话题",
    "我对你描述的",
    "如果您有特别的偏好",
    "你是否有过特别的偏好",
)
FOOD_TOPICS = ("拌面", "面", "火锅", "米饭", "饺子", "馄饨", "烧烤", "奶茶", "咖啡")
LIKE_WORDS = ("喜欢", "爱吃", "想吃")
STRONG_WANT_WORDS = ("特别想吃", "很想吃", "馋")
INTEREST_WORDS = ("感兴趣", "想了解", "想聊")


def natural_reply(user_input: str, conv: Conversation) -> str | None:
    topic = _topic(user_input, conv)
    if not topic:
        return None
    if _has(user_input, STRONG_WANT_WORDS):
        return f"这就很真实。特别想吃{topic}的时候，其实不是随便吃点就能糊弄过去的。你一般会选辣一点的，还是酱香重一点的？"
    if _has(user_input, LIKE_WORDS):
        return f"{topic}这个喜欢很具体，比泛泛说美食有意思多了。你喜欢的是它拌开的酱香、面条的劲道，还是那种几口下去很满足的感觉？"
    if _has(user_input, INTEREST_WORDS):
        return f"那我们就从{topic}说起。先别泛泛聊，你更在意口味、配菜，还是面条本身的劲道？"
    return None


def polish_reply(user_input: str, reply: str, conv: Conversation) -> str:
    if not _is_robotic(reply):
        return reply
    natural = natural_reply(user_input, conv)
    if natural:
        return natural
    return "我刚才那句太像模板了。你说的是一个具体的小感觉，我应该先接住它，再慢慢往下聊。"


def _topic(user_input: str, conv: Conversation) -> str:
    direct = _first_topic(user_input)
    if direct:
        return direct
    for message in reversed(conv.messages[:-1]):
        found = _first_topic(message.content)
        if found:
            return found
    return ""


def _first_topic(text: str) -> str:
    return next((item for item in FOOD_TOPICS if item in text), "")


def _has(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)


def _is_robotic(reply: str) -> bool:
    return any(phrase in reply for phrase in ROBOTIC_PHRASES)
