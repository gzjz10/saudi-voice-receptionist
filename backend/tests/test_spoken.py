import csv
from pathlib import Path

import pytest

from backend.app import spoken

GOLDEN = Path(__file__).with_name("golden_spoken.csv")
UNITS = {"علبة": ("علبتين", "علب"), "طقم": ("طقمين", "أطقم"), "حبة": ("حبتين", "حبات")}


def rows():
    lines = [l for l in GOLDEN.read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")]
    return list(csv.DictReader(lines))


def render(kind: str, value: str) -> str:
    if kind == "money":
        return spoken.money_ar(int(value))
    if kind == "phone":
        return spoken.phone_ar(value)
    if kind == "order_id":
        return spoken.order_id_ar(value)
    qty, unit, gender = value.split("|")
    dual, plural = UNITS[unit]
    return spoken.qty_ar(int(qty), unit, dual, plural, gender)


@pytest.mark.parametrize("row", rows(), ids=lambda r: f"{r['kind']}-{r['input']}")
def test_golden_spoken(row):
    assert render(row["kind"], row["input"]) == row["expected"]


def test_signed_tts_lines_present():
    signed = {r["source"] for r in rows() if r["source"].startswith("tts_line_")}
    assert signed == {f"tts_line_{n}" for n in range(2, 7)}


def test_signed_lines_match_tts_script():
    script = Path(__file__).resolve().parents[2] / "docs" / "phase0" / "tts_script.md"
    text = script.read_text(encoding="utf-8")
    for r in rows():
        if r["source"].startswith("tts_line_"):
            assert r["expected"] in text, r


def test_number_words():
    assert spoken.number_ar(117) == "مية وسبعطعش"
    assert spoken.number_ar(2965) == "ألفين وتسعمية وخمسة وستين"
