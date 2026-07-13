from .entities import Conversation, Reflection
from .agent_gateway import agent_intent, delegated_instruction, delegated_reply
from .conversation_style import natural_reply, polish_reply
from .dual_loop import DUAL_LOOP_SYSTEM, format_search_context, needs_web_search
from .ports import AgentRunnerPort, ContextRecallPort, EventStorePort, EvolutionEnginePort, LLMEnginePort, PythonExampleRunnerPort, ReflectionEnginePort, ShortTermMemoryPort, WebSearchPort
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
        python_runner: PythonExampleRunnerPort,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        shared_context: SharedContext | None = None,
        web_search: WebSearchPort | None = None,
        context_recall: ContextRecallPort | None = None,
        agent_runner: AgentRunnerPort | None = None,
        allow_private_model_context: bool = True,
    ) -> None:
        self.llm = llm
        self.memory = memory
        self.reflection = reflection
        self.evolution = evolution
        self.event_store = event_store
        self.python_runner = python_runner
        self.system_prompt = system_prompt
        self.shared_context = shared_context
        self.web_search = web_search
        self.context_recall = context_recall
        self.agent_runner = agent_runner
        self.allow_private_model_context = allow_private_model_context
        self._reflection_buffer: list[Reflection] = []
        self.evolution_window = 3
        self.evolution_threshold = 0.7

    async def process_user_input(self, session_id: str, user_input: str, allow_agent_write: bool = False) -> str:
        conv = await self._conversation(session_id)
        conv.add_message("user", user_input)
        delegated = await self._agent_reply(session_id, conv, user_input, allow_agent_write)
        if delegated:
            return delegated
        fast = await self._fast_reply(session_id, conv, user_input)
        if fast:
            return fast
        try:
            return await self._model_reply(session_id, conv, user_input)
        except Exception as exc:
            return await self._llm_failure(session_id, conv, user_input, exc)

    async def _agent_reply(self, session_id: str, conv: Conversation, user_input: str, allow_write: bool) -> str:
        intent = agent_intent(user_input)
        if not intent or not self.agent_runner:
            return ""
        result = await self.agent_runner.execute(delegated_instruction(user_input, intent), allow_write=allow_write)
        reply = delegated_reply(result, allow_write)
        await self._save_answer(session_id, conv, user_input, reply)
        await self.event_store.append_event(session_id, "AGENT_DELEGATED", {"intent": intent, "allow_write": allow_write})
        return reply

    async def _fast_reply(self, session_id: str, conv: Conversation, user_input: str) -> str:
        if needs_web_search(user_input):
            return await self._web_reply(session_id, conv, user_input)
        recalled = self.context_recall.recall(user_input) if self.context_recall else None
        fast = await quick_reply(user_input, self.python_runner)
        replies = (("PRIVATE_RECALL", recalled), ("NATURAL_REPLY", natural_reply(user_input, conv)), ("FAST_REPLY", fast))
        for event_type, reply in replies:
            if reply:
                await self._save_answer(session_id, conv, user_input, reply)
                await self.event_store.append_event(session_id, event_type, {"reply": reply})
                return reply
        return ""

    async def _web_reply(self, session_id: str, conv: Conversation, user_input: str) -> str:
        if not self.web_search:
            reply = "联网检索未启用，当前不会假装已经联网。"
            await self._save_answer(session_id, conv, user_input, reply)
            return reply
        try:
            results = await self.web_search.search(user_input)
        except Exception as exc:
            reply = f"联网检索失败：{exc}。"
            await self.event_store.append_event(session_id, "WEB_SEARCH_FAILED", {"error": str(exc)})
        else:
            reply = "已联网检索（仅发送本次检索词）：\n" + (format_search_context(results) or "没有找到结果。")
            await self.event_store.append_event(session_id, "WEB_SEARCH", {"query": user_input, "results": results})
        await self._save_answer(session_id, conv, user_input, reply)
        return reply

    async def _model_reply(self, session_id: str, conv: Conversation, user_input: str) -> str:
        raw = await self._draft(session_id, conv, user_input)
        reflection = await self._reflect(conv, user_input, raw)
        await self._record_reflection(session_id, raw, reflection)
        final = polish_reply(user_input, reflection.revised_response or raw, conv)
        await self._save_answer(session_id, conv, user_input, final)
        await self._maybe_evolve(session_id, reflection)
        return final

    async def _llm_failure(self, session_id: str, conv: Conversation, user_input: str, exc: Exception) -> str:
        reply = "本地模型暂时不可用，连接没有断；后端仍在运行。请确认 Ollama 已下载并可运行当前模型。"
        await self.event_store.append_event(session_id, "LLM_FAILED", {"error": str(exc)})
        await self._save_answer(session_id, conv, user_input, reply)
        return reply

    def _llm_messages(self, conv: Conversation, private_context: str) -> list[dict[str, str]]:
        messages = conv.to_llm_format()
        messages.insert(1, {"role": "system", "content": DUAL_LOOP_SYSTEM})
        if private_context:
            messages.insert(1, {"role": "system", "content": f"本机私人记忆中与本轮相关的原话：\n{private_context}"})
        if self.shared_context:
            context = self.shared_context.render()
            if context:
                messages.insert(1, {"role": "system", "content": context})
        return messages

    async def _draft(self, session_id: str, conv: Conversation, user_input: str) -> str:
        private_context = self._private_context(user_input)
        await self.event_store.append_event(session_id, "DUAL_LOOP", {"mode": "forward_reverse_prompt", "web": False})
        return await self.llm.generate_response(self._llm_messages(conv, private_context))

    def _private_context(self, user_input: str) -> str:
        if not self.allow_private_model_context or not self.context_recall:
            return ""
        return self.context_recall.relevant(user_input)

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
