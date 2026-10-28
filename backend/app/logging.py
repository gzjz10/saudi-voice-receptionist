"""JSON-lines tool-call log (data-model C4). Header values are never written."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LOG = Path(__file__).resolve().parents[2] / "backend" / "logs" / "tool_calls.jsonl"
_lock = threading.Lock()


def log_path() -> Path:
    return Path(os.environ.get("SARA_TOOL_LOG", DEFAULT_LOG))


def write(*, tool: str, conversation_id: str | None, request_body: dict | None, status: str | None,
          error_code: str | None, http_status: int, latency_ms: float) -> None:
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "tool": tool, "conversation_id": conversation_id, "request_body": request_body,
        "status": status, "error_code": error_code, "latency_ms": round(latency_ms, 2), "http_status": http_status,
    }
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _lock, path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
