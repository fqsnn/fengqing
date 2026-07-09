from .entities import Conversation, Reflection
from .dual_loop import DUAL_LOOP_SYSTEM, format_search_context, needs_web_search
from .ports import EventStorePort, EvolutionEnginePort, LLMEnginePort, ReflectionEnginePort, ShortTermMemoryPort, WebSearchPort
from .prompts import DEFAULT_SYSTEM_PROMPT
from .quick_replies import quick_reply
from .shared_context import SharedContext


class AICoreService:
    def __init__(
        self,
        llm: LLMEnginePort,
        memory: ShortTermMemoryPort,
        reflection: ReflectionEnginePort,
        evolution: EvolutionEnginePort,
        event_store: EventStorePort,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        shared_context: SharedContext | None = None,
        web_search: WebSearchPort | None = None,
    ) -> None:
        self.llm = llm
        self.memory = memory
        self.reflection = reflection
        self.evolution = evolution
        self.event_store = event_store
        self.system_prompt = system_prompt
        self.shared_context = shared_context
        self.web_search = web_search
        self._reflection_buffer: list[Reflection] = []
        self.evolution_window = 3
        self.evolution_threshold = 0.7

    async def process_user_input(self, session_id: str, user_input: str) -> str:
        conv = await self._conversation(session_id)
        conv.add_message("user", user_input)
        quick = quick_reply(user_input)
        if quick and not needs_web_search(user_input):
            await self._save_answer(session_id, conv, user_input, quick)
            await self.event_store.append_event(session_id, "FAST_REPLY", {"reply": quick})
            return quick
        raw = await self._draft(session_id, conv, user_input)
        reflection = await self._reflect(conv, user_input, raw)
        await self._record_reflection(session_id, raw, reflection)
        final = reflection.revised_response or raw
        await self._save_answer(session_id, conv, user_input, final)
        await self._maybe_evolve(session_id, reflection)
        return final

    def _llm_messages(self, conv: Conversation, web_context: str) -> list[dict[str, str]]:
        messages = conv.to_llm_format()
        messages.insert(1, {"role": "system", "content": DUAL_LOOP_SYSTEM})
        if web_context:
            messages.insert(2, {"role": "system", "content": web_context})
        if self.shared_context:
            context = self.shared_context.render()
            if context:
                messages.insert(1, {"role": "system", "content": context})
        return messages

    async def _draft(self, session_id: str, conv: Conversation, user_input: str) -> str:
        web_context = await self._web_context(session_id, user_input)
        await self.event_store.append_event(session_id, "DUAL_LOOP", {"mode": "forward_reverse_prompt", "web": bool(web_context)})
        return await self.llm.generate_response(self._llm_messages(conv, web_context))

    async def _web_context(self, session_id: str, user_input: str) -> str:
        if not self.web_search or not needs_web_search(user_input):
            return ""
        try:
            results = await self.web_search.search(user_input)
        except Exception as exc:
            await self.event_store.append_event(session_id, "WEB_SEARCH_FAILED", {"error": str(exc)})
            return "联网检索失败；必须诚实说明无法确认外部事实。"
        await self.event_store.append_event(session_id, "WEB_SEARCH", {"query": user_input, "results": results})
        return format_search_context(results)

    async def _conversation(self, session_id: str) -> Conversation:
        conv = await self.memory.load(session_id) or Conversation(session_id=session_id)
        if not conv.messages:
            conv.add_message("system", self.system_prompt)
        return conv

    async def _reflect(self, conv: Conversation, user_input: str, raw: str) -> Reflection:
        history = [{"role": m.role, "content": m.content} for m in conv.messages[-3:]]
        return await self.reflection.reflect(user_input, raw, history)

    async def _record_reflection(self, session_id: str, raw: str, reflection: Reflection) -> None:
        await self.event_store.append_event(session_id, "REFLECTION", self._reflection_event(raw, reflection))

    async def _save_answer(self, session_id: str, conv: Conversation, user_input: str, final: str) -> None:
        conv.add_message("assistant", final)
        await self.memory.save(session_id, conv)
        if self.shared_context:
            self.shared_context.add("ai", f"用户：{user_input}\n回答：{final}")

    async def _maybe_evolve(self, session_id: str, reflection: Reflection) -> None:
        self._reflection_buffer = (self._reflection_buffer + [reflection])[-5:]
        recent = self._reflection_buffer[-self.evolution_window :]
        if len(recent) < self.evolution_window or self._average_confidence(recent) >= self.evolution_threshold:
            return
        await self._apply_evolution(session_id, recent)

    def _average_confidence(self, reflections: list[Reflection]) -> float:
        return sum(item.confidence for item in reflections) / len(reflections)

    def _reflection_event(self, raw: str, reflection: Reflection) -> dict[str, object]:
        return {
            "original": raw,
            "revised": reflection.revised_response,
            "confidence": reflection.confidence,
            "contradictions": reflection.contradictions,
            "inner_monologue": reflection.inner_monologue,
        }

    async def _apply_evolution(self, session_id: str, reflections: list[Reflection]) -> None:
        new_prompt = await self.evolution.mutate(reflections)
        if new_prompt == self.system_prompt:
            return
        self.system_prompt = new_prompt
        await self.event_store.append_event(session_id, "EVOLUTION", {"new_prompt": new_prompt})
