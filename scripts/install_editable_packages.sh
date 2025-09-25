#!/usr/bin/env bash
set -euo pipefail

# Simple helper to install all local monorepo packages in editable mode (no deps),
# skipping those with missing src/ layout or build errors, and printing a summary.

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

PIP_BIN="${PIP_BIN:-.venv/bin/pip}"

echo "📦 Installing local editable packages (monorepo)"

skipped=()
succeeded=()

install_pkg() {
  local d="$1"
  # Skip if src-layout configured but src/ missing
  if grep -q 'package-dir.*"src"' "$d/pyproject.toml" 2>/dev/null && [[ ! -d "$d/src" ]]; then
    echo "  - ⏭️  skipping $d (src/ missing for src-layout)"
    skipped+=("$d")
    return 0
  fi
  echo "  - $PIP_BIN install -e $d --no-deps"
  if ! "$PIP_BIN" install -e "$d" --no-deps; then
    echo "    ⚠️  Failed to install $d; continuing"
    skipped+=("$d")
  else
    succeeded+=("$d")
  fi
}

shopt -s nullglob
for d in packages/* packages/mcp-servers/*; do
  [[ -f "$d/pyproject.toml" ]] || continue
  install_pkg "$d"
done

if ((${#skipped[@]})); then
  echo -n "⚠️  Skipped packages:"; printf " %s" "${skipped[@]}"; echo
fi

exit 0
