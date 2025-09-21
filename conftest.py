"""Pytest configuration ensuring package src directories are importable."""

from __future__ import annotations

import sys
from pathlib import Path


def _add_to_path(path: Path) -> None:
    if path.is_dir():
        resolved = str(path)
        if resolved not in sys.path:
            sys.path.insert(0, resolved)


def _bootstrap_sys_path() -> None:
    root = Path(__file__).resolve().parent
    for pattern in ("packages/**/src", "apps/**/src"):
        for src in root.glob(pattern):
            _add_to_path(src)


_bootstrap_sys_path()


def pytest_configure(config: object) -> None:  # pragma: no cover - pytest hook
    _bootstrap_sys_path()
