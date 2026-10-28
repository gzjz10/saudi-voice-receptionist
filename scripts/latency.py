"""100 calls per tool through the full app (guard, validation, SQLite, log); p50/p95 per tool."""

from __future__ import annotations

import os
import statistics
import sys
import tempfile
import time
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
tmp = tempfile.mkdtemp()
os.environ.update(TOOL_SECRET="latency", RATE_LIMIT_PER_MIN="0",
                  SARA_DB_PATH=os.path.join(tmp, "sara.db"), SARA_TOOL_LOG=os.path.join(tmp, "log.jsonl"))
warnings.filterwarnings("ignore")

from fastapi.testclient import TestClient  # noqa: E402

from backend.app.main import app  # noqa: E402

N, LIMIT_MS = 100, 300.0
NOW = "2026-10-28T10:00:00+03:00"


def main() -> int:
    h = {"X-Tool-Secret": "latency"}
    failed = False
    with TestClient(app) as c:
        quote = {"items": [{"product_id": "CLN-002", "qty": 3}], "fulfillment": "pickup", "time_slot": "بكرة العصر", "now": NOW}
        bodies = {
            "get_product": lambda i: {"query": ["الصحون الزجاج", "بكم الصحون", "كاسات ورق", "ايفون"][i % 4]},
            "get_store_info": lambda i: {"topic": ["hours", "location", "delivery", "returns", "phone"][i % 5]},
            "quote_order": lambda i: {**quote, "conversation_id": f"lat-{i}"},
            "create_order": lambda i: {"quote_id": c.post("/tools/quote_order", json=quote, headers=h).json()["quote_id"],
                                       "customer_name": "فهد", "phone": "0500000009"},
            "check_order_status": lambda i: {"order_id": "4821"} if i % 2 else {"phone": "0500000001"},
            "escalate_to_human": lambda i: {"reason": "asked_for_human", "summary": "اختبار"},
        }
        print(f"{'tool':20} {'p50 ms':>8} {'p95 ms':>8}")
        for tool, make in bodies.items():
            times = []
            for i in range(N):
                body = make(i)
                t = time.perf_counter()
                r = c.post(f"/tools/{tool}", json=body, headers=h)
                times.append((time.perf_counter() - t) * 1000)
                assert r.status_code == 200, (tool, r.status_code, r.text)
            p50 = statistics.median(times)
            p95 = statistics.quantiles(times, n=20)[-1]
            flag = "" if p95 < LIMIT_MS else "  FAIL"
            failed |= p95 >= LIMIT_MS
            print(f"{tool:20} {p50:8.1f} {p95:8.1f}{flag}")
    print("LATENCY:", "FAIL" if failed else f"PASS (every p95 < {LIMIT_MS:.0f} ms over {N} calls)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
