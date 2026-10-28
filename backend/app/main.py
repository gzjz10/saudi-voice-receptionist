"""FastAPI app: POST /tools/<name> for the 6 webhook tools.

    uvicorn backend.app.main:app --port 8000      (scripts/dev.sh)
"""

from __future__ import annotations

import time
from contextlib import closing

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from . import db
from . import logging as toollog
from .security import ToolGuard
from .tools import HANDLERS

app = FastAPI(title="Sara tools backend", version="0.1.0", docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(ToolGuard)


@app.on_event("startup")
def _startup() -> None:
    db.init()


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


@app.exception_handler(RequestValidationError)
async def _schema_error(request: Request, exc: RequestValidationError):
    tool = request.url.path.rsplit("/", 1)[-1]
    toollog.write(tool=tool, conversation_id=None, request_body=None, status=None, error_code=None,
                  http_status=422, latency_ms=0.0)
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(exc.errors())})


def _route(name: str, model, handler, needs_db: bool):
    def endpoint(req) -> dict:
        started = time.perf_counter()
        if needs_db:
            # sqlite3's context manager only commits; closing() releases the file handle.
            with closing(db.connect()) as conn, conn:
                result = handler(req, conn)
        else:
            result = handler(req)
        toollog.write(tool=name, conversation_id=getattr(req, "conversation_id", None),
                      request_body=req.model_dump(mode="json"), status=result["status"],
                      error_code=result.get("error_code"), http_status=200,
                      latency_ms=(time.perf_counter() - started) * 1000)
        return result

    endpoint.__name__ = name
    # Annotations are strings under `from __future__ import annotations`; give FastAPI the class.
    endpoint.__annotations__ = {"req": model, "return": dict}
    app.post(f"/tools/{name}")(endpoint)


for _name, (_model, _handler, _needs_db) in HANDLERS.items():
    _route(_name, _model, _handler, _needs_db)
