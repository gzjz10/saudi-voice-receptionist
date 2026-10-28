#!/usr/bin/env python3
"""Phase 0b TTS dialect gate scorer (reviews/plan-review.md section G.2).

Joins the raters' blind ratings with the blind key written by tts_samples.py
--blind and decides GO / RETRY / GO_WITH_RISK_FLAG / NO_GO per (voice, model).

    python phase0/tts_score.py docs/phase0/tts_ratings.csv phase0/samples/blind_key.csv
    python phase0/tts_score.py ... --round retry
    python phase0/tts_score.py --selftest

ratings CSV columns : rater_id,blind_id,naturalness,number_correct,note
                      (one file; raters' sheets concatenated; blind_id = 001..048)
key CSV columns     : seed,blind_id,voice_label,voice_id,model_id,line,file
                      (tts_samples.py --blind output; keep it from the raters)

Thresholds are the G.2 proposals and need Ahmed's confirmation before 0b.
Standard library only. Nothing printed here is a result unless the ratings
come from real raters listening to real clips.
"""

from __future__ import annotations

import argparse
import csv
import io
import random
import sys
from collections import defaultdict
from pathlib import Path

GATE = {
    "go_mean": 4.0,
    "retry_low": 3.5,          # initial round: below this -> NO_GO, else RETRY
    "risk_flag_low": 3.8,      # retry round: >= this (and < go_mean) -> GO_WITH_RISK_FLAG
    "min_rater_mean": 3.0,
    "number_lines": {2, 3, 4, 5, 6},
    "raters": 3,
    "lines": 8,
}
YES = {"y", "yes", "1", "true", "نعم"}
NO = {"n", "no", "0", "false", "لا"}


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def pair_stats(ratings: list[dict], key: list[dict]) -> tuple[dict, list[str]]:
    """Return ({(voice_label, model_id): stats}, problems)."""
    by_blind = {k["blind_id"].strip().zfill(3): k for k in key}
    problems: list[str] = []
    pairs: dict = defaultdict(lambda: {"scores": [], "by_rater": defaultdict(list),
                                       "numbers": defaultdict(list), "voice_id": ""})
    for r in ratings:
        bid = (r.get("blind_id") or "").strip().zfill(3)
        k = by_blind.get(bid)
        if not k:
            problems.append(f"blind_id {bid!r} not in key")
            continue
        try:
            score = int(r["naturalness"])
            assert 1 <= score <= 5
        except (KeyError, ValueError, AssertionError):
            problems.append(f"blind_id {bid}: naturalness {r.get('naturalness')!r} not 1-5")
            continue
        p = pairs[(k["voice_label"], k["model_id"])]
        p["voice_id"] = k["voice_id"]
        p["scores"].append(score)
        p["by_rater"][r["rater_id"].strip()].append(score)
        line = int(k["line"])
        if line in GATE["number_lines"]:
            v = (r.get("number_correct") or "").strip().lower()
            if v in YES:
                p["numbers"][line].append(True)
            elif v in NO:
                p["numbers"][line].append(False)
            else:
                problems.append(f"blind_id {bid} (line {line}): number_correct {v!r} must be y/n")
    out = {}
    for pk, p in pairs.items():
        n_raters = len(p["by_rater"])
        expected = n_raters * GATE["lines"]
        num_ok = {ln: bool(v) and all(v) for ln, v in p["numbers"].items()}
        out[pk] = {
            "voice_id": p["voice_id"],
            "n": len(p["scores"]),
            "expected": expected,
            "mean": sum(p["scores"]) / len(p["scores"]),
            "rater_means": {r: sum(s) / len(s) for r, s in p["by_rater"].items()},
            "number_ok": num_ok,
            "numbers_all_ok": len(num_ok) == len(GATE["number_lines"]) and all(num_ok.values()),
            "complete": len(p["scores"]) == expected and n_raters >= GATE["raters"],
        }
    return out, problems


