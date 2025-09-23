.PHONY: api.run api.docker build clean test precommit-install precommit bootstrap dev.up dev.down dev.logs lock lock-upgrade \
        index.colbert index.splade lint format expertise-mcp.run expertise-mcp.schemas experts.mcp.up \
        phase2.up phase2.down phase2.full phase2.status telemetry.up collaboration.up ml.up dev.phase2 setup health-check \
        assets.plan assets.pull assets.verify assets.required deps.check deps.plan deps.upgrade deps.upgrade.safe \
        security.scan security.install security.baseline security.check

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

expertise-mcp.run:
	[ -d .venv ] || python -m venv .venv
	PYTHONNOUSERSITE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 .venv/bin/python -m pip install -e packages/mcp-servers/expertise-mcp -e packages/api
	cd packages/mcp-servers/expertise-mcp && PYTHONPATH=../../../packages/api/src:src python main.py

# Generate JSON schemas for Expert Council models
expertise-mcp.schemas:
	[ -d .venv ] || python -m venv .venv
	PYTHONNOUSERSITE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 .venv/bin/python -m pip install -e packages/api
	PYTHONNOUSERSITE=1 .venv/bin/python packages/api/src/stratmaster_api/models/experts/generate_json_schemas.py

# Start expertise-mcp in Docker
experts.mcp.up:
	docker compose up -d expertise-mcp

api.docker:
	docker build -t stratmaster-api:dev ./packages/api && docker run --rm -p 8080:8080 stratmaster-api:dev

clean:
	rm -rf .venv

test:
	[ -d .venv ] || python3 -m venv .venv
	PYTHONNOUSERSITE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 .venv/bin/python -m pip install -e packages/api -e packages/mcp-servers/research-mcp -e packages/mcp-servers/expertise-mcp pytest
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

# Phase 2 Implementation - Production telemetry and monitoring
.PHONY: phase2.up phase2.down phase2.status telemetry.up collaboration.up ml.up

# Start Phase 2 services (monitoring, telemetry)
phase2.up:
	@echo "🚀 Starting Phase 2 services (monitoring, telemetry)"
	docker compose up -d prometheus grafana
	@echo "✅ Grafana available at: http://localhost:3001 (admin/admin)"
	@echo "✅ Prometheus available at: http://localhost:9090"

# Start full Phase 2 stack including collaboration and ML
phase2.full:
	@echo "🚀 Starting full Phase 2 stack"
	docker compose --profile collaboration --profile ml up -d
	@echo "✅ Real-time collaboration available at: ws://localhost:8084/ws"
	@echo "✅ Constitutional ML API available at: http://localhost:8085"

# Stop Phase 2 services
phase2.down:
	@echo "🛑 Stopping Phase 2 services"
	docker compose stop prometheus grafana constitutional-bert collaboration-ws

# Check Phase 2 service status
phase2.status:
	@echo "📊 Phase 2 Service Status"
	@echo "========================"
	@docker compose ps prometheus grafana constitutional-bert collaboration-ws 2>/dev/null || echo "No Phase 2 services running"

# Start only telemetry services
telemetry.up:
	@echo "📊 Starting telemetry services"
	docker compose up -d prometheus grafana

# Start only collaboration services  
collaboration.up:
	@echo "🤝 Starting collaboration services"
	docker compose --profile collaboration up -d collaboration-ws

# Start only ML services
ml.up:
	@echo "🧠 Starting ML services"
	docker compose --profile ml up -d constitutional-bert

# Development helpers for Phase 2
dev.phase2: dev.up phase2.up
	@echo "🎉 Full development environment with Phase 2 features ready!"
	@echo ""
	@echo "Available services:"
	@echo "  - API: http://localhost:8080"
	@echo "  - API Docs: http://localhost:8080/docs"  
	@echo "  - Grafana: http://localhost:3001 (admin/admin)"
	@echo "  - Prometheus: http://localhost:9090"
	@echo "  - Langfuse: http://localhost:3000"
	@echo ""

# Easy setup command for non-power-users
setup: 
	@echo "🚀 Setting up StratMaster for local development"
	@echo "This will run the user-friendly setup script..."
	./setup.sh

# Health check for all services
health-check:
	@echo "🏥 Checking service health..."
	@echo "API Health:"
	@curl -f http://localhost:8080/healthz 2>/dev/null || echo "  ❌ API not responding"
	@echo ""
	@echo "Grafana Health:"
	@curl -f http://localhost:3001/api/health 2>/dev/null || echo "  ❌ Grafana not responding" 
	@echo ""
	@echo "Prometheus Health:"
	@curl -f http://localhost:9090/-/healthy 2>/dev/null || echo "  ❌ Prometheus not responding"

# Asset Management System - Cryptographically verified downloads
assets.plan:
	@echo "📋 Planning asset downloads..."
	python scripts/assets_pull.py plan

assets.pull:
	@echo "📥 Downloading all assets..."
	python scripts/assets_pull.py pull --all

assets.required:
	@echo "📦 Downloading required assets only..."
	python scripts/assets_pull.py pull --required-only

assets.verify:
	@echo "🔍 Verifying downloaded assets..."
	python scripts/assets_pull.py verify

# Asset management dry run for testing
assets.plan.dry:
	@echo "🔍 Dry run: Asset download plan"
	python scripts/assets_pull.py --dry-run plan

assets.pull.dry:
	@echo "🔍 Dry run: Asset download simulation"  
	python scripts/assets_pull.py --dry-run pull --all

# Safe Dependency Upgrade System
deps.check:
	@echo "🔍 Checking for dependency updates..."
	python scripts/dependency_upgrade.py check

deps.plan:
	@echo "📋 Planning dependency upgrades..."
	python scripts/dependency_upgrade.py plan --scope python

deps.upgrade.safe:
	@echo "🚀 Applying safe patch updates..."
	python scripts/dependency_upgrade.py upgrade --type patch

deps.upgrade:
	@echo "⚠️  Applying minor updates (requires manual review)..."
	python scripts/dependency_upgrade.py upgrade --type minor

# Dependency upgrade dry runs
deps.check.dry:
	@echo "🔍 Dry run: Dependency check"
	python scripts/dependency_upgrade.py --dry-run check

deps.upgrade.dry:
	@echo "🔍 Dry run: Dependency upgrade simulation"
	python scripts/dependency_upgrade.py --dry-run upgrade --type patch

# Security scanning and vulnerability assessment  
security.scan:
	@echo "🔒 Running comprehensive security scan..."
	@echo "Python Security (bandit):"
	@bandit -c .security.cfg -r packages/ || echo "  ⚠️  Bandit not installed: pip install bandit"
	@echo ""
	@echo "Dependency Vulnerabilities (pip-audit):"
	@pip-audit --desc || echo "  ⚠️  pip-audit not installed: pip install pip-audit"

security.install:
	@echo "🔒 Installing security scanning tools..."
	.venv/bin/python -m pip install bandit pip-audit safety detect-secrets

security.baseline:
	@echo "🔒 Creating security baseline..."
	@detect-secrets scan --baseline .secrets.baseline || echo "  ⚠️  detect-secrets not installed"

security.check:
	@echo "🔒 Quick security check..."
	@bandit -c .security.cfg -r packages/ -f json -o bandit-report.json || echo "  ⚠️  Bandit scan issues found"
	@echo "Security scan complete. Check bandit-report.json for details."
