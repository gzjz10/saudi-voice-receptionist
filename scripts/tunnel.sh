#!/usr/bin/env bash
# Expose the local backend (scripts/dev.sh, port 8000) through a cloudflared quick tunnel.
# Writes the new hostname to .env as TOOLS_BASE_URL and renders agent/tool_configs/*.json
# from *.json.tmpl when templates exist (Phase 2). Quick-tunnel hostnames change every run.
# Ctrl-C stops the tunnel.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
command -v cloudflared >/dev/null || { echo "cloudflared not installed (macOS: brew install cloudflared; Windows: winget install Cloudflare.cloudflared)" >&2; exit 1; }
echo "cloudflared: $(cloudflared --version)"
LOG="$(mktemp)"
cloudflared tunnel --no-autoupdate --url "http://localhost:${PORT:-8000}" >"$LOG" 2>&1 &
PID=$!
trap 'kill $PID 2>/dev/null; rm -f "$LOG"' EXIT
URL=""
for _ in $(seq 1 60); do
  URL="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG" | head -1 || true)"
  [ -n "$URL" ] && break
  sleep 1
done
[ -n "$URL" ] || { echo "no tunnel URL after 60 s:"; cat "$LOG"; exit 1; }
touch .env
if grep -q '^TOOLS_BASE_URL=' .env; then
  sed -i.bak "s#^TOOLS_BASE_URL=.*#TOOLS_BASE_URL=$URL#" .env && rm -f .env.bak
else
  printf 'TOOLS_BASE_URL=%s\n' "$URL" >> .env
fi
echo "TOOLS_BASE_URL=$URL (written to .env)"
shopt -s nullglob
for t in agent/tool_configs/*.json.tmpl; do
  sed "s#{{TOOLS_BASE_URL}}#$URL#g" "$t" > "${t%.tmpl}"
  echo "rendered ${t%.tmpl}"
done
cat <<MSG
Check from another network (expect 200, then 401):
  curl -s -o /dev/null -w '%{http_code}\n' -X POST $URL/tools/get_store_info -H 'Content-Type: application/json' -H "X-Tool-Secret: \$TOOL_SECRET" -d '{"topic":"hours"}'
  curl -s -o /dev/null -w '%{http_code}\n' -X POST $URL/tools/get_store_info -H 'Content-Type: application/json' -d '{"topic":"hours"}'
Tunnel running; Ctrl-C to stop.
MSG
wait $PID
