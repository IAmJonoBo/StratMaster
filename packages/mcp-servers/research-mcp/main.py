"""research-mcp stub entrypoint.
TODO: Implement MCP server with tools: metasearch, crawl.
"""

import argparse


def main():
    parser = argparse.ArgumentParser(
        prog="research-mcp", description="Research MCP server (stub)"
    )
    parser.add_argument("--port", type=int, default=8001, help="Port to listen on")
    args = parser.parse_args()
    print(f"[research-mcp] Stub server would start on port {args.port} (TODO)")


if __name__ == "__main__":
    main()
