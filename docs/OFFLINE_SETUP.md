# Offline/Restricted-Network Setup for StratMaster

When running in network-restricted environments (e.g., GitHub Copilot agent, CI runners without internet), use a local wheelhouse and the offline Make targets to install dependencies without hitting PyPI.

## Quick start

1) On a machine with internet access (ideally macOS for local use or Linux for CI parity), build a wheelhouse:

- macOS/local dev (includes dev deps):
  make wheelhouse.build.dev

- Linux wheelhouse for CI/agents (Python 3.13, manylinux2014_x86_64):
  make wheelhouse.build.linux

- Production/runtime only:
  make wheelhouse.build.prod

2) Transfer the wheelhouse directory to the restricted environment:

- Copy the `wheels/` directory into the repo root.
- Ensure it is not committed (ignored by .gitignore).

3) Install in offline mode:

- Development:
  make SM_OFFLINE=1 venv.sync.dev

- Production/runtime:
  make SM_OFFLINE=1 venv.sync.prod

These call the offline targets under the hood and install from `wheels/` using `--no-index --find-links wheels`.

## Notes and tips

- Lockfiles: If `requirements*.lock` files exist, offline targets try `--require-hashes` first and fall back to non-hash mode if necessary.
- Python version: The Linux wheelhouse target defaults to CPython 3.13 and manylinux2014_x86_64. Adjust via PLATFORM_FLAGS in the Makefile if your runner differs.
- Editable installs: The API package is installed editable without pulling dependencies (`--no-deps`) in prod/offline flows.
- Verifications: `pip check` runs but is non-fatal in offline mode.
- Refreshing wheels: Re-run the appropriate `wheelhouse.build.*` after changing requirements.

## Troubleshooting

- Missing wheels: If a package has no wheel for your platform/Python, `pip download --only-binary=:all:` will fail; the Makefile falls back to allowing source downloads during wheelhouse build (on a machine with internet access). You must build wheels there first; fully offline installs require wheels to exist in `wheels/`.
- Platform mismatch: Ensure that the wheel tags (cp3x, manylinux) match the target environment. Use `pip debug --verbose` to see supported tags on the agent.
- Private indexes: If you have an internal PyPI mirror, you can skip wheelhouse and use environment variables `PIP_INDEX_URL` / `PIP_EXTRA_INDEX_URL` with the normal venv targets.
