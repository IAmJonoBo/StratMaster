from __future__ import annotations

import os

import pytest
from research_mcp import cli


def _clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "RESEARCH_MCP_HOST",
        "RESEARCH_MCP_PORT",
        "RESEARCH_MCP_RELOAD",
        "RESEARCH_MCP_LOG_LEVEL",
        "RESEARCH_MCP_WORKERS",
        "RESEARCH_MCP_PROXY_HEADERS",
        "RESEARCH_MCP_ROOT_PATH",
        "RESEARCH_MCP_ALLOWLIST",
        "RESEARCH_MCP_BLOCKLIST",
        "RESEARCH_MCP_ENABLE_NETWORK",
        "RESEARCH_MCP_USE_PLAYWRIGHT",
    ):
        monkeypatch.delenv(name, raising=False)


def _capture_uvicorn(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    captured: dict[str, object] = {}

    def fake_run(app: str, **kwargs: object) -> None:
        captured["app"] = app
        captured["kwargs"] = kwargs

    monkeypatch.setattr(cli.uvicorn, "run", fake_run)
    return captured


def test_main_invokes_uvicorn_with_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_env(monkeypatch)
    captured = _capture_uvicorn(monkeypatch)

    cli.main([])

    assert captured["app"] == "research_mcp.app:create_app"
    kwargs = captured["kwargs"]
    assert kwargs["host"] == "0.0.0.0"
    assert kwargs["port"] == 8081
    assert kwargs["reload"] is False
    assert kwargs["log_level"] == "info"
    assert kwargs["proxy_headers"] is False
    assert "workers" not in kwargs
    assert "root_path" not in kwargs


def test_cli_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_env(monkeypatch)
    captured = _capture_uvicorn(monkeypatch)

    cli.main(
        [
            "--host",
            "127.0.0.1",
            "--port",
            "9000",
            "--reload",
            "--log-level",
            "debug",
            "--workers",
            "4",
            "--proxy-headers",
            "--root-path",
            "/mcp",
        ]
    )

    kwargs = captured["kwargs"]
    assert kwargs["host"] == "127.0.0.1"
    assert kwargs["port"] == 9000
    assert kwargs["reload"] is True
    assert kwargs["log_level"] == "debug"
    assert kwargs["proxy_headers"] is True
    assert kwargs["root_path"] == "/mcp"
    # workers are ignored when reload is enabled
    assert "workers" not in kwargs


def test_cli_uses_environment_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("RESEARCH_MCP_HOST", "127.0.0.2")
    monkeypatch.setenv("RESEARCH_MCP_PORT", "9100")
    monkeypatch.setenv("RESEARCH_MCP_RELOAD", "true")
    monkeypatch.setenv("RESEARCH_MCP_LOG_LEVEL", "warning")
    monkeypatch.setenv("RESEARCH_MCP_WORKERS", "2")
    monkeypatch.setenv("RESEARCH_MCP_PROXY_HEADERS", "1")
    monkeypatch.setenv("RESEARCH_MCP_ROOT_PATH", "/prefix")
    monkeypatch.setenv("RESEARCH_MCP_ALLOWLIST", "example.com,acme.com")
    monkeypatch.setenv("RESEARCH_MCP_BLOCKLIST", "evil.invalid")
    monkeypatch.setenv("RESEARCH_MCP_ENABLE_NETWORK", "1")
    monkeypatch.setenv("RESEARCH_MCP_USE_PLAYWRIGHT", "1")
    captured = _capture_uvicorn(monkeypatch)

    cli.main([])

    kwargs = captured["kwargs"]
    assert kwargs["host"] == "127.0.0.2"
    assert kwargs["port"] == 9100
    assert kwargs["reload"] is True
    assert kwargs["log_level"] == "warning"
    assert kwargs["proxy_headers"] is True
    assert kwargs["root_path"] == "/prefix"
    assert "workers" not in kwargs
    assert os.environ["RESEARCH_MCP_ALLOWLIST"] == "example.com,acme.com"
    assert os.environ["RESEARCH_MCP_BLOCKLIST"] == "evil.invalid"
    assert os.environ["RESEARCH_MCP_ENABLE_NETWORK"] == "1"
    assert os.environ["RESEARCH_MCP_USE_PLAYWRIGHT"] == "1"


def test_cli_sets_workers_when_reload_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_env(monkeypatch)
    captured = _capture_uvicorn(monkeypatch)

    cli.main(["--workers", "3", "--no-reload"])

    kwargs = captured["kwargs"]
    assert kwargs["reload"] is False
    assert kwargs["workers"] == 3


def test_cli_sets_service_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_env(monkeypatch)
    captured = _capture_uvicorn(monkeypatch)

    cli.main(
        [
            "--allowlist",
            "example.com",
            "--allowlist",
            "acme.com,news.example",
            "--blocklist",
            "tracker.example",
            "--enable-network",
            "--use-playwright",
        ]
    )

    assert os.environ["RESEARCH_MCP_ALLOWLIST"] == "example.com,acme.com,news.example"
    assert os.environ["RESEARCH_MCP_BLOCKLIST"] == "tracker.example"
    assert os.environ["RESEARCH_MCP_ENABLE_NETWORK"] == "1"
    assert os.environ["RESEARCH_MCP_USE_PLAYWRIGHT"] == "1"

    kwargs = captured["kwargs"]
    assert kwargs["proxy_headers"] is False


def test_cli_can_disable_network(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("RESEARCH_MCP_ENABLE_NETWORK", "1")
    monkeypatch.setenv("RESEARCH_MCP_USE_PLAYWRIGHT", "1")
    captured = _capture_uvicorn(monkeypatch)

    cli.main(["--disable-network", "--no-playwright"])

    assert os.environ["RESEARCH_MCP_ENABLE_NETWORK"] == "0"
    assert os.environ["RESEARCH_MCP_USE_PLAYWRIGHT"] == "0"

    kwargs = captured["kwargs"]
    assert kwargs["reload"] is False
