from datetime import date, datetime

import pytest

from backend.app.phone import normalize_phone
from backend.app.redact import redact
from backend.app.timeslot import RIYADH, SlotError, resolve
from backend.app.tools import store


@pytest.mark.parametrize("raw", [
    "0551234567", "+966551234567", "966551234567", "00966551234567", "551234567",
    "055 123 4567", "055-123-4567", "+966 55 123 4567", "٠٥٥١٢٣٤٥٦٧",
    "صفر خمسة خمسة، واحد اثنين ثلاثة، أربعة خمسة ستة سبعة",
])
def test_phone_forms(raw):
    assert normalize_phone(raw) == "0551234567"


def test_phone_paired_numbers():
    assert normalize_phone("صفر خمسة وخمسين، ثمانية وسبعين، ثلاثة أربعة خمسة ستة سبعة") == "0557834567"


@pytest.mark.parametrize("raw", ["", None, "12345", "0451234567", "05512345", "05512345678", "رقمي ما اعرفه"])
def test_phone_invalid(raw):
    assert normalize_phone(raw) is None


WED_10 = datetime(2026, 10, 28, 10, 0, tzinfo=RIYADH)   # Wednesday
WED_19 = datetime(2026, 10, 28, 19, 0, tzinfo=RIYADH)


@pytest.mark.parametrize("text,now,day,window,spoken", [
    ("بكرة العصر", WED_10, date(2026, 10, 29), "afternoon", "بكرة العصر"),
    ("اليوم الظهر", WED_10, date(2026, 10, 28), "noon", "اليوم الظهر"),
    ("العصر", WED_10, date(2026, 10, 28), "afternoon", "اليوم العصر"),
    ("الصبح", WED_19, date(2026, 10, 29), "morning", "بكرة الصبح"),
    ("بعد بكرة المغرب", WED_10, date(2026, 10, 30), "evening", "بعد بكرة المغرب"),
    ("يوم السبت بالليل", WED_10, date(2026, 10, 31), "night", "يوم السبت الليل"),
    ("الجمعة العصر", WED_10, date(2026, 10, 30), "afternoon", "بعد بكرة العصر"),
])
def test_slot_resolves(text, now, day, window, spoken):
    s = resolve(text, store(), now)
    assert (s.date, s.window, s.spoken_ar) == (day, window, spoken)


@pytest.mark.parametrize("text,now,code", [
    ("بكرة", WED_10, "missing_field"),
    ("أي وقت", WED_10, "missing_field"),
    ("يوم الجمعة الصبح", WED_10, "outside_hours"),
    ("اليوم الصبح", WED_19, "outside_hours"),
])
def test_slot_errors(text, now, code):
    with pytest.raises(SlotError) as e:
        resolve(text, store(), now)
    assert e.value.code == code


def test_redact():
    text = "أنا فهد ورقمي 0551234567 أو +966551234567 والطلب ٠٥٥١٢٣٤٥٦٧ والسجل 12345678 وطلب 4821"
    out = redact(text, names=["فهد"])
    assert "0551234567" not in out and "966551234567" not in out and "٠٥٥١٢٣٤٥٦٧" not in out
    assert "12345678" not in out and "فهد" not in out
    assert "4821" in out  # 4-digit order ids stay
