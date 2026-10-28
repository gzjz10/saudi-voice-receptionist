"""Phase 0a offline checks on fake data. Runs under pytest or as a plain script:

    python -m pytest phase0/test_phase0.py -q
    python phase0/test_phase0.py

No API key, no network. Nothing here is a Phase 0 result.
"""

from __future__ import annotations

import csv
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))

import stt_score  # noqa: E402
import tts_samples  # noqa: E402
import tts_score  # noqa: E402


def test_stt_scorer_selftest():
    with redirect_stdout(io.StringIO()):
        assert stt_score._selftest() == 0


def test_tts_scorer_selftest():
    with redirect_stdout(io.StringIO()):
        assert tts_score._selftest() == 0


def test_stt_results_template_is_blank_10x2():
    rows = stt_score.read_rows(REPO / "docs" / "phase0" / "stt_results.csv")
    assert len(rows) == 20 and len({r["id"] for r in rows}) == 10
    assert {r["speaker"] for r in rows} == {"S1", "S2"}
    for r in rows:
        for col in ("conversation_id", "transcript_heard", "entities_correct", "intent_ok"):
            assert not r[col].strip(), f"template row {r['id']}/{r['speaker']} has a filled {col}"
    # expected phone/order digits agree with the utterances (the #5 fix)
    for r in rows:
        ents = stt_score.parse_entities(r["critical_entities"])
        for name in ("phone", "order_id"):
            if name in ents:
                assert stt_score.digit_stream(r["utterance"]) == ents[name], (r["id"], ents[name])


def test_tts_ratings_template_header_only():
    with (REPO / "docs" / "phase0" / "tts_ratings.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    assert rows == [["rater_id", "blind_id", "naturalness", "number_correct", "note"]]


def test_tts_script_md_matches_builtin_lines():
    md = tts_samples.parse_script(REPO / "docs" / "phase0" / "tts_script.md")
    assert [(n, lang, text) for n, _, lang, text in md] == \
           [(n, lang, text) for n, _, lang, text in tts_samples.LINES]
    assert len(md) == 8 and all(lang == "ar" for _, _, lang, _ in md)
    assert sum(len(t) for *_, t in md) * 3 * 2 == 2022


def winner_voice_id():
    """Slot A of the voice_selection.md ID table: the 0b winner (Ahmed, 2026-10-28)."""
    text = (REPO / "docs" / "phase0" / "voice_selection.md").read_text(encoding="utf-8")
    import re
    return re.search(r"^\| A \| `([A-Za-z0-9]{20})`", text, re.M).group(1)


def test_agent_config_has_winner_voice_and_no_tools():
    for name in ("sara.json", "sara_stt_probe.json"):
        cfg = json.loads((REPO / "agent" / "agent_configs" / name).read_text(encoding="utf-8"))
        cc = cfg["conversation_config"]
        assert cc["agent"]["language"] == "ar"
        assert cc["tts"].get("voice_id") == winner_voice_id()
        assert not cc["agent"]["prompt"].get("tool_ids") and not cc["agent"]["prompt"].get("tools")
    sara = json.loads((REPO / "agent" / "agent_configs" / "sara.json").read_text(encoding="utf-8"))
    assert sara["conversation_config"]["agent"]["prompt"]["prompt"] == \
        (REPO / "prompts" / "system_v0.md").read_text(encoding="utf-8")


def test_no_voice_ids_in_tracked_phase0_docs():
    # ElevenLabs voice ids are 20-char base62 strings. Since 0b step 3 they may appear only in
    # the ID table of voice_selection.md and in decision.md, copied from find_voices.py output.
    import re
    rx = re.compile(r"\b[A-Za-z0-9]{20}\b")
    allowed = {"voice_selection.md", "decision.md"}
    for p in [*(REPO / "docs").rglob("*.md"), *(REPO / "docs").rglob("*.csv"),
              REPO / "agent" / "agent_configs" / "sara.json"]:
        if p.name in allowed:
            continue
        hits = [h for h in rx.findall(p.read_text(encoding="utf-8")) if not h.isalpha() and not h.isdigit()]
        if p.name == "sara.json":
            hits = [h for h in hits if h != winner_voice_id()]
        assert not hits, f"{p.relative_to(REPO)} contains id-like token(s): {hits}"


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as exc:
                failed += 1
                print(f"FAIL {name}: {exc}")
    print("ALL PASS" if not failed else f"{failed} FAILED")
    sys.exit(1 if failed else 0)
