#!/usr/bin/env bash
# T074: call all 6 tools through the public tunnel (TOOLS_BASE_URL in .env).
# Expect 200 with the secret and 401 without. Needs scripts/dev.sh and scripts/tunnel.sh running.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
. scripts/env.sh
: "${TOOLS_BASE_URL:?run scripts/tunnel.sh first}"
: "${TOOL_SECRET:?TOOL_SECRET missing in .env}"
declare -a CASES=(
  'get_product|{"query":"الصحون الزجاج"}'
  'get_store_info|{"topic":"hours"}'
  'quote_order|{"items":[{"product_id":"CLN-002","qty":3}],"fulfillment":"pickup","time_slot":"بكرة العصر"}'
  'create_order|{"quote_id":"q_tunnel_check","customer_name":"فحص","phone":"0500000009"}'
  'check_order_status|{"order_id":"4821"}'
  'escalate_to_human|{"reason":"other","summary":"فحص النفق"}'
)
fail=0
echo "URL: $TOOLS_BASE_URL"
for c in "${CASES[@]}"; do
  tool="${c%%|*}"; body="${c#*|}"
  with=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$TOOLS_BASE_URL/tools/$tool" \
    -H 'Content-Type: application/json' -H "X-Tool-Secret: $TOOL_SECRET" --data "$body")
  without=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$TOOLS_BASE_URL/tools/$tool" \
    -H 'Content-Type: application/json' --data "$body")
  ok=PASS; { [ "$with" = 200 ] && [ "$without" = 401 ]; } || { ok=FAIL; fail=1; }
  printf '%-20s with secret %s · without %s  %s\n' "$tool" "$with" "$without" "$ok"
done
echo "TUNNEL CHECK: $([ $fail = 0 ] && echo PASS || echo FAIL)"
exit $fail
