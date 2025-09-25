#!/usr/bin/env bash
set -euo pipefail

# Remove AppleDouble files and other common macOS artifacts across the repo.
# This is safe to run repeatedly; it only removes junk files that should not be committed.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "${ROOT_DIR}"

# Find and delete patterns:
#  - ._* (AppleDouble resource forks)
#  - .DS_Store (Finder metadata)
#  - .AppleDouble directories
#  - Icon? (special Finder icon files like 'Icon\r')
#  - Common macOS system metadata folders (if somehow copied in):
#    __MACOSX/, .Spotlight-V100, .Trashes, .fseventsd, .metadata_never_index,
#    .DocumentRevisions-V100, .TemporaryItems, .apdisk, .LSOverride

# Use -prune to skip heavy directories for speed.
# Prune heavy/common directories explicitly for speed.
# shellcheck disable=SC2016
find . \
  \( -name .git -o -name .venv -o -name test_venv -o -name node_modules -o -name build -o -name dist -o -name .next -o -name out -o -name site \) -prune -o \
  \( \
    -name '._*' \
    -o -name '.DS_Store' \
    -o -name '.AppleDouble' \
    -o -name 'Icon?' \
    -o -name '__MACOSX' -o -name '__MACOSX/' \
    -o -name '.Spotlight-V100' \
    -o -name '.Trashes' \
    -o -name '.fseventsd' \
    -o -name '.metadata_never_index' \
    -o -name '.DocumentRevisions-V100' \
    -o -name '.TemporaryItems' \
    -o -name '.apdisk' \
    -o -name '.LSOverride' \
  \) \
  -print -delete || true

# Additionally, clean AppleDouble junk that may have been created inside .git
# (e.g., when .git directory is copied with Finder to a non-HFS volume).
# Only remove files that match the AppleDouble pattern '._*' within .git to
# avoid touching legitimate git objects.
if [[ -d .git ]]; then
  find .git -type f -name '._*' -print -delete || true
fi

exit 0
