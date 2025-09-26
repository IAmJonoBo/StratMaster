"""Validate the structure and integrity of ISSUES.md.

Checks performed:
 1. Unique external IDs (three-digit codes) and sequential ordering (optional warning if gaps)
 2. Required metadata presence: labels, milestone, priority (optional), flag (optional), status (optional)
 3. Label name hygiene: no whitespace-only, no duplicates per issue
 4. All labels exist in repository (unless --skip-label-exists)
 5. All referenced milestones exist (unless --skip-milestone-exists)
 6. Normalized title uniqueness (duplicate detection)
 7. Hash stability preview (compute & list truncated hashes) for debugging

Exit codes:
 0 -> Success (no errors)
 1 -> Structural errors found
 2 -> Environment / invocation error

Intended CI Usage:
  python scripts/validate_issues_source.py --strict

"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Set
import re

from issues_lib import (
    parse_issues_md,
    normalize_title,
    ensure_labels,
    ensure_milestones,
    collect_all_labels,
    DEFAULT_REQUIRED_MILESTONES,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
ISSUES_MD = REPO_ROOT / 'ISSUES.md'


def _load_milestones_titles() -> Set[str]:
    # Lazy import of subprocess to keep top-level lightweight
    import subprocess, json as _json

    try:
        out = subprocess.check_output([
            'gh', 'api', 'repos/:owner/:repo/milestones', '--paginate'
        ], text=True)
    except Exception:
        return set()
    try:
        data = _json.loads(out)
        return {m.get('title', '') for m in data if m.get('title')}
    except Exception:
        return set()


def validate(strict: bool, skip_label_exists: bool, skip_milestone_exists: bool, milestone_pattern: str | None = None, path: Path | None = None) -> int:
    """Validate issues source.

    Added optional path parameter to facilitate testing with a temporary ISSUES.md.
    """
    issues_path = path or ISSUES_MD
    if not issues_path.exists():
        print('ERROR: ISSUES.md not found')
        return 2
    try:
        specs = parse_issues_md(issues_path)
    except Exception as e:
        print(f'ERROR: Failed to parse ISSUES.md: {e}')
        return 1

    errors: List[str] = []
    warnings: List[str] = []

    _check_ids(specs, strict, errors, warnings)
    _check_required_metadata(specs, errors)
    _check_label_hygiene(specs, errors)
    if not skip_label_exists:
        _check_label_existence(specs, errors)
    if not skip_milestone_exists:
        _check_milestone_existence(specs, errors)
    _check_normalized_title_uniqueness(specs, errors)
    if milestone_pattern:
        _check_milestone_pattern(specs, milestone_pattern, errors)
    _emit_report(specs, errors, warnings)
    return 1 if errors else 0


def _check_ids(specs, strict, errors, warnings):
    seen = set()
    numeric = []
    for s in specs:
        if s.external_id in seen:
            errors.append(f'Duplicate external id: {s.external_id}')
        seen.add(s.external_id)
        try:
            numeric.append(int(s.external_id))
        except ValueError:
            errors.append(f'Non-numeric external id: {s.external_id}')
    if numeric:
        numeric.sort()
        missing = [x for x in range(numeric[0], numeric[-1] + 1) if x not in numeric]
        if missing and strict:
            warnings.append(f'Gap in external id sequence: missing {missing}')


def _check_required_metadata(specs, errors):
    for s in specs:
        if not s.labels:
            errors.append(f'Issue {s.external_id} missing labels')
        if not s.milestone:
            errors.append(f'Issue {s.external_id} missing milestone')
        if s.status_hint and s.status_hint.lower() == 'closed':
            if 'status:closed' not in s.labels:
                errors.append(f'Issue {s.external_id} marked closed but missing status:closed label')


def _check_label_hygiene(specs, errors):
    for s in specs:
        dup = {l for l in s.labels if s.labels.count(l) > 1}
        if dup:
            errors.append(f'Issue {s.external_id} has duplicate labels: {sorted(dup)}')
        if any(not l.strip() for l in s.labels):
            errors.append(f'Issue {s.external_id} has blank/whitespace label entries')


def _check_label_existence(specs, errors):
    all_labels = collect_all_labels(specs)
    missing_labels = _missing_labels(all_labels)
    if missing_labels:
        errors.append(f'Missing labels in repository: {sorted(missing_labels)}')


def _check_milestone_existence(specs, errors):
    milestones = _load_milestones_titles()
    referenced = {s.milestone for s in specs if s.milestone}
    missing_ms = {m for m in referenced if m not in milestones}
    if missing_ms:
        errors.append(f'Missing milestones in repository: {sorted(missing_ms)}')


def _check_normalized_title_uniqueness(specs, errors):
    norm = {}
    for s in specs:
        k = normalize_title(s.full_title)
        norm.setdefault(k, []).append(s.external_id)
    for k, ids in norm.items():
        if len(ids) > 1:
            errors.append(f'Duplicate normalized title group {k!r}: ids={ids}')


def _emit_report(specs, errors, warnings):  # pragma: no cover - formatting only
    if warnings:
        print('Warnings:')
        for w in warnings:
            print('  -', w)
    if errors:
        print('Errors:')
        for e in errors:
            print('  -', e)
    print('\nHash Preview:')
    for s in specs:
        print(f'  {s.external_id}: {s.hash}')


def _missing_labels(all_labels: Set[str]) -> Set[str]:
    import subprocess, json as _json
    try:
        out = subprocess.check_output(['gh', 'api', 'repos/:owner/:repo/labels', '--paginate'], text=True)
    except Exception:
        return set(all_labels)  # treat all as missing if call fails
    try:
        data = _json.loads(out)
        present = {l.get('name', '') for l in data}
        return {l for l in all_labels if l not in present}
    except Exception:
        return set(all_labels)


def main():  # pragma: no cover - CLI entry
    p = argparse.ArgumentParser(description='Validate ISSUES.md integrity')
    p.add_argument('--strict', action='store_true', help='Enable stricter warnings (id gaps)')
    p.add_argument('--skip-label-exists', action='store_true', help='Skip label existence checks against repository')
    p.add_argument('--skip-milestone-exists', action='store_true', help='Skip milestone existence checks against repository')
    p.add_argument('--milestone-pattern', help='Regex pattern milestone titles must match (e.g. ^M[0-9]+: )')
    args = p.parse_args()
    rc = validate(args.strict, args.skip_label_exists, args.skip_milestone_exists, args.milestone_pattern)
    sys.exit(rc)


if __name__ == '__main__':  # pragma: no cover
    main()

def _check_milestone_pattern(specs, pattern: str, errors):
    try:
        rx = re.compile(pattern)
    except re.error as e:
        errors.append(f'Invalid milestone regex pattern: {e}')
        return
    for s in specs:
        if s.milestone and not rx.search(s.milestone):
            errors.append(f"Issue {s.external_id} milestone '{s.milestone}' does not match pattern '{pattern}'")
