"""Phase 0b: synthesize the fixed listening script with each candidate voice and model.

Default run = 3 voices x 2 models x 8 gate lines = 48 clips, using the same voice
settings as agent/agent_configs/sara.json (stability, similarity_boost, speed;
style is fixed at 0 because the agent TTS config has no style field).

    python phase0/tts_samples.py --dry-run                 # offline: plan + character count, no key
    python phase0/tts_samples.py --voice A=<id> --voice B=<id> --voice C=<id>
    python phase0/tts_samples.py ... --blind --seed 4821    # shuffled, blind-labelled copies for raters
    python phase0/tts_samples.py ... --script docs/phase0/tts_script.md   # lines from another file

Output (git-ignored): phase0/samples/<label>__<model>__L<nn>.mp3, manifest.csv,
and with --blind: phase0/samples/blind/<nnn>.mp3 + blind_key.csv (keep the key
away from raters until scoring).

SDK call used (verified by introspecting elevenlabs==2.74.1):
  client.text_to_speech.convert(voice_id, text=, model_id=, language_code=,
      voice_settings=VoiceSettings(stability, similarity_boost, style, speed),
      output_format=) -> Iterator[bytes]      # POST /v1/text-to-speech/{voice_id}
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import re
import secrets
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SAMPLES = REPO / "phase0" / "samples"
AGENT_CONFIG = REPO / "agent" / "agent_configs" / "sara.json"
DEFAULT_MODELS = ["eleven_v4_turbo", "eleven_flash_v2_5"]
OUTPUT_FORMAT = "mp3_44100_128"

# Lines 1-8 are the gate script from reviews/plan-review.md section G.1, spoken
# strings exactly as spoken.py will emit them. Ahmed may still correct the
# register of lines 2-4; if he does, pass the corrected file with --script.
LINES: list[tuple[int, str, str, str]] = [  # (n, label, language, text)
    (1, "greeting", "ar", "هلا والله، معكم سارة من مقاضينا، كيف أقدر أخدمكم؟"),
    (2, "price_9_75", "ar", "الصحون الزجاج بتسعة ريال وخمسة وسبعين هللة"),
    (3, "total_17_25", "ar", "المجموع سبعطعش ريال وخمسة وعشرين هللة"),
    (4, "total_117", "ar", "المجموع مية وسبعطعش ريال"),
    (5, "phone_3_3_4", "ar", "رقمكم صفر خمسة خمسة، واحد اثنين ثلاثة، أربعة خمسة ستة سبعة، صح؟"),
    (6, "order_id", "ar", "رقم طلبكم أربعة، ثمانية، اثنين، واحد"),
    (7, "clarify_2_options", "ar", "تقصدون صحون زجاج أو صحون بلاستيك؟"),
    (8, "escalate_close", "ar", "أعتذر منكم، بحوّلكم لموظف يتواصل معكم، شكراً لاتصالكم"),
]
LINE_RE = re.compile(r"^\s*(\d+)\.\s+([^:]+):\s*(.+?)\s*$")


def parse_script(path: Path) -> list[tuple[int, str, str, str]]:
    """Read `N. label: text` lines (the docs/phase0/tts_script.md list format)."""
    out = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        m = LINE_RE.match(raw)
        if m:
            n, label, text = int(m.group(1)), m.group(2).strip("*` "), m.group(3).strip("*` ")
            lang = "ar" if re.search(r"[؀-ۿ]", text) else "en"
            out.append((n, re.sub(r"\W+", "_", label.lower()).strip("_"), lang, text))
    if not out:
        sys.exit(f"No `N. label: text` lines found in {path}")
    return out


def agent_settings() -> dict:
    tts = json.loads(AGENT_CONFIG.read_text(encoding="utf-8"))["conversation_config"]["tts"]
    return {
        "stability": tts.get("stability", 0.5),
        "similarity_boost": tts.get("similarity_boost", 0.8),
        "speed": tts.get("speed", 1.0),
        "style": 0.0,
    }


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def ensure_ignored_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    gi = path / ".gitignore"
    if not gi.exists():
        gi.write_text("*\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Synthesize the Phase 0 listening script per voice and model.")
    ap.add_argument("--voice", action="append", default=[], metavar="LABEL=VOICE_ID",
                    help="candidate voice; label is a short name like A, B, C (repeatable)")
    ap.add_argument("--model", action="append", help=f"TTS model id (repeatable); default {DEFAULT_MODELS}")
    ap.add_argument("--script", type=Path, help="read lines from a `N. label: text` file instead of the built-in 8")
    ap.add_argument("--stability", type=float)
    ap.add_argument("--similarity-boost", type=float)
    ap.add_argument("--speed", type=float)
    ap.add_argument("--no-language-code", action="store_true", help="do not send language_code")
    ap.add_argument("--force", action="store_true", help="re-synthesize clips that already exist")
    ap.add_argument("--blind", action="store_true", help="also write shuffled blind copies + key")
    ap.add_argument("--seed", type=int, help="shuffle seed for --blind (recorded in blind_key.csv)")
    ap.add_argument("--dry-run", action="store_true", help="print the plan and character count; no API call")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Arabic prints correctly on Windows consoles

    lines = parse_script(args.script) if args.script else list(LINES)
    models = args.model or DEFAULT_MODELS
    settings = agent_settings()
    for key in ("stability", "similarity_boost", "speed"):
        if getattr(args, key) is not None:
            settings[key] = getattr(args, key)

    voices: list[tuple[str, str]] = []
    for spec in args.voice:
        label, _, vid = spec.partition("=")
        if not label or not vid:
            sys.exit(f"--voice must be LABEL=VOICE_ID, got {spec!r}")
        voices.append((label.strip(), vid.strip()))
    if not voices and not args.dry_run:
        sys.exit("Give at least one --voice LABEL=VOICE_ID (IDs from find_voices.py output).")

    chars_per_pass = sum(len(t) for *_, t in lines)
    n_voices = len(voices) or 3
    print(f"Lines: {len(lines)}  models: {models}  voices: {[v[0] for v in voices] or '(3 assumed)'}")
    print(f"Settings: {settings}  output_format: {OUTPUT_FORMAT}")
    print(f"Clips: {n_voices * len(models) * len(lines)}  characters: {chars_per_pass * n_voices * len(models)}")
    if args.dry_run:
        for n, label, lang, text in lines:
            print(f"  L{n:02d} {label} [{lang}] {text}")
        return 0

    from dotenv import load_dotenv
    from elevenlabs import VoiceSettings
    from elevenlabs.client import ElevenLabs

    load_dotenv(REPO / ".env")
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("ELEVENLABS_API_KEY is not set. Put it in the repo-root .env (see .env.example).")
    client = ElevenLabs(api_key=key)
    vs = VoiceSettings(**settings)

    ensure_ignored_dir(SAMPLES)
    manifest = []
    for label, vid in voices:
        for model in models:
            for n, line_label, lang, text in lines:
                path = SAMPLES / f"{label}__{model}__L{n:02d}.mp3"
                if not path.exists() or args.force:
                    kwargs = dict(text=text, model_id=model, voice_settings=vs, output_format=OUTPUT_FORMAT)
                    if not args.no_language_code and model != "eleven_multilingual_v2":
                        kwargs["language_code"] = lang
                    audio = client.text_to_speech.convert(vid, **kwargs)
                    with path.open("wb") as fh:
                        for chunk in audio:
                            fh.write(chunk)
                    print(f"wrote {rel(path)}")
                else:
                    print(f"skip  {rel(path)} (exists; --force to redo)")
                manifest.append({"voice_label": label, "voice_id": vid, "model_id": model, "line": n,
                                 "line_label": line_label, "language": lang, "text": text,
                                 "file": path.name, **settings})

    with (SAMPLES / "manifest.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(manifest[0].keys()))
        w.writeheader()
        w.writerows(manifest)
    print(f"manifest: {rel(SAMPLES / 'manifest.csv')}")

    if args.blind:
        seed = args.seed if args.seed is not None else secrets.randbelow(10**6)
        order = list(manifest)
        random.Random(seed).shuffle(order)
        blind = SAMPLES / "blind"
        if blind.exists():
            shutil.rmtree(blind)
        blind.mkdir()
        with (SAMPLES / "blind_key.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["seed", "blind_id", "voice_label", "voice_id", "model_id", "line", "file"])
            for i, m in enumerate(order, start=1):
                bid = f"{i:03d}"
                shutil.copyfile(SAMPLES / m["file"], blind / f"{bid}.mp3")
                w.writerow([seed, bid, m["voice_label"], m["voice_id"], m["model_id"], m["line"], m["file"]])
        print(f"blind set: {len(order)} clips in {rel(blind)}, seed={seed}; "
              f"key in phase0/samples/blind_key.csv (do not share with raters)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
