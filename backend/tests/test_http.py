import json

from conftest import SECRET


def test_missing_or_wrong_secret_is_401(client):
    for headers in [{}, {"X-Tool-Secret": ""}, {"X-Tool-Secret": "nope"}]:
        r = client.post("/tools/get_product", json={"query": "مناديل"}, headers=headers)
        assert r.status_code == 401 and r.json() == {"detail": "unauthorized"}


def test_401_comes_before_schema_validation(client):
    r = client.post("/tools/get_product", content=b"not json", headers={"Content-Type": "application/json"})
    assert r.status_code == 401


def test_no_secret_configured_fails_closed(client, monkeypatch):
    monkeypatch.setenv("TOOL_SECRET", "")
    r = client.post("/tools/get_product", json={"query": "x"}, headers={"X-Tool-Secret": ""})
    assert r.status_code == 401


def test_body_over_8kb_is_413(client):
    body = json.dumps({"query": "ا" * 9000}).encode()
    r = client.post("/tools/get_product", content=body,
                    headers={"X-Tool-Secret": SECRET, "Content-Type": "application/json"})
    assert r.status_code == 413


def test_schema_violation_is_422(client):
    h = {"X-Tool-Secret": SECRET}
    assert client.post("/tools/get_product", json={"query": ""}, headers=h).status_code == 422
    assert client.post("/tools/get_product", json={"query": "x" * 121}, headers=h).status_code == 422
    assert client.post("/tools/get_product", json={"query": "x", "extra": 1}, headers=h).status_code == 422
    assert client.post("/tools/get_product", content=b"{bad", headers={**h, "Content-Type": "application/json"}).status_code == 422


def test_rate_limit_429_per_client_ip(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_MIN", "3")
    h = {"X-Tool-Secret": SECRET, "CF-Connecting-IP": "203.0.113.7"}
    codes = [client.post("/tools/get_store_info", json={"topic": "hours"}, headers=h).status_code for _ in range(4)]
    assert codes == [200, 200, 200, 429]
    other = client.post("/tools/get_store_info", json={"topic": "hours"},
                        headers={"X-Tool-Secret": SECRET, "CF-Connecting-IP": "203.0.113.8"})
    assert other.status_code == 200


def test_health_needs_no_secret(client):
    assert client.get("/healthz").json() == {"ok": True}
