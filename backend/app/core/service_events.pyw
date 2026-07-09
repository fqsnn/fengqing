from .entities import Reflection


def reflection_event(raw: str, reflection: Reflection) -> dict[str, object]:
    return {
        "original": raw,
        "revised": reflection.revised_response,
        "confidence": reflection.confidence,
        "contradictions": reflection.contradictions,
        "inner_monologue": reflection.inner_monologue,
    }
