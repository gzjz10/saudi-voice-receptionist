"""ASGI guard for /tools/*: rate limit (429), secret (401), 8 KB body cap (413) — review M18.

It runs before FastAPI parses the body, so an unauthenticated or oversized request never
reaches validation (no 422 leak).
"""

from __future__ import annotations

import hmac
import json
import os
import time
from collections import defaultdict, deque

from . import logging as toollog

MAX_BODY = 8 * 1024


def _secret() -> str:
    return os.environ.get("TOOL_SECRET", "")


def _rate_limit() -> int:
    return int(os.environ.get("RATE_LIMIT_PER_MIN", "30"))


class ToolGuard:
    def __init__(self, app):
        self.app = app
        self.hits: dict[str, deque] = defaultdict(deque)

    async def _reply(self, send, status: int, body: dict | None, scope, started: float) -> None:
        payload = json.dumps(body or {}).encode()
        await send({"type": "http.response.start", "status": status,
                    "headers": [(b"content-type", b"application/json")]})
        await send({"type": "http.response.body", "body": payload})
        tool = scope["path"].rsplit("/", 1)[-1]
        toollog.write(tool=tool, conversation_id=None, request_body=None, status=None, error_code=None,
                      http_status=status, latency_ms=(time.perf_counter() - started) * 1000)

    def _client_ip(self, scope) -> str:
        headers = dict(scope.get("headers") or [])
        cf = headers.get(b"cf-connecting-ip")
        if cf:
            return cf.decode(errors="ignore")
        client = scope.get("client")
        return client[0] if client else "unknown"

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope["path"].startswith("/tools/"):
            return await self.app(scope, receive, send)
        started = time.perf_counter()

        limit = _rate_limit()
        if limit > 0:
            ip, now = self._client_ip(scope), time.monotonic()
            window = self.hits[ip]
            while window and now - window[0] > 60:
                window.popleft()
            if len(window) >= limit:
                return await self._reply(send, 429, {"detail": "rate_limited"}, scope, started)
            window.append(now)

        headers = dict(scope.get("headers") or [])
        given = headers.get(b"x-tool-secret", b"")
        secret = _secret().encode()
        if not secret or not hmac.compare_digest(given, secret):
            return await self._reply(send, 401, {"detail": "unauthorized"}, scope, started)

        declared = headers.get(b"content-length")
        if declared and declared.isdigit() and int(declared) > MAX_BODY:
            return await self._reply(send, 413, {"detail": "body_too_large"}, scope, started)
        chunks, size = [], 0
        while True:
            msg = await receive()
            if msg["type"] != "http.request":
                break
            chunk = msg.get("body", b"")
            size += len(chunk)
            if size > MAX_BODY:
                return await self._reply(send, 413, {"detail": "body_too_large"}, scope, started)
            chunks.append(chunk)
            if not msg.get("more_body"):
                break
        body = b"".join(chunks)
        sent = False

        async def replay():
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()

        return await self.app(scope, replay, send)
