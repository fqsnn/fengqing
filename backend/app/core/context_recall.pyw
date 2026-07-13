import re

from .ports import ContextRecallPort

QUERY_MARKERS = ("为什么", "什么", "哪里", "哪", "记得", "说过", "告诉过", "是不是", "是否", "吗", "？", "?")
QUERY_FILLERS = ("为什么", "什么", "哪里", "哪儿", "请问", "记得", "告诉过", "说过", "是不是", "是否", "吗", "呢")
MIN_SCORE = 2


class LocalContextRecall(ContextRecallPort):
    def __init__(self, context: str) -> None:
        self.facts = _facts(context)

    def recall(self, query: str) -> str | None:
        if not _is_query(query):
            return None
        ranked = _rank(query, self.facts)
        if not ranked or ranked[0][0] < MIN_SCORE:
            return None
        if len(ranked) > 1 and ranked[0][0] == ranked[1][0]:
            return None
        return _answer(ranked[0][1])

    def relevant(self, query: str) -> str:
        matches = [fact for score, fact in _rank(query, self.facts) if score >= MIN_SCORE][:3]
        return "\n".join(f"- {fact}" for fact in matches)


def _facts(context: str) -> list[str]:
    facts: list[str] = []
    in_code = False
    for line in context.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
        elif not in_code and (fact := _fact_line(line)):
            facts.append(fact)
    return list(dict.fromkeys(facts))


def _fact_line(line: str) -> str | None:
    value = line.strip()
    if not value or value.startswith(("#", "|", "---")):
        return None
    value = re.sub(r"^(?:[-*+>]|\d+[.)])\s*", "", value)
    clean = _clean(value)
    return clean if len(clean) >= 4 else None


def _clean(text: str) -> str:
    return text.strip().strip('“”"')


def _is_query(text: str) -> bool:
    return any(marker in text for marker in QUERY_MARKERS)


def _normalize(text: str) -> str:
    value = re.sub(r"[^\w\u4e00-\u9fff]", "", text).lower()
    for filler in QUERY_FILLERS:
        value = value.replace(filler, "")
    return value


def _ngrams(text: str, size: int) -> set[str]:
    return {text[index : index + size] for index in range(len(text) - size + 1)}


def _score(query: str, fact: str) -> int:
    query_text, fact_text = _normalize(query), _normalize(fact)
    return len(_ngrams(query_text, 2) & _ngrams(fact_text, 2)) + 2 * len(_ngrams(query_text, 3) & _ngrams(fact_text, 3))


def _rank(query: str, facts: list[str]) -> list[tuple[int, str]]:
    return sorted(((_score(query, fact), fact) for fact in facts), reverse=True)


def _answer(fact: str) -> str:
    if "因为" not in fact:
        return f"你之前告诉过我：‘{fact}’"
    reason = fact.split("因为", 1)[1].rstrip("。！？!?")
    return f"因为{reason}。这是你之前亲口告诉我的。"
