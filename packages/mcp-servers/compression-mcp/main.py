"""compression-mcp entrypoint.
Starts the FastAPI application that exposes LLMLingua compression tools."""

from __future__ import annotations

import argparse

import uvicorn


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="compression-mcp", description="Compression MCP server"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host interface to bind",
    )
    parser.add_argument("--port", type=int, default=8005, help="Port to listen on")
    parser.add_argument(
        "--reload", action="store_true", help="Enable autoreload (development only)"
    )
    args = parser.parse_args(argv)

    uvicorn.run(
        "compression_mcp.app:create_app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        factory=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
