"""compression-mcp stub entrypoint.
Exposes LLMLingua-based prompt compression via MCP tools.
"""

import argparse


def main():
    parser = argparse.ArgumentParser(
        prog="compression-mcp", description="Compression MCP server (stub)"
    )
    parser.add_argument("--port", type=int, default=8005, help="Port to listen on")
    args = parser.parse_args()
    print(
        f"[compression-mcp] Stub server would start on port {args.port} "
        "(TODO[COMP-502]: replace with FastAPI app; see docs/backlog.md#todo-comp-502-compression-mcp-server-implementation)"
    )


if __name__ == "__main__":
    main()
