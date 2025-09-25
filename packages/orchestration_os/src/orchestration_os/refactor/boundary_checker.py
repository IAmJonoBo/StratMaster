"""Static import boundary checker for orchestration modules."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml


@dataclass(slots=True)
class BoundaryIssue:
    file_path: Path
    imported_module: str
    message: str


def _iter_python_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.py"):
        if path.name.startswith("test_"):
            continue
        yield path


def _discover_imports(path: Path) -> Iterable[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def check_boundaries(config_path: Path, repo_root: Path | None = None) -> list[BoundaryIssue]:
    repo_root = repo_root or Path.cwd()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    modules: dict[str, dict[str, object]] = config.get("modules", {})
    issues: list[BoundaryIssue] = []
    for name, spec in modules.items():
        allowed = set(spec.get("allowed_dependencies", [])) | {f"orchestration_os.{name}"}
        roots = [repo_root / Path(root) for root in spec.get("roots", [])]
        for root in roots:
            if not root.exists():
                continue
            for file_path in _iter_python_files(root):
                for import_name in _discover_imports(file_path):
                    if not import_name.startswith("orchestration_os."):
                        continue
                    imported_module = import_name.split(".")[1]
                    if f"orchestration_os.{imported_module}" not in allowed:
                        issues.append(
                            BoundaryIssue(
                                file_path=file_path.relative_to(repo_root),
                                imported_module=import_name,
                                message=f"{name} may not depend on {import_name}",
                            )
                        )
    return issues
