#!/usr/bin/env python3
"""Phase 0b STT scorer for the Saudi Voice Receptionist.

Scores the 10-utterance x 2-speaker STT sheet (docs/phase0/stt_results.csv)
against the Phase 0 STT gate in reviews/plan-review.md section G.3.
Entities are scored, not WER; a simple character error rate is printed
for information only.

Usage (python 3.12, standard library only for scoring):
    python phase0/stt_score.py docs/phase0/stt_results.csv
    python phase0/stt_score.py docs/phase0/stt_results.csv --fetch
    python phase0/stt_score.py docs/phase0/stt_results.csv --add-run scribe_realtime
    python phase0/stt_score.py --selftest

--fetch fills empty `transcript_heard` cells from the realtime-ASR transcript
of each row's `conversation_id`:
    GET https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}
    header  xi-api-key: $ELEVENLABS_API_KEY
    reads   transcript[].message where transcript[].role == "user"
Verified 2026-10-27 against
    https://elevenlabs.io/docs/api-reference/conversations/get
    https://elevenlabs.io/docs/api-reference/authentication
Never exercised against the live API yet (no key on the laptop): run it once
on the Mac and check the result by hand before trusting it.

Thresholds are proposals for Ahmed to confirm before 0b (plan-review.md G).
Nothing printed by this script is a result unless the CSV holds real
transcripts from real calls.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------
# Gate thresholds: reviews/plan-review.md section G.3 (proposals, 2026-10-27)
# --------------------------------------------------------------------------
GATE = {
    "clips_per_run": 20,          # 10 utterances x 2 speakers
    "intent_min": 18,             # (a) intent recoverable in >= 18/20
    "english_ids": ("10",),       # (a) both English clips transcribed in English
    "product_ids": ("1", "2", "3"),
    "product_min": 5,             # (b) product correct in >= 5/6
    "qty_id": "3",                # (c) quantity 2/2
    "order_id_id": "6",           # (c) order-id digits exact 2/2
    "phone_ids": ("4", "5"),
    "phone_digit_acc_min": 0.95,  # (d) >= 95% over 40 digits (<= 2 wrong)
    "phone_exact_min": 2,         # (d) >= 2/4 exactly right
    "area_slot_id": "7",          # (e) area + slot 2/2
    "hours_id": "8",              # (e) hours/day 2/2
    "escalate_id": "9",           # (e) escalation 2/2
    "min_providers": 2,           # G.3: default asr.provider + one other
}

COLUMNS = [
    "id", "speaker", "asr_provider", "utterance", "intent",
    "critical_entities", "acceptable_variants", "speaker_notes",
    "conversation_id", "transcript_heard", "entities_correct",
    "intent_ok", "notes",
]

API_BASE = "https://api.elevenlabs.io"

# --------------------------------------------------------------------------
# Arabic normalization (order follows plan-review.md B4)
# --------------------------------------------------------------------------
_TASHKEEL = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭ]")
_TATWEEL = "ـ"
_CLITIC_AL = re.compile(r"^(و|ف)?(ب|ل|ك)?ال")
_CLITIC_LL = re.compile(r"^لل")
_LETTERS = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ة": "ه", "ى": "ي", "ؤ": "و", "ئ": "ي",
})
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_PUNCT = re.compile(r"[^\w\s]|_", re.UNICODE)


def strip_marks(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "")
    return _TASHKEEL.sub("", text).replace(_TATWEEL, "")


def strip_clitic(token: str) -> str:
    for rx in (_CLITIC_LL, _CLITIC_AL):
        m = rx.match(token)
        if m and len(token) - m.end() >= 3:
            return token[m.end():]
    return token


def normalize(text: str, clitics: bool = False) -> str:
    """tashkeel/tatweel -> (clitics) -> letter unify -> digits -> punct -> lower."""
    text = strip_marks(text)
    text = _PUNCT.sub(" ", text)
    tokens = text.split()
    if clitics:
        tokens = [strip_clitic(t) for t in tokens]
    out = " ".join(tokens).translate(_LETTERS).translate(_DIGITS)
    return out.lower()


# --------------------------------------------------------------------------
# Spoken Saudi numbers -> digits (enough for phones, order ids, quantities)
# Keys are already normalized (ة->ه, أ->ا, ى->ي).
# --------------------------------------------------------------------------
UNITS = {
    "صفر": 0, "زيرو": 0,
    "واحد": 1, "وحده": 1,
    "اثنين": 2, "اثنان": 2, "ثنين": 2, "اتنين": 2, "اثنتين": 2,
    "ثنتين": 2, "اثنا": 2, "اثني": 2,
    "ثلاثه": 3, "ثلاث": 3, "تلاته": 3, "تلات": 3,
    "اربعه": 4, "اربع": 4,
    "خمسه": 5, "خمس": 5,
    "سته": 6, "ست": 6,
    "سبعه": 7, "سبع": 7,
    "ثمانيه": 8, "ثمان": 8, "ثماني": 8, "ثمنيه": 8, "تمانيه": 8,
    "تسعه": 9, "تسع": 9,
}
TEN_WORDS = {"عشر", "عشره"}
TEENS = {
    "احدعش": 11, "حدعش": 11, "احدعشر": 11, "حداش": 11,
    "اثنعش": 12, "اثنعشر": 12, "ثنعش": 12, "اطنعش": 12, "اتنعش": 12,
    "ثلطعش": 13, "ثلاثطعش": 13, "تلطعش": 13,
    "اربعطعش": 14, "اربعتعش": 14,
    "خمسطعش": 15, "خمستعش": 15,
    "سطعش": 16, "ستطعش": 16,
    "سبعطعش": 17, "سبعتعش": 17,
    "ثمنطعش": 18, "ثمانطعش": 18, "ثمانتعش": 18,
    "تسعطعش": 19, "تسعتعش": 19,
}
TENS = {
    "عشرين": 20, "ثلاثين": 30, "تلاتين": 30, "اربعين": 40, "خمسين": 50,
    "ستين": 60, "سبعين": 70, "ثمانين": 80, "تمانين": 80, "تسعين": 90,
}


def _word_kind(tok: str):
    if tok in UNITS:
        return "unit", UNITS[tok]
    if tok in TEENS:
        return "teen", TEENS[tok]
    if tok in TENS:
        return "tens", TENS[tok]
    if tok in TEN_WORDS:
        return "ten", 10
    return None, None


def number_tokens(text: str) -> list[str]:
    """Return the numbers in `text`, in order, as digit strings.

    'صفر خمسة وخمسين' -> ['0', '55']; 'اثنا عشر' -> ['12'];
    '055 123 4567' -> ['055', '123', '4567']; 'خمسة خمسين' -> ['5', '50'].
    """
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
        kind, val = _word_kind(tok)
        if kind is None and tok.startswith("و") and len(tok) > 2:
            kind, val = _word_kind(tok[1:])
            if kind is not None:
                conj = True
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
        elif kind == "tens":
            if conj and pending is not None and 1 <= pending <= 9:
                out.append(str(val + pending))
                pending = None
            else:
                flush()
                out.append(str(val))
        conj = False
    flush()
    return out


def digit_stream(text: str) -> str:
    return "".join(number_tokens(text))


def levenshtein(a, b) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def cer(reference: str, hypothesis: str) -> float | None:
    ref = normalize(reference)
    hyp = normalize(hypothesis)
    if not ref or not hyp:
        return None
    return levenshtein(ref, hyp) / len(ref)


# --------------------------------------------------------------------------
# Entity and intent checks
# --------------------------------------------------------------------------
NUMERIC = {"qty", "phone", "order_id"}

# Intent cue groups: every group needs at least one cue (normalized,
# clitic-stripped). Heuristic only; a human `intent_ok` always wins.
INTENT_CUES = {
    "price_check": [["بكم", "بكام", "سعر", "كم"]],
    "availability": [["عندكم", "فيه", "موجود", "متوفر", "توفر"]],
    "order_item": [["ابي", "ابغي", "ابغا", "ودي", "اطلب", "بغيت"]],
    "give_phone": [["رقمي", "جوالي", "رقم", "جوال"]],
    "order_status": [["طلبي", "طلب", "طلبيه"], ["وين", "وصل", "متي"]],
    "delivery_order": [["delivery", "ديليفري", "دليفري", "توصيل", "توصلون", "وصلوه"]],
    "store_hours": [["تفتحون", "تفتحو", "تفتحوا", "دوام", "دوامكم", "فاتحين", "مفتوح", "تسكرون"]],
    "escalate": [["موظف", "اكلم", "مسوول", "مدير", "احد"]],
    "delivery_area_question": [["deliver", "delivery"]],
}


def _phrase_in(phrase: str, haystack: str) -> bool:
    p = normalize(phrase, clitics=True)
    return bool(p) and f" {p} " in f" {haystack} "


def _alt_matches(alt: str, haystack: str) -> bool:
    return all(_phrase_in(part, haystack) for part in alt.split("+") if part.strip())


def is_english(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    latin = sum(1 for c in letters if "a" <= c.lower() <= "z")
    return latin / len(letters) >= 0.6


def parse_entities(cell: str) -> dict[str, str]:
    ents = {}
    for chunk in (cell or "").split("|"):
        if "=" in chunk:
            k, v = chunk.split("=", 1)
            ents[k.strip()] = v.strip()
    return ents


def parse_variants(cell: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for chunk in (cell or "").split("|"):
        if ":" in chunk:
            k, v = chunk.split(":", 1)
            out[k.strip()] = [x.strip() for x in v.split(";") if x.strip()]
    return out


@dataclass
class EntityResult:
    name: str
    ok: bool
    detail: str = ""
    digits_total: int = 0
    digits_wrong: int = 0


def check_entity(name: str, expected: str, variants: list[str], transcript: str) -> EntityResult:
    if name == "lang":
        ok = is_english(transcript) if expected == "en" else not is_english(transcript)
        return EntityResult(name, ok, f"lang={'en' if is_english(transcript) else 'ar'}")
    if name in NUMERIC:
        nums = number_tokens(transcript)
        if name == "qty":
            ok = expected in nums
            return EntityResult(name, ok, f"numbers={nums}")
        stream = "".join(nums)
        wrong = min(levenshtein(expected, stream), len(expected))
        return EntityResult(name, stream == expected, f"digits={stream or '-'}",
                            len(expected), wrong)
    hay = normalize(transcript, clitics=True)
    forbidden = [v[1:] for v in variants if v.startswith("!")]
    alts = [expected] + [v for v in variants if not v.startswith("!")]
    hit = next((a for a in alts if _alt_matches(a, hay)), None)
    bad = next((f for f in forbidden if _phrase_in(f, hay)), None)
    if bad:
        return EntityResult(name, False, f"forbidden '{bad}'")
    return EntityResult(name, hit is not None, f"matched '{hit}'" if hit else "no match")


def auto_intent(intent: str, transcript: str, entities: list[EntityResult]) -> bool:
    hay = normalize(transcript, clitics=True)
    groups = INTENT_CUES.get(intent)
    if not groups:
        return False
    cue_ok = all(any(_phrase_in(c, hay) for c in g) for g in groups)
    if intent == "give_phone" and not cue_ok:
        cue_ok = len(digit_stream(transcript)) >= 9
    return cue_ok


# --------------------------------------------------------------------------
# Row scoring
# --------------------------------------------------------------------------
def _parse_human_entities(cell: str, names: list[str]):
    """'x/n' or 'product=1;qty=0'. Returns ({name: bool}, warning)."""
    cell = (cell or "").strip()
    if not cell:
        return None, ""
    per = dict(re.findall(r"([a-z_]+)\s*=\s*([01])", cell))
    if per:
        return {k: v == "1" for k, v in per.items() if k in names}, ""
    m = re.fullmatch(r"(\d+)\s*/\s*(\d+)", cell)
    if not m:
        return None, f"unreadable entities_correct '{cell}'"
    x, n = int(m.group(1)), int(m.group(2))
    if n != len(names):
        return None, f"entities_correct n={n} but sheet has {len(names)} entities"
    if x == n:
        return {k: True for k in names}, ""
    if x == 0:
        return {k: False for k in names}, ""
    return None, "partial x/n override: use 'name=1;name=0' form; auto values kept"


def _parse_yes_no(cell: str):
    c = (cell or "").strip().lower()
    if c in {"y", "yes", "1", "true", "ok", "نعم"}:
        return True
    if c in {"n", "no", "0", "false", "لا"}:
        return False
    return None


@dataclass
class ClipScore:
    row: dict
    entities: list[EntityResult] = field(default_factory=list)
    final: dict[str, bool] = field(default_factory=dict)
    intent_auto: bool = False
    intent_final: bool = False
    cer: float | None = None
    warnings: list[str] = field(default_factory=list)
    scored: bool = False

    @property
    def key(self):
        return self.row["id"].strip()


def score_row(row: dict) -> ClipScore:
    cs = ClipScore(row)
    transcript = (row.get("transcript_heard") or "").strip()
    expected = parse_entities(row.get("critical_entities", ""))
    variants = parse_variants(row.get("acceptable_variants", ""))
    if not transcript:
        return cs
    cs.scored = True
    for name, exp in expected.items():
        cs.entities.append(check_entity(name, exp, variants.get(name, []), transcript))
    cs.final = {e.name: e.ok for e in cs.entities}
    human, warn = _parse_human_entities(row.get("entities_correct", ""), list(expected))
    if warn:
        cs.warnings.append(warn)
    if human:
        for k, v in human.items():
            if cs.final.get(k) != v:
                cs.warnings.append(f"human overrides {k}: auto={cs.final.get(k)} human={v}")
            cs.final[k] = v
    cs.intent_auto = auto_intent(row.get("intent", ""), transcript, cs.entities)
    h_int = _parse_yes_no(row.get("intent_ok", ""))
    cs.intent_final = cs.intent_auto if h_int is None else h_int
    if h_int is not None and h_int != cs.intent_auto:
        cs.warnings.append(f"human overrides intent: auto={cs.intent_auto} human={h_int}")
    cs.cer = cer(row.get("utterance", ""), transcript)
    return cs


# --------------------------------------------------------------------------
# Gate evaluation per provider
# --------------------------------------------------------------------------
@dataclass
class RunVerdict:
    provider: str
    clips: list[ClipScore]
    checks: list[tuple[str, bool, str]] = field(default_factory=list)
    complete: bool = False
    entity_acc: float = 0.0
    intent_acc: float = 0.0
    mean_cer: float | None = None

    @property
    def passed(self) -> bool:
        return self.complete and all(ok for _, ok, _ in self.checks)


def _ent(clips, cid, name):
    return [c.final.get(name, False) for c in clips if c.key == cid]


def evaluate_run(provider: str, clips: list[ClipScore]) -> RunVerdict:
    v = RunVerdict(provider, clips)
    scored = [c for c in clips if c.scored]
    v.complete = len(scored) == GATE["clips_per_run"] == len(clips)
    n_ent = sum(len(c.final) for c in scored)
    v.entity_acc = sum(sum(c.final.values()) for c in scored) / n_ent if n_ent else 0.0
    v.intent_acc = sum(c.intent_final for c in scored) / len(scored) if scored else 0.0
    cers = [c.cer for c in scored if c.cer is not None]
    v.mean_cer = sum(cers) / len(cers) if cers else None

    intents = sum(c.intent_final for c in scored)
    eng = [x for cid in GATE["english_ids"] for x in _ent(scored, cid, "lang")]
    eng_ok = len(eng) == 2 * len(GATE["english_ids"]) and all(eng)
    v.checks.append(("(a) intent >= %d/20 + English clips in English" % GATE["intent_min"],
                     intents >= GATE["intent_min"] and eng_ok,
                     f"intent {intents}/{len(scored)}, english {sum(eng)}/{len(eng)}"))

    prod = [x for cid in GATE["product_ids"] for x in _ent(scored, cid, "product")]
    v.checks.append(("(b) product >= %d/6" % GATE["product_min"],
                     sum(prod) >= GATE["product_min"], f"{sum(prod)}/{len(prod)}"))

    qty = _ent(scored, GATE["qty_id"], "qty")
    oid = _ent(scored, GATE["order_id_id"], "order_id")
    v.checks.append(("(c) qty 2/2 and order id 2/2",
                     len(qty) == 2 and all(qty) and len(oid) == 2 and all(oid),
                     f"qty {sum(qty)}/{len(qty)}, order id {sum(oid)}/{len(oid)}"))

    total = wrong = exact = n_phone = 0
    for c in scored:
        if c.key in GATE["phone_ids"]:
            e = next((e for e in c.entities if e.name == "phone"), None)
            if e is None:
                continue
            n_phone += 1
            ok = c.final.get("phone", False)
            total += e.digits_total
            wrong += 0 if ok else max(e.digits_wrong, 1)
            exact += ok
    acc = (total - wrong) / total if total else 0.0
    v.checks.append(("(d) phone digits >= %d%% and >= %d/4 exact"
                     % (GATE["phone_digit_acc_min"] * 100, GATE["phone_exact_min"]),
                     n_phone == 4 and acc >= GATE["phone_digit_acc_min"]
                     and exact >= GATE["phone_exact_min"],
                     f"{total - wrong}/{total} digits ({acc:.1%}), exact {exact}/{n_phone}"))

    area = _ent(scored, GATE["area_slot_id"], "area")
    slot = _ent(scored, GATE["area_slot_id"], "slot")
    day = _ent(scored, GATE["hours_id"], "day")
    hrs = [c.intent_final for c in scored if c.key == GATE["hours_id"]]
    esc = [c.intent_final for c in scored if c.key == GATE["escalate_id"]]
    e_ok = (len(area) == 2 and all(area) and all(slot) and len(day) == 2 and all(day)
            and len(hrs) == 2 and all(hrs) and len(esc) == 2 and all(esc))
    v.checks.append(("(e) area+slot 2/2, hours/day 2/2, escalation 2/2", e_ok,
                     f"area {sum(area)}/{len(area)}, slot {sum(slot)}/{len(slot)}, "
                     f"hours {sum(hrs)}/{len(hrs)}, day {sum(day)}/{len(day)}, "
                     f"escalate {sum(esc)}/{len(esc)}"))
    return v


# --------------------------------------------------------------------------
# CSV I/O, fetch, reporting
# --------------------------------------------------------------------------
def read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    missing = [c for c in COLUMNS if rows and c not in rows[0]]
    if missing:
        raise SystemExit(f"{path}: missing columns {missing}")
    return rows


def write_rows(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in COLUMNS})


def load_api_key() -> str | None:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if key:
        return key
    env = Path(__file__).resolve().parent.parent / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("ELEVENLABS_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'") or None
    return None


def fetch_user_text(conversation_id: str, key: str) -> str:
    url = f"{API_BASE}/v1/convai/conversations/{urllib.request.quote(conversation_id)}"
    req = urllib.request.Request(url, headers={"xi-api-key": key, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if data.get("status") not in ("done", None):
        raise RuntimeError(f"conversation status is {data.get('status')!r}, try again later")
    msgs = [t.get("message") or "" for t in data.get("transcript", []) if t.get("role") == "user"]
    return " / ".join(m.strip() for m in msgs if m.strip())


def do_fetch(path: Path, rows: list[dict]) -> None:
    key = load_api_key()
    if not key:
        raise SystemExit("ELEVENLABS_API_KEY not set (env or .env); nothing fetched.")
    changed = 0
    for r in rows:
        cid = (r.get("conversation_id") or "").strip()
        if cid and not (r.get("transcript_heard") or "").strip():
            try:
                r["transcript_heard"] = fetch_user_text(cid, key)
                changed += 1
            except (urllib.error.URLError, RuntimeError, ValueError) as exc:
                print(f"  fetch failed for id={r['id']} {r['speaker']} {cid}: {exc}", file=sys.stderr)
    write_rows(path, rows)
    print(f"fetched {changed} transcript(s) into {path}")


def add_run(path: Path, rows: list[dict], provider: str) -> None:
    base = [r for r in rows if r["asr_provider"] == rows[0]["asr_provider"]]
    for r in base:
        new = {k: r.get(k, "") for k in COLUMNS}
        new.update(asr_provider=provider, conversation_id="", transcript_heard="",
                   entities_correct="", intent_ok="", notes="")
        rows.append(new)
    write_rows(path, rows)
    print(f"appended {len(base)} blank rows for asr_provider={provider} to {path}")


def report(rows: list[dict], allow_single: bool = False, out=None) -> bool:
    out = out or sys.stdout
    runs: dict[str, list[ClipScore]] = {}
    for r in rows:
        runs.setdefault(r["asr_provider"].strip() or "?", []).append(score_row(r))

    verdicts = []
    for provider, clips in runs.items():
        v = evaluate_run(provider, clips)
        verdicts.append(v)
        print(f"\n== asr_provider: {provider} ==", file=out)
        print(f"{'id':>3} {'spk':<3} {'entities':<9} {'intent':<6} {'cer':>5}  detail", file=out)
        for c in clips:
            if not c.scored:
                print(f"{c.key:>3} {c.row['speaker']:<3} {'-':<9} {'-':<6} {'-':>5}  (no transcript)", file=out)
                continue
            ent = f"{sum(c.final.values())}/{len(c.final)}"
            cer_s = f"{c.cer:.2f}" if c.cer is not None else "-"
            det = "; ".join(f"{e.name}:{'ok' if c.final[e.name] else 'X'} {e.detail}" for e in c.entities)
            print(f"{c.key:>3} {c.row['speaker']:<3} {ent:<9} {'ok' if c.intent_final else 'X':<6} {cer_s:>5}  {det}", file=out)
            for w in c.warnings:
                print(f"{'':>14}! {w}", file=out)
        cer_txt = f"{v.mean_cer:.2f}" if v.mean_cer is not None else "-"
        print(f"overall entity accuracy {v.entity_acc:.1%} | intent accuracy {v.intent_acc:.1%} "
              f"| mean CER {cer_txt} (info only) | clips scored "
              f"{sum(c.scored for c in clips)}/{len(clips)}", file=out)
        for name, ok, detail in v.checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}", file=out)
        print(f"  run verdict: {'PASS' if v.passed else ('FAIL' if v.complete else 'INCOMPLETE')}", file=out)

    complete = [v for v in verdicts if v.complete]
    best = max(complete, key=lambda v: (v.passed, sum(ok for _, ok, _ in v.checks), v.entity_acc),
               default=None)
    print("\n== STT GATE (plan-review.md G.3, thresholds pending Ahmed's confirmation) ==", file=out)
    if best is None:
        print("STT GATE: INCOMPLETE - no provider has all 20 clips transcribed.", file=out)
        return False
    if len(complete) < GATE["min_providers"] and not allow_single:
        print(f"best so far: {best.provider} ({'PASS' if best.passed else 'FAIL'})", file=out)
        print(f"STT GATE: INCOMPLETE - G.3 needs {GATE['min_providers']} asr.provider runs, "
              f"have {len(complete)} complete (use --add-run).", file=out)
        return False
    print(f"best provider: {best.provider}", file=out)
    if best.passed:
        print("STT GATE: PASS", file=out)
    else:
        print("STT GATE: FAIL -> RETRY once (30 min): switch asr.provider, add product names "
              "to asr.keywords, re-run failing clips; then NO-GO -> Vapi + Azure ar-SA STT.", file=out)
    return best.passed


# --------------------------------------------------------------------------
# Self-test on a synthetic filled example (fake transcripts, not results)
# --------------------------------------------------------------------------
SHEET = Path(__file__).resolve().parent.parent / "docs" / "phase0" / "stt_results.csv"

GOOD = {  # (id, speaker) -> transcript; Arabic-Indic digits, tashkeel, ال/لل on purpose
    ("1", "S1"): "بكم الصُّحون الزجاج؟", ("1", "S2"): "بكم صحون الزياي",
    ("2", "S1"): "عندكم كاسات ورق", ("2", "S2"): "عندكم اكواب ورق؟",
    ("3", "S1"): "أبي اثنعش علبة من أكياس الزبالة", ("3", "S2"): "ابي ١٢ علبه اكياس زباله",
    ("4", "S1"): "رقمي صفر خمسة خمسة واحد اثنين ثلاثة أربعة خمسة ستة سبعة",
    ("4", "S2"): "رقمي ٠٥٥ ١٢٣ ٤٥٦٧",
    ("5", "S1"): "جوالي صفر خمسة وخمسين ثمانية وسبعين ثلاثة أربعة خمسة ستة سبعة",
    ("5", "S2"): "جوالي 055 78 34567",
    ("6", "S1"): "وين وصل طلبي رقمه أربعة ثمانية اثنين واحد", ("6", "S2"): "وين وصل طلبي رقمه ٤٨٢١",
    ("7", "S1"): "أبي delivery للمبرز بكرة العصر", ("7", "S2"): "ابي ديليفري المبرز بكره العصر",
    ("8", "S1"): "متى تفتحون يوم الجمعة", ("8", "S2"): "متى تفتحون يوم الجمعه؟",
    ("9", "S1"): "أبي أكلم موظف", ("9", "S2"): "ابي اكلم موظف!",
    ("10", "S1"): "Do you deliver to Hofuf?", ("10", "S2"): "do you deliver to al hofuf",
}
BAD = dict(GOOD)
BAD.update({
    ("1", "S1"): "بكم الصحون البلاستيك",          # near-duplicate trap -> product wrong
    ("2", "S2"): "عندكم كاسات",                   # product incomplete
    ("4", "S2"): "رقمي ٠٥٥ ١٢٨ ٤٥٦٧",             # one digit wrong
    ("5", "S1"): "جوالي صفر خمسة خمسين ثمانية سبعين ثلاثة",  # paired numbers mangled
    ("10", "S2"): "دو يو ديليفر تو الهفوف",       # transcribed in Arabic script
})


def _selftest() -> int:
    # unit checks
    assert normalize("الصُّحـون") == "الصحون"
    assert normalize("إأآٱ ة ى ؤ ئ") == "اااا ه ي و ي"
    assert normalize("٠٥٥١٢٣٤٥٦٧") == "0551234567"
    assert normalize("للمبرز والصحون", clitics=True) == "مبرز صحون"
    assert normalize("بكرة", clitics=True) == "بكره"
    assert digit_stream("صفر خمسة وخمسين، ثمانية وسبعين، ثلاثة أربعة خمسة ستة سبعة") == "0557834567"
    assert digit_stream("صفر خمسة و خمسين") == "055"
    assert number_tokens("اثنا عشر علبة") == ["12"]
    assert number_tokens("أبي اثنعش علبة") == ["12"]
    assert digit_stream("رقمه أربعة، ثمانية، اثنين، واحد") == "4821"
    assert levenshtein("0551234567", "0551284567") == 1
    assert is_english("Do you deliver to Hofuf?") and not is_english("دو يو ديليفر")
    assert check_entity("product", "صحون زجاج", ["!بلاستيك"], "الصحون البلاستيك").ok is False
    assert check_entity("slot", "بكرة+العصر", [], "بكره وقت العصر").ok is True

    template = read_rows(SHEET)
    assert len(template) == 20 and len({r["id"] for r in template}) == 10, "sheet must be 10 x 2"

    def filled(provider, transcripts):
        rows = []
        for r in template:
            r = dict(r, asr_provider=provider)
            r["transcript_heard"] = transcripts[(r["id"], r["speaker"])]
            rows.append(r)
        return rows

    rows = filled("selftest_good", GOOD) + filled("selftest_bad", BAD)
    buf = io.StringIO()
    ok = report(rows, out=buf)
    text = buf.getvalue()
    print(text)
    runs = {}
    for r in rows:
        runs.setdefault(r["asr_provider"], []).append(score_row(r))
    good = evaluate_run("selftest_good", runs["selftest_good"])
    bad = evaluate_run("selftest_bad", runs["selftest_bad"])
    assert good.passed and good.entity_acc == 1.0, good.checks
    assert not bad.passed
    failed = {name[:3] for name, ok_, _ in bad.checks if not ok_}
    assert failed == {"(a)", "(b)", "(d)"}, failed
    assert ok is True and "STT GATE: PASS" in text
    # single provider must not pass the gate without --allow-single-provider
    assert report(filled("only_one", GOOD), out=io.StringIO()) is False
    assert report(filled("only_one", GOOD), allow_single=True, out=io.StringIO()) is True
    print("SELFTEST OK (synthetic transcripts; not a Phase 0 result)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="?", type=Path, help="filled docs/phase0/stt_results.csv")
    ap.add_argument("--fetch", action="store_true", help="fill empty transcripts from the ElevenLabs API")
    ap.add_argument("--add-run", metavar="PROVIDER", help="append 20 blank rows for another asr.provider")
    ap.add_argument("--allow-single-provider", action="store_true",
                    help="judge the gate on one provider run (G.3 asks for two)")
    ap.add_argument("--selftest", action="store_true", help="run the synthetic self-test")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    if a.selftest:
        return _selftest()
    if not a.csv:
        ap.error("csv path required (or --selftest)")
    rows = read_rows(a.csv)
    if a.add_run:
        add_run(a.csv, rows, a.add_run)
        return 0
    if a.fetch:
        do_fetch(a.csv, rows)
    return 0 if report(rows, allow_single=a.allow_single_provider) else 1


if __name__ == "__main__":
    sys.exit(main())
