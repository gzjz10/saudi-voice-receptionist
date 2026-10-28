import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import build_agent_config as b  # noqa: E402


def test_phase0_render_equals_committed_sara_json():
    assert b.render(REPO / "prompts" / "system_v0.md") == b.CONFIG.read_text(encoding="utf-8")


def test_render_replaces_only_the_prompt(tmp_path):
    prompt = tmp_path / "p.md"
    prompt.write_text("تجربة", encoding="utf-8")
    before = json.loads(b.CONFIG.read_text(encoding="utf-8"))
    after = json.loads(b.render(prompt))
    assert after["conversation_config"]["agent"]["prompt"]["prompt"] == "تجربة"
    after["conversation_config"]["agent"]["prompt"]["prompt"] = before["conversation_config"]["agent"]["prompt"]["prompt"]
    assert after == before


def test_check_mode_reports_no_drift():
    r = subprocess.run([sys.executable, str(REPO / "scripts" / "build_agent_config.py"),
                        "--prompt", str(REPO / "prompts" / "system_v0.md"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
