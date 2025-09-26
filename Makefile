.PHONY: api.run api.docker build clean clean.macos test precommit-install precommit bootstrap bootstrap-full dev.up dev.down dev.logs lock lock-upgrade \
        index.colbert index.splade lint format expertise-mcp.run expertise-mcp.schemas experts.mcp.up \
        monitoring.up monitoring.down monitoring.full monitoring.status telemetry.up collaboration.up ml.up dev.monitoring setup health-check \
	assets.plan assets.pull assets.verify assets.required assets.plan.dry assets.pull.dry \
        deps.check deps.plan deps.upgrade deps.upgrade.safe deps.register deps.scan deps.validate deps.install.robust \
	setup setup.full setup.dry setup.validate \
        security.scan security.install security.baseline security.check \
        accessibility.scan accessibility.fix accessibility.test \
        test.advanced test.property test.contract test.load test.integration \
	health.monitor health.check health.report heal.auto heal.analyze heal.recover heal.rollback system.snapshot \
	venv.create venv.ensure venv.info venv.clean venv.doctor venv.recreate.dev venv.recreate.prod \
	venv.sync.dev venv.sync.prod venv.sync.dev.exact venv.sync.prod.exact venv.sync.remote \
	wheelhouse.build.dev wheelhouse.build.prod wheelhouse.build.linux wheelhouse.clean venv.sync.offline.dev venv.sync.offline.prod

# -------------------------------
# IssueSuite Helper Targets (external CLI)
# -------------------------------
.PHONY: issuesuite.install issuesuite.validate issuesuite.schema issuesuite.sync.dry issuesuite.summary

# Install IssueSuite from PyPI; fallback to cloning repo if unavailable
issuesuite.install: venv.ensure
	@bash scripts/install_issuesuite.sh

# Install IssueSuite from a local tarball path
.PHONY: issuesuite.install.local
issuesuite.install.local: venv.ensure
	@echo "📦 Installing IssueSuite from local tarball"
	@[ -n "$(TARBALL)" ] || { echo "❌ Provide tarball path via make var: make issuesuite.install.local TARBALL=/path/to/issuesuite-x.y.z.tar.gz"; exit 1; }
	@ISSUESUITE_TARBALL="$(TARBALL)" bash scripts/install_issuesuite.sh

issuesuite.validate: issuesuite.install
	@ISSUES_SUITE_MOCK?=1; . .venv/bin/activate && ISSUES_SUITE_MOCK=$$ISSUES_SUITE_MOCK issuesuite validate --config issue_suite.config.yaml

issuesuite.schema: issuesuite.install
	@. .venv/bin/activate && issuesuite schema --config issue_suite.config.yaml

issuesuite.sync.dry: issuesuite.install
	@. .venv/bin/activate && ISSUES_SUITE_MOCK=1 issuesuite sync --dry-run --update --config issue_suite.config.yaml --summary-json issues_summary.json

issuesuite.summary: issuesuite.install
	@. .venv/bin/activate && ISSUES_SUITE_MOCK=1 issuesuite summary --config issue_suite.config.yaml



dev.up:
	docker compose up -d

dev.down:
	docker compose down

dev.logs:
	docker compose logs -f

api.run:
	[ -d .venv ] || python -m venv .venv
	PYTHONNOUSERSITE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 .venv/bin/python -m pip install $(PIP_FLAGS) -e packages/api
	.venv/bin/uvicorn stratmaster_api.app:create_app --factory --reload --host 127.0.0.1 --port 8080

research-mcp.run:
	[ -d .venv ] || python -m venv .venv
	PYTHONNOUSERSITE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 .venv/bin/python -m pip install $(PIP_FLAGS) -e packages/mcp-servers/research-mcp
	.venv/bin/uvicorn research_mcp.app:create_app --factory --reload --host 127.0.0.1 --port 8081

expertise-mcp.run:
	[ -d .venv ] || python -m venv .venv
	PYTHONNOUSERSITE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 .venv/bin/python -m pip install $(PIP_FLAGS) -e packages/mcp-servers/expertise-mcp -e packages/api
	cd packages/mcp-servers/expertise-mcp && PYTHONPATH=../../../packages/api/src:src python main.py

