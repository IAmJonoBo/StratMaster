#!/usr/bin/env python3
"""Shared utilities for roadmap issue management.

Provides:
- IssueSpec dataclass
- parse_issues_md() -> List[IssueSpec]
- normalization + hashing helpers
- label/milestone preflight utilities
"""
from __future__ import annotations
import re
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict
import subprocess
import json

ISSUES_MD = Path(__file__).resolve().parent.parent / 'ISSUES.md'
SECTION_RE = re.compile(r'^##\s+(\d{3})\s*\|\s*(.+)$')
TITLE_PREFIX_RE = re.compile(r'^issue\s+\d+:\s*', re.IGNORECASE)
BRACKET_TAG_RE = re.compile(r'^\[[^\]]+\]\s*')
WHITESPACE_RE = re.compile(r'\s+')

DEFAULT_REQUIRED_MILESTONES = [
    'Sprint 0: Mobilize & Baseline',
    'M1: Real-Time Foundation',
    'M2: Performance & Validation',
    'M3: Advanced Analytics'
]

LABEL_CANON_MAP = {
    'p0-critical': 'P0-critical',
    'p1-important': 'P1-important',
    'p2-enhancement': 'P2-enhancement',
}

@dataclass
class IssueSpec:
    external_id: str
    canonical_title: str
    labels: List[str]
    milestone: Optional[str]
    flag: Optional[str]
    priority: Optional[str]
    body: str
    status_hint: Optional[str] = None
    issue_number: Optional[int] = None
    hash: str = field(init=False)

    def __post_init__(self):
        self.hash = compute_issue_hash(self)

    @property
    def full_title(self) -> str:
        return f"Issue {self.external_id}: {self.canonical_title}"


def normalize_title(title: str) -> str:
    t = TITLE_PREFIX_RE.sub('', title).strip()
    t = BRACKET_TAG_RE.sub('', t).strip()
    t = WHITESPACE_RE.sub(' ', t)
    return t.lower()


def compute_issue_hash(spec: IssueSpec) -> str:
    h = hashlib.sha256()
    components = [
        spec.external_id,
        spec.canonical_title,
        ','.join(sorted(spec.labels)),
        spec.milestone or '',
        spec.flag or '',
        spec.priority or '',
        spec.body.strip(),
    ]
    h.update('\x1f'.join(components).encode('utf-8'))
    return h.hexdigest()[:16]


def parse_issues_md(path: Path = ISSUES_MD) -> List[IssueSpec]:
    text = path.read_text(encoding='utf-8')
    lines = text.splitlines()
    specs: List[IssueSpec] = []
    i = 0
    while i < len(lines):
        m = SECTION_RE.match(lines[i])
        if not m:
            i += 1
            continue
        external_id = m.group(1)
        canonical_title = m.group(2).strip()
        meta: Dict[str, str] = {}
        body_lines: List[str] = []
        i += 1
        while i < len(lines) and lines[i].strip() != '---':
            line = lines[i].strip()
            if ':' in line:
                k, v = line.split(':', 1)
                meta[k.strip().lower()] = v.strip()
            i += 1
        if i < len(lines) and lines[i].strip() == '---':
            i += 1
        while i < len(lines) and not lines[i].startswith('## '):
            body_lines.append(lines[i])
            i += 1
        labels = [l.strip() for l in meta.get('labels', '').split(',') if l.strip()]
        # Canonicalize priority labels
        normalized_labels = []
        for l in labels:
            key = l.lower()
            normalized_labels.append(LABEL_CANON_MAP.get(key, l))
        spec = IssueSpec(
            external_id=external_id,
            canonical_title=canonical_title,
            labels=normalized_labels,
            milestone=meta.get('milestone'),
            flag=meta.get('flag'),
            priority=meta.get('priority'),
            body='\n'.join(body_lines).strip() + '\n',
            status_hint=meta.get('status'),
        )
        specs.append(spec)
    return specs

# Preflight helpers

def run(cmd: List[str]) -> str:
    return subprocess.check_output(cmd, text=True)


def ensure_labels(labels: List[str]):
    existing = set()
    try:
        out = run(['gh', 'label', 'list', '--limit', '300', '--json', 'name', '--jq', '.[].name'])
        existing = set(out.strip().splitlines())
    except Exception:
        return
    for lbl in labels:
        if lbl not in existing:
            try:
                subprocess.check_call(['gh', 'label', 'create', lbl, '--color', 'ededed', '--description', 'Auto-created (issues_lib)'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass


def ensure_milestones(milestones: List[str]):
    try:
        out = run(['gh', 'api', 'repos/:owner/:repo/milestones', '--paginate', '--jq', '.[].title'])
        existing = set(out.strip().splitlines())
    except Exception:
        return
    for ms in milestones:
        if ms not in existing:
            try:
                subprocess.check_call(['gh', 'api', 'repos/:owner/:repo/milestones', '-f', f'title={ms}', '-f', 'description=Auto-created for V2 roadmap'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass


def collect_all_labels(specs: List[IssueSpec]) -> List[str]:
    all_labels = set()
    for s in specs:
        for l in s.labels:
            all_labels.add(l)
    return sorted(all_labels)
