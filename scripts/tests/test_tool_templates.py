"""Tool templates (agent/tool_configs/*.json.tmpl) must match the backend contract, or live calls 422."""

import json
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
SPEC = yaml.safe_load((REPO / "specs" / "001-saudi-voice-receptionist" / "contracts" / "tools.openapi.yaml")
                      .read_text(encoding="utf-8"))
TEMPLATES = sorted((REPO / "agent" / "tool_configs").glob("*.json.tmpl"))


def _contract(name: str) -> dict:
    ref = SPEC["paths"][f"/tools/{name}"]["post"]["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    return SPEC["components"]["schemas"][ref.split("/")[-1]]


def test_one_template_per_contract_path():
    assert {p.name.removesuffix(".json.tmpl") for p in TEMPLATES} == {
        k.removeprefix("/tools/") for k in SPEC["paths"]}


def test_template_bodies_fit_the_contract():
    for path in TEMPLATES:
        tool = json.loads(path.read_text(encoding="utf-8"))
        body = tool["api_schema"]["request_body_schema"]
        contract = _contract(tool["name"])
        sent = set(body["properties"])
        assert sent <= set(contract["properties"]), (tool["name"], sent - set(contract["properties"]))
        assert set(contract.get("required", [])) <= set(body.get("required", [])), tool["name"]
        for field, prop in body["properties"].items():
            allowed = contract["properties"][field].get("enum")
            if prop.get("enum") and allowed:
                assert set(prop["enum"]) <= set(allowed), (tool["name"], field)
