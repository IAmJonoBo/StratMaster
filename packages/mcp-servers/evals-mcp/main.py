"""evals-mcp stub entrypoint.
TODO: Implement MCP server with tool: evals.run.
"""

import argparse


def main():
    parser = argparse.ArgumentParser(
        prog="evals-mcp", description="Evals MCP server (stub)"
    )
    parser.add_argument("--port", type=int, default=8003, help="Port to listen on")
    args = parser.parse_args()
    print(f"[evals-mcp] Stub server would start on port {args.port} (TODO)")


if __name__ == "__main__":
    main()
