import time
from pathlib import Path
from shutil import copy

from .code_prompts import extract_code, file_stats, improve_prompt, review_prompt, static_review
from .ports import LLMEnginePort
from .source_tree import SourceTree


class CodeAgent:
    MAX_FILE_CHARS = 12000

    def __init__(self, llm: LLMEnginePort, target_dir: str | Path) -> None:
        self.llm = llm
        self.tree = SourceTree(target_dir)

    def analyze_project(self) -> dict[str, object]:
        rows = self._rows()
        return {
            "root": str(self.tree.target_dir),
            "file_count": len(rows),
            "line_count": sum(int(item["lines"]) for item in rows),
            "largest_files": rows[:8],
        }

    def read_file(self, path: str, max_chars: int = MAX_FILE_CHARS) -> dict[str, object]:
        file_path = self.tree.safe_path(path)
        text = file_path.read_text(encoding="utf-8")
        rel = str(file_path.relative_to(self.tree.target_dir))
        return {"path": rel, "content": text[:max_chars], "truncated": len(text) > max_chars}

    async def review_project(self, max_files: int = 5) -> dict[str, object]:
        reviews, llm_failed = [], False
        for item in self._largest(max_files):
            review = self._fallback_review(item["path"]) if llm_failed else await self._review_file(item["path"])
            llm_failed = str(review["review"]).startswith("- LLM 不可用")
            reviews.append(review)
        return {"reviewed": len(reviews), "items": reviews}

    async def improve(self, path: str, allow_write: bool = False) -> dict[str, object]:
        proposal = await self._propose_improvement(path)
        if not allow_write:
            preview = str(proposal["code"])[:2000]
            return {"path": proposal["path"], "changed": False, "dry_run": True, "preview": preview}
        return self._write_proposal(path, proposal)

    def validate_project(self) -> dict[str, object]:
        errors = []
        for path in self.tree.source_files():
            try:
                compile(path.read_text(encoding="utf-8"), str(path), "exec")
            except SyntaxError as exc:
                errors.append({"path": str(path.relative_to(self.tree.target_dir)), "error": str(exc)})
        return {"passed": not errors, "checked": len(self.tree.source_files()), "errors": errors}

    async def _run_self_improvement_cycle(self, allow_write: bool = False, max_files: int = 1) -> list[dict[str, object]]:
        return [await self.improve(str(item["path"]), allow_write=allow_write) for item in self._largest(max_files)]

    def _rows(self) -> list[dict[str, object]]:
        rows = [file_stats(path, self.tree.target_dir) for path in self.tree.source_files()]
        return sorted(rows, key=lambda item: int(item["lines"]), reverse=True)

    def _largest(self, limit: int) -> list[dict[str, object]]:
        return self._rows()[:limit]

    async def _review_file(self, path: object) -> dict[str, object]:
        item = self.read_file(str(path))
        try:
            prompt = review_prompt(str(item["path"]), str(item["content"]))
            review = await self.llm.generate_response([{"role": "user", "content": prompt}])
        except Exception as exc:
            review = static_review(str(item["content"]), exc)
        return {"path": item["path"], "review": review}

    def _fallback_review(self, path: object) -> dict[str, object]:
        item = self.read_file(str(path))
        error = RuntimeError("previous LLM request failed")
        return {"path": item["path"], "review": static_review(str(item["content"]), error)}

    async def _propose_improvement(self, path: str) -> dict[str, object]:
        item = self.read_file(path)
        prompt = improve_prompt(str(item["path"]), str(item["content"]))
        code = extract_code(await self.llm.generate_response([{"role": "user", "content": prompt}]))
        compile(code, str(item["path"]), "exec")
        return {"path": item["path"], "code": code}

    def _write_proposal(self, path: str, proposal: dict[str, object]) -> dict[str, object]:
        file_path = self.tree.safe_path(path)
        backup = self.tree.backup_path(file_path, int(time.time()))
        copy(file_path, backup)
        file_path.write_text(proposal["code"], encoding="utf-8")
        validation = self.validate_project()
        if not validation["passed"]:
            copy(backup, file_path)
            return {"path": proposal["path"], "changed": False, "restored": True, "validation": validation}
        return {"path": proposal["path"], "changed": True, "backup": str(backup), "validation": validation}
