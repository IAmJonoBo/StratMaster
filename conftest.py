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
    try:
        # Register asyncio marker to silence warnings when pytest-asyncio isn't installed
        import pytest  # type: ignore

        if hasattr(pytest, "config"):
            # Legacy guard; modern pytest passes config param
            pass
        # Add marker description for documentation and to avoid warnings
        try:
            config.addinivalue_line(  # type: ignore[attr-defined]
                "markers", "asyncio: mark a test as asyncio-based"
            )
        except Exception:
            pass
    except Exception:
        pass

    # Provide pytest.mock compatibility if pytest-mock plugin isn't installed
    try:
        import pytest  # type: ignore
        import sys as _sys
        import unittest.mock as _umock

        if not hasattr(pytest, "mock"):
            class _ModulePatcher:
                """Context-manager patcher for module-only targets.

                Mimics unittest.mock.patch for cases like pytest.mock.patch('mod').
                """

                def __init__(self, name: str, replacement=None) -> None:
                    self._name = name
                    self._replacement = replacement or _umock.MagicMock()
                    self._had_prev = name in _sys.modules
                    self._prev = _sys.modules.get(name)

                def start(self):
                    _sys.modules[self._name] = self._replacement
                    return self._replacement

                def stop(self):
                    if self._had_prev:
                        _sys.modules[self._name] = self._prev  # type: ignore[assignment]
                    else:
                        _sys.modules.pop(self._name, None)

                def __enter__(self):
                    return self.start()

                def __exit__(self, exc_type, exc, tb):
                    self.stop()
                    return False

            class _CompatMock:
                """Minimal shim to satisfy tests using pytest.mock.patch(...)."""

                def patch(self, target: str, replacement=None):  # type: ignore[override]
                    # Support module-only targets by injecting into sys.modules with context manager
                    if "." not in target:
                        return _ModulePatcher(target, replacement)

                    # Delegate to unittest.mock.patch (context manager / decorator)
                    return (
                        _umock.patch(target, replacement)
                        if replacement is not None
                        else _umock.patch(target)
                    )

            pytest.mock = _CompatMock()  # type: ignore[attr-defined]

    except Exception:
        # Safe to ignore; tests that rely on pytest.mock may fail explicitly
        pass

    # Provide a minimal stub for Playwright if it's not installed, so tests can patch
    # 'playwright.async_api.async_playwright' without ModuleNotFoundError.
    try:
        import sys as _sys
        if "playwright" not in _sys.modules:
            import types as _types
            _playwright = _types.ModuleType("playwright")
            _async_api = _types.ModuleType("playwright.async_api")

            # Placeholder async_playwright factory; tests will patch over this.
            # Must be a regular function (not async) because Playwright's real
            # async_playwright() returns an async context manager, not a coroutine.
            def _async_playwright():  # type: ignore
                class _Stub:
                    async def __aenter__(self):  # pragma: no cover - defensive
                        raise RuntimeError(
                            "Playwright stub invoked; tests should patch this function."
                        )

                    async def __aexit__(self, exc_type, exc, tb):  # pragma: no cover
                        return False

                return _Stub()

            _async_api.async_playwright = _async_playwright  # type: ignore[attr-defined]
            _playwright.async_api = _async_api  # type: ignore[attr-defined]
            _sys.modules["playwright"] = _playwright
            _sys.modules["playwright.async_api"] = _async_api
    except Exception:
        pass


def pytest_pyfunc_call(pyfuncitem):  # pragma: no cover - pytest hook
    """Lightweight async support when pytest-asyncio isn't available.

    If the test function is an `async def`, run it with asyncio.run(...).
    Return True to indicate the call was handled.
    """
    # If pytest-asyncio is available, let it handle async tests
    try:
        import pytest_asyncio  # type: ignore  # noqa: F401
        return False
    except Exception:
        pass

    import asyncio
    import inspect

    func = pyfuncitem.obj
    if inspect.iscoroutinefunction(func):
        # Build kwargs from resolved fixtures
        try:
            argnames = list(getattr(pyfuncitem._fixtureinfo, "argnames", []) or [])
        except Exception:
            argnames = []
        kwargs = {
            name: pyfuncitem.funcargs[name]
            for name in argnames
            if name in pyfuncitem.funcargs
        }
        asyncio.run(func(**kwargs))
        return True
    return False