# Generate JSON schemas for Expert Council models
expertise-mcp.schemas:
	[ -d .venv ] || python -m venv .venv
	PYTHONNOUSERSITE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 .venv/bin/python -m pip install $(PIP_FLAGS) -e packages/api
	PYTHONNOUSERSITE=1 .venv/bin/python packages/api/src/stratmaster_api/models/experts/generate_json_schemas.py

# Start expertise-mcp in Docker
experts.mcp.up:
	docker compose up -d expertise-mcp

api.docker:
	docker build -t stratmaster-api:dev ./packages/api && docker run --rm -p 8080:8080 stratmaster-api:dev

clean:
	rm -rf .venv

# Remove macOS Finder junk and AppleDouble files safely
clean.macos:
	@echo "🧹 Cleaning macOS metadata (._*, .DS_Store, __MACOSX, etc.)"
	bash scripts/cleanup_appledouble.sh
	@echo "✅ macOS cleanup complete"

# -------------------------------
# Virtual environment management
# -------------------------------

# Common pip environment flags for reproducible, non-interactive installs
export PYTHONNOUSERSITE=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_NO_INPUT=1
export PIP_PROGRESS_BAR=on
export PIP_DEFAULT_TIMEOUT=60

# Reusable flags for pip network resilience and visibility
PIP_FLAGS=--retries 5 --timeout 60 --progress-bar on

# Offline controls
# Set SM_OFFLINE=1 to force offline installation using a local wheelhouse directory.
# Customize wheelhouse directory via WHEELHOUSE (default: wheels)
SM_OFFLINE ?= 0
WHEELHOUSE ?= wheels
export SM_OFFLINE
export WHEELHOUSE

# Create .venv with the best available Python (prefers 3.13/3.12, falls back to python3)
venv.create:
	@echo "🐍 Creating virtual environment at .venv (if missing)"
	@PY=$$(command -v python3.13 || command -v python3.12 || command -v python3 || command -v python); \
	  [ -n "$$PY" ] || { echo "❌ No suitable Python found in PATH"; exit 1; }; \
	  [ -d .venv ] || $$PY -m venv .venv; \
	  .venv/bin/python -V

# Ensure .venv exists and Python >= 3.11 as per pyproject
venv.ensure: venv.create
	@.venv/bin/python -c 'import sys; maj,min=sys.version_info[:2]; req=(3,11); print(f"Python {sys.version.split()[0]} (required >= {req[0]}.{req[1]})"); sys.exit(0 if (maj,min) >= req else 1)' \
	  || { echo "❌ Python in .venv is older than 3.11. Please recreate with Python 3.11+"; exit 1; };
	@echo "✅ Python version OK"

# Clean common metadata issues inside .venv that cause noisy pip warnings
venv.doctor: venv.ensure
	@echo "🩺 Inspecting and cleaning virtualenv"
	@echo "🧹 Removing AppleDouble (._*) and Finder files inside .venv"
	@find .venv -type f -name '._*' -print -delete || true
	@find .venv -type f -name '.DS_Store' -print -delete || true
	@echo "🔎 Listing dist-info/egg-info directories inside .venv (report only)"
	@find .venv -type d \( -name '*.dist-info' -o -name '*.egg-info' \) -maxdepth 7 -print | sed 's/^/info: /' || true
	@echo "✅ venv.doctor completed"

# Print venv info
venv.info: venv.ensure
	@echo "📦 Pip version:" && .venv/bin/pip -V || true
	@echo "📚 Top installed packages (trimmed):" && .venv/bin/pip list --format=columns | sed -n '1,20p' || true

