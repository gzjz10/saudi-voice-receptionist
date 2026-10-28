"""Render agent/agent_configs/sara.json from a prompt file (review M1, task T050).

    python scripts/build_agent_config.py --prompt prompts/system_v0.md --profile phase0
    python scripts/build_agent_config.py --prompt prompts/system_v0.md --check   # exit 1 on drift

The current sara.json is the base, so values chosen in Phase 0b (voice, model, ASR) are kept;
only the prompt is replaced. `--profile full` (tools, dynamic variables) arrives in Phase 2.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "agent" / "agent_configs" / "sara.json"


def render(prompt_path: Path, base_path: Path = CONFIG) -> str:
    cfg = json.loads(base_path.read_text(encoding="utf-8"))
    cfg["conversation_config"]["agent"]["prompt"]["prompt"] = prompt_path.read_text(encoding="utf-8")
    return json.dumps(cfg, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prompt", type=Path, required=True)
    ap.add_argument("--profile", choices=["phase0"], default="phase0")
    ap.add_argument("--check", action="store_true", help="compare with sara.json instead of writing")
    args = ap.parse_args()
    out = render(args.prompt)
    if args.check:
        same = out == CONFIG.read_text(encoding="utf-8")
        print("sara.json matches the prompt" if same else "sara.json differs from the prompt")
        return 0 if same else 1
    CONFIG.write_text(out, encoding="utf-8")
    print(f"wrote {CONFIG.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
