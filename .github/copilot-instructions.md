# StratMaster — GitHub Copilot Instructions

These instructions define how we use GitHub Copilot and Copilot Chat effectively and safely in this repository. They incorporate GitHub’s official best practices and StratMaster-specific policies.

Reference: [GitHub Copilot Best Practices](https://docs.github.com/en/copilot/get-started/best-practices)

Contents
- Purpose and scope
- How to work with Copilot in this repo
- Safe Internet Access policy for Copilot
- Repository architecture and invariants
- Development commands and validations
- Code quality, security, and CI/CD
- Suggested Copilot Chat prompts

## 1) Purpose and scope

- Copilot is a pair-programmer. You remain the reviewer and approver. Treat suggestions like third‑party code.
- Prefer repository context first. Only use additional web search or external context when necessary (see Internet Access policy below).
- Always validate outputs with our tests, linters, and manual checks before committing.

## 2) How to work with Copilot in this repo

Follow these best-practice patterns when prompting Copilot or Copilot Chat:

- Be specific and provide context
  - Include: file paths, function/class names, interfaces, examples, constraints, and acceptance criteria.
  - Add relevant snippets (minimal necessary code) rather than entire files.
- Set constraints and goals
  - Specify frameworks (FastAPI, Pydantic v2), Python version (3.13+), patterns (e.g., dependency injection), performance or memory limits, and desired outputs (tests, docs, types).
- Work iteratively
  - Start small, request a scaffold or outline, then refine. Ask Copilot to add tests, then have it explain the diff or reasoning.
- Prefer existing patterns
  - Ask Copilot to follow similar code within packages/api, existing Pydantic models, and current project conventions (imports, logging, error handling).
- Ask for verification
  - Have Copilot produce or update unit tests, run through edge cases, add docstrings, and explain security implications of proposed changes.
- Keep prompts privacy‑safe
  - Do not paste secrets, tokens, or sensitive customer or company data into prompts. Redact or use placeholders.

Security and licensing considerations:
- Review all code suggestions for:
  - Vulnerabilities, unsafe patterns, injection risks, insecure defaults.
  - License compatibility if snippets resemble public code; prefer standard library and official docs.
- Never accept “curl | bash” style commands without verification and justification.
- Prefer pinned dependencies and reproducible builds.

## 3) Safe Internet Access policy for Copilot

We allow Copilot or contributors to use the internet when needed, with safeguards:

When to use the internet
- Use local repository context first.
- Use internet search only when:
  - The answer is not in this repo, or is time-sensitive (new CVEs, library changes, API deprecations).
  - You need official documentation (Python, FastAPI, Pydantic, Helm, Kubernetes, Docker, GitHub Actions).
  - You need authoritative security guidance (CWE, NIST, vendor advisories).

How to use it safely
- Source quality and citations
  - Prefer official docs, standards, and vendor sources.
  - Provide explicit citations (markdown links) for all external claims or copied patterns.
- Data hygiene
  - Never include secrets, tokens, or proprietary data in web queries.
  - Minimize code shared; include only what’s necessary for the question.
- Code provenance and licensing
  - If adopting code from the web, link the source, check license compatibility, and adapt to our style.
  - Avoid copying large excerpts; prefer understanding and re-implementing.
- Security review
  - Validate shell commands; avoid piping to shell from unverified URLs.
  - For downloads, prefer checksums/signatures, and our Make targets that verify integrity.
- Reproducibility
  - If internet content changes behavior, add tests or notes explaining the dependency and pin versions where applicable.

Recommended doc sources
- Python: https://docs.python.org/3/
- FastAPI: https://fastapi.tiangolo.com/
- Pydantic v2: https://docs.pydantic.dev/
- Pytest: https://docs.pytest.org/
- Helm: https://helm.sh/docs/
- Kubernetes: https://kubernetes.io/docs/
- Docker: https://docs.docker.com/
- GitHub Actions: https://docs.github.com/actions

## 4) Repository architecture and invariants

- Language/runtime: Python 3.13+
- Web: FastAPI app in packages/api with Pydantic v2 models
- MCP microservices: research-mcp, knowledge-mcp, router-mcp, evals-mcp, compression-mcp
- Infra: Postgres, Qdrant, OpenSearch, NebulaGraph, MinIO, Temporal, Langfuse, Keycloak
- Build system: Make + venvs
- Quality: pre-commit, Trunk, pytest
- Deployment: Helm charts, docker-compose for local full stack

Architectural invariants Copilot must respect:
- Pydantic v2 usage and validation patterns
- Consistent FastAPI routing, dependency injection, and error handling
- Typed code with clear docstrings and tests
- No breaking changes to public API or schemas without explicit approval and migration notes

## 5) Development commands and validations

Bootstrap (always first)
```bash
make bootstrap
```
- Creates .venv, installs API package, pytest, and pre-commit.
- Internet-enabled. If behind a firewall, see “Docker-based testing” below.

Primary tests (fast, reliable)
```bash
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -q
```
- Expect all tests to pass. Do not rely on a specific test count.

Run API locally
```bash
.venv/bin/uvicorn stratmaster_api.app:create_app --factory --reload --host 127.0.0.1 --port 8080
# Health: http://127.0.0.1:8080/healthz  -> {"status":"ok"}
# Docs:   http://127.0.0.1:8080/docs
```

Full stack (if Docker available)
```bash
make dev.up
make dev.logs
make dev.down
```

Validation checklist before commit/PR
1) Bootstrap completes without errors:
```bash
make bootstrap
```
2) API tests pass:
```bash
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -q
```
3) API functionality sanity:
```bash
.venv/bin/uvicorn stratmaster_api.app:create_app --factory --reload --host 127.0.0.1 --port 8080 &
curl http://127.0.0.1:8080/healthz
```
4) Helm chart linting:
```bash
helm lint helm/stratmaster-api
helm lint helm/research-mcp
```

