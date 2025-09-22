"""CLI entrypoint for the knowledge MCP server."""

from __future__ import annotations

import argparse

import uvicorn

from .app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Knowledge MCP server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8082, help="Port to bind")
    args = parser.parse_args()

    uvicorn.run(create_app, host=args.host, port=args.port, factory=True)


if __name__ == "__main__":
    main()
