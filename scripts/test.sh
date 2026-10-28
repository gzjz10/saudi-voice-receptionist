#!/usr/bin/env bash
# Run every offline test: backend, Phase 0 checks. Works on macOS and Git Bash.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="$(bash scripts/py.sh)"
"$PY" -m pytest backend/tests scripts/tests -q -p no:cacheprovider "$@"
"$PY" phase0/test_phase0.py
