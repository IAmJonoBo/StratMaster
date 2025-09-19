"""knowledge-mcp stub entrypoint.
TODO: Implement MCP server with tools: graphrag, vector search, rerank.
"""

import argparse


def main():
    parser = argparse.ArgumentParser(
        prog="knowledge-mcp", description="Knowledge MCP server (stub)"
    )
    parser.add_argument("--port", type=int, default=8002, help="Port to listen on")
    args = parser.parse_args()
    print(f"[knowledge-mcp] Stub server would start on port {args.port} (TODO)")


if __name__ == "__main__":
    main()
