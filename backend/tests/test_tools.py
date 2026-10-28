import json
import os

from conftest import NOW, SECRET


def quote(call, items=None, **kw):
    body = {"items": items or [{"product_id": "CLN-002", "qty": 3}], "fulfillment": "pickup",
            "time_slot": "بكرة العصر", "now": NOW, "conversation_id": "conv-1", **kw}
    return call("quote_order", body).json()


# ----------------------------------------------------------------- get_product
def test_get_product_exact(call):
    r = call("get_product", {"query": "الصحون الزجاج"}).json()
    assert r["status"] == "ok" and r["matches"][0]["product_id"] == "KIT-004"
    assert r["matches"][0]["price_spoken_ar"] == "تسعة ريال وخمسة وسبعين هللة"
    assert "تسعة ريال" in r["say_ar"]


def test_get_product_clarify(call):
    r = call("get_product", {"query": "بكم الصحون"}).json()
    assert r["status"] == "needs_clarification" and r["needs_clarification"] is True
    assert sorted(r["clarify_options_ar"]) == ["صحون بلاستيك", "صحون زجاج"]
    assert len(r["matches"]) == 2


def test_get_product_out_of_stock_suggests(call):
    r = call("get_product", {"query": "أكواب زجاج"}).json()
    assert r["status"] == "ok" and r["matches"][0]["in_stock"] is False
    assert 1 <= len(r["suggestions"]) <= 2 and all(s["in_stock"] for s in r["suggestions"])
    assert "خلصت" in r["say_ar"]


def test_get_product_not_found(call):
    r = call("get_product", {"query": "ايفون"}).json()
    assert r["status"] == "not_found" and r["error_code"] == "not_found" and r["matches"] == []


# -------------------------------------------------------------- get_store_info
def test_store_info_topics(call):
    for topic in ["hours", "location", "delivery", "returns", "phone"]:
        r = call("get_store_info", {"topic": topic}).json()
        assert r["status"] == "ok" and r["text_ar"] == r["say_ar"] and r["text_ar"]
    d = call("get_store_info", {"topic": "delivery"}).json()
    assert "المبرز" in d["served_areas_ar"] and "للهفوف" in d["say_ar"]
    fri = call("get_store_info", {"topic": "hours", "day": "fri"}).json()
    assert "الجمعة" in fri["say_ar"] and "أربعة العصر" in fri["say_ar"]
    assert not any(ch.isdigit() for ch in call("get_store_info", {"topic": "phone"}).json()["say_ar"])


def test_store_info_unknown_topic(call):
    r = call("get_store_info", {"topic": "parking"})
    assert r.status_code == 200 and r.json()["error_code"] == "unknown_topic" and r.json()["say_ar"]
    assert call("get_store_info", {"topic": "x" * 21}).status_code == 422


# ---------------------------------------------------------------- quote_order
def test_quote_pickup(call):
    r = quote(call)
    assert r["status"] == "ok" and r["quote_id"]
    assert r["total_halalas"] == 1725 and r["delivery_fee_halalas"] == 0
    assert r["total_spoken_ar"] == "سبعطعش ريال وخمسة وعشرين هللة"
    assert r["lines"][0]["qty_spoken_ar"] == "ثلاث علب"
    assert r["slot"] == {"date": "2026-10-29", "window": "afternoon", "time_slot_spoken_ar": "بكرة العصر"}


def test_quote_delivery_adds_fee_and_merges_lines(call):
    items = [{"product_id": "KIT-004", "qty": 3}, {"product_id": "CLN-001", "qty": 2}, {"product_id": "KIT-004", "qty": 1}]
    r = quote(call, items, fulfillment="delivery", area="المبرز")
    assert r["status"] == "ok" and len(r["lines"]) == 2
    assert r["subtotal_halalas"] == 4 * 975 + 2 * 975 and r["delivery_fee_halalas"] == 1500
    assert r["total_halalas"] == r["subtotal_halalas"] + 1500 and "للمبرز" in r["say_ar"]


def test_quote_errors(call):
    cases = [
        ({"items": [{"product_id": "KIT-999", "qty": 1}]}, "unknown_product"),
        ({"items": [{"product_id": "KIT-004", "qty": 21}]}, "invalid_qty"),
        ({"items": [{"product_id": "KIT-004", "qty": 0}]}, "invalid_qty"),
        ({"items": [{"product_id": "KIT-002", "qty": 1}]}, "out_of_stock"),
        ({"fulfillment": "delivery"}, "missing_field"),
        ({"fulfillment": "delivery", "area": "الدمام", "items": [{"product_id": "GFT-004", "qty": 5}]}, "area_not_served"),
        ({"fulfillment": "delivery", "area": "الهفوف"}, "below_minimum"),
        ({"time_slot": "بكرة"}, "missing_field"),
        ({"time_slot": "يوم الجمعة الصبح"}, "outside_hours"),
    ]
    for kw, code in cases:
        r = quote(call, **kw)
        assert r["status"] == "error" and r["error_code"] == code, (kw, r)
        assert r["say_ar"]
    served = quote(call, fulfillment="delivery", area="الدمام", items=[{"product_id": "GFT-004", "qty": 5}])
    assert "الهفوف" in served["served_areas_ar"]
    low = quote(call, fulfillment="delivery", area="الهفوف")
    assert low["below_minimum"] is True and low["total_spoken_ar"]


