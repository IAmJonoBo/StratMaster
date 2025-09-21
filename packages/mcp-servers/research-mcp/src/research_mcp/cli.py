"""Command-line interface for launching the Research MCP server."""

from __future__ import annotations

import argparse
import os
from typing import Any, Sequence

import uvicorn

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8081
LOG_LEVEL_CHOICES = ("critical", "error", "warning", "info", "debug", "trace")
_TRUE_VALUES = {"1", "true", "t", "yes", "y", "on"}


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in _TRUE_VALUES


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError as exc:  # pragma: no cover - defensive branch
        raise SystemExit(
            f"Environment variable {name} must be an integer, got {value!r}"
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    """Return the CLI argument parser used by :func:`main`."""

    parser = argparse.ArgumentParser(
        prog="research-mcp",
        description="Run the Research MCP FastAPI application.",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("RESEARCH_MCP_HOST", DEFAULT_HOST),
        help="Host interface to bind (default: %(default)s).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=_env_int("RESEARCH_MCP_PORT", DEFAULT_PORT),
        help="Port to bind (default: %(default)s).",
    )
    parser.add_argument(
        "--reload",
        dest="reload",
        action="store_true",
        help="Enable autoreload. Use for local development only.",
    )
    parser.add_argument(
        "--no-reload",
        dest="reload",
        action="store_false",
        help="Disable autoreload (default).",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("RESEARCH_MCP_LOG_LEVEL", "info"),
        choices=LOG_LEVEL_CHOICES,
        help="Log level for uvicorn (default: %(default)s).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=_env_int("RESEARCH_MCP_WORKERS", 1),
        help="Number of worker processes. Ignored when reload is enabled.",
    )
    parser.add_argument(
        "--proxy-headers",
        dest="proxy_headers",
        action="store_true",
        help="Enable proxy headers support (X-Forwarded-For, etc.).",
    )
    parser.add_argument(
        "--no-proxy-headers",
        dest="proxy_headers",
        action="store_false",
        help="Disable proxy headers (default).",
    )
    parser.add_argument(
        "--root-path",
        default=os.getenv("RESEARCH_MCP_ROOT_PATH"),
        help="ASGI root_path when served behind a reverse proxy.",
    )
    parser.set_defaults(
        reload=_env_flag("RESEARCH_MCP_RELOAD", False),
        proxy_headers=_env_flag("RESEARCH_MCP_PROXY_HEADERS", False),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Parse CLI arguments and start the uvicorn server."""

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.workers < 1:
        parser.error("--workers must be >= 1")

    uvicorn_kwargs: dict[str, Any] = {
        "factory": True,
        "host": args.host,
        "port": args.port,
        "reload": args.reload,
        "log_level": args.log_level,
        "proxy_headers": args.proxy_headers,
    }

    if args.root_path:
        uvicorn_kwargs["root_path"] = args.root_path

    if not args.reload and args.workers > 1:
        uvicorn_kwargs["workers"] = args.workers

    uvicorn.run("research_mcp.app:create_app", **uvicorn_kwargs)


__all__ = ["build_parser", "main"]

