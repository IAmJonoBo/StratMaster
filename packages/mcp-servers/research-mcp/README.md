# research-mcp

A minimal MCP server placeholder providing health and info endpoints.

- Language: Python 3.11+
- Framework: FastAPI

## Run locally

See root Makefile targets to install the monorepo and run tests. This package has its own
entrypoint for standalone runs.

### Dev run via Makefile

- Shared venv:

```bash
make research-mcp.run
```

This will install the package into the shared venv and start a dev server on <http://127.0.0.1:8081>.

### Dev run via Docker

```bash
docker build -t research-mcp:dev packages/mcp-servers/research-mcp
docker run --rm -p 8081:8081 research-mcp:dev
```

Alternatively, using docker-compose from the repo root:

```bash
docker compose up research-mcp
```
