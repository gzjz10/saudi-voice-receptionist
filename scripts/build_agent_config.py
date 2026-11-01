"""Render agent/agent_configs/sara.json from a prompt file (review M1, task T050, T081).

    python scripts/build_agent_config.py --prompt prompts/system_v0.md --profile phase0
    python scripts/build_agent_config.py --prompt prompts/system_v1.md --profile full
    python scripts/build_agent_config.py --prompt prompts/system_v1.md --profile full --check   # exit 1 on drift

The current sara.json is the base, so values chosen in Phase 0b (voice, model, ASR) and the
platform limits are kept. `phase0` replaces only the prompt. `full` also attaches the webhook
tools by id from agent/tools.json (written by scripts/push_tools.py) and the end_call built-in.
Arabic only: no language_presets or language_detection (Ahmed, 2026-10-28).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "agent" / "agent_configs" / "sara.json"
TOOLS = REPO / "agent" / "tools.json"

END_CALL = {
    "name": "end_call",
    "description": "End the call after the caller says goodbye, the order number has been read out, "
                   "or a callback ticket has been confirmed.",
    "params": {"system_tool_type": "end_call"},
}


def tool_ids() -> list[str]:
    tools = json.loads(TOOLS.read_text(encoding="utf-8")).get("tools", [])
    ids = [t["id"] for t in tools if t.get("id")]
    if not ids:
        raise SystemExit("agent/tools.json has no tool ids; run scripts/push_tools.py first")
    return ids


def render(prompt_path: Path, profile: str, base_path: Path = CONFIG) -> str:
    cfg = json.loads(base_path.read_text(encoding="utf-8"))
    prompt = cfg["conversation_config"]["agent"]["prompt"]
    prompt["prompt"] = prompt_path.read_text(encoding="utf-8")
    if profile == "full":
        prompt["tool_ids"] = tool_ids()
        prompt["built_in_tools"] = {"end_call": END_CALL}
    return json.dumps(cfg, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prompt", type=Path, required=True)
    ap.add_argument("--profile", choices=["phase0", "full"], default="phase0")
    ap.add_argument("--check", action="store_true", help="compare with sara.json instead of writing")
    args = ap.parse_args()
    out = render(args.prompt, args.profile)
    if args.check:
        same = out == CONFIG.read_text(encoding="utf-8")
        print("sara.json matches the prompt" if same else "sara.json differs from the prompt")
        return 0 if same else 1
    CONFIG.write_text(out, encoding="utf-8")
    print(f"wrote {CONFIG.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
