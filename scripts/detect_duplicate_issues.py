#!/usr/bin/env python3
"""Detect duplicate roadmap issues in GitHub.

Heuristics:
- Normalize by removing leading 'Issue NNN:' prefix
- Normalize by removing bracket tags like [IMPL], [SPRINT-0]
- Lowercase + collapse whitespace
- Group and report groups with >1 issue number

Optional: --close-duplicates will close *later* issues in a duplicate group keeping the oldest (smallest number) open.
Dry run by default; must pass --execute with --close-duplicates to perform closing.

Usage:
  python scripts/detect_duplicate_issues.py            # report only
  python scripts/detect_duplicate_issues.py --close-duplicates --execute
"""
from __future__ import annotations
import re
import subprocess
import json
import argparse
import sys
from dataclasses import dataclass
from typing import List, Dict

NORMALIZE_PREFIX_RE = re.compile(r'^issue\s+\d{1,4}:\s*', re.IGNORECASE)
TAG_RE = re.compile(r'^\[[^\]]+\]\s*')

@dataclass
class Issue:
    number: int
    title: str
    state: str


def gh_json(cmd: List[str]):
    try:
        out = subprocess.check_output(cmd, text=True)
        return json.loads(out)
    except Exception as e:
        print(f"Error running {' '.join(cmd)}: {e}", file=sys.stderr)
        return []


def fetch_issues() -> List[Issue]:
    data = gh_json(['gh', 'issue', 'list', '--state', 'all', '--limit', '1000', '--json', 'number,title,state'])
    return [Issue(d['number'], d['title'], d['state']) for d in data]


def normalize_title(title: str) -> str:
    t = title.strip()
    t = NORMALIZE_PREFIX_RE.sub('', t)
    t = TAG_RE.sub('', t)
    t = re.sub(r'\s+', ' ', t)
    return t.lower()


def group_duplicates(issues: List[Issue]) -> Dict[str, List[Issue]]:
    groups: Dict[str, List[Issue]] = {}
    for issue in issues:
        key = normalize_title(issue.title)
        groups.setdefault(key, []).append(issue)
    # Keep only groups with >1
    return {k: v for k, v in groups.items() if len(v) > 1}


def close_duplicates(dupe_groups: Dict[str, List[Issue]], execute: bool):
    for key, issues in dupe_groups.items():
        # Keep earliest (smallest number) open
        sorted_issues = sorted(issues, key=lambda i: i.number)
        keeper = sorted_issues[0]
        closing = [i for i in sorted_issues[1:] if i.state != 'CLOSED']
        if not closing:
            continue
        print(f"Group: '{key}' -> keeping #{keeper.number}, closing {[i.number for i in closing]}")
        if execute:
            for issue in closing:
                subprocess.call(['gh', 'issue', 'close', str(issue.number), '--comment', f'Duplicate of #{keeper.number} (auto-detected)'])


def main():
    parser = argparse.ArgumentParser(description='Detect duplicate roadmap issues')
    parser.add_argument('--close-duplicates', action='store_true')
    parser.add_argument('--execute', action='store_true', help='Actually perform close operations (requires --close-duplicates)')
    args = parser.parse_args()

    try:
        subprocess.check_call(['gh', 'auth', 'status'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        print('GitHub CLI not authenticated. Run gh auth login', file=sys.stderr)
        sys.exit(1)

    issues = fetch_issues()
    dupe_groups = group_duplicates(issues)

    if not dupe_groups:
        print('✅ No duplicate issue title groups detected (after normalization).')
        return

    print('🚨 Duplicate Issue Groups Detected:')
    for key, grp in dupe_groups.items():
        nums = ', '.join(f"#{i.number}" for i in sorted(grp, key=lambda x: x.number))
        print(f"  - {key} -> {nums}")

    if args.close_duplicates:
        if not args.execute:
            print('\n(--close-duplicates specified without --execute; dry-run mode)')
        close_duplicates(dupe_groups, execute=args.execute)
    else:
        print('\nPass --close-duplicates to close later duplicates automatically (requires --execute to actually apply).')

if __name__ == '__main__':
    main()
