#!/usr/bin/env python3
"""Synchronize GitHub issues from ISSUES.md source-of-truth.

Features:
- Parses structured sections in ISSUES.md
- Creates missing GitHub issues (matched by canonical title or External ID prefix)
- Optionally updates body/labels/milestone if drift detected (--update)
- Optional dry-run mode
- Writes/updates mapping file issues_mapping.json { external_id: issue_number }
- Can mark issues closed if status: closed in ISSUES.md and --respect-status provided

Assumptions:
- GitHub CLI (gh) installed & authenticated
- Repository inferred via `gh repo view --json nameWithOwner`

Usage:
  python scripts/sync_issues_from_markdown.py            # create missing only
  python scripts/sync_issues_from_markdown.py --update   # create + update drift
  python scripts/sync_issues_from_markdown.py --dry-run  # show planned actions
  python scripts/sync_issues_from_markdown.py --respect-status --update
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Optional
from issues_lib import (
    parse_issues_md, IssueSpec, normalize_title, compute_issue_hash,
    collect_all_labels, ensure_labels, ensure_milestones, DEFAULT_REQUIRED_MILESTONES
)
import difflib

REPO_ROOT = Path(__file__).resolve().parent.parent
MAPPING_FILE = REPO_ROOT / 'issues_mapping.json'
LOCK_FILE = REPO_ROOT / '.issues_sync.lock'
STATE_FILE = REPO_ROOT / '.issues_sync_state.json'


def run(cmd: List[str]) -> str:
    return subprocess.check_output(cmd, text=True)


def gh_json(args: List[str]):
    try:
        out = run(args)
        return json.loads(out)
    except Exception:
        return []


def load_existing_issues():
    return gh_json(['gh', 'issue', 'list', '--state', 'all', '--limit', '1000', '--json', 'number,title,body,labels,milestone,state'])


def acquire_lock():
    if LOCK_FILE.exists():
        print('🔒 Another sync appears in progress (lock file present). Remove if stale:', LOCK_FILE)
        sys.exit(2)
    LOCK_FILE.write_text('locked')


def release_lock():
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except Exception:
        pass


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_state(hashes):
    STATE_FILE.write_text(json.dumps({'hashes': hashes}, indent=2) + '\n')


def match_issue(spec: IssueSpec, existing: List[dict]) -> Optional[dict]:
    for issue in existing:
        if issue['title'] == spec.full_title:
            return issue
        # Fallback: match if external id present and normalized titles match
        if spec.external_id in issue['title']:
            if normalize_title(issue['title']) == normalize_title(spec.full_title):
                return issue
    return None


def extract_labels(issue: dict) -> set:
    return {l['name'] for l in (issue.get('labels') or [])}


def needs_update(spec: IssueSpec, issue: dict, previous_hash: Optional[str]) -> bool:
    # If previous hash equals current, no update needed regardless of GitHub state
    if previous_hash and previous_hash == spec.hash:
        return False
    existing_labels = extract_labels(issue)
    if set(spec.labels) != existing_labels:
        return True
    desired_ms = spec.milestone or ''
    existing_ms = (issue.get('milestone') or {}).get('title', '')
    if desired_ms and desired_ms != existing_ms:
        return True
    body = issue.get('body') or ''
    if body.strip() != spec.body.strip():
        return True
    return False


def summarize_diff(spec: IssueSpec, issue: dict) -> str:
    """Produce a compact human-readable diff summary for planned update."""
    changes = []
    existing_labels = extract_labels(issue)
    if set(spec.labels) != existing_labels:
        changes.append(f"labels: {sorted(existing_labels)} -> {sorted(spec.labels)}")
    desired_ms = spec.milestone or ''
    existing_ms = (issue.get('milestone') or {}).get('title', '')
    if desired_ms and desired_ms != existing_ms:
        changes.append(f"milestone: '{existing_ms}' -> '{desired_ms}'")
    old_body = (issue.get('body') or '').strip().splitlines()
    new_body = spec.body.strip().splitlines()
    if old_body != new_body:
        diff_lines = list(difflib.unified_diff(old_body, new_body, lineterm='', n=3))
        # Limit large diffs
        if len(diff_lines) > 80:
            diff_lines = diff_lines[:80] + ['... (diff truncated)']
        changes.append('body:\n' + '\n'.join(diff_lines))
    return '\n'.join(changes)


def create_issue(spec: IssueSpec, dry_run: bool):
    cmd = ['gh', 'issue', 'create', '--title', spec.full_title, '--body', spec.body]
    if spec.labels:
        cmd += ['--label', ','.join(spec.labels)]
    if spec.milestone:
        cmd += ['--milestone', spec.milestone]
    if dry_run:
        print('DRY-RUN create:', ' '.join(cmd))
        return None
    out = run(cmd)
    print(out.strip())


def update_issue(spec: IssueSpec, issue: dict, dry_run: bool):
    number = str(issue['number'])
    if dry_run:
        print(f"DRY-RUN update: {number} (labels/body/milestone)")
        return
    if spec.labels:
        run(['gh', 'issue', 'edit', number, '--add-label', ','.join(spec.labels)])
    if spec.milestone:
        run(['gh', 'issue', 'edit', number, '--milestone', spec.milestone])
    run(['gh', 'api', f'repos/:owner/:repo/issues/{number}', '--method', 'PATCH', '-f', f'body={spec.body}'])
    print(f"Updated issue #{number}")


def close_issue(issue: dict, dry_run: bool):
    number = str(issue['number'])
    if dry_run:
        print(f"DRY-RUN close: {number}")
        return
    run(['gh', 'issue', 'close', number])
    print(f"Closed issue #{number}")


def main():
    parser = argparse.ArgumentParser(description='Sync GitHub issues from ISSUES.md (hash + lock aware)')
    parser.add_argument('--update', action='store_true', help='Update drift for existing issues (labels/body/milestone)')
    parser.add_argument('--dry-run', action='store_true', help='Show actions without executing')
    parser.add_argument('--respect-status', action='store_true', help='Close issues marked status: closed')
    parser.add_argument('--preflight', action='store_true', help='Ensure labels & milestones exist before operations')
    parser.add_argument('--no-lock', action='store_true', help='Disable lock file enforcement (advanced)')
    args = parser.parse_args()

    try:
        run(['gh', 'auth', 'status'])
    except Exception:
        print('GitHub CLI not authenticated (gh auth login)')
        sys.exit(1)

    specs = parse_issues_md()
    if args.preflight:
        _run_preflight(specs)

    if not args.no_lock:
        acquire_lock()

    try:
        created, updated, skipped, closed, _ = _process_specs(specs, args)
    finally:
        if not args.no_lock:
            release_lock()

    _print_summary(args, specs, created, updated, skipped, closed)


def _run_preflight(specs: List[IssueSpec]):
    ensure_labels(collect_all_labels(specs))
    ensure_milestones(DEFAULT_REQUIRED_MILESTONES)


def _process_specs(specs: List[IssueSpec], args):
    state = load_state()
    previous_hashes = state.get('hashes', {})
    existing = load_existing_issues()
    mapping = {}
    created = updated = skipped = closed = 0
    for spec in specs:
        _maybe_inject_status_label(spec)
        match = match_issue(spec, existing)
        prev_hash = previous_hashes.get(spec.external_id)
        if not match:
            create_issue(spec, args.dry_run)
            created += 1
            continue
        mapping[spec.external_id] = match['number']
        if args.respect_status and spec.status_hint == 'closed' and match['state'] != 'CLOSED':
            close_issue(match, args.dry_run)
            closed += 1
        if args.update and needs_update(spec, match, prev_hash):
            if args.dry_run:
                diff_summary = summarize_diff(spec, match)
                print(f"DRY-RUN diff for #{match['number']} ({spec.external_id}):\n{diff_summary}\n---")
            update_issue(spec, match, args.dry_run)
            updated += 1
        else:
            skipped += 1
    if not args.dry_run:
        MAPPING_FILE.write_text(json.dumps(mapping, indent=2) + '\n')
        save_state({s.external_id: s.hash for s in specs})
    return created, updated, skipped, closed, mapping


def _maybe_inject_status_label(spec: IssueSpec):
    if spec.status_hint and spec.status_hint.lower() == 'closed' and 'status:closed' not in spec.labels:
        spec.labels.append('status:closed')


def _print_summary(args, specs, created, updated, skipped, closed):  # pragma: no cover - formatting only
    print('\nSummary:')
    print(f'  Specs: {len(specs)}')
    print(f'  Created: {created}')
    print(f'  Updated: {updated}')
    print(f'  Skipped: {skipped}')
    if args.respect_status:
        print(f'  Closed: {closed}')
    print(f'  Mapping file: {MAPPING_FILE.name}')
    if not args.dry_run:
        print('  State file: .issues_sync_state.json (hash-based drift)')

if __name__ == '__main__':  # pragma: no cover
    main()
