#!/usr/bin/env bash
# Run the tools backend on http://localhost:8000 with TOOL_SECRET from .env.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
. scripts/env.sh
: "${TOOL_SECRET:?set TOOL_SECRET in .env (python -c 'import secrets; print(secrets.token_urlsafe(32))')}"
PY="$(bash scripts/py.sh)"
exec "$PY" -m uvicorn backend.app.main:app --host 127.0.0.1 --port "${PORT:-8000}"
