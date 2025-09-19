"""router-mcp stub entrypoint.
TODO: Implement MCP server with provider shims and policy enforcement.
"""

import argparse


def main():
    parser = argparse.ArgumentParser(
        prog="router-mcp", description="Router MCP server (stub)"
    )
    parser.add_argument("--port", type=int, default=8004, help="Port to listen on")
    args = parser.parse_args()
    print(f"[router-mcp] Stub server would start on port {args.port} (TODO)")


if __name__ == "__main__":
    main()
