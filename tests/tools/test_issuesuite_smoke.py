import os
import importlib.util
import subprocess
import sys
import shutil
import pytest

CONFIG_PATH = os.path.join(os.getcwd(), 'issue_suite.config.yaml')

@pytest.mark.skipif(not os.path.exists(CONFIG_PATH), reason='issue_suite.config.yaml missing')
def test_issuesuite_validate_smoke():
    """Lightweight smoke test: validate + summary in mock mode.

    Skips if issuesuite is not installed; installation is handled by workflows or
    `make issuesuite.install` locally. This avoids forcing the dependency into the
    core runtime environment.
    """
    if importlib.util.find_spec('issuesuite') is None:
        pytest.skip('issuesuite not installed (run make issuesuite.install)')

    env = os.environ.copy()
    env['ISSUES_SUITE_MOCK'] = '1'

    # Validate structure
    r = subprocess.run([sys.executable, '-m', 'issuesuite.cli', 'validate', '--config', CONFIG_PATH], capture_output=True, text=True, env=env)
    assert r.returncode == 0, f"validate failed: stdout={r.stdout}\nstderr={r.stderr}"

    # Summary (limit purposely omitted; expecting at least header lines)
    r2 = subprocess.run([sys.executable, '-m', 'issuesuite.cli', 'summary', '--config', CONFIG_PATH], capture_output=True, text=True, env=env)
    assert r2.returncode == 0, f"summary failed: stdout={r2.stdout}\nstderr={r2.stderr}"
    assert 'IssueSuite' not in r2.stderr, 'Unexpected errors in summary'
    assert len(r2.stdout.strip()) > 0, 'Empty summary output'
