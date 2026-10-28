"""Resolve a spoken time slot («بكرة العصر») to {date, window} in Asia/Riyadh."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from .arabic import normalize

RIYADH = ZoneInfo("Asia/Riyadh")

# Normalized cue -> window key of store.time_windows.
WINDOW_CUES = {
    "صبح": "morning", "صباح": "morning", "صبحيه": "morning",
    "ظهر": "noon", "ظهريه": "noon",
    "عصر": "afternoon", "عصريه": "afternoon",
    "مغرب": "evening", "مسا": "evening", "مساء": "evening", "مسائ": "evening",
    "ليل": "night", "بليل": "night",
}
TOMORROW = {"بكره", "بكرا", "باكر", "بكرى"}
# Normalized forms: «اليوم» -> يوم, «الحين» -> حين (clitic ال stripped).
TODAY = {"يوم", "حين"}
# Python weekday(): Monday = 0.
DAYS = {
    "سبت": 5, "احد": 6, "اثنين": 0, "ثلاثاء": 1, "ثلاثا": 1, "اربعاء": 2, "اربعا": 2,
    "خميس": 3, "جمعه": 4,
}
DAY_NAMES_AR = {5: "السبت", 6: "الأحد", 0: "الاثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس", 4: "الجمعة"}


class SlotError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code  # missing_field | outside_hours


@dataclass(frozen=True)
class Slot:
    date: date
    window: str
    spoken_ar: str


def parse_now(now: str | None) -> datetime:
    """`system__time` as ISO 8601 (format UNVERIFIED until Phase 2); else the server clock."""
    if now:
        try:
            dt = datetime.fromisoformat(now.replace("Z", "+00:00"))
            return dt.astimezone(RIYADH) if dt.tzinfo else dt.replace(tzinfo=RIYADH)
        except ValueError:
            pass
    return datetime.now(RIYADH)


def _hhmm(s: str) -> int:
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def _open_hours(store: dict, d: date) -> tuple[int, int]:
    h = store["hours"]["fri" if d.weekday() == 4 else "sat_thu"]
    return _hhmm(h["open"]), _hhmm(h["close"])


def _window_open(store: dict, d: date, window: str) -> bool:
    w = store["time_windows"][window]
    open_, close = _open_hours(store, d)
    return _hhmm(w["to"]) > open_ and _hhmm(w["from"]) < close


def resolve(text: str, store: dict, now: datetime) -> Slot:
    toks = normalize(text).split()
    raw = set(toks)
    window = next((WINDOW_CUES[t] for t in toks if t in WINDOW_CUES), None)
    if window is None:
        raise SlotError("missing_field")
    today = now.date()
    after_tomorrow = "بعد" in raw and raw & TOMORROW
    if after_tomorrow:
        d = today + timedelta(days=2)
    elif raw & TOMORROW:
        d = today + timedelta(days=1)
    else:
        named = next((DAYS[t] for t in toks if t in DAYS), None)
        if named is not None:
            d = today + timedelta(days=(named - today.weekday()) % 7)
        else:
            d = today
    if d == today:
        ends = _hhmm(store["time_windows"][window]["to"])
        if now.hour * 60 + now.minute >= ends:
            if raw & (TODAY | set(DAYS)):
                raise SlotError("outside_hours")
            d = today + timedelta(days=1)
    if not _window_open(store, d, window):
        raise SlotError("outside_hours")
    w_spoken = store["time_windows"][window]["spoken_ar"]
    return Slot(d, window, f"{day_phrase(d, today)} {w_spoken}")


def day_phrase(d: date, today: date) -> str:
    delta = (d - today).days
    if delta == 0:
        return "اليوم"
    if delta == 1:
        return "بكرة"
    if delta == 2:
        return "بعد بكرة"
    return f"يوم {DAY_NAMES_AR[d.weekday()]}"
