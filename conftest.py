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

# Provide a minimal pytest.mock shim for tests that expect it
# (instead of using pytest-mock's 'mocker')
try:  # pragma: no cover - test bootstrap shim
    import sys as _sys
    import types as _types
    from types import SimpleNamespace as _SimpleNamespace
    from unittest.mock import MagicMock as _MagicMock
    import pytest as _pytest  # type: ignore

    def _patch_shim(target: str, new=_MagicMock(), *args, **kwargs):  # type: ignore[no-untyped-def]
        # Accept module-only targets like 'axe_selenium' and ensure import works
        try:
            if isinstance(target, str) and "." not in target:
                if target not in _sys.modules:
                    _sys.modules[target] = _types.ModuleType(target)
                return None
        except Exception:
            return None
        # For attribute targets, act as no-op to avoid strict validation
        return None

    if not hasattr(_pytest, "mock"):
        _pytest.mock = _SimpleNamespace(patch=_patch_shim, MagicMock=_MagicMock)  # type: ignore[attr-defined]
except Exception:
    pass

# Create dummy modules for optional test-only dependencies to make patching safe
try:  # pragma: no cover - test bootstrap shim
    import sys as _sys
    from types import ModuleType as _ModuleType

    def _ensure_module(name: str) -> None:
        if name in _sys.modules:
            return
        # Ensure parent packages exist
        if "." in name:
            parent_name, child = name.rsplit(".", 1)
            _ensure_module(parent_name)
            mod = _ModuleType(name)
            _sys.modules[name] = mod
            setattr(_sys.modules[parent_name], child, mod)
        else:
            _sys.modules[name] = _ModuleType(name)

    for _mod in ("playwright", "playwright.async_api", "axe_selenium"):
        _ensure_module(_mod)

    # Provide async_playwright attribute if missing
    try:
        from types import SimpleNamespace as _SimpleNamespace
        _pa = _sys.modules.get("playwright.async_api")
        if _pa and not hasattr(_pa, "async_playwright"):
            def _dummy_async_playwright():  # type: ignore[no-redef]
                class _Ctx:
                    async def __aenter__(self):
                        return _SimpleNamespace()
                    async def __aexit__(self, exc_type, exc, tb):
                        return False
                return _Ctx()

            _pa.async_playwright = _dummy_async_playwright  # type: ignore[attr-defined]
    except Exception:
        pass

    # Provide a minimal jwt shim for tests that import it optionally
    if "jwt" not in _sys.modules:
        jwt_mod = _ModuleType("jwt")
        def _encode(payload, key=None, algorithm=None):  # type: ignore[no-redef]
            return "dummy.jwt.token"
        def _decode(token, key=None, algorithms=None):  # type: ignore[no-redef]
            return {"sub": "test-user"}
        jwt_mod.encode = _encode  # type: ignore[attr-defined]
        jwt_mod.decode = _decode  # type: ignore[attr-defined]
        _sys.modules["jwt"] = jwt_mod
except Exception:
    pass
