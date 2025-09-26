#!/usr/bin/env python3
"""Generate mapping between feature flags and GitHub issues.

Outputs JSON file v2_issue_feature_flags.json with structure:
{
  "flags": { "ENABLE_COLLAB_LIVE": {"issues": [161, 172], "titles": [...] }, ... },
  "unmapped_issues": [...]
}

Detection heuristics:
- Parses local create_github_issues.sh for flag names within each issue body segment.
- Fetches live issues via `gh issue list --limit 500 --json number,title,body` if gh is available & authed.
- Scans bodies for backticked or plain occurrences of flag names.
- Consolidates deduplicated mapping.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / 'create_github_issues.sh'
OUTPUT_PATH = REPO_ROOT / 'v2_issue_feature_flags.json'

FLAG_PATTERN = re.compile(r'ENABLE_[A-Z0-9_]+')

# Optionally extend known flags (in case not all are present in script bodies)
KNOWN_FLAGS = [
    'ENABLE_COLLAB_LIVE',
    'ENABLE_MODEL_RECOMMENDER_V2',
    'ENABLE_RETRIEVAL_BENCHMARKS',
    'ENABLE_RESPONSE_CACHE_V2',
    'ENABLE_EDGE_CACHE_HINTS',
    'ENABLE_PREDICTIVE_ANALYTICS',
    'ENABLE_EVENT_STREAMING',
    'ENABLE_INDUSTRY_TEMPLATES',
    'ENABLE_CUSTOM_FINE_TUNING',
    'ENABLE_KNOWLEDGE_REASONING',
    'ENABLE_LIGHTHOUSE_CI'
]

TITLE_PREFIX_RE = re.compile(r'^Issue\s+\d+:\s*', re.IGNORECASE)
BRACKET_TAG_RE = re.compile(r'^\[[^\]]+\]\s*')


def normalize_title(title: str) -> str:
        """Normalize a title by stripping numeric issue prefix and leading bracket tags.

        Example:
            'Issue 001: Real-Time Collaboration Engine' -> 'real-time collaboration engine'
            '[IMPL] Real-Time Collaboration Engine' -> 'real-time collaboration engine'
        """
        t = TITLE_PREFIX_RE.sub('', title).strip()
        t = BRACKET_TAG_RE.sub('', t).strip()
        t = re.sub(r'\s+', ' ', t)
        return t.lower()


def load_script_issue_sections() -> list[str]:
    if not SCRIPT_PATH.exists():
        return []
    text = SCRIPT_PATH.read_text(encoding='utf-8', errors='ignore')
    # Split on marker for each issue body heredoc start
    sections = re.split(r'# Issue \d+:', text)
    return sections[1:]  # first chunk preamble


def extract_flags_from_text(text: str) -> set[str]:
    found = set(FLAG_PATTERN.findall(text))
    for f in KNOWN_FLAGS:
        if f in text:
            found.add(f)
    return found


def gh_json(cmd: list[str]):
    try:
        out = subprocess.check_output(cmd, text=True)
        return json.loads(out)
    except Exception:
        return []


def fetch_live_issues():
    # Check gh availability
    try:
        subprocess.check_call(
            ['gh', 'auth', 'status'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return []
    return gh_json([
        'gh', 'issue', 'list', '--state', 'all', '--limit', '500',
        '--json', 'number,title,body'
    ])


def main():
    mapping = init_mapping()
    populate_from_script(mapping)
    live_issues = correlate_live(mapping)
    unmapped = compute_unmapped(mapping, live_issues)
    write_output(mapping, unmapped)


def init_mapping() -> dict[str, dict[str, list]]:
    return {flag: {"issues": [], "titles": [], "normalized_titles": []} for flag in KNOWN_FLAGS}


def populate_from_script(mapping: dict[str, dict[str, list]]):
    for section in load_script_issue_sections():
        flags = extract_flags_from_text(section)
        title_match = re.search(r'Issue 0?\d+:[^\n]+', section)
        title = title_match.group(0).strip() if title_match else None
        if not title:
            continue
        for flag in flags:
            titles = mapping[flag]["titles"]
            if title not in titles:
                titles.append(title)
                norm = normalize_title(title)
                nlist = mapping[flag]["normalized_titles"]
                if norm not in nlist:
                    nlist.append(norm)


def correlate_live(mapping: dict[str, dict[str, list]]):
    issues = fetch_live_issues()
    for issue in issues:
        body = issue.get('body') or ''
        flags = extract_flags_from_text(body)
        for flag in flags:
            data = mapping[flag]
            if issue['number'] not in data['issues']:
                data['issues'].append(issue['number'])
            if issue['title'] not in data['titles']:
                data['titles'].append(issue['title'])
                norm = normalize_title(issue['title'])
                if norm not in data['normalized_titles']:
                    data['normalized_titles'].append(norm)
    return issues


def compute_unmapped(mapping: dict[str, dict[str, list]], live_issues):
    all_issue_numbers = {i['number'] for i in live_issues}
    mapped_numbers = {n for v in mapping.values() for n in v['issues']}
    return sorted(all_issue_numbers - mapped_numbers)


def write_output(mapping: dict[str, dict[str, list]], unmapped: list[int]):
    output = {
        'flags': mapping,
        'unmapped_issues': unmapped,
        'generated_from': 'generate_issue_feature_index.py',
    }
    OUTPUT_PATH.write_text(json.dumps(output, indent=2) + '\n')
    covered = sum(1 for v in mapping.values() if v['issues'])
    print(f"✅ Generated feature flag issue index: {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    print(f"   Flags covered: {covered}/{len(mapping)}")
    if unmapped:
        print(f"   Unmapped issues (no flag refs): {unmapped}")

if __name__ == '__main__':
    main()