# Install development environment (uses lockfile with hashes when available)
venv.sync.dev: venv.ensure
	@echo "📥 Syncing development dependencies"
	@if [ "$(SM_OFFLINE)" = "1" ]; then \
	  $(MAKE) venv.sync.offline.dev; \
	else \
	  if [ -f requirements-dev.lock ]; then \
	    echo "➡️  Using requirements-dev.lock with hashes"; \
	    .venv/bin/pip install $(PIP_FLAGS) --upgrade pip setuptools wheel; \
	    .venv/bin/pip install $(PIP_FLAGS) --require-hashes -r requirements-dev.lock || { echo "⚠️  Hash-based install failed, falling back to requirements-dev.txt"; .venv/bin/pip install $(PIP_FLAGS) -r requirements-dev.txt; }; \
	  else \
	    echo "➡️  Using requirements-dev.txt"; \
	    .venv/bin/pip install $(PIP_FLAGS) --upgrade pip setuptools wheel; \
	    .venv/bin/pip install $(PIP_FLAGS) -r requirements-dev.txt; \
	  fi; \
	  bash scripts/install_editable_packages.sh; \
	  .venv/bin/pip check || true; \
	  echo "✅ Development venv ready"; \
	fi

# Install production/runtime environment (prefer lockfile with hashes)
venv.sync.prod: venv.ensure
	@echo "📥 Syncing production/runtime dependencies"
	@if [ "$(SM_OFFLINE)" = "1" ]; then \
	  $(MAKE) venv.sync.offline.prod; \
	else \
	  if [ -f requirements.lock ]; then \
	    echo "➡️  Using requirements.lock with hashes"; \
	    .venv/bin/pip install $(PIP_FLAGS) --upgrade pip setuptools wheel; \
	    .venv/bin/pip install $(PIP_FLAGS) --require-hashes -r requirements.lock || { echo "⚠️  Hash-based install failed, falling back to requirements.txt"; .venv/bin/pip install $(PIP_FLAGS) -r requirements.txt; }; \
	  else \
	    echo "➡️  Using requirements.txt"; \
	    .venv/bin/pip install $(PIP_FLAGS) --upgrade pip setuptools wheel; \
	    .venv/bin/pip install $(PIP_FLAGS) -r requirements.txt; \
	  fi; \
	  echo "📦 Installing API package (editable, no deps)"; \
	  .venv/bin/pip install $(PIP_FLAGS) -e packages/api --no-deps; \
	  .venv/bin/pip check || true; \
	  echo "✅ Production/runtime venv ready"; \
	fi

# Exact sync using pip-tools' pip-sync to remove extras and enforce lock
venv.sync.dev.exact: venv.ensure
	@echo "📥 Exact sync (dev) using pip-sync"
	.venv/bin/pip install $(PIP_FLAGS) --upgrade pip setuptools wheel 'pip-tools~=7.5.0'
	@if [ -f requirements-dev.lock ]; then \
	  .venv/bin/pip-sync -q requirements-dev.lock; \
	else \
	  .venv/bin/pip-sync -q requirements-dev.txt; \
	fi
	@bash scripts/install_editable_packages.sh || true
	@.venv/bin/pip check || true
	@echo "✅ Exact development sync complete"

venv.sync.prod.exact: venv.ensure
	@echo "📥 Exact sync (prod) using pip-sync"
	.venv/bin/pip install $(PIP_FLAGS) --upgrade pip setuptools wheel 'pip-tools~=7.5.0'
	@if [ -f requirements.lock ]; then \
	  .venv/bin/pip-sync -q requirements.lock; \
	else \
	  .venv/bin/pip-sync -q requirements.txt; \
	fi
	@echo "📦 Installing API package (editable, no deps)"
	@.venv/bin/pip install -e packages/api --no-deps
	@.venv/bin/pip check || true
	@echo "✅ Exact production/runtime sync complete"

# Remote setup alias (same as production sync)
venv.sync.remote: venv.sync.prod
	@echo "🌐 Remote venv synchronized (runtime)"

# --------------------------------
# Offline wheelhouse and installs
# --------------------------------

wheelhouse.clean:
	rm -rf $(WHEELHOUSE)

