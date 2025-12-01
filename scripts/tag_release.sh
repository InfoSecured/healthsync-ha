#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version>" >&2
  echo "Example: $0 0.2.0" >&2
  exit 1
fi

version="$1"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree is dirty. Commit or stash changes first." >&2
  exit 1
fi

git tag -a "v${version}" -m "Release v${version}"
echo "Created tag v${version}. Push with: git push origin v${version}"
