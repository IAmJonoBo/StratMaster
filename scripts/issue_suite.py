#!/usr/bin/env python3
"""Unified Issue Automation Suite CLI.

Subcommands (initial phase):
  validate      -> structural validation (wraps validate_issues_source.py)
  sync          -> create/update/close issues (integrates summary JSON output)
  export        -> export structured JSON of specs
  report        -> generate HTML report from export
  summary       -> quick parse + counts + hash preview
  project-sync  -> (stub) GitHub Project assignment integration
  schema        -> emit JSON Schemas for export & summary formats

Reads configuration from issue_suite.config.yaml at repo root.

Design Goals:
  - Single entrypoint for local + CI + AI agents (stable contract)
  - Machine-readable change summary for sync operations
  - Config-driven to allow reuse across repositories with minimal edits
  - Backwards-compatible: legacy scripts can delegate here over time
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# Local imports
from issues_lib import (
    parse_issues_md,
    IssueSpec,
    collect_all_labels,
    ensure_labels,
    ensure_milestones,
    DEFAULT_REQUIRED_MILESTONES,
    normalize_title,
)

# Mock mode (for tests / offline CI without gh). Enable by setting ISSUES_SUITE_MOCK=1
MOCK_MODE = os.environ.get('ISSUES_SUITE_MOCK') == '1'

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / 'issue_suite.config.yaml'


try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - yaml optional but recommended
    yaml = None


class ConfigError(RuntimeError):
    pass


@dataclass
class SuiteConfig:
    version: int
    source_file: Path
    id_pattern: str
    milestone_required: bool
    auto_status_label: bool
    milestone_pattern: Optional[str]
    github_repo: Optional[str]
    project_enable: bool
    project_number: Optional[int]
    project_field_mappings: Dict[str, str]
    inject_labels: List[str]
    ensure_milestones_list: List[str]
    summary_json: str
    export_json: str
    report_html: str
    hash_state_file: str
    mapping_file: str
    lock_file: str
    truncate_body_diff: int
    dry_run_default: bool
    emit_change_events: bool
    schema_export_file: str
    schema_summary_file: str
    schema_version: int


def load_config(path: Path = CONFIG_PATH) -> SuiteConfig:
    if not path.exists():
        raise ConfigError(f'Configuration file not found: {path}')
    if yaml is None:
        raise ConfigError('PyYAML not installed; add to dev requirements to use unified CLI.')
    data = yaml.safe_load(path.read_text()) or {}
    try:
        version = int(data.get('version', 1))
    except Exception as e:  # pragma: no cover - trivial
        raise ConfigError(f'Invalid version field: {e}')
    src = data.get('source', {})
    gh = data.get('github', {})
    defaults = data.get('defaults', {})
    out = data.get('output', {})
    behavior = data.get('behavior', {})
    ai = data.get('ai', {})
    project = gh.get('project', {}) or {}
    cfg = SuiteConfig(
        version=version,
        source_file=REPO_ROOT / src.get('file', 'ISSUES.md'),
        id_pattern=src.get('id_pattern', '^[0-9]{3}$'),
        milestone_required=bool(src.get('milestone_required', True)),
        auto_status_label=bool(src.get('auto_status_label', True)),
        milestone_pattern=src.get('milestone_pattern'),
        github_repo=gh.get('repo'),
        project_enable=bool(project.get('enable', False)),
        project_number=project.get('number'),
        project_field_mappings=project.get('field_mappings', {}) or {},
        inject_labels=defaults.get('inject_labels', []) or [],
        ensure_milestones_list=defaults.get('ensure_milestones', DEFAULT_REQUIRED_MILESTONES),
        summary_json=out.get('summary_json', 'issues_summary.json'),
        export_json=out.get('export_json', 'issues_export.json'),
        report_html=out.get('report_html', 'issues_report.html'),
        hash_state_file=out.get('hash_state_file', '.issues_sync_state.json'),
        mapping_file=out.get('mapping_file', 'issues_mapping.json'),
        lock_file=behavior.get('lock_file', '.issues_sync.lock'),
        truncate_body_diff=int(behavior.get('truncate_body_diff', 80)),
        dry_run_default=bool(behavior.get('dry_run_default', False)),
        emit_change_events=bool(ai.get('emit_change_events', True)),
        schema_export_file=ai.get('schema_export_file', 'issue_export.schema.json'),
        schema_summary_file=ai.get('schema_summary_file', 'issue_change_summary.schema.json'),
        schema_version=int(ai.get('schema_version', 1)),
    )
    # Basic key validation: warn for unknown top-level keys
    allowed_top = {'version','source','github','defaults','output','behavior','ai'}
    extra = set(data.keys()) - allowed_top
    if extra:
        print(f'[config] Warning: unknown top-level keys: {sorted(extra)}')
    return cfg


def _gh_authenticated() -> bool:
    if MOCK_MODE:
        return True
    try:
        subprocess.check_output(['gh', 'auth', 'status'], stderr=subprocess.STDOUT)
        return True
    except Exception:
        return False


def _match_id(cfg: SuiteConfig, external_id: str) -> bool:
    return re.match(cfg.id_pattern, external_id) is not None


def cmd_validate(cfg: SuiteConfig, args: argparse.Namespace) -> int:
    from validate_issues_source import validate as low_level_validate  # local import
    strict = args.strict
    print('[validate] Parsing issues...')
    specs = parse_issues_md(cfg.source_file)
    # Quick inline id pattern check before delegating to existing validator
    bad_ids = [s.external_id for s in specs if not _match_id(cfg, s.external_id)]
    if bad_ids:
        print(f'Errors:\n  - External IDs failing pattern {cfg.id_pattern!r}: {bad_ids}')
        return 1
    rc = low_level_validate(
        strict=strict,
        skip_label_exists=args.skip_label_exists,
        skip_milestone_exists=args.skip_milestone_exists,
        milestone_pattern=cfg.milestone_pattern,
    )
    if rc == 0:
        print('[validate] Success.')
    return rc


def _acquire_lock(path: Path):
    if path.exists():
        raise SystemExit(f'Lock present, another sync in progress: {path}')
    path.write_text('locked')


def _release_lock(path: Path):  # pragma: no cover - best effort
    try:
        if path.exists():
            path.unlink()
    except Exception:
        pass


def _load_state(path: Path) -> Dict[str, Any]:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return {}
    return {}


def _save_state(path: Path, specs: List[IssueSpec]):
    path.write_text(json.dumps({'hashes': {s.external_id: s.hash for s in specs}}, indent=2) + '\n')


def _run(cmd: List[str]) -> str:
    if MOCK_MODE:
        print('[mock-run]', ' '.join(cmd))
        return ''
    return subprocess.check_output(cmd, text=True)


def _gh_json(args: List[str]):
    try:
        out = _run(args)
        return json.loads(out)
    except Exception:
        return []


def _existing_issues() -> List[Dict[str, Any]]:
    if MOCK_MODE:
        return []
    return _gh_json(['gh','issue','list','--state','all','--limit','1000','--json','number,title,body,labels,milestone,state'])


def _extract_labels(issue: Dict[str, Any]) -> set:
    return {l['name'] for l in (issue.get('labels') or [])}


def _match_issue(spec: IssueSpec, existing: List[Dict[str, Any]]):
    for issue in existing:
        if issue['title'] == spec.full_title:
            return issue
        if spec.external_id in issue['title'] and normalize_title(issue['title']) == normalize_title(spec.full_title):
            return issue
    return None


def _needs_update(spec: IssueSpec, issue: Dict[str, Any], prev_hash: Optional[str]) -> bool:
    if prev_hash and prev_hash == spec.hash:
        return False
    labels_current = _extract_labels(issue)
    if set(spec.labels) != labels_current:
        return True
    desired_ms = spec.milestone or ''
    existing_ms = (issue.get('milestone') or {}).get('title','')
    if desired_ms and desired_ms != existing_ms:
        return True
    body = (issue.get('body') or '').strip()
    if body != spec.body.strip():
        return True
    return False


def _diff_summary(spec: IssueSpec, issue: Dict[str, Any], truncate: int) -> Dict[str, Any]:
    import difflib
    changes: Dict[str, Any] = {}
    labels_current = _extract_labels(issue)
    if set(spec.labels) != labels_current:
        changes['labels_added'] = sorted(set(spec.labels) - labels_current)
        changes['labels_removed'] = sorted(labels_current - set(spec.labels))
    desired_ms = spec.milestone or ''
    existing_ms = (issue.get('milestone') or {}).get('title','')
    if desired_ms and desired_ms != existing_ms:
        changes['milestone_from'] = existing_ms
        changes['milestone_to'] = desired_ms
    old_body = (issue.get('body') or '').strip().splitlines()
    new_body = spec.body.strip().splitlines()
    if old_body != new_body:
        diff_lines = list(difflib.unified_diff(old_body, new_body, lineterm='', n=3))
        if truncate and len(diff_lines) > truncate:
            diff_lines = diff_lines[:truncate] + ['... (truncated)']
        changes['body_changed'] = True
        changes['body_diff'] = diff_lines
    return changes


def _maybe_inject_status_label(cfg: SuiteConfig, spec: IssueSpec):
    if not cfg.auto_status_label:
        return
    if spec.status_hint and spec.status_hint.lower() == 'closed' and 'status:closed' not in spec.labels:
        spec.labels.append('status:closed')
    # Inject global labels
    for g in cfg.inject_labels:
        if g not in spec.labels:
            spec.labels.append(g)


def _create_issue(spec: IssueSpec, dry_run: bool):
    if MOCK_MODE:
        print(f'[mock] create issue {spec.external_id} title={spec.full_title}')
        return f'MOCK-{spec.external_id}'
    cmd = ['gh','issue','create','--title',spec.full_title,'--body',spec.body]
    if spec.labels:
        cmd += ['--label', ','.join(spec.labels)]
    if spec.milestone:
        cmd += ['--milestone', spec.milestone]
    if dry_run:
        print('DRY-RUN create:', ' '.join(cmd))
        return 'DRY-RUN'
    out = _run(cmd).strip()
    print(out)
    return out


def _apply_update(spec: IssueSpec, match: Dict[str, Any], diff: Dict[str, Any], dry_run: bool):
    number = str(match['number'])
    if dry_run:
        print(f'DRY-RUN update: #{number} diff={list(diff.keys())}')
        return
    if MOCK_MODE:
        print(f'[mock] update issue #{number} diff={list(diff.keys())}')
        return
    if spec.labels:
        _run(['gh','issue','edit', number, '--add-label', ','.join(spec.labels)])
    if spec.milestone:
        _run(['gh','issue','edit', number, '--milestone', spec.milestone])
    _run(['gh','api', f'repos/:owner/:repo/issues/{number}', '--method', 'PATCH', '-f', f'body={spec.body}'])
    print(f'Updated issue #{number}')


def _close_issue(match: Dict[str, Any], dry_run: bool):
    number = str(match['number'])
    if dry_run:
        print(f'DRY-RUN close: {number}')
        return
    if MOCK_MODE:
        print(f'[mock] close issue #{number}')
        return
    _run(['gh','issue','close', number])
    print(f'Closed issue #{number}')


def _write_summary(cfg: SuiteConfig, specs: List[IssueSpec], created, updated, closed, skipped: int, dry_run: bool, path_override: Optional[str]):
    summary_obj = {
        'schemaVersion': cfg.schema_version,
        'generated_at': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
        'dry_run': dry_run,
        'totals': {
            'specs': len(specs),
            'created': len(created),
            'updated': len(updated),
            'closed': len(closed),
            'skipped': skipped,
        },
        'changes': {
            'created': created,
            'updated': updated,
            'closed': closed,
        }
    }
    if path_override:
        Path(path_override).write_text(json.dumps(summary_obj, indent=2) + '\n')
        print(f'[sync] Summary JSON written -> {path_override}')
    else:
        default_path = REPO_ROOT / cfg.summary_json
        default_path.write_text(json.dumps(summary_obj, indent=2) + '\n')
        print(f'[sync] Summary JSON written -> {default_path}')


# Insert new helper abstractions to lower cognitive complexity of cmd_sync

def _prepare_specs(cfg: SuiteConfig) -> List[IssueSpec]:
    specs = parse_issues_md(cfg.source_file)
    for s in specs:
        _maybe_inject_status_label(cfg, s)
    return specs


def _preflight_if_requested(cfg: SuiteConfig, specs: List[IssueSpec], args: argparse.Namespace):
    if getattr(args, 'preflight', False):
        ensure_labels(collect_all_labels(specs) + cfg.inject_labels)
        ensure_milestones(cfg.ensure_milestones_list)


def _load_previous_hashes(state_path: Path) -> Dict[str, str]:
    state = _load_state(state_path)
    return state.get('hashes', {})


def _process_single_spec(spec: IssueSpec, existing: List[Dict[str, Any]], prev_hashes: Dict[str, str],
                          actions: Dict[str, List[Dict[str, Any]]], mapping: Dict[str, int],
                          args: argparse.Namespace, cfg: SuiteConfig):
    match = _match_issue(spec, existing)
    prev_hash = prev_hashes.get(spec.external_id)
    if not match:
        _create_issue(spec, args.dry_run)
        actions['created'].append({'external_id': spec.external_id, 'title': spec.full_title,
                                    'labels': spec.labels, 'milestone': spec.milestone, 'hash': spec.hash})
        return False  # not skipped
    mapping[spec.external_id] = match['number']
    if args.respect_status and spec.status_hint == 'closed' and match['state'] != 'CLOSED':
        _close_issue(match, args.dry_run)
        actions['closed'].append({'external_id': spec.external_id, 'number': match['number']})
        return False
    if args.update and _needs_update(spec, match, prev_hash):
        diff = _diff_summary(spec, match, cfg.truncate_body_diff)
        _apply_update(spec, match, diff, args.dry_run)
        actions['updated'].append({'external_id': spec.external_id, 'number': match['number'],
                                   'prev_hash': prev_hash, 'new_hash': spec.hash, 'diff': diff})
        return False
    return True  # skipped


def _write_mapping_and_state(mapping_path: Path, state_path: Path, specs: List[IssueSpec], mapping: Dict[str, int], dry_run: bool):
    if dry_run:
        return
    mapping_path.write_text(json.dumps(mapping, indent=2) + '\n')
    _save_state(state_path, specs)


def cmd_sync(cfg: SuiteConfig, args: argparse.Namespace) -> int:  # type: ignore[override]
    """Delegate sync to package orchestrator while preserving legacy options."""
    if not _gh_authenticated():
        print('[sync] ERROR: GitHub CLI not authenticated (gh auth login).', file=sys.stderr)
        return 2
    lock_path = REPO_ROOT / cfg.lock_file
    if not args.no_lock:
        _acquire_lock(lock_path)
    try:
        # Defer to orchestrator (library) to perform sync & summary writing
        try:
            from issuesuite.orchestrator import sync_with_summary  # type: ignore
            summary = sync_with_summary(
                cfg,
                dry_run=args.dry_run,
                update=args.update,
                respect_status=args.respect_status,
                preflight=args.preflight,
                summary_path=args.summary_json,
            )
            print('[sync] Summary:', json.dumps(summary['totals'], sort_keys=True))
            print('[sync] Done.')
            return 0
        except Exception as e:  # pragma: no cover - fallback
            print(f'[sync] Fallback path due to orchestrator error: {e}')
            # Fall back to previous inline logic for resilience
            specs = _prepare_specs(cfg)
            _preflight_if_requested(cfg, specs, args)
            state_path = REPO_ROOT / cfg.hash_state_file
            mapping_path = REPO_ROOT / cfg.mapping_file
            prev_hashes = _load_previous_hashes(state_path)
            existing = _existing_issues()
            actions: Dict[str, List[Dict[str, Any]]] = {'created': [], 'updated': [], 'closed': []}
            mapping: Dict[str, int] = {}
            skipped = 0
            for spec in specs:
                skipped_flag = _process_single_spec(spec, existing, prev_hashes, actions, mapping, args, cfg)
                if skipped_flag:
                    skipped += 1
            _write_mapping_and_state(mapping_path, state_path, specs, mapping, args.dry_run)
            _write_summary(cfg, specs, actions['created'], actions['updated'], actions['closed'], skipped, args.dry_run, args.summary_json)
            print('[sync] Done (fallback).')
            return 0
    finally:
        if not args.no_lock:
            _release_lock(lock_path)


def cmd_export(cfg: SuiteConfig, args: argparse.Namespace) -> int:
    from export_issues_json import to_dict as export_to_dict  # reuse
    specs = parse_issues_md(cfg.source_file)
    data = [export_to_dict(s) for s in specs]
    path = Path(args.output or cfg.export_json)
    path.write_text(json.dumps(data, indent=2 if args.pretty else None) + ('\n' if args.pretty else ''))
    print(f'[export] Wrote {len(data)} issues -> {path}')
    return 0


def cmd_report(cfg: SuiteConfig, args: argparse.Namespace) -> int:
    # We reuse existing JSON export if present else generate ephemeral list
    export_path = Path(args.input or cfg.export_json)
    if not export_path.exists():
        print(f'[report] Export file not found, generating ephemeral export -> {export_path}')
        cmd_export(cfg, argparse.Namespace(output=str(export_path), pretty=True))
    from generate_issues_report import load_issues, compute_stats, render_html
    issues = load_issues(export_path)
    stats = compute_stats(issues)
    html_doc = render_html(issues, stats, title=args.title, top_labels=args.top_labels)
    out_path = Path(args.output or cfg.report_html)
    out_path.write_text(html_doc, encoding='utf-8')
    print(f'[report] Wrote HTML report -> {out_path}')
    return 0


def cmd_summary(cfg: SuiteConfig, _args: argparse.Namespace) -> int:
    specs = parse_issues_md(cfg.source_file)
    print(f'Total specs: {len(specs)}')
    for s in specs[:20]:  # show first 20 only
        print(f'  {s.external_id} {s.hash} {s.canonical_title[:60]}')
    if len(specs) > 20:
        print(f'  ... ({len(specs)-20} more)')
    return 0


def cmd_project_sync(cfg: SuiteConfig, _args: argparse.Namespace) -> int:  # type: ignore[override]
    if not cfg.project_enable:
        print('[project-sync] Project integration disabled in config (enable github.project.enable).')
        return 0
    print('[project-sync] Feature flagged on but implementation is pending. Returning non-zero to signal no-op to CI.')
    return 3


def _export_schema() -> Dict[str, Any]:
    return {
        '$schema': 'http://json-schema.org/draft-07/schema#',
        'title': 'IssueExport',
        'type': 'array',
        'items': {
            'type': 'object',
            'required': ['external_id','title','labels','hash','normalized_title'],
            'properties': {
                'external_id': {'type':'string'},
                'title': {'type':'string'},
                'canonical_title': {'type':'string'},
                'labels': {'type':'array','items':{'type':'string'}},
                'milestone': {'type':['string','null']},
                'flag': {'type':['string','null']},
                'priority': {'type':['string','null']},
                'status': {'type':['string','null']},
                'hash': {'type':'string'},
                'short_hash': {'type':'string'},
                'normalized_title': {'type':'string'},
                'body': {'type':'string'},
            }
        }
    }


def _summary_schema() -> Dict[str, Any]:
    return {
        '$schema': 'http://json-schema.org/draft-07/schema#',
        'title': 'IssueChangeSummary',
        'type': 'object',
        'required': ['schemaVersion','generated_at','dry_run','totals','changes'],
        'properties': {
            'schemaVersion': {'type':'integer'},
            'generated_at': {'type':'string'},
            'dry_run': {'type':'boolean'},
            'totals': {
                'type':'object',
                'required':['specs','created','updated','closed','skipped'],
                'properties': {k:{'type':'integer'} for k in ['specs','created','updated','closed','skipped']}
            },
            'changes': {
                'type':'object',
                'required':['created','updated','closed'],
                'properties': {
                    'created': {'type':'array','items':{'type':'object'}},
                    'updated': {'type':'array','items':{'type':'object'}},
                    'closed': {'type':'array','items':{'type':'object'}},
                }
            }
        }
    }


def cmd_schema(cfg: SuiteConfig, args: argparse.Namespace) -> int:  # type: ignore[override]
    export_schema = _export_schema()
    summary_schema = _summary_schema()
    if args.stdout:
        print(json.dumps({'export': export_schema, 'summary': summary_schema}, indent=2))
        return 0
    try:
        export_path = REPO_ROOT / cfg.schema_export_file
        summary_path = REPO_ROOT / cfg.schema_summary_file
        export_path.write_text(json.dumps(export_schema, indent=2) + '\n')
        summary_path.write_text(json.dumps(summary_schema, indent=2) + '\n')
        print(f'[schema] Wrote {export_path.name}, {summary_path.name}')
        return 0
    except Exception as e:  # pragma: no cover
        print(f'[schema] ERROR: {e}', file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description='Unified Issue Automation Suite')
    sub = p.add_subparsers(dest='cmd', required=True)

    pv = sub.add_parser('validate', help='Validate ISSUES.md structure')
    pv.add_argument('--strict', action='store_true')
    pv.add_argument('--skip-label-exists', action='store_true')
    pv.add_argument('--skip-milestone-exists', action='store_true')

    ps = sub.add_parser('sync', help='Sync issues to GitHub (create/update/close)')
    ps.add_argument('--update', action='store_true')
    ps.add_argument('--dry-run', action='store_true')
    ps.add_argument('--respect-status', action='store_true')
    ps.add_argument('--preflight', action='store_true')
    ps.add_argument('--no-lock', action='store_true')
    ps.add_argument('--summary-json', help='Path to write machine-readable change summary JSON')

    pe = sub.add_parser('export', help='Export issues to JSON')
    pe.add_argument('--output')
    pe.add_argument('--pretty', action='store_true')

    pr = sub.add_parser('report', help='Generate HTML report from export JSON')
    pr.add_argument('--input')
    pr.add_argument('--output')
    pr.add_argument('--title', default='Issue Roadmap Report')
    pr.add_argument('--top-labels', type=int, default=30)

    sub.add_parser('summary', help='Quick summary listing of parsed specs')
    # no options

    sub.add_parser('project-sync', help='Assign issues to GitHub Project (stub)')
    # placeholder arguments could be added later

    psc = sub.add_parser('schema', help='Emit JSON Schema files for AI tooling')
    psc.add_argument('--stdout', action='store_true', help='Print combined schemas to stdout')

    return p


def main(argv: Optional[List[str]] = None) -> int:  # pragma: no cover - top-level orchestrator
    try:
        cfg = load_config()
    except ConfigError as e:
        print(f'[config] ERROR: {e}', file=sys.stderr)
        return 2
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd == 'validate':
        return cmd_validate(cfg, args)
    if args.cmd == 'sync':
        # default dry-run if config sets it and flag not provided
        if not getattr(args, 'dry_run') and cfg.dry_run_default:
            args.dry_run = True  # type: ignore
        return cmd_sync(cfg, args)
    if args.cmd == 'export':
        return cmd_export(cfg, args)
    if args.cmd == 'report':
        return cmd_report(cfg, args)
    if args.cmd == 'summary':
        return cmd_summary(cfg, args)
    if args.cmd == 'project-sync':
        return cmd_project_sync(cfg, args)
    if args.cmd == 'schema':
        return cmd_schema(cfg, args)
    parser.print_help()
    return 1


if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main())
