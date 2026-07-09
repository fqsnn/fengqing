from ..core.entities import Reflection


class EvolutionEngine:
    def __init__(self, initial_prompt: str) -> None:
        self.base_prompt = initial_prompt
        self.prompt = initial_prompt
        self.version = 0

    async def mutate(self, reflections: list[Reflection]) -> str:
        issues = self._collect_issues(reflections)
        if not issues:
            return self.prompt
        self.version += 1
        fixes = self._build_fixes(issues)
        self.prompt = f"{self.base_prompt}\n\n进化版本：{self.version}\n约束：{'；'.join(fixes)}"
        return self.prompt

    def _collect_issues(self, reflections: list[Reflection]) -> list[str]:
        issues: list[str] = []
        for item in reflections:
            if item.confidence < 0.7:
                issues.extend(item.contradictions)
                issues.append(item.inner_monologue[:80])
        return [item for item in issues if item]

    def _build_fixes(self, issues: list[str]) -> list[str]:
        text = "\n".join(issues)
        fixes = ["回答前检查事实、上下文和用户真实意图"]
        if "逻辑" in text or "矛盾" in text:
            fixes.append("先处理自洽性，再处理表达")
        if "风格" in text or "诗意" in text:
            fixes.append("保留克制的审美，不用空泛修辞")
        return list(dict.fromkeys(fixes))
