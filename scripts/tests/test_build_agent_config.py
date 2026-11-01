import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import build_agent_config as b  # noqa: E402
import pytest  # noqa: E402

V1 = REPO / "prompts" / "system_v1.md"


def _has_tool_ids() -> bool:
    return any(t.get("id") for t in json.loads(b.TOOLS.read_text(encoding="utf-8")).get("tools", []))


@pytest.mark.skipif(not _has_tool_ids(), reason="tools not pushed yet (scripts/push_tools.py)")
def test_full_render_equals_committed_sara_json():
    assert b.render(V1, "full") == b.CONFIG.read_text(encoding="utf-8")


def test_render_replaces_only_the_prompt(tmp_path):
    prompt = tmp_path / "p.md"
    prompt.write_text("تجربة", encoding="utf-8")
    before = json.loads(b.CONFIG.read_text(encoding="utf-8"))
    after = json.loads(b.render(prompt, "phase0"))
    assert after["conversation_config"]["agent"]["prompt"]["prompt"] == "تجربة"
    after["conversation_config"]["agent"]["prompt"]["prompt"] = before["conversation_config"]["agent"]["prompt"]["prompt"]
    assert after == before


def test_full_profile_attaches_tools_and_end_call(tmp_path, monkeypatch):
    reg = tmp_path / "tools.json"
    reg.write_text(json.dumps({"tools": [{"name": "get_product", "id": "tool_x"}]}), encoding="utf-8")
    monkeypatch.setattr(b, "TOOLS", reg)
    prompt = json.loads(b.render(V1, "full"))["conversation_config"]["agent"]["prompt"]
    assert prompt["tool_ids"] == ["tool_x"]
    assert prompt["built_in_tools"]["end_call"]["params"] == {"system_tool_type": "end_call"}
    assert "tools" not in prompt


@pytest.mark.skipif(not _has_tool_ids(), reason="tools not pushed yet (scripts/push_tools.py)")
def test_check_mode_reports_no_drift():
    r = subprocess.run([sys.executable, str(REPO / "scripts" / "build_agent_config.py"),
                        "--prompt", str(V1), "--profile", "full", "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
