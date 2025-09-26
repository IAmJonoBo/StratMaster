import subprocess
from pathlib import Path
import textwrap
import sys
import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / 'scripts'
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


VALID = textwrap.dedent(
    """
    ## 010 | Alpha
    labels: area:alpha
    milestone: M1
    ---
    Alpha body

    ## 011 | Beta
    labels: area:beta
    milestone: M1
    ---
    Beta body
    """.strip()
)

MISSING_LABELS = textwrap.dedent(
    """
    ## 020 | No Labels
    milestone: M1
    ---
    Body
    """.strip()
)


def run_validator(tmp_path: Path, content: str):
    issues = tmp_path / 'ISSUES.md'
    issues.write_text(content, encoding='utf-8')
    script = Path('scripts/validate_issues_source.py').resolve()
    cmd = [sys.executable, str(script), '--skip-label-exists', '--skip-milestone-exists']
    proc = subprocess.run(cmd, cwd=tmp_path, capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def test_validator_ok(tmp_path):
    code, out = run_validator(tmp_path, VALID)
    assert code == 0, out
    assert 'Hash Preview:' in out


def test_validator_detects_missing_labels(tmp_path):
    code, out = run_validator(tmp_path, MISSING_LABELS)
    assert code == 1
    assert 'missing labels' in out.lower()
