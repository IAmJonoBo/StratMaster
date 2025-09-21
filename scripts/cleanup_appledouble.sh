#!/usr/bin/env bash
set -euo pipefail

# Remove AppleDouble files and other common macOS artifacts across the repo.
# This is safe to run repeatedly; it only removes junk files that should not be committed.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$ROOT_DIR"

# Find and delete patterns:
#  - ._* (AppleDouble resource forks)
#  - .DS_Store (Finder metadata)
#  - ._.* (nested AppleDouble)
#  - .AppleDouble directories
#  - .Spotlight-V100, .Trashes (if somehow copied in)

# Use -prune to skip heavy directories for speed.
prune_dirs=(-name .git -o -name .venv -o -name node_modules -o -name build -o -name dist)

# shellcheck disable=SC2016
find . \( ${prune_dirs[@]} \) -prune -o \
  \( -name '._*' -o -name '.DS_Store' -o -name '.AppleDouble' -o -name '.Spotlight-V100' -o -name '.Trashes' \) \
  -print -delete || true

# Additionally, clean AppleDouble junk that may have been created inside .git
# (e.g., when .git directory is copied with Finder to a non-HFS volume).
# Only remove files that match the AppleDouble pattern '._*' within .git to
# avoid touching legitimate git objects.
if [ -d .git ]; then
  find .git -type f -name '._*' -print -delete || true
fi

exit 0
