"""CLI entrypoint for evals MCP."""

from __future__ import annotations

import argparse

import uvicorn

from .app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Evals MCP server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8084)
    args = parser.parse_args()

    uvicorn.run(create_app, host=args.host, port=args.port, factory=True)


if __name__ == "__main__":
    main()