# Build a wheelhouse for development (includes runtime via -r requirements.txt)
wheelhouse.build.dev: venv.ensure
	@echo "📦 Building wheelhouse (dev) in $(WHEELHOUSE)"
	mkdir -p $(WHEELHOUSE)
	@if [ -f requirements-dev.lock ]; then \
	  echo "➡️  Downloading wheels from requirements-dev.lock"; \
	  .venv/bin/pip download $(PIP_FLAGS) --only-binary=:all: -d $(WHEELHOUSE) -r requirements-dev.lock || { echo "⚠️  Strict wheel-only download failed; retrying without only-binary"; .venv/bin/pip download $(PIP_FLAGS) -d $(WHEELHOUSE) -r requirements-dev.lock; }; \
	else \
	  echo "➡️  Downloading wheels from requirements-dev.txt"; \
	  .venv/bin/pip download $(PIP_FLAGS) --only-binary=:all: -d $(WHEELHOUSE) -r requirements-dev.txt || { echo "⚠️  Strict wheel-only download failed; retrying without only-binary"; .venv/bin/pip download $(PIP_FLAGS) -d $(WHEELHOUSE) -r requirements-dev.txt; }; \
	fi
	@echo "✅ Wheelhouse (dev) ready at $(WHEELHOUSE)"

# Build a wheelhouse for production/runtime
wheelhouse.build.prod: venv.ensure
	@echo "📦 Building wheelhouse (prod) in $(WHEELHOUSE)"
	mkdir -p $(WHEELHOUSE)
	@if [ -f requirements.lock ]; then \
	  echo "➡️  Downloading wheels from requirements.lock"; \
	  .venv/bin/pip download $(PIP_FLAGS) --only-binary=:all: -d $(WHEELHOUSE) -r requirements.lock || { echo "⚠️  Strict wheel-only download failed; retrying without only-binary"; .venv/bin/pip download $(PIP_FLAGS) -d $(WHEELHOUSE) -r requirements.lock; }; \
	else \
	  echo "➡️  Downloading wheels from requirements.txt"; \
	  .venv/bin/pip download $(PIP_FLAGS) --only-binary=:all: -d $(WHEELHOUSE) -r requirements.txt || { echo "⚠️  Strict wheel-only download failed; retrying without only-binary"; .venv/bin/pip download $(PIP_FLAGS) -d $(WHEELHOUSE) -r requirements.txt; }; \
	fi
	@echo "✅ Wheelhouse (prod) ready at $(WHEELHOUSE)"

# Cross-platform wheelhouse for Linux (use on macOS to prepare for remote Linux agents)
# Requires pip>=23 to support --platform/--abi flags
wheelhouse.build.linux: venv.ensure
	@echo "🐧 Building Linux wheelhouse in $(WHEELHOUSE) (Python 3.13, manylinux2014_x86_64)"
	mkdir -p $(WHEELHOUSE)
	PLATFORM_FLAGS="--platform manylinux2014_x86_64 --implementation cp --python-version 313 --abi cp313"; \
	if [ -f requirements.lock ]; then \
	  .venv/bin/pip download $(PIP_FLAGS) $$PLATFORM_FLAGS --only-binary=:all: -d $(WHEELHOUSE) -r requirements.lock; \
	else \
	  .venv/bin/pip download $(PIP_FLAGS) $$PLATFORM_FLAGS --only-binary=:all: -d $(WHEELHOUSE) -r requirements.txt; \
	fi
	@echo "✅ Linux wheelhouse ready at $(WHEELHOUSE)"

# Offline dev install using local wheelhouse
venv.sync.offline.dev: venv.ensure
	@echo "📴 Offline install (dev) from $(WHEELHOUSE)"
	@if [ ! -d "$(WHEELHOUSE)" ]; then echo "❌ Wheelhouse '$(WHEELHOUSE)' not found. Run 'make wheelhouse.build.dev' (or wheelhouse.build.linux) first."; exit 1; fi
	@if [ -f requirements-dev.lock ]; then \
	  .venv/bin/pip install --no-index --find-links $(WHEELHOUSE) --require-hashes -r requirements-dev.lock || .venv/bin/pip install --no-index --find-links $(WHEELHOUSE) -r requirements-dev.lock; \
	else \
	  .venv/bin/pip install --no-index --find-links $(WHEELHOUSE) -r requirements-dev.txt; \
	fi
	@bash scripts/install_editable_packages.sh || true
	@.venv/bin/pip check || true
	@echo "✅ Offline development venv ready"