def test_quote_writes_no_order(call, client):
    before = call("check_order_status", {"phone": "0500000001"}).json()
    quote(call)
    assert call("check_order_status", {"phone": "0500000001"}).json() == before


# --------------------------------------------------------------- create_order
def test_create_order_and_idempotency(call):
    q = quote(call)
    body = {"quote_id": q["quote_id"], "customer_name": "فهد", "phone": "+966 55 123 4567", "conversation_id": "conv-1"}
    first = call("create_order", body).json()
    assert first["status"] == "ok" and first["duplicate"] is False
    assert len(first["order_id"]) == 4 and first["order_id"].isdigit()
    assert first["total_halalas"] == 1725 and first["total_spoken_ar"] == q["total_spoken_ar"]
    assert first["phone_spoken_ar"] == "صفر خمسة خمسة، واحد اثنين ثلاثة، أربعة خمسة ستة سبعة"
    again = call("create_order", body).json()
    assert again["duplicate"] is True and again["order_id"] == first["order_id"]
    status = call("check_order_status", {"order_id": first["order_id"]}).json()
    assert status["orders"][0]["status"] == "received"


def test_create_order_idempotent_without_conversation_id(call):
    q = quote(call, conversation_id=None)
    body = {"quote_id": q["quote_id"], "customer_name": "سارة", "phone": "0551234567"}
    a = call("create_order", body).json()
    b = call("create_order", body).json()
    assert a["duplicate"] is False and b["duplicate"] is True and a["order_id"] == b["order_id"]


def test_create_order_errors(call):
    q = quote(call)
    base = {"quote_id": q["quote_id"], "customer_name": "فهد", "phone": "0551234567", "conversation_id": "conv-1"}
    assert call("create_order", {**base, "quote_id": "q_missing"}).json()["error_code"] == "quote_not_found"
    assert call("create_order", {**base, "conversation_id": "other"}).json()["error_code"] == "quote_mismatch"
    assert call("create_order", {**base, "phone": "12345"}).json()["error_code"] == "invalid_phone"
    assert call("create_order", {**base, "customer_name": ""}).status_code == 422
    assert call("create_order", {**base, "customer_name": "ا" * 41}).status_code == 422


# --------------------------------------------------------- check_order_status
def test_status_by_id_and_phone(call):
    r = call("check_order_status", {"order_id": "4821"}).json()
    assert r["status"] == "ok" and r["orders"][0]["status"] == "preparing"
    assert r["orders"][0]["order_id_spoken_ar"] == "أربعة، ثمانية، اثنين، واحد"
    by_phone = call("check_order_status", {"phone": "٠٥٠٠٠٠٠٠٠٢"}).json()
    assert by_phone["orders"][0]["order_id"] == "3157"


def test_status_phone_returns_two_latest(call):
    for _ in range(3):
        q = quote(call, conversation_id=None)
        call("create_order", {"quote_id": q["quote_id"], "customer_name": "فهد", "phone": "0500000001"})
    r = call("check_order_status", {"phone": "0500000001"}).json()
    assert len(r["orders"]) == 2


def test_status_not_found_and_errors(call):
    r = call("check_order_status", {"order_id": "9999"}).json()
    assert r["status"] == "not_found" and r["orders"] == []
    assert call("check_order_status", {"phone": "123"}).json()["error_code"] == "invalid_phone"
    assert call("check_order_status", {}).status_code == 422
    assert call("check_order_status", {"order_id": "4821", "phone": "0500000001"}).status_code == 422
    assert call("check_order_status", {"order_id": "MG-4821"}).status_code == 422


# ---------------------------------------------------------- escalate_to_human
def test_escalate(call):
    r = call("escalate_to_human", {"reason": "angry", "summary": "العميل زعلان من التأخير", "phone": "0551234567"}).json()
    assert r["status"] == "ok" and r["ticket_id"] and r["callback_text_ar"] == r["say_ar"]
    c = call("escalate_to_human", {"reason": "cancel_request", "summary": "يبي يلغي طلب 4821"}).json()
    assert "ألغي" in c["say_ar"]
    assert call("escalate_to_human", {"reason": "other", "summary": "ا" * 301}).status_code == 422
    assert call("escalate_to_human", {"reason": "bored", "summary": "x"}).status_code == 422


# ------------------------------------------------------------------- logging
def test_tool_log_has_no_secret(call):
    call("get_product", {"query": "مناديل", "conversation_id": "conv-log"})
    call("get_product", {"query": "مناديل"}, headers={"X-Tool-Secret": "wrong"})
    text = open(os.environ["SARA_TOOL_LOG"], encoding="utf-8").read()
    assert SECRET not in text and "wrong" not in text
    recs = [json.loads(l) for l in text.splitlines()]
    ok = next(r for r in recs if r["conversation_id"] == "conv-log")
    assert ok["tool"] == "get_product" and ok["http_status"] == 200 and ok["latency_ms"] >= 0
    assert any(r["http_status"] == 401 for r in recs)
