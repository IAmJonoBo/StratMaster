from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.dependency_sync import diff_packages, run


def write_freeze(tmp_path: Path, content: str) -> Path:
    freeze = tmp_path / "freeze.txt"
    freeze.write_text(content)
    return freeze


def test_diff_packages_detects_drift() -> None:
    local = {"fastapi": "0.116.0", "uvicorn": "0.37.0", "numpy": "1.0.0"}
    remote = {"fastapi": "0.117.1", "httpx": "0.28.1", "uvicorn": "0.37.0"}

    diff = diff_packages(local, remote)
    assert diff.missing_local == {"httpx": "0.28.1"}
    assert diff.version_mismatch == {"fastapi": ("0.116.0", "0.117.1")}
    assert diff.extra_local == {"numpy": "1.0.0"}


def test_run_uses_freeze_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    remote = tmp_path / "remote.json"
    remote.write_text(json.dumps({
        "packages": [
            {"name": "fastapi", "version": "0.117.1"},
            {"name": "uvicorn", "version": "0.37.0"}
        ]
    }))

    freeze = write_freeze(tmp_path, "fastapi==0.117.1\nuvicorn==0.37.0\n")
    rc = run(["status", "--remote", str(remote), "--freeze", str(freeze), "--json"])
    assert rc == 0

    freeze2 = write_freeze(tmp_path, "fastapi==0.116.0\n")
    rc2 = run(["sync", "--remote", str(remote), "--freeze", str(freeze2), "--json"])
    assert rc2 == 1
