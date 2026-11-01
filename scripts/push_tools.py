"""Create or update Sara's 6 webhook tools on ElevenLabs (T078-T082, T087).

    python scripts/push_tools.py            # needs scripts/dev.sh + scripts/tunnel.sh running
    python scripts/push_tools.py --dry-run  # render and print, no network call

CLI 1.7.1 has no `tools push` and inline agent `tools` are deprecated, so this script talks to
the REST API that `agents tools create/update/list` wrap. It:
1. refuses unless TOOLS_BASE_URL answers 200 with the secret (a dead quick tunnel is the usual failure);
2. stores TOOL_SECRET as an ElevenLabs workspace secret once and keeps only TOOL_SECRET_ID in .env;
3. renders agent/tool_configs/*.json.tmpl and upserts each tool by name, so a new tunnel URL
   updates the same 6 tools instead of creating new ones;
4. writes the names and ids to agent/tools.json for build_agent_config.py --profile full.
The secret value is never printed.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOL_DIR = REPO / "agent" / "tool_configs"
REGISTRY = REPO / "agent" / "tools.json"
ENV = REPO / ".env"
API = "https://api.elevenlabs.io"
SECRET_NAME = "sara_tool_secret"


def read_env() -> dict[str, str]:
    env = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def set_env(key: str, value: str) -> None:
    lines = ENV.read_text(encoding="utf-8").splitlines()
    lines = [ln for ln in lines if not ln.startswith(key + "=")] + [f"{key}={value}"]
    ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")


def api(method: str, path: str, key: str, body: dict | None = None) -> dict:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method,
                                 headers={"xi-api-key": key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"{method} {path} -> {exc.code}: {exc.read().decode('utf-8', 'replace')[:400]}")


def tunnel_ok(base: str, secret: str) -> bool:
    req = urllib.request.Request(base.rstrip("/") + "/tools/get_store_info", method="POST",
                                 data=json.dumps({"topic": "hours"}).encode(),
                                 headers={"Content-Type": "application/json", "X-Tool-Secret": secret,
                                          "User-Agent": "sara-push-tools"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError):
        return False


def ensure_secret(env: dict[str, str], key: str) -> str:
    if env.get("TOOL_SECRET_ID"):
        return env["TOOL_SECRET_ID"]
    existing = api("GET", "/v1/convai/secrets", key).get("secrets", [])
    for s in existing:
        if s.get("name") == SECRET_NAME:
            raise SystemExit(f"secret {SECRET_NAME!r} exists ({s.get('secret_id')}) but TOOL_SECRET_ID is not in "
                             ".env; its value cannot be read back. Put that id in .env if TOOL_SECRET is "
                             "unchanged, or delete the secret in the dashboard and re-run.")
    out = api("POST", "/v1/convai/secrets", key, {"type": "new", "name": SECRET_NAME, "value": env["TOOL_SECRET"]})
    set_env("TOOL_SECRET_ID", out["secret_id"])
    print(f"created workspace secret {SECRET_NAME} -> TOOL_SECRET_ID written to .env")
    return out["secret_id"]


def render(path: Path, base: str, secret_id: str) -> dict:
    text = path.read_text(encoding="utf-8")
    text = text.replace("{{TOOLS_BASE_URL}}", base.rstrip("/")).replace("{{TOOL_SECRET_ID}}", secret_id)
    if "{{" in text:
        raise SystemExit(f"{path.name}: unrendered placeholder")
    return json.loads(text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="render the tool configs and stop")
    args = ap.parse_args()

    env = read_env()
    base = env.get("TOOLS_BASE_URL", "")
    templates = sorted(TOOL_DIR.glob("*.json.tmpl"))
    if args.dry_run:
        for t in templates:
            cfg = render(t, base or "https://example.trycloudflare.com", env.get("TOOL_SECRET_ID") or "secret_id")
            print(f"{cfg['name']}: POST {cfg['api_schema']['url']}")
        return 0

    key, secret = env.get("ELEVENLABS_API_KEY"), env.get("TOOL_SECRET")
    if not (key and secret and base):
        raise SystemExit("ELEVENLABS_API_KEY, TOOL_SECRET and TOOLS_BASE_URL must be set in .env")
    if not tunnel_ok(base, secret):
        raise SystemExit(f"{base} does not answer 200 with the secret; start scripts/dev.sh and "
                         "scripts/tunnel.sh first")
    secret_id = ensure_secret(env, key)

    remote = {t.get("tool_config", {}).get("name"): t.get("id")
              for t in api("GET", "/v1/convai/tools?types=webhook&page_size=100", key).get("tools", [])}
    registry = []
    for t in templates:
        cfg = render(t, base, secret_id)
        name = cfg["name"]
        if name in remote:
            api("PATCH", f"/v1/convai/tools/{remote[name]}", key, {"tool_config": cfg})
            tool_id, verb = remote[name], "updated"
        else:
            tool_id, verb = api("POST", "/v1/convai/tools", key, {"tool_config": cfg})["id"], "created"
        (TOOL_DIR / f"{name}.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        registry.append({"name": name, "id": tool_id})
        print(f"{verb:7} {name:20} {tool_id}")
    REGISTRY.write_text(json.dumps({"tools": registry}, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    print(f"wrote {REGISTRY.relative_to(REPO)}; next: python scripts/build_agent_config.py "
          "--prompt prompts/system_v1.md --profile full, then agents push")
    return 0


if __name__ == "__main__":
    sys.exit(main())
