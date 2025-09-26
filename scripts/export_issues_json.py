#!/usr/bin/env python3
"""Export parsed ISSUES.md to structured JSON.

Fields per issue:
  external_id, title, labels, milestone, flag, priority, status, hash, body
Derived:
  short_hash (first 8 chars), normalized_title

Usage:
  python scripts/export_issues_json.py > issues_export.json
  python scripts/export_issues_json.py --pretty --filter-label area:core
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Iterable

from issues_lib import parse_issues_md, normalize_title, IssueSpec


def filter_issues(issues: Iterable[IssueSpec], label: str | None):
    for i in issues:
        if label and label not in i.labels:
            continue
        yield i


def to_dict(spec: IssueSpec) -> dict:
    return {
        'external_id': spec.external_id,
        'title': spec.full_title,
        'canonical_title': spec.canonical_title,
        'labels': spec.labels,
        'milestone': spec.milestone,
        'flag': spec.flag,
        'priority': spec.priority,
        'status': spec.status_hint,
        'hash': spec.hash,
        'short_hash': spec.hash[:8],
        'normalized_title': normalize_title(spec.full_title),
        'body': spec.body.rstrip('\n'),
    }


def main():  # pragma: no cover - CLI
    p = argparse.ArgumentParser(description='Export ISSUES.md as structured JSON')
    p.add_argument('--pretty', action='store_true', help='Pretty-print JSON')
    p.add_argument('--filter-label', help='Only include issues containing this label')
    args = p.parse_args()

    issues = list(filter_issues(parse_issues_md(), args.filter_label))
    data = [to_dict(i) for i in issues]
    print(json.dumps(data, indent=2 if args.pretty else None))


if __name__ == '__main__':  # pragma: no cover
    main()
