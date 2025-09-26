#!/usr/bin/env bash
set -euo pipefail

echo "Installing IssueSuite (PyPI preferred)"
if .venv/bin/pip install --disable-pip-version-check "issuesuite>=0.1.4" >/dev/null 2>&1; then
  echo "IssueSuite installed from PyPI"
else
  echo "PyPI install failed; attempting source clone"
  rm -rf .issuesuite_tmp
  COPYFILE_DISABLE=1 git clone --depth 1 https://github.com/IAmJonoBo/IssueSuite .issuesuite_tmp
  # Remove macOS AppleDouble / resource fork files that can break wheel builds (._*)
  find .issuesuite_tmp -name '._*' -type f -delete || true
  source .venv/bin/activate
  echo "Editable install fallback (to avoid AppleDouble wheel duplication)"
  if (cd .issuesuite_tmp && COPYFILE_DISABLE=1 pip install -e .); then
    echo "IssueSuite installed (editable) from source clone"
  else
    echo "Editable install failed, attempting direct path injection"
    SITE=$(.venv/bin/python -c 'import site,sys; print(site.getsitepackages()[0])')
    mkdir -p "$SITE/issuesuite"
    rsync -a --delete --exclude '__pycache__' .issuesuite_tmp/issuesuite/ "$SITE/issuesuite/"
    echo "[WARNING] Installed by direct file copy; CLI entrypoint may be missing. Use: python -m issuesuite.cli"
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
  echo "IssueSuite import OK"
else
  echo "IssueSuite import FAILED" >&2
  exit 1
fi