def passes_full(st: dict) -> bool:
    return (st["mean"] >= GATE["go_mean"]
            and min(st["rater_means"].values()) >= GATE["min_rater_mean"]
            and st["numbers_all_ok"])


def verdict(stats: dict, rnd: str) -> tuple[str, tuple | None, str]:
    if not stats:
        return "INCOMPLETE", None, "no ratings"
    if not all(s["complete"] for s in stats.values()):
        bad = [f"{v}/{m}: {s['n']}/{s['expected']} ratings, {len(s['rater_means'])} raters"
               for (v, m), s in stats.items() if not s["complete"]]
        return "INCOMPLETE", None, "; ".join(bad)
    ranked = sorted(stats.items(), key=lambda kv: -kv[1]["mean"])
    best_pair, best = ranked[0]
    winner = next((pk for pk, s in ranked if passes_full(s)), None)
    if winner:
        return "GO", winner, f"mean {stats[winner]['mean']:.2f}"
    # a number line wrong on every pair -> NO_GO regardless of mean
    dead = [ln for ln in sorted(GATE["number_lines"])
            if not any(s["number_ok"].get(ln) for s in stats.values())]
    if dead:
        return "NO_GO", best_pair, f"number line(s) {dead} wrong on every voice"
    why = f"best {best_pair[0]}/{best_pair[1]} mean {best['mean']:.2f}"
    if rnd == "initial":
        if best["mean"] < GATE["retry_low"]:
            return "NO_GO", best_pair, why + f" < {GATE['retry_low']}"
        return "RETRY", best_pair, why + " (adjust stability/similarity, <=3 more voices, eleven_v3_conversational; 45 min)"
    # retry round
    if best["mean"] >= GATE["risk_flag_low"] and min(best["rater_means"].values()) >= GATE["min_rater_mean"] \
            and best["numbers_all_ok"]:
        return "GO_WITH_RISK_FLAG", best_pair, why + " (write the risk flag into docs/STATUS.md)"
    return "NO_GO", best_pair, why + " -> TTS fallback: re-rate Azure ar-SA-ZariyahNeural"


def report(ratings: list[dict], key: list[dict], rnd: str, out=None) -> str:
    out = out or sys.stdout
    stats, problems = pair_stats(ratings, key)
    for p in problems:
        print(f"! {p}", file=out)
    seeds = {k.get("seed") for k in key}
    print(f"blind key seed(s): {sorted(seeds)}   round: {rnd}", file=out)
    print(f"{'voice':<6} {'model':<24} {'n':>5} {'mean':>5}  rater means            numbers(2-6)", file=out)
    for (v, m), s in sorted(stats.items(), key=lambda kv: -kv[1]["mean"]):
        rm = " ".join(f"{r}={x:.2f}" for r, x in sorted(s["rater_means"].items()))
        nums = "".join("y" if s["number_ok"].get(ln) else "N" for ln in sorted(GATE["number_lines"]))
        flag = "" if s["complete"] else "  (incomplete)"
        print(f"{v:<6} {m:<24} {s['n']:>2}/{s['expected']:<2} {s['mean']:>5.2f}  {rm:<22} {nums}{flag}", file=out)
    vd, pair, why = verdict(stats, rnd)
    print(f"\nTTS GATE ({rnd}, G.2 thresholds confirmed by Ahmed 2026-10-28): {vd}", file=out)
    if pair:
        s = stats[pair]
        print(f"  pair: voice {pair[0]} ({s['voice_id'] or 'id unknown'}), model {pair[1]} - {why}", file=out)
    else:
        print(f"  {why}", file=out)
    return vd


# ---------------------------------------------------------------- self-test
def _fake_key(seed: int = 4821) -> list[dict]:
    clips = [{"voice_label": v, "voice_id": f"fake_{v}", "model_id": m, "line": str(ln)}
             for v in "ABC" for m in ("eleven_v4_turbo", "eleven_flash_v2_5") for ln in range(1, 9)]
    random.Random(seed).shuffle(clips)
    return [{"seed": str(seed), "blind_id": f"{i:03d}", **c, "file": f"{c['voice_label']}__{c['model_id']}__L{int(c['line']):02d}.mp3"}
            for i, c in enumerate(clips, 1)]


