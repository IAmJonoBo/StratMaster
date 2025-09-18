# StratMaster

![CI](https://github.com/IAmJonoBo/StratMaster/actions/workflows/ci.yml/badge.svg)

Initial scaffolding for the StratMaster monorepo. See `PROJECT.md` for the full engineering blueprint.

## Quick start

- Python 3.11+
- Optional: uv or pipx

### Run the API (dev)

1. Create a virtual env and install deps
2. Start the FastAPI dev server

See `packages/api/README.md` once created.

## Running tests

If your local Python environment is clean (not Conda-managed), you can run:

1) Create a virtual environment and install tooling

```bash
make bootstrap
```

1) Run tests

```bash
make test
```

If you encounter pip/Conda interference on macOS (UnicodeDecodeError in importlib.metadata), use one of these alternatives:


- Use pyenv to install a clean CPython and recreate the venv

```bash
# Install a clean CPython (example)
pyenv install 3.12.5
pyenv local 3.12.5
make clean && make bootstrap && make test
```


- Run tests in Docker (no local Python needed)

```bash
make test-docker
```


- Quick local run without installs (only if pytest is available globally)

```bash
make test-fast
```

Troubleshooting hints:

- Ensure Docker Desktop is running before `make test-docker`.
- If using Conda, set `PYTHONNOUSERSITE=1` to reduce user-site contamination.