# Offline prod install using local wheelhouse
venv.sync.offline.prod: venv.ensure
	@echo "📴 Offline install (prod) from $(WHEELHOUSE)"
	@if [ ! -d "$(WHEELHOUSE)" ]; then echo "❌ Wheelhouse '$(WHEELHOUSE)' not found. Run 'make wheelhouse.build.prod' (or wheelhouse.build.linux) first."; exit 1; fi
	@if [ -f requirements.lock ]; then \
	  .venv/bin/pip install --no-index --find-links $(WHEELHOUSE) --require-hashes -r requirements.lock || .venv/bin/pip install --no-index --find-links $(WHEELHOUSE) -r requirements.lock; \
	else \
	  .venv/bin/pip install --no-index --find-links $(WHEELHOUSE) -r requirements.txt; \
	fi
	@echo "📦 Installing API package (editable, no deps)"
	@.venv/bin/pip install -e packages/api --no-deps
	@.venv/bin/pip check || true
	@echo "✅ Offline production/runtime venv ready"

# Remove and fully recreate venvs
venv.clean:
	rm -rf .venv

venv.recreate.dev: venv.clean venv.sync.dev venv.info

venv.recreate.prod: venv.clean venv.sync.prod venv.info

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
	@echo "🚀 StratMaster Bootstrap"
	[ -d .venv ] || python3 -m venv .venv
	@echo "📦 Installing core dependencies..."
	PYTHONNOUSERSITE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 .venv/bin/python -m pip install $(PIP_FLAGS) --upgrade pip
	PYTHONNOUSERSITE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 .venv/bin/python -m pip install $(PIP_FLAGS) pydantic fastapi uvicorn pytest
	PYTHONNOUSERSITE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 .venv/bin/python -m pip install $(PIP_FLAGS) -e packages/api
	@echo "✅ Bootstrap completed. Run 'make setup' for full integrated setup."

# Enhanced bootstrap with integrated setup (registers deps, downloads assets, upgrades)
bootstrap-full:
	$(MAKE) bootstrap
	.venv/bin/python scripts/integrated_setup.py setup --required-only

# Developer convenience target to run tests without pip (uses local sources)
test-fast:
        PYTHONPATH=packages/api/src:packages/mcp-servers/research-mcp/src python3 -m pytest -q

index.colbert:
        PYTHONPATH=packages/retrieval/src/colbert/src python -m colbert.index build --config configs/retrieval/colbert.yaml

index.splade:
        PYTHONPATH=packages/retrieval/src/splade/src python -m splade.index build --config configs/retrieval/splade.yaml

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

# Lock variants that include unsafe pins (pip, setuptools, wheel)
lock-allow-unsafe:
	[ -d .venv ] || python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip && pip install 'pip-tools~=7.5.0'
	. .venv/bin/activate && pip-compile --generate-hashes --resolver=backtracking --allow-unsafe -o requirements.lock requirements.txt
	. .venv/bin/activate && pip-compile --generate-hashes --resolver=backtracking --allow-unsafe -o requirements-dev.lock requirements-dev.txt

# Upgrade to latest allowed versions and refresh lock files
lock-upgrade:
	[ -d .venv ] || python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip && pip install 'pip-tools~=7.5.0'
	. .venv/bin/activate && pip-compile --upgrade --generate-hashes --resolver=backtracking -o requirements.lock requirements.txt
	. .venv/bin/activate && pip-compile --upgrade --generate-hashes --resolver=backtracking -o requirements-dev.lock requirements-dev.txt

lock-upgrade-allow-unsafe:
	[ -d .venv ] || python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip && pip install 'pip-tools~=7.5.0'
	. .venv/bin/activate && pip-compile --upgrade --generate-hashes --resolver=backtracking --allow-unsafe -o requirements.lock requirements.txt
	. .venv/bin/activate && pip-compile --upgrade --generate-hashes --resolver=backtracking --allow-unsafe -o requirements-dev.lock requirements-dev.txt

# Monitoring and telemetry services
.PHONY: monitoring.up monitoring.down monitoring.status telemetry.up collaboration.up ml.up