def _fake_ratings(key, score_of, number_of=lambda v, m, ln, r: "y"):
    rows = []
    for r in ("R1", "R2", "R3"):
        for k in key:
            ln = int(k["line"])
            rows.append({"rater_id": r, "blind_id": k["blind_id"],
                         "naturalness": str(score_of(k["voice_label"], k["model_id"], ln, r)),
                         "number_correct": number_of(k["voice_label"], k["model_id"], ln, r) if ln in GATE["number_lines"] else "",
                         "note": ""})
    return rows


def _selftest() -> int:
    key = _fake_key()
    assert len(key) == 48 and len({k["blind_id"] for k in key}) == 48
    run = lambda rows, rnd="initial": report(rows, key, rnd, out=io.StringIO())
    # GO: B/v4_turbo scores 4-5 everywhere, numbers all y
    go = _fake_ratings(key, lambda v, m, ln, r: 5 if (v, m) == ("B", "eleven_v4_turbo") else 3)
    assert run(go) == "GO"
    # best pair >= 4.0 but one rater mean < 3.0 -> next pair checked -> RETRY (others at 3.6)
    low_rater = _fake_ratings(key, lambda v, m, ln, r: (2 if r == "R3" else 5) if (v, m) == ("B", "eleven_v4_turbo") else (4 if ln % 2 else 3))
    assert run(low_rater) == "RETRY"
    # best pair >= 4.0 but a number line judged wrong by one rater -> RETRY
    num_slip = _fake_ratings(key, lambda v, m, ln, r: 5 if v == "B" else 3,
                             lambda v, m, ln, r: "n" if (v, m, ln, r) == ("B", "eleven_v4_turbo", 5, "R2") or (v, m, ln) == ("B", "eleven_flash_v2_5", 4) else "y")
    assert run(num_slip) == "RETRY"
    # NO_GO by mean < 3.5
    assert run(_fake_ratings(key, lambda v, m, ln, r: 3)) == "NO_GO"
    # NO_GO: line 4 wrong on every voice even though means are high
    dead = _fake_ratings(key, lambda v, m, ln, r: 5, lambda v, m, ln, r: "n" if ln == 4 else "y")
    assert run(dead) == "NO_GO"
    # retry round: 3.8-3.99 -> GO_WITH_RISK_FLAG; same ratings in initial round -> RETRY
    risk = _fake_ratings(key, lambda v, m, ln, r: (4 if ln <= 7 else 3) if (v, m) == ("A", "eleven_flash_v2_5") else 3)
    assert run(risk, "retry") == "GO_WITH_RISK_FLAG"
    assert run(risk) == "RETRY"
    assert run(_fake_ratings(key, lambda v, m, ln, r: 3), "retry") == "NO_GO"
    # incomplete: only two raters
    two = [r for r in go if r["rater_id"] != "R3"]
    assert run(two) == "INCOMPLETE"
    # the blank template is INCOMPLETE
    assert run([]) == "INCOMPLETE"
    report(go, key, "initial")
    print("\nSELFTEST OK (synthetic ratings; not a Phase 0 result)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ratings", nargs="?", type=Path, help="docs/phase0/tts_ratings.csv (all raters)")
    ap.add_argument("key", nargs="?", type=Path, help="phase0/samples/blind_key.csv")
    ap.add_argument("--round", choices=["initial", "retry"], default="initial")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if a.selftest:
        return _selftest()
    if not (a.ratings and a.key):
        ap.error("ratings and key paths required (or --selftest)")
    vd = report(read_csv(a.ratings), read_csv(a.key), a.round)
    return 0 if vd in ("GO", "GO_WITH_RISK_FLAG") else 1


if __name__ == "__main__":
    sys.exit(main())
