#!/usr/bin/env bash
# Print the Python 3.12 to use: the repo .venv first, then python / python3 on PATH.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for c in "$ROOT/.venv/bin/python" "$ROOT/.venv/Scripts/python.exe" python python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(sys.version_info[:2] != (3, 12))' 2>/dev/null; then
    echo "$c"; exit 0
  fi
done
echo "Python 3.12 not found (create .venv: python3.12 -m venv .venv)" >&2
exit 1
