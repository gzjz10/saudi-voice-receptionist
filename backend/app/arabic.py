"""Arabic normalization and product matching (review B4 pipeline, amendment 5).

Normalization only ever builds an internal match key; `name_ar` and spoken fields are
never rewritten.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from rapidfuzz import fuzz

_TASHKEEL = re.compile("[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]")
_TATWEEL = "ـ"
_CLITIC_AL = re.compile(r"^(و|ف)?(ب|ل|ك)?ال")
_CLITIC_LL = re.compile(r"^لل")
_LETTERS = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ة": "ه", "ى": "ي", "ؤ": "و", "ئ": "ي",
})
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_PUNCT = re.compile(r"[^\w\s]|_", re.UNICODE)

# Words that carry no product meaning (normalized form). Review B4 list plus a few
# fillers callers say around a product name.
FILLERS = {
    "بكم", "كم", "عندكم", "فيه", "في", "ابي", "ابغى", "ابغي", "ابغا", "ممكن", "لو", "سمحت",
    "من", "عن", "هل", "وش", "ايش", "سعر", "حق", "يا", "طيب", "الحين", "تكفون", "اريد",
    "موجود", "متوفر", "متوفره", "موجوده", "ودي", "بغيت", "اطلب", "عطني", "عطوني",
}

# Clarification is offered when the runner-up is within this many points of the best.
AMBIGUITY_POINTS = 5
FUZZY_MIN = 82
SUGGEST_MIN = 75
HEAD_BONUS = 6


def strip_marks(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "")
    return _TASHKEEL.sub("", text).replace(_TATWEEL, "")


def strip_clitic(token: str) -> str:
    for rx in (_CLITIC_LL, _CLITIC_AL):
        m = rx.match(token)
        if m and len(token) - m.end() >= 3:
            return token[m.end():]
    return token


def normalize(text: str, drop_fillers: bool = False) -> str:
    """tashkeel/tatweel -> clitics -> letter unify -> digits -> punctuation (-> fillers)."""
    text = _PUNCT.sub(" ", strip_marks(text))
    tokens = [strip_clitic(t) for t in text.split()]
    out = " ".join(tokens).translate(_LETTERS).translate(_DIGITS).lower()
    if drop_fillers:
        out = " ".join(t for t in out.split() if t not in FILLERS)
    return out


# --------------------------------------------------------------------------
# Spoken Saudi numbers -> digits (phones, order ids). Keys are normalized.
# --------------------------------------------------------------------------
UNITS = {
    "صفر": 0, "زيرو": 0, "واحد": 1, "وحده": 1,
    "اثنين": 2, "اثنان": 2, "ثنين": 2, "اتنين": 2, "ثنتين": 2,
    "ثلاثه": 3, "ثلاث": 3, "تلاته": 3, "اربعه": 4, "اربع": 4, "خمسه": 5, "خمس": 5,
    "سته": 6, "ست": 6, "سبعه": 7, "سبع": 7, "ثمانيه": 8, "ثمان": 8, "ثماني": 8, "ثمنيه": 8,
    "تسعه": 9, "تسع": 9,
}
TEENS = {
    "احدعش": 11, "حدعش": 11, "اثنعش": 12, "ثنعش": 12, "ثلطعش": 13, "اربعطعش": 14,
    "خمسطعش": 15, "ستطعش": 16, "سطعش": 16, "سبعطعش": 17, "ثمنطعش": 18, "تسعطعش": 19,
}
TENS = {
    "عشرين": 20, "ثلاثين": 30, "اربعين": 40, "خمسين": 50, "ستين": 60, "سبعين": 70,
    "ثمانين": 80, "تسعين": 90,
}
TEN_WORDS = {"عشر", "عشره"}


def _kind(tok: str):
    if tok in UNITS:
        return "unit", UNITS[tok]
    if tok in TEENS:
        return "teen", TEENS[tok]
    if tok in TENS:
        return "tens", TENS[tok]
    if tok in TEN_WORDS:
        return "ten", 10
    return None, None


def digit_stream(text: str) -> str:
    """'صفر خمسة وخمسين، ثمانية وسبعين' -> '05578'; digits pass through."""
    out: list[str] = []
    pending: int | None = None
    conj = False

    def flush():
        nonlocal pending
        if pending is not None:
            out.append(str(pending))
            pending = None

    for tok in normalize(text).split():
        if tok.isdigit():
            flush()
            out.append(tok)
            conj = False
            continue
        if tok == "و":
            conj = True
            continue
        kind, val = _kind(tok)
        if kind is None and tok.startswith("و") and len(tok) > 2:
            kind, val = _kind(tok[1:])
            conj = conj or kind is not None
        if kind is None:
            flush()
            conj = False
            continue
        if kind == "unit":
            flush()
            pending = val
        elif kind == "ten":
            if pending is not None and 1 <= pending <= 9:
                out.append(str(10 + pending))
                pending = None
            else:
                flush()
                out.append("10")
        elif kind == "teen":
            flush()
            out.append(str(val))
        else:  # tens
            if conj and pending is not None and 1 <= pending <= 9:
                out.append(str(val + pending))
                pending = None
            else:
                flush()
                out.append(str(val))
        conj = False
    flush()
    return "".join(out)


# --------------------------------------------------------------------------
# Product matching
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Hit:
    product_id: str
    score: float


class Matcher:
    """Exact alias phrase first, then fuzzy. Built once from products.json."""

    def __init__(self, products: list[dict]):
        self.keys: list[tuple[str, str]] = []  # (match_key, product_id)
        for p in products:
            for name in [p["name_ar"], *p.get("aliases_ar", [])]:
                key = normalize(name)
                if key:
                    self.keys.append((key, p["id"]))

    def _phrase_hits(self, q: str) -> dict[str, int]:
        padded = f" {q} "
        best: dict[str, int] = {}
        for key, pid in self.keys:
            if f" {key} " in padded:
                best[pid] = max(best.get(pid, 0), len(key))
        return best

    def _fuzzy(self, q: str) -> dict[str, float]:
        best: dict[str, float] = {}
        head = q.split()[0]
        for key, pid in self.keys:
            s = max(fuzz.token_sort_ratio(q, key), 0.9 * fuzz.partial_ratio(q, key))
            # A shared head noun (صحون → صحون زجاج, not صابون صحون) breaks near-ties.
            if key.split()[0] == head:
                s += HEAD_BONUS
            if s > best.get(pid, 0):
                best[pid] = s
        return best

    def match(self, query: str) -> tuple[list[Hit], bool, list[Hit]]:
        """Return (matches ≤ 3, needs_clarification, weak hits for suggestions)."""
        q = normalize(query, drop_fillers=True)
        if not q:
            return [], False, []
        phrase = self._phrase_hits(q)
        if phrase:
            longest = max(phrase.values())
            top = [pid for pid, n in phrase.items() if n == longest]
            hits = [Hit(pid, 100.0) for pid in sorted(top)]
            return hits[:2] if len(hits) > 1 else hits, len(hits) > 1, []
        scored = sorted(self._fuzzy(q).items(), key=lambda kv: (-kv[1], kv[0]))
        strong = [Hit(pid, s) for pid, s in scored if s >= FUZZY_MIN][:3]
        if not strong:
            weak = [Hit(pid, s) for pid, s in scored if s >= SUGGEST_MIN][:2]
            return [], False, weak
        ambiguous = len(strong) > 1 and strong[0].score - strong[1].score <= AMBIGUITY_POINTS
        if ambiguous:
            return strong[:2], True, []
        return strong, False, []

    def similar(self, product_id: str, candidates: list[dict], n: int = 2) -> list[str]:
        """Product ids from `candidates` closest by name to `product_id`'s keys."""
        own = [k for k, pid in self.keys if pid == product_id]
        ranked = []
        for c in candidates:
            keys = [k for k, pid in self.keys if pid == c["id"]]
            s = max(fuzz.token_set_ratio(a, b) for a in own for b in keys)
            ranked.append((s, c["id"]))
        ranked.sort(key=lambda t: (-t[0], t[1]))
        return [pid for _, pid in ranked[:n]]