# Start monitoring services (telemetry and analytics)
monitoring.up:
	@echo "🚀 Starting monitoring services (telemetry, analytics)"
	docker compose up -d prometheus grafana
	@echo "✅ Grafana available at: http://localhost:3001 (admin/admin)"
	@echo "✅ Prometheus available at: http://localhost:9090"

# Start full monitoring stack including collaboration and ML
monitoring.full:
	@echo "🚀 Starting full monitoring stack"
	docker compose --profile collaboration --profile ml up -d
	@echo "✅ Real-time collaboration available at: ws://localhost:8084/ws"
	@echo "✅ Constitutional ML API available at: http://localhost:8085"

# Stop monitoring services
monitoring.down:
	@echo "🛑 Stopping monitoring services"
	docker compose stop prometheus grafana constitutional-bert collaboration-ws

# Check monitoring service status
monitoring.status:
	@echo "📊 Monitoring Service Status"
	@echo "========================"
	@docker compose ps prometheus grafana constitutional-bert collaboration-ws 2>/dev/null || echo "No monitoring services running"

# Start only telemetry services
telemetry.up:
	@echo "📊 Starting telemetry services"
	docker compose up -d prometheus grafana

# Start only collaboration services
collaboration.up:
	@echo "🤝 Starting collaboration services"
	docker compose --profile collaboration up -d collaboration-ws

# Development monitoring stack (alias for monitoring.up)
dev.monitoring: monitoring.up
	@echo "🔧 Development monitoring ready"

# Start only ML services
ml.up:
	@echo "🧠 Starting ML services"
	docker compose --profile ml up -d constitutional-bert

# Development helpers for monitoring stack
dev.monitoring: dev.up monitoring.up
	@echo "🎉 Full development environment with monitoring features ready!"
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

# Dependency Registry System - Scan and register all package dependencies
deps.register:
	@echo "📦 Registering package dependencies..."
	python scripts/register_dependencies.py register

deps.scan:
	@echo "🔍 Scanning package dependencies..."
	python scripts/register_dependencies.py scan

deps.validate:
	@echo "✅ Validating dependency registry..."
	python scripts/register_dependencies.py validate

# Integrated Setup System - Complete environment setup with chaining
setup:
	@echo "🚀 Running integrated setup (required assets only)..."
	python scripts/integrated_setup.py setup --required-only

setup.full:
	@echo "🚀 Running full integrated setup (all assets)..."
	python scripts/integrated_setup.py setup --full

setup.dry:
	@echo "🔍 Dry run: Integrated setup simulation"
	python scripts/integrated_setup.py setup --dry-run

setup.validate:
	@echo "✅ Validating complete environment..."
	python scripts/integrated_setup.py validate

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

# Accessibility Enhancement System - WCAG 2.1 AA compliance
accessibility.scan:
	@echo "♿ Running accessibility audit..."
	.venv/bin/python scripts/accessibility_audit.py scan

accessibility.fix:
	@echo "🔧 Applying accessibility fixes..."
	.venv/bin/python scripts/accessibility_audit.py fix

accessibility.test:
	@echo "⌨️  Testing keyboard navigation..."
	.venv/bin/python scripts/accessibility_audit.py test-keyboard

# Accessibility dry runs
accessibility.scan.dry:
	@echo "🔍 Dry run: Accessibility scan"
	.venv/bin/python scripts/accessibility_audit.py --dry-run scan

accessibility.fix.dry:
	@echo "🔍 Dry run: Accessibility fixes"
	.venv/bin/python scripts/accessibility_audit.py --dry-run fix

# Advanced Testing Suite - Frontier-grade testing capabilities
test.advanced:
	@echo "🧪 Running advanced test suite..."
	.venv/bin/python scripts/advanced_testing.py all

test.property:
	@echo "🧪 Running property-based tests..."
	.venv/bin/python scripts/advanced_testing.py property-tests

test.contract:
	@echo "📋 Running API contract tests..."
	.venv/bin/python scripts/advanced_testing.py contract-tests

test.load:
	@echo "⚡ Running load tests..."
	.venv/bin/python scripts/advanced_testing.py load-test --duration 30

