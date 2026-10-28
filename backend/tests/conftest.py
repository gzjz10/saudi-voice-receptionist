import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

SECRET = "test-secret"


@pytest.fixture(autouse=True)
def _env(tmp_path, monkeypatch):
    monkeypatch.setenv("TOOL_SECRET", SECRET)
    monkeypatch.setenv("RATE_LIMIT_PER_MIN", "0")
    monkeypatch.setenv("SARA_DB_PATH", str(tmp_path / "sara.db"))
    monkeypatch.setenv("SARA_TOOL_LOG", str(tmp_path / "tool_calls.jsonl"))
    from backend.app import db
    db.init(reset=True)


@pytest.fixture
def client():
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    from fastapi.testclient import TestClient
    from backend.app.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture
def call(client):
    def _call(tool, body, headers=None):
        h = {"X-Tool-Secret": SECRET} if headers is None else headers
        return client.post(f"/tools/{tool}", json=body, headers=h)
    return _call


# A Wednesday morning in Riyadh; quote tests pass it as `now`.
NOW = "2026-10-28T10:00:00+03:00"
