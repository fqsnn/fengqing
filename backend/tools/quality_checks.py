import ast
from pathlib import Path

from quality_config import ROOT, effective_lines


def check_file_size(path: Path, limit: int) -> list[str]:
    count = effective_lines(path)
    return [f"{path}: {count} effective lines > {limit}"] if count > limit else []


def check_hardcoded(path: Path, markers: list[str]) -> list[str]:
    if path.suffix == ".css" or path.name in {".env.example", "config.yaml"}:
        return []
    issues: list[str] = []
    for no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if any(marker in line for marker in markers):
            issues.append(f"{path}:{no}: hardcoded config/path/url")
    return issues


def check_functions(path: Path, limit: int) -> list[str]:
    if path.suffix not in {".py", ".pyw"}:
        return []
    issues: list[str] = []
    for node in _functions(path):
        issues += _function_lines(path, node, limit)
        issues += _function_annotations(path, node)
    return issues


def check_class_methods(path: Path, limit: int) -> list[str]:
    if path.suffix not in {".py", ".pyw"}:
        return []
    issues: list[str] = []
    for node in _tree(path).body:
        if isinstance(node, ast.ClassDef) and _public_method_count(node) > limit:
            issues.append(f"{path}:{node.lineno}: too many public methods")
    return issues


def check_dependencies(limit: int) -> list[str]:
    req = ROOT / "requirements.txt"
    deps = [x for x in req.read_text(encoding="utf-8").splitlines() if x.strip() and not x.startswith("#")]
    return [f"{req}: {len(deps)} dependencies > {limit}"] if len(deps) > limit else []


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _functions(path: Path) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    return [node for node in ast.walk(_tree(path)) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _function_lines(path: Path, node: ast.FunctionDef | ast.AsyncFunctionDef, limit: int) -> list[str]:
    end = node.end_lineno or node.lineno
    start = node.body[0].lineno if node.body else node.lineno
    return [f"{path}:{node.lineno}: function too long"] if end - start + 1 > limit else []


def _function_annotations(path: Path, node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    issues = [] if node.returns is not None and not _returns_any(node) else [f"{path}:{node.lineno}: invalid return annotation"]
    for arg in node.args.args + node.args.kwonlyargs:
        if arg.arg != "self" and arg.annotation is None:
            issues.append(f"{path}:{node.lineno}: missing parameter annotation")
    return issues


def _returns_any(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return isinstance(node.returns, ast.Name) and node.returns.id == "Any"


def _public_method_count(node: ast.ClassDef) -> int:
    return sum(1 for item in node.body if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"))
