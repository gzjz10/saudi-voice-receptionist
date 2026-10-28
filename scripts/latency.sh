#!/usr/bin/env bash
# 100 local calls per tool against an in-process app; fails if any tool's p95 >= 300 ms.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="$(bash scripts/py.sh)"
exec "$PY" scripts/latency.py "$@"
