from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.issuesuite_bridge import IssueSuiteBridge


def _write_minimal_config(tmp_path: Path) -> Path:
    cfg = tmp_path / "issue_suite.config.yaml"
    cfg.write_text("version: 1\nsource:\n  file: ISSUES.md\n")
    return cfg


def test_bridge_requires_config(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        IssueSuiteBridge(tmp_path / "missing.yaml")


def test_bridge_runs_validate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cfg = _write_minimal_config(tmp_path)
    captured: dict[str, object] = {}

    def fake_runner(cmd, env):
        captured["cmd"] = cmd
        captured["env"] = env
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    bridge = IssueSuiteBridge(cfg, mock_mode=True, runner=fake_runner)
    monkeypatch.setattr(IssueSuiteBridge, "is_installed", staticmethod(lambda: True))

    result = bridge.validate()
    assert result.ok
    assert "--config" in captured["cmd"]
    env = captured["env"]
    assert isinstance(env, dict)
    assert env.get("ISSUES_SUITE_MOCK") == "1"


def test_bridge_raises_when_missing_dependency(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cfg = _write_minimal_config(tmp_path)
    bridge = IssueSuiteBridge(cfg)
    monkeypatch.setattr(IssueSuiteBridge, "is_installed", staticmethod(lambda: False))

    with pytest.raises(RuntimeError):
        bridge.summary()
