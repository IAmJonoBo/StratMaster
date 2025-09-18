# Contributing to StratMaster

Thanks for your interest in contributing! This repo uses:

- Trunk for linting (ruff, black, mypy, markdownlint, yamllint, shellcheck, hadolint)
- GitHub Actions for tests and Helm checks

## Workflow

1. Create a feature branch
2. Commit changes with clear messages
3. Open a PR
4. Ensure Trunk and CI checks pass

## Local dev (optional)

- Use `make bootstrap` to set up a venv
- Use `make test` to run tests, or rely on CI

## Code style & types

- Python: ruff + black
- Type hints: mypy (strict defaults in `mypy.ini`)

## Security

Please see `SECURITY.md` for reporting.