test.integration:
	@echo "🔗 Running integration tests..."
	.venv/bin/python scripts/advanced_testing.py integration-tests

# Advanced testing dry runs
test.advanced.dry:
	@echo "🔍 Dry run: Advanced testing suite"
	.venv/bin/python scripts/advanced_testing.py --dry-run all

test.load.dry:
	@echo "🔍 Dry run: Load testing"
	.venv/bin/python scripts/advanced_testing.py --dry-run load-test

# Backward compatibility aliases (deprecated - use monitoring.* targets)
# TODO: Remove in v0.2.0
phase2.up: monitoring.up
	@echo "⚠️  'phase2.up' is deprecated. Use 'monitoring.up' instead."

phase2.down: monitoring.down
	@echo "⚠️  'phase2.down' is deprecated. Use 'monitoring.down' instead."

phase2.status: monitoring.status
	@echo "⚠️  'phase2.status' is deprecated. Use 'monitoring.status' instead."

phase2.full: monitoring.full
	@echo "⚠️  'phase2.full' is deprecated. Use 'monitoring.full' instead."

dev.phase2: dev.monitoring
	@echo "⚠️  'dev.phase2' is deprecated. Use 'dev.monitoring' instead."

# Enhanced dependency management with network resilience
deps.install.robust:
	python3 scripts/robust_installer.py install --requirements requirements.txt

deps.install.robust.dev:
	python3 scripts/robust_installer.py install --requirements requirements-dev.txt

deps.cache.warmup:
	python3 scripts/robust_installer.py cache-warmup

deps.validate.environment:
	python3 scripts/robust_installer.py validate-environment

# System health monitoring
health.monitor:
	python3 scripts/system_health_monitor.py monitor --interval 60

health.check:
	python3 scripts/system_health_monitor.py check --all

health.check.services:
	python3 scripts/system_health_monitor.py check --services-only

health.check.deps:
	python3 scripts/system_health_monitor.py check --dependencies-only

health.check.resources:
	python3 scripts/system_health_monitor.py check --resources-only

health.report:
	python3 scripts/system_health_monitor.py report --format json --output health_report.json

health.report.text:
	python3 scripts/system_health_monitor.py report --format text

# Self-healing automation
heal.auto:
	python3 scripts/self_healing.py analyze --auto-heal

heal.analyze:
	python3 scripts/self_healing.py analyze --dry-run

heal.recover.service:
	python3 scripts/self_healing.py recover --service $(SERVICE)

heal.recover.deps:
	python3 scripts/self_healing.py recover --dependencies

heal.recover.env:
	python3 scripts/self_healing.py recover --environment

heal.cleanup:
	python3 scripts/self_healing.py recover --cleanup

heal.rollback:
	python3 scripts/self_healing.py rollback --to-last-known-good

heal.rollback.snapshot:
	python3 scripts/self_healing.py rollback --snapshot-id $(SNAPSHOT_ID)

heal.validate:
	python3 scripts/self_healing.py validate-and-heal

system.snapshot:
	python3 scripts/self_healing.py snapshot

# Enhanced bootstrap with network resilience
bootstrap.robust: bootstrap-with-fallback

bootstrap-with-fallback:
	@echo "🚀 StratMaster Robust Bootstrap"
	[ -d .venv ] || python3 -m venv .venv
	@echo "📦 Installing core dependencies with network resilience..."
	python3 scripts/robust_installer.py install --package "pip>=20.0.0"
	python3 scripts/robust_installer.py install --package "pydantic>=2.0.0"
	python3 scripts/robust_installer.py install --package "fastapi>=0.100.0"
	python3 scripts/robust_installer.py install --package "uvicorn[standard]"
	python3 scripts/robust_installer.py install --package "pytest"
	@echo "📦 Installing StratMaster API..."
	PYTHONNOUSERSITE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 .venv/bin/python -m pip install -e packages/api --timeout=300
	@echo "🔧 Installing development tools..."
	python3 scripts/robust_installer.py install --requirements requirements-dev.txt || echo "⚠️  Some dev dependencies failed, continuing..."
	@echo "✅ Robust bootstrap completed"
