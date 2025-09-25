#!/usr/bin/env python3
"""Verify that commits reference an ADR and supporting debate artifacts."""
from __future__ import annotations

import argparse
import os
import re
import subprocess
from pathlib import Path
from typing import Iterable

ADR_PATTERN = re.compile(r"ADR-[0-9]{4}")


class DecisionLintError(RuntimeError):
    """Raised when decision hygiene requirements are not satisfied."""


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _collect_commit_messages(revision_range: str | None) -> Iterable[str]:
    if revision_range:
        log = _git("log", "--format=%s%n%b", revision_range)
    else:
        log = _git("log", "-1", "--format=%s%n%b")
    for entry in log.splitlines():
        yield entry


def _adr_exists(adr_id: str) -> bool:
    index_path = Path("docs/architecture/adr/ADR_INDEX.md")
    if not index_path.exists():
        return False
    return adr_id in index_path.read_text(encoding="utf-8")


def _has_debate_artifact(adr_id: str) -> bool:
    results_dir = Path("DECISIONS/ach_results")
    if not results_dir.exists():
        return False
    for file in results_dir.glob(f"{adr_id.lower()}*.json"):
        return True
    return False


def lint(revision_range: str | None = None) -> None:
    messages = list(_collect_commit_messages(revision_range))
    combined = "\n".join(messages) + os.environ.get("PR_BODY", "")
    matches = ADR_PATTERN.findall(combined)
    if not matches:
        raise DecisionLintError(
            "No ADR reference found. Include an ADR ID (e.g. ADR-0001) in the commit or PR description."
        )
    missing_records = [adr for adr in set(matches) if not _adr_exists(adr)]
    if missing_records:
        raise DecisionLintError(f"ADR(s) {', '.join(missing_records)} are not present in ADR_INDEX.md")
    unresolved = [adr for adr in set(matches) if not _has_debate_artifact(adr)]
    if unresolved:
        raise DecisionLintError(
            "Missing ACH debate artifacts for: " + ", ".join(unresolved) + ". Run strat-orchestrate ach evaluate."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Decision lint for ADR references")
    parser.add_argument(
        "revision_range",
        nargs="?",
        default=None,
        help="Optional git revision range (e.g. origin/main..HEAD). Default inspects the latest commit.",
    )
    args = parser.parse_args()
    try:
        lint(args.revision_range)
    except DecisionLintError as exc:  # pragma: no cover - CLI use
        raise SystemExit(str(exc))


if __name__ == "__main__":
    main()
