from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="Research MCP", version="0.1.0")

    @app.get("/healthz")
    async def healthz():
        return {"status": "ok"}

    @app.get("/info")
    async def info():
        return {
            "name": "research-mcp",
            "version": "0.1.0",
            "capabilities": ["health", "info"],
        }

    return app
