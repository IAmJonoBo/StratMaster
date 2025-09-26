from pathlib import Path
import textwrap
import sys

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / 'scripts'
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:  # pragma: no cover - import path guard
    import issues_lib  # type: ignore  # noqa: E402
except ModuleNotFoundError as e:  # pragma: no cover
    raise AssertionError(f"issues_lib not found on sys.path: {sys.path}") from e


ISSUES_SNIPPET = textwrap.dedent(
    """
    ## 001 | First Feature
    labels: area:core, type:feature
    milestone: Alpha
    priority: P1
    ---
    Body A line 1\nBody A line 2

    ## 002 | Second Feature
    labels: area:core, type:enhancement
    milestone: Alpha
    priority: P2
    ---
    Body B
    """.strip()
)


def write_issues(tmp_path: Path, content: str):
    (tmp_path / 'ISSUES.md').write_text(content, encoding='utf-8')
    return tmp_path / 'ISSUES.md'


def test_parse_issues_md_basic(tmp_path, monkeypatch):
    write_issues(tmp_path, ISSUES_SNIPPET)
    # Monkeypatch repo root resolution in issues_lib if it uses relative path (it expects caller to read file directly)
    specs = issues_lib.parse_issues_md(path=tmp_path / 'ISSUES.md')
    assert len(specs) == 2
    first = specs[0]
    assert first.external_id == '001'
    assert 'First Feature' in first.full_title
    assert 'area:core' in first.labels
    assert first.body.endswith('Body A line 2\n')


def test_hash_changes_with_body(tmp_path):
    write_issues(tmp_path, ISSUES_SNIPPET)
    specs1 = issues_lib.parse_issues_md(path=tmp_path / 'ISSUES.md')
    h1 = specs1[0].hash
    # Modify body
    modified = ISSUES_SNIPPET.replace('Body A line 2', 'Body A line TWO!')
    write_issues(tmp_path, modified)
    specs2 = issues_lib.parse_issues_md(path=tmp_path / 'ISSUES.md')
    h2 = specs2[0].hash
    assert h1 != h2, 'Hash should change when body content changes'


def test_normalize_title_edge_cases():
    norm = issues_lib.normalize_title
    assert norm('Issue 001: My  Title  !!') == norm('issue 001: my title')
    assert norm('[CORE]  Fancy - Title') == norm('core fancy title')


def test_compute_issue_hash_stability(tmp_path):
    write_issues(tmp_path, ISSUES_SNIPPET)
    specs = issues_lib.parse_issues_md(path=tmp_path / 'ISSUES.md')
    h_again = issues_lib.compute_issue_hash(specs[0])[:12]
    assert specs[0].hash.startswith(h_again[:12])
