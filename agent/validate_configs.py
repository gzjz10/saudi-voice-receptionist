"""Offline validation of the ElevenLabs agent configs in this folder.

Why this exists: with @elevenlabs/cli 1.7.1, `agents push --dry-run` only checks
that each config file parses as JSON (and still exits 0 when one does not), and
`agents create --dry-run --json -` only rejects unknown properties. Neither checks
enum values or numeric ranges. This script adds those checks, reading every enum
and range from the CLI's own embedded OpenAPI spec (`agents create --spec`), so
nothing here is hard-coded from memory.

No API key and no network call is needed. Run from anywhere:

    python agent/validate_configs.py            # Phase 0a: voice_id must be absent
    python agent/validate_configs.py --allow-voice-id   # Phase 0b+: winner voice set

It also checks every webhook tool template in tool_configs/*.json.tmpl against the spec
(`agents tools create --dry-run` in 1.7.1 accepts unknown properties, so it is no check).

Requires `npm ci` in agent/ first (installs the pinned CLI). Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent
REPO = AGENT_DIR.parent
PROMPT_FOR = {"agent_configs/sara.json": REPO / "prompts" / "system_v1.md"}
# Phase 0 rules (no tools) still hold for the STT probe; Sara gets tools in Phase 2.
NO_TOOLS = {"agent_configs/sara_stt_probe.json"}
TOOL_DIR = AGENT_DIR / "tool_configs"
PLACEHOLDERS = {"{{TOOLS_BASE_URL}}": "https://example.trycloudflare.com", "{{TOOL_SECRET_ID}}": "secret_placeholder"}


def cli_path() -> Path:
    name = "elevenlabs.cmd" if os.name == "nt" else "elevenlabs"
    p = AGENT_DIR / "node_modules" / ".bin" / name
    if not p.exists():
        sys.exit(f"CLI not found at {p}. Run `npm ci` in {AGENT_DIR} first.")
    return p


def run_cli(args: list[str], stdin: str | None = None) -> str:
    res = subprocess.run(
        [str(cli_path()), *args],
        input=stdin.encode("utf-8") if stdin is not None else None,
        capture_output=True,
        cwd=AGENT_DIR,
    )
    return (res.stdout + res.stderr).decode("utf-8", errors="replace")


def load_spec() -> dict:
    out = run_cli(["agents", "create", "--spec"])
    return json.loads(out)["components"]["schemas"]


def check_config(rel: str, cfg: dict, schemas: dict, allow_voice_id: bool) -> list[str]:
    errs: list[str] = []
    cc = cfg.get("conversation_config", {})
    agent = cc.get("agent", {})
    prompt = agent.get("prompt", {})
    tts = cc.get("tts", {})
    asr = cc.get("asr", {})

    def enum_of(name: str) -> list[str]:
        return schemas[name]["enum"]

    def in_enum(value, schema_name: str, field: str) -> None:
        if value is not None and value not in enum_of(schema_name):
            errs.append(f"{field}={value!r} not in {schema_name} enum")

    in_enum(prompt.get("llm"), "LLM", "agent.prompt.llm")
    in_enum(tts.get("model_id"), "TTSConversationalModel", "tts.model_id")
    in_enum(asr.get("provider"), "ASRProvider", "asr.provider")
    in_enum(asr.get("quality"), "ASRQuality", "asr.quality")
    in_enum(tts.get("text_normalisation_type"), "TextNormalisationType", "tts.text_normalisation_type")

    deprecated = schemas["TTSConversationalModel"].get("x-fern-enum", {})
    if deprecated.get(tts.get("model_id"), {}).get("deprecated"):
        errs.append(f"tts.model_id={tts.get('model_id')!r} is deprecated in the spec")

    tts_props = schemas["TTSConversationalConfig-Input"]["properties"]
    for key in ("stability", "similarity_boost", "speed"):
        if key in tts:
            lo, hi = tts_props[key].get("minimum"), tts_props[key].get("maximum")
            v = tts[key]
            if not isinstance(v, (int, float)) or (lo is not None and v < lo) or (hi is not None and v > hi):
                errs.append(f"tts.{key}={v!r} outside [{lo}, {hi}]")

    ints = [
        (cc.get("conversation", {}).get("max_duration_seconds"), "conversation.max_duration_seconds"),
        (cfg.get("platform_settings", {}).get("privacy", {}).get("retention_days"), "privacy.retention_days"),
        (cfg.get("platform_settings", {}).get("call_limits", {}).get("daily_limit"), "call_limits.daily_limit"),
        (cfg.get("platform_settings", {}).get("call_limits", {}).get("agent_concurrency_limit"),
         "call_limits.agent_concurrency_limit"),
    ]
    for v, field in ints:
        if v is not None and (not isinstance(v, int) or isinstance(v, bool)):
            errs.append(f"{field}={v!r} must be an integer")

    # Phase 0 rules (reviews/plan-review.md, section G).
    if agent.get("language") != "ar":
        errs.append(f"agent.language={agent.get('language')!r}, Phase 0 requires 'ar'")
    for key in ("tool_ids", "tools", "built_in_tools", "mcp_server_ids"):
        if rel in NO_TOOLS and prompt.get(key):
            errs.append(f"agent.prompt.{key} is set; Phase 0 agents have no tools")
    if prompt.get("tools"):
        errs.append("agent.prompt.tools is deprecated in the spec; use tool_ids (scripts/push_tools.py)")
    if "voice_id" in tts and not allow_voice_id:
        errs.append("tts.voice_id is set; Phase 0a must not record voice IDs (use --allow-voice-id in 0b)")
    if rel in PROMPT_FOR:
        expected = PROMPT_FOR[rel].read_text(encoding="utf-8")
        if prompt.get("prompt") != expected:
            errs.append(f"agent.prompt.prompt differs from {PROMPT_FOR[rel].relative_to(REPO)}")

    # The CLI's own body check (rejects unknown properties).
    out = run_cli(["agents", "create", "--dry-run", "--json", "-"], stdin=json.dumps(cfg, ensure_ascii=False))
    try:
        parsed = json.loads(out)
    except json.JSONDecodeError:
        errs.append(f"CLI dry-run returned non-JSON output: {out[:200]}")
    else:
        if "error" in parsed:
            errs.append(f"CLI schema check: {parsed['error'].get('message')}")
    return errs


def _keys_known(obj: dict, schema: dict, where: str, errs: list[str]) -> None:
    unknown = set(obj) - set(schema.get("properties", {}))
    if unknown:
        errs.append(f"{where}: unknown keys {sorted(unknown)}")


def _check_body_prop(name: str, prop: dict, schemas: dict, where: str, errs: list[str]) -> None:
    kind = prop.get("type")
    key = {"object": "ObjectJsonSchemaProperty-Input", "array": "ArrayJsonSchemaProperty-Input"}.get(
        kind, "LiteralJsonSchemaProperty")
    _keys_known(prop, schemas[key], f"{where}.{name}", errs)
    sources = [k for k in ("description", "dynamic_variable", "constant_value", "is_system_provided", "is_omitted")
               if prop.get(k)]
    if kind not in ("object", "array") and len(sources) != 1:
        errs.append(f"{where}.{name}: needs exactly one of description/dynamic_variable/constant_value, has {sources}")
    if kind == "object":
        for n, p in prop.get("properties", {}).items():
            _check_body_prop(n, p, schemas, f"{where}.{name}", errs)
        missing = set(prop.get("required", [])) - set(prop.get("properties", {}))
        if missing:
            errs.append(f"{where}.{name}: required {sorted(missing)} not in properties")
    if kind == "array":
        _check_body_prop("items", prop.get("items", {}), schemas, f"{where}.{name}", errs)


def check_tool(path: Path, schemas: dict) -> list[str]:
    errs: list[str] = []
    text = path.read_text(encoding="utf-8")
    for ph, val in PLACEHOLDERS.items():
        text = text.replace(ph, val)
    if "{{" in text:
        errs.append("unknown {{placeholder}} left after rendering")
    tool = json.loads(text)
    _keys_known(tool, schemas["WebhookToolConfig-Input"], "tool", errs)
    api = tool.get("api_schema", {})
    _keys_known(api, schemas["WebhookToolApiSchemaConfig-Input"], "api_schema", errs)
    t = tool.get("response_timeout_secs", 20)
    if not isinstance(t, int) or not 5 <= t <= 300:
        errs.append(f"response_timeout_secs={t!r} outside [5, 300]")
    if tool.get("pre_tool_speech", "auto") not in schemas["PreToolSpeechMode"]["enum"]:
        errs.append(f"pre_tool_speech={tool.get('pre_tool_speech')!r} not in PreToolSpeechMode enum")
    if api.get("method") != "POST" or not api.get("url", "").endswith("/tools/" + tool.get("name", "")):
        errs.append("api_schema must POST to {{TOOLS_BASE_URL}}/tools/<name>")
    if not isinstance(api.get("request_headers", {}).get("X-Tool-Secret"), dict):
        errs.append("X-Tool-Secret must be a {secret_id} locator, never a literal")
    body = api.get("request_body_schema", {})
    for n, prop in body.get("properties", {}).items():
        _check_body_prop(n, prop, schemas, "body", errs)
    cid = body.get("properties", {}).get("conversation_id", {})
    if cid.get("dynamic_variable") != "system__conversation_id":
        errs.append("body.conversation_id must bind system__conversation_id")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--allow-voice-id", action="store_true", help="allow tts.voice_id (Phase 0b and later)")
    args = ap.parse_args()

    schemas = load_spec()
    registry = json.loads((AGENT_DIR / "agents.json").read_text(encoding="utf-8"))
    failed = False
    for entry in registry["agents"]:
        rel = entry["config"]
        try:
            cfg = json.loads((AGENT_DIR / rel).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"FAIL {rel}: {exc}")
            failed = True
            continue
        errs = check_config(rel, cfg, schemas, args.allow_voice_id)
        print(f"{'FAIL' if errs else 'OK  '} {rel}")
        for e in errs:
            print(f"     - {e}")
        failed |= bool(errs)

    for path in sorted(TOOL_DIR.glob("*.json.tmpl")):
        errs = check_tool(path, schemas)
        print(f"{'FAIL' if errs else 'OK  '} tool_configs/{path.name}")
        for e in errs:
            print(f"     - {e}")
        failed |= bool(errs)

    push = run_cli(["agents", "push", "--dry-run"])
    push_ok = "error" not in push.lower()
    print(f"{'OK  ' if push_ok else 'FAIL'} agents push --dry-run")
    if not push_ok:
        print(push)
    return 1 if (failed or not push_ok) else 0


if __name__ == "__main__":
    sys.exit(main())