## 6) Code quality, security, and CI/CD

Pre-commit
```bash
.venv/bin/pre-commit install
.venv/bin/pre-commit run --all-files
```

Trunk
```bash
trunk check --all --no-fix
```

Security and dependencies
```bash
make security.install     # install security tools
make security.scan        # vulnerability scan
make deps.check           # check for updates
make deps.upgrade.safe    # safe patch updates
make deps.upgrade         # minor updates with review
```

Assets (verify integrity)
```bash
make assets.required
make assets.pull
make assets.verify
```

CI parity
- CI runs on Python 3.13, installs packages, runs pytest, lints Helm, and executes Trunk checks.
- Ensure local commands match CI before pushing.

## 7) Suggested Copilot Chat prompts

General
- “Explain what this FastAPI endpoint does and propose tests to cover edge cases.”
- “Refactor this Pydantic v2 model for clarity and add type annotations and docstrings.”
- “Given these acceptance criteria, implement the endpoint and generate pytest unit tests.”
- “Create a Helm values override example for enabling X and document it in README.”

Security and safety
- “Review this change for security issues (injection, deserialization, SSRF, path traversal). Propose safer alternatives.”
- “Propose dependency pins and reasons, and update pyproject.toml accordingly.”

Internet-assisted (with citations)
- “Summarize the breaking changes from FastAPI X.Y release that affect this code and link to the docs. Then recommend minimal changes.”

## 8) Important files and locations

- Main API: packages/api/src/stratmaster_api/
- API tests: packages/api/tests/
- MCP servers: packages/mcp-servers/
- Docker Compose: docker-compose.yml
- Helm charts: helm/stratmaster-api/, helm/research-mcp/
- CI/CD: .github/workflows/
- Quality config: .pre-commit-config.yaml, .trunk/trunk.yaml
- Makefile: canonical dev, quality, security, and infra targets

---

By using Copilot with the above practices—clear prompting, iterative refinement, comprehensive validation, and safe internet usage—we maintain quality, security, and velocity across StratMaster.
