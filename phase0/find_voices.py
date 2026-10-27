"""Phase 0b: search the ElevenLabs shared voice library for female Saudi/Gulf voices.

Needs ELEVENLABS_API_KEY in the repo-root .env (run on the Mac). Read-only by
default: it lists accents and voices and writes nothing to the account.

    python phase0/find_voices.py                       # list Arabic accents, then search
    python phase0/find_voices.py --accent saudi         # search one accent value
    python phase0/find_voices.py --search "Hana"        # look up a lead from docs/phase0/voice_selection.md
    python phase0/find_voices.py --add <voice_id> --name "Sara candidate A"   # add to My Voices

SDK calls used (verified by introspecting elevenlabs==2.74.1):
  client.voices.accents.get(language=...)  -> GET /v1/voices/accents
  client.voices.get_shared(...)            -> GET /v1/shared-voices
  client.voices.share(public_user_id, voice_id, new_name=...)  -> adds a library voice to the account

Voice IDs printed here come from the API response; copy them into the docs only
from this output (never from third-party sites).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

REPO = Path(__file__).resolve().parent.parent
OUT_DEFAULT = REPO / "phase0" / "samples" / "voices_found.json"
# Accent labels that plausibly mean Saudi or Gulf. The real values come from
# `accents.get`; this pattern only pre-selects which of them to search.
GULF_PATTERN = re.compile(r"saudi|gulf|khaleeji|khaliji|najdi|hijazi|emirati|kuwaiti|qatari|bahraini|omani", re.I)


def client() -> ElevenLabs:
    load_dotenv(REPO / ".env")
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("ELEVENLABS_API_KEY is not set. Put it in the repo-root .env (see .env.example).")
    return ElevenLabs(api_key=key)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def ensure_ignored_dir(path: Path) -> None:
    """Create a local-only folder whose contents git ignores (clips, API dumps)."""
    path.mkdir(parents=True, exist_ok=True)
    gi = path / ".gitignore"
    if not gi.exists():
        gi.write_text("*\n", encoding="utf-8")


def list_accents(c: ElevenLabs) -> list[str]:
    resp = c.voices.accents.get(language="ar")
    print("Arabic accents returned by the API (accent | code | name):")
    for a in resp.accents:
        print(f"  {a.accent} | {a.code} | {a.name}")
    return [a.accent for a in resp.accents]


def search(c: ElevenLabs, accent: str | None, use_case: str | None, text: str | None, size: int) -> list:
    kwargs = dict(language="ar", gender="female", include_custom_rates=False, page_size=size)
    if accent:
        kwargs["accent"] = accent
    if use_case:
        kwargs["use_cases"] = use_case
    if text:
        kwargs["search"] = text
    return list(c.voices.get_shared(**kwargs).voices)


def has_custom_rate(v) -> bool:
    # fiat_rate is null when the default rate applies (API reference, shared voices).
    return v.fiat_rate is not None


def row(v) -> dict:
    ar_verified = [
        {"model_id": x.model_id, "accent": x.accent, "locale": x.locale}
        for x in (v.verified_languages or [])
        if (x.language or "").lower().startswith("ar")
    ]
    return {
        "voice_id": v.voice_id,
        "public_owner_id": v.public_owner_id,
        "name": v.name,
        "accent": v.accent,
        "age": v.age,
        "gender": v.gender,
        "use_case": v.use_case,
        "language": v.language,
        "locale": v.locale,
        "descriptive": v.descriptive,
        "category": v.category,
        "fiat_rate": v.fiat_rate,
        "free_users_allowed": v.free_users_allowed,
        "cloned_by_count": v.cloned_by_count,
        "verified_arabic": ar_verified,
        "preview_url": v.preview_url,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Search the shared voice library for female Saudi/Gulf voices.")
    ap.add_argument("--accent", action="append", help="accent value from the accents list (repeatable)")
    ap.add_argument("--use-case", default="conversational", help="use_cases filter; '' to disable")
    ap.add_argument("--search", help="free-text search, e.g. a voice name from docs/phase0/voice_selection.md")
    ap.add_argument("--page-size", type=int, default=100, help="max 100 per the API reference")
    ap.add_argument("--out", type=Path, default=OUT_DEFAULT, help="JSON dump of all rows (git-ignored folder)")
    ap.add_argument("--add", metavar="VOICE_ID", help="add this library voice to My Voices (writes to the account)")
    ap.add_argument("--name", help="name for --add")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    c = client()

    if args.add:
        if not args.out.exists():
            sys.exit(f"Run a search first; {args.out} holds the public_owner_id needed for --add.")
        rows = json.loads(args.out.read_text(encoding="utf-8"))
        match = next((r for r in rows if r["voice_id"] == args.add), None)
        if not match:
            sys.exit(f"{args.add} is not in {args.out}; search for it first.")
        resp = c.voices.share(match["public_owner_id"], args.add, new_name=args.name or match["name"])
        print(f"Added. Response: {resp}")
        return 0

    accents = args.accent
    if not accents and not args.search:
        accents = [a for a in list_accents(c) if GULF_PATTERN.search(a)]
        print(f"\nSearching accents matching Saudi/Gulf: {accents or 'none matched'}")
        if not accents:
            print("No Saudi/Gulf accent label found; pass --accent explicitly from the list above.")
            return 1

    found: dict[str, dict] = {}
    for accent in accents or [None]:
        voices = search(c, accent, args.use_case or None, args.search, args.page_size)
        if not voices and args.use_case:
            print(f"[{accent}] 0 results with use_cases={args.use_case!r}; retrying without it.")
            voices = search(c, accent, None, args.search, args.page_size)
        for v in voices:
            if has_custom_rate(v):
                continue
            found.setdefault(v.voice_id, row(v))

    rows = sorted(found.values(), key=lambda r: -(r["cloned_by_count"] or 0))
    print(f"\n{len(rows)} female Arabic voice(s), custom-rate voices excluded:\n")
    for r in rows:
        print(f"- {r['name']}  [{r['voice_id']}]")
        print(f"    accent={r['accent']} age={r['age']} use_case={r['use_case']} locale={r['locale']} "
              f"descriptive={r['descriptive']} free_users_allowed={r['free_users_allowed']} "
              f"cloned_by={r['cloned_by_count']}")
        print(f"    verified_arabic={r['verified_arabic']}")
        print(f"    preview={r['preview_url']}")

    ensure_ignored_dir(args.out.parent)
    args.out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved {len(rows)} rows to {rel(args.out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
