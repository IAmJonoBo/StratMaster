import uvicorn


def main():
    uvicorn.run("research_mcp.app:create_app", factory=True, host="0.0.0.0", port=8081)


if __name__ == "__main__":
    main()
