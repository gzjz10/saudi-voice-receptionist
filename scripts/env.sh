#!/usr/bin/env bash
# Source me: load the repo-root .env into the environment.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ ! -f "$ROOT/.env" ]; then
  echo ".env missing: copy .env.example to .env and fill it in" >&2
  return 1 2>/dev/null || exit 1
fi
set -a; . "$ROOT/.env"; set +a
