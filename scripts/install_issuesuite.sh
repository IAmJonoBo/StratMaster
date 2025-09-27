#!/usr/bin/env bash
set -euo pipefail

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 9ebce7a (feat(ci,tooling): IssueSuite portable integration (tarball vendoring, env override) + mypy coverage + CI extras lane; websockets asyncio migration; docs and LFS hints)
# Configurable inputs
ISSUESUITE_VERSION_DEFAULT="0.1.10"
ISSUESUITE_VERSION="${ISSUESUITE_VERSION:-$ISSUESUITE_VERSION_DEFAULT}"
TARBALL_PATH="${ISSUESUITE_TARBALL:-}"

echo "Installing IssueSuite (prefer local tarball > PyPI >= ${ISSUESUITE_VERSION})"

# Helper: try pip install quietly with resilience flags
pip_q() {
  .venv/bin/pip install --disable-pip-version-check -q "$@"
}

# 1) Local tarball if provided via env
if [[ -n "$TARBALL_PATH" ]]; then
  # Expand ~ and resolve relative paths
  EXPANDED_TARBALL=$(python - <<'PY'
import os,sys
path=os.path.expanduser(os.environ.get('TARBALL_PATH',''))
print(os.path.abspath(path) if path else '')
PY
)
  if [[ -f "$EXPANDED_TARBALL" ]]; then
    echo "➡️  Installing IssueSuite from local tarball: $EXPANDED_TARBALL"
    if pip_q "$EXPANDED_TARBALL"; then
      INSTALLED_FROM="local-tarball"
    else
      echo "⚠️  Failed to install from local tarball, will try PyPI/clone next"
    fi
  else
    echo "⚠️  Provided ISSUESUITE_TARBALL not found: $EXPANDED_TARBALL — ignoring"
  fi
fi

# 2) Auto-discover tarball in common project locations (if not yet installed)
if [[ -z "${INSTALLED_FROM:-}" ]]; then
  for candidate in \
    "$(pwd)/third_party/issuesuite/issuesuite-${ISSUESUITE_VERSION}.tar.gz" \
    "$(pwd)/vendor/issuesuite/issuesuite-${ISSUESUITE_VERSION}.tar.gz" \
    "$(pwd)/external/issuesuite/issuesuite-${ISSUESUITE_VERSION}.tar.gz"; do
    if [[ -f "$candidate" ]]; then
      echo "➡️  Installing IssueSuite from discovered tarball: $candidate"
      if pip_q "$candidate"; then
        INSTALLED_FROM="discovered-tarball"
        break
      fi
    fi
  done
fi

# 3) PyPI install (version floor)
if [[ -z "${INSTALLED_FROM:-}" ]]; then
  if pip_q "issuesuite>=${ISSUESUITE_VERSION}"; then
    echo "IssueSuite installed from PyPI (>= ${ISSUESUITE_VERSION})"
    INSTALLED_FROM="pypi"
  fi
fi

# 4) Source clone fallback
if [[ -z "${INSTALLED_FROM:-}" ]]; then
<<<<<<< HEAD
=======
echo "Installing IssueSuite (PyPI preferred)"
if .venv/bin/pip install --disable-pip-version-check "issuesuite>=0.1.4" >/dev/null 2>&1; then
  echo "IssueSuite installed from PyPI"
else
>>>>>>> 1cd0540 (chore: sync local changes (issue suite tooling, CI workflows, API flags))
=======
>>>>>>> 9ebce7a (feat(ci,tooling): IssueSuite portable integration (tarball vendoring, env override) + mypy coverage + CI extras lane; websockets asyncio migration; docs and LFS hints)
  echo "PyPI install failed; attempting source clone"
  rm -rf .issuesuite_tmp
  COPYFILE_DISABLE=1 git clone --depth 1 https://github.com/IAmJonoBo/IssueSuite .issuesuite_tmp
  # Remove macOS AppleDouble / resource fork files that can break wheel builds (._*)
  find .issuesuite_tmp -name '._*' -type f -delete || true
  source .venv/bin/activate
  echo "Editable install fallback (to avoid AppleDouble wheel duplication)"
  if (cd .issuesuite_tmp && COPYFILE_DISABLE=1 pip install -e .); then
    echo "IssueSuite installed (editable) from source clone"
<<<<<<< HEAD
<<<<<<< HEAD
    INSTALLED_FROM="git-editable"
=======
>>>>>>> 1cd0540 (chore: sync local changes (issue suite tooling, CI workflows, API flags))
=======
    INSTALLED_FROM="git-editable"
>>>>>>> 9ebce7a (feat(ci,tooling): IssueSuite portable integration (tarball vendoring, env override) + mypy coverage + CI extras lane; websockets asyncio migration; docs and LFS hints)
  else
    echo "Editable install failed, attempting direct path injection"
    SITE=$(.venv/bin/python -c 'import site,sys; print(site.getsitepackages()[0])')
    mkdir -p "$SITE/issuesuite"
    rsync -a --delete --exclude '__pycache__' .issuesuite_tmp/issuesuite/ "$SITE/issuesuite/"
    echo "[WARNING] Installed by direct file copy; CLI entrypoint may be missing. Use: python -m issuesuite.cli"
<<<<<<< HEAD
<<<<<<< HEAD
    INSTALLED_FROM="direct-copy"
=======
>>>>>>> 1cd0540 (chore: sync local changes (issue suite tooling, CI workflows, API flags))
=======
    INSTALLED_FROM="direct-copy"
>>>>>>> 9ebce7a (feat(ci,tooling): IssueSuite portable integration (tarball vendoring, env override) + mypy coverage + CI extras lane; websockets asyncio migration; docs and LFS hints)
  fi
  # Ensure CLI script present; fallback shim
  if ! command -v issuesuite >/dev/null 2>&1; then
    echo '#!/usr/bin/env bash' > .venv/bin/issuesuite
    echo 'exec python -m issuesuite.cli "$@"' >> .venv/bin/issuesuite
    chmod +x .venv/bin/issuesuite
  fi
fi

# Verification
if .venv/bin/python -c 'import issuesuite,sys; print(getattr(issuesuite,"__version__","unknown"))' >/dev/null 2>&1; then
<<<<<<< HEAD
<<<<<<< HEAD
  echo "✅ IssueSuite import OK (${INSTALLED_FROM:-unknown-source})"
=======
  echo "IssueSuite import OK"
>>>>>>> 1cd0540 (chore: sync local changes (issue suite tooling, CI workflows, API flags))
=======
  echo "✅ IssueSuite import OK (${INSTALLED_FROM:-unknown-source})"
>>>>>>> 9ebce7a (feat(ci,tooling): IssueSuite portable integration (tarball vendoring, env override) + mypy coverage + CI extras lane; websockets asyncio migration; docs and LFS hints)
else
  echo "IssueSuite import FAILED" >&2
  exit 1
fi
