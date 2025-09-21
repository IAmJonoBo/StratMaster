"""Command-line interface for launching the Research MCP server."""

from __future__ import annotations

import argparse
import os
from typing import Any, Iterable, Sequence

import uvicorn

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8081
LOG_LEVEL_CHOICES = ("critical", "error", "warning", "info", "debug", "trace")
_TRUE_VALUES = {"1", "true", "t", "yes", "y", "on"}
_DEFAULT_ALLOWLIST = ("example.com",)


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


def _env_list(name: str, default: Iterable[str]) -> list[str]:
    value = os.getenv(name)
    if value is None:
        return [item for item in default]
    return _split_domains([value])


def _split_domains(values: Iterable[str]) -> list[str]:
    domains: list[str] = []
    for value in values:
        for part in value.split(","):
            part = part.strip()
            if part:
                domains.append(part)
    return domains


def _format_domains(domains: Iterable[str]) -> str:
    return ",".join(domains)


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
        enable_network=_env_flag("RESEARCH_MCP_ENABLE_NETWORK", False),
        use_playwright=_env_flag("RESEARCH_MCP_USE_PLAYWRIGHT", False),
    )

    service_group = parser.add_argument_group(
        "service options",
        "Configure Research MCP integrations (applied via environment variables).",
    )
    service_group.add_argument(
        "--allowlist",
        action="append",
        metavar="DOMAIN[,DOMAIN...]",
        help=(
            "Allowed domains for crawling. Provide multiple times or comma-separated. "
            f"Defaults to environment or {', '.join(_DEFAULT_ALLOWLIST)}."
        ),
    )
    service_group.add_argument(
        "--blocklist",
        action="append",
        metavar="DOMAIN[,DOMAIN...]",
        help="Blocked domains for crawling. Provide multiple times or comma-separated.",
    )
    service_group.add_argument(
        "--enable-network",
        dest="enable_network",
        action="store_true",
        help="Allow outbound network requests for metasearch/crawling.",
    )
    service_group.add_argument(
        "--disable-network",
        dest="enable_network",
        action="store_false",
        help="Disable outbound network requests (default).",
    )
    service_group.add_argument(
        "--use-playwright",
        dest="use_playwright",
        action="store_true",
        help="Enable Playwright rendering when crawling (requires network access).",
    )
    service_group.add_argument(
        "--no-playwright",
        dest="use_playwright",
        action="store_false",
        help="Disable Playwright rendering (default).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Parse CLI arguments and start the uvicorn server."""

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.workers < 1:
        parser.error("--workers must be >= 1")

    allowlist = (
        _split_domains(args.allowlist)
        if args.allowlist
        else _env_list("RESEARCH_MCP_ALLOWLIST", _DEFAULT_ALLOWLIST)
    )
    blocklist = (
        _split_domains(args.blocklist)
        if args.blocklist
        else _env_list("RESEARCH_MCP_BLOCKLIST", ())
    )
    os.environ["RESEARCH_MCP_ALLOWLIST"] = _format_domains(allowlist)
    os.environ["RESEARCH_MCP_BLOCKLIST"] = _format_domains(blocklist)
    os.environ["RESEARCH_MCP_ENABLE_NETWORK"] = "1" if args.enable_network else "0"
    os.environ["RESEARCH_MCP_USE_PLAYWRIGHT"] = "1" if args.use_playwright else "0"

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

