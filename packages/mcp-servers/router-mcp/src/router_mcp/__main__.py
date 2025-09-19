"""CLI entrypoint for router MCP."""

from __future__ import annotations

import argparse

import uvicorn

from .app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Router MCP server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8083)
    args = parser.parse_args()

    uvicorn.run(create_app, host=args.host, port=args.port, factory=True)


if __name__ == "__main__":
    main()
