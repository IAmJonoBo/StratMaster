.PHONY: api.run api.docker build clean test precommit-install precommit bootstrap dev.up dev.down dev.logs lock lock-upgrade \
        index.colbert index.splade lint format

dev.up:
	docker compose up -d

dev.down:
	docker compose down

dev.logs:
	docker compose logs -f

api.run:
	[ -d .venv ] || python -m venv .venv
	PYTHONNOUSERSITE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 .venv/bin/python -m pip install -e packages/api
	.venv/bin/uvicorn stratmaster_api.app:create_app --factory --reload --host 127.0.0.1 --port 8080

research-mcp.run:
	[ -d .venv ] || python -m venv .venv
	PYTHONNOUSERSITE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 .venv/bin/python -m pip install -e packages/mcp-servers/research-mcp
	.venv/bin/uvicorn research_mcp.app:create_app --factory --reload --host 127.0.0.1 --port 8081

api.docker:
	docker build -t stratmaster-api:dev ./packages/api && docker run --rm -p 8080:8080 stratmaster-api:dev

clean:
	rm -rf .venv

test:
	[ -d .venv ] || python3 -m venv .venv
	PYTHONNOUSERSITE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 .venv/bin/python -m pip install -e packages/api -e packages/mcp-servers/research-mcp pytest
	PYTHONNOUSERSITE=1 .venv/bin/python -m pytest -q

precommit-install:
	[ -d .venv ] || python3 -m venv .venv
	PYTHONNOUSERSITE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 .venv/bin/python -m pip install pre-commit
	.venv/bin/pre-commit install
	.venv/bin/pre-commit install --hook-type pre-push

precommit:
	. .venv/bin/activate && pre-commit run --all-files

# Quick local lint check (requires ruff and black to be installed)
lint:
	.venv/bin/ruff check .
	
# Auto-format code (requires ruff and black to be installed)
format:
	.venv/bin/ruff check --fix .
	.venv/bin/black .

bootstrap:
	[ -d .venv ] || python3 -m venv .venv
	PYTHONNOUSERSITE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 .venv/bin/python -m pip install -e packages/api pytest pre-commit

# Developer convenience target to run tests without pip (uses local sources)
test-fast:
        PYTHONPATH=packages/api/src:packages/mcp-servers/research-mcp/src python3 -m pytest -q

index.colbert:
        PYTHONPATH=packages/retrieval/colbert/src python -m colbert.index build --config configs/retrieval/colbert.yaml

index.splade:
        PYTHONPATH=packages/retrieval/splade/src python -m splade.index build --config configs/retrieval/splade.yaml

# Run tests in Docker to avoid local Python/Conda interference
test-docker:
	docker run --rm -t \
		-v $(PWD):/work \
		-w /work \
		python:3.13-slim bash -lc "python -m venv .venv && . .venv/bin/activate && pip install -e packages/api -e packages/mcp-servers/research-mcp pytest && pytest -q"

# Generate lock files with pinned, hashed dependencies from requirements*.txt
lock:
	[ -d .venv ] || python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip && pip install 'pip-tools~=7.5.0'
	. .venv/bin/activate && pip-compile --generate-hashes --resolver=backtracking -o requirements.lock requirements.txt
	. .venv/bin/activate && pip-compile --generate-hashes --resolver=backtracking -o requirements-dev.lock requirements-dev.txt

# Upgrade to latest allowed versions and refresh lock files
lock-upgrade:
	[ -d .venv ] || python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip && pip install 'pip-tools~=7.5.0'
	. .venv/bin/activate && pip-compile --upgrade --generate-hashes --resolver=backtracking -o requirements.lock requirements.txt
	. .venv/bin/activate && pip-compile --upgrade --generate-hashes --resolver=backtracking -o requirements-dev.lock requirements-dev.txt
