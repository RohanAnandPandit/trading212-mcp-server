#!/usr/bin/env bash
# Resolve updates and regenerate the pip export as one operation.
# With no arguments refresh all packages; otherwise update only named packages.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ "$#" -eq 0 ]; then
  uv lock --upgrade
else
  args=()
  for package in "$@"; do
    args+=(--upgrade-package "$package")
  done
  uv lock "${args[@]}"
fi
uv export --frozen --no-dev --no-emit-project --output-file requirements.txt
uv sync --frozen
