"""Every tool response (ok and each error path) validates against tools.openapi.yaml."""

from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from conftest import NOW

SPEC = Path(__file__).resolve().parents[2] / "specs" / "001-saudi-voice-receptionist" / "contracts" / "tools.openapi.yaml"


@pytest.fixture(scope="module")
def validate():
    components = yaml.safe_load(SPEC.read_text(encoding="utf-8"))["components"]

    def _validate(schema_name: str, payload: dict):
        v = Draft202012Validator({"$ref": f"#/components/schemas/{schema_name}", "components": components})
        errors = sorted(v.iter_errors(payload), key=str)
        assert not errors, [e.message for e in errors]
    return _validate


def test_spec_has_six_tools():
    paths = yaml.safe_load(SPEC.read_text(encoding="utf-8"))["paths"]
    assert sorted(p.rsplit("/", 1)[-1] for p in paths) == sorted(
        ["get_product", "get_store_info", "quote_order", "create_order", "check_order_status", "escalate_to_human"])


def test_responses_match_contract(call, validate):
    for q in ["الصحون الزجاج", "بكم الصحون", "أكواب زجاج", "ايفون"]:
        validate("GetProductResponse", call("get_product", {"query": q}).json())
    for topic in ["hours", "location", "delivery", "returns", "phone", "parking"]:
        validate("GetStoreInfoResponse", call("get_store_info", {"topic": topic}).json())

    base = {"items": [{"product_id": "CLN-002", "qty": 3}], "fulfillment": "pickup",
            "time_slot": "بكرة العصر", "now": NOW, "conversation_id": "c"}
    for kw in [{}, {"items": [{"product_id": "KIT-999", "qty": 1}]}, {"items": [{"product_id": "KIT-004", "qty": 30}]},
               {"items": [{"product_id": "KIT-002", "qty": 1}]}, {"fulfillment": "delivery"},
               {"fulfillment": "delivery", "area": "الدمام"}, {"fulfillment": "delivery", "area": "الهفوف"},
               {"time_slot": "بكرة"}, {"time_slot": "يوم الجمعة الصبح"}]:
        validate("QuoteOrderResponse", call("quote_order", {**base, **kw}).json())

    q = call("quote_order", base).json()
    order = {"quote_id": q["quote_id"], "customer_name": "فهد", "phone": "0551234567", "conversation_id": "c"}
    for kw in [{}, {}, {"quote_id": "q_none"}, {"conversation_id": "x"}, {"phone": "1"}]:
        validate("CreateOrderResponse", call("create_order", {**order, **kw}).json())

    for body in [{"order_id": "4821"}, {"order_id": "9999"}, {"phone": "0500000002"}, {"phone": "1"}]:
        validate("CheckOrderStatusResponse", call("check_order_status", body).json())
    for reason in ["asked_for_human", "angry", "not_understood", "cancel_request", "other"]:
        validate("EscalateResponse", call("escalate_to_human", {"reason": reason, "summary": "x"}).json())
