# Quickstart: resume on the Mac Mini and run the Phase 0 gate

**Feature**: `specs/001-saudi-voice-receptionist` | **Date**: 2026-10-27

This guide gets a fresh Mac Mini from `git clone` to the Phase 0 decision, then lists the
validation scenario for every later gate. It references [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/) and the 0a files instead of repeating
them. Commands are bash and also work in Git Bash on the Windows laptop, except where a step is
marked **Mac only**.

## 0. Prerequisites

| Need | Version | How (macOS) | Check |
| --- | --- | --- | --- |
| git + GitHub access to `gzjz10/saudi-voice-receptionist` | any | Xcode CLT (`xcode-select --install`) or git-scm.com | `git --version` |
| Python | 3.12 (`.python-version`) | python.org installer, pyenv, or `brew install python@3.12` (optional) | `python3 --version` → 3.12.x |
| Node.js + npm | Node ≥ 20 (laptop has 24.19.0, npm 11.17.0) | nodejs.org installer or nvm | `node --version` |
| ElevenLabs plan + key | Starter (research R8) | **Ahmed** re-checks https://elevenlabs.io/pricing/agents, buys it, and creates an API key in the dashboard | key exists |
| Raters / speakers | 2 native Saudi raters (≥ 1 from Al-Ahsa) + 1 extra STT speaker | Ahmed books them | names stay out of git |
| cloudflared | pinned in Phase 1 | `brew install cloudflared` or a GitHub release binary | Phase 1 only |

Claude never handles payment or types the API key. Ahmed pastes it into `.env` himself.

## 1. Clone and install (Mac Mini)

```bash
cd ~/Desktop
git clone https://github.com/gzjz10/saudi-voice-receptionist.git
cd saudi-voice-receptionist
git pull --ff-only                       # always start from the latest laptop push

python3 -m venv .venv
source .venv/bin/activate                # Windows Git Bash: source .venv/Scripts/activate
pip install -r requirements-dev.txt -r phase0/requirements.txt   # pytest; elevenlabs==2.74.1, python-dotenv==1.2.4

(cd agent && npm ci)                     # pinned @elevenlabs/cli 1.7.1 from agent/package-lock.json
(cd agent && npx elevenlabs --version)   # expect: elevenlabs 1.7.1
# Never run `npx elevenlabs` outside agent/ before `npm ci`: it would fetch the unrelated npm package "elevenlabs".

cp .env.example .env                     # then Ahmed edits .env and pastes ELEVENLABS_API_KEY
cat docs/STATUS.md                       # expect: "Phase 0 gate: OPEN — waiting for API key and raters"

# Spec Kit pointer (git-ignored, so it does not travel with the clone; tasks T134):
printf '{"feature_directory": "specs/001-saudi-voice-receptionist"}\n' > .specify/feature.json
bash .specify/scripts/bash/check-prerequisites.sh --json   # expect FEATURE_DIR = specs/001-saudi-voice-receptionist
```

`.env` is git-ignored. The CLI finds the repo-root `.env` by walking up from `agent/`, and the
`phase0/*.py` helpers load it with python-dotenv.

## 2. Re-run the 0a gate on the Mac (no key needed)

```bash
bash scripts/check_phase0a.sh
```

Expected: every line `PASS`. The checks are listed in tasks.md T022:

- `python3 -m pytest phase0/test_phase0.py agent/tests -q` (or `python3 phase0/test_phase0.py`);
- `python3 phase0/stt_score.py --selftest` and `python3 phase0/tts_score.py --selftest`;
- `python3 phase0/tts_samples.py --dry-run`;
- `python3 agent/validate_configs.py`;
- the offline `agents push --dry-run`;
- the file list;
- "no results written";
- `phase0/samples/`, `phase0/recordings/` and `.env` are git-ignored.

## 3. Phase 0b: dialect go/no-go (Mac only, key + humans)

Follow these in order and stop on any failure. Every value written comes from a command's output
or a human score. Task IDs refer to [tasks.md](tasks.md).

1. **Confirm inputs with Ahmed (T025)**:
   - thresholds in `docs/phase0/thresholds.json` (status → `CONFIRMED by Ahmed <date>`);
   - the register of TTS lines 2–4 in `docs/phase0/tts_script.md` (`register_signed_off: yes`);
   - the store name in line 1.
2. **Usage baseline (T028)**: run `(cd agent && npx elevenlabs user subscription get --format json)`
   and note the counters in `docs/STATUS.md`.
3. **Voices (T029)**:
   1. Run `python3 phase0/find_voices.py`, which lists the real accent values and then searches
      female, Arabic, conversational, non-custom-rate voices.
   2. Ahmed listens to 5 and keeps 3.
   3. Copy the IDs from that output into `docs/phase0/voice_selection.md` §2 slots A–C.
   4. Record the R4 answers in research.md.
4. **48 clips (T030)**:
   1. `python3 phase0/tts_samples.py --script docs/phase0/tts_script.md --dry-run` checks the
      character count.
   2. Then run it with `--voice A=<id> --voice B=<id> --voice C=<id>`. Clips go to git-ignored
      `phase0/samples/`, with the voice settings from `agent/agent_configs/sara.json`.
   3. If `eleven_v4_turbo` is rejected by the TTS endpoint, follow research R5 and note it.
5. **Blind (T031)**: re-run with `--blind --seed <N>`, which writes `phase0/samples/blind/` and
   `phase0/samples/blind_key.csv`. Give the raters only the blind folder and the rating form.
6. **Rate and score (T032–T034)**:
   1. Each rater fills `docs/phase0/tts_ratings_R<n>.csv` independently (form: `voice_selection.md` §5).
   2. Concatenate them into `docs/phase0/tts_ratings.csv` (one header) and run
      `python3 phase0/tts_score.py docs/phase0/tts_ratings.csv phase0/samples/blind_key.csv`.
   3. On `RETRY`, do the one 45-minute retry and re-score with `--round retry`.
7. **STT (T035–T038)**:
   1. Set the winning triple in both agent configs and run
      `python3 agent/validate_configs.py --allow-voice-id`.
   2. Run `(cd agent && npx elevenlabs agents pull && npx elevenlabs agents push)`.
   3. Run 1 on the probe's `asr.provider` (`scribe_realtime`): S1 and S2 each say the 10 cards
      from `docs/phase0/stt_sheet.md` into the STT probe agent, one conversation per clip, and
      write each `conversation_id` and the provider value into `docs/phase0/stt_results.csv`.
   4. Run `python3 phase0/stt_score.py docs/phase0/stt_results.csv --fetch`.
   5. Run 2: `python3 phase0/stt_score.py docs/phase0/stt_results.csv --add-run <other provider>`,
      edit the probe config, push, repeat and fetch.
   6. Run `python3 phase0/stt_score.py docs/phase0/stt_results.csv`. On `FAIL`, do the one
      30-minute retry with `asr.keywords` and a provider switch.
   7. Before committing, apply the T038 privacy decision for `transcript_heard`.
8. **Billing check (T040)**: run one Simulation test with `(cd agent && npx elevenlabs agents test <agent>)`,
   then re-read `user subscription get` and record whether the test consumed minutes.
9. **Runtime match (T039)**: Ahmed confirms the live agent voice matches the rated winning clip.
10. **Decide (T042–T043)**:
    1. Fill `docs/phase0/decision.md` with every FR-012 field.
    2. Ahmed signs.
    3. Update `docs/STATUS.md` (gate status and minutes from the counter).
    4. Commit the blind key as `docs/phase0/clip_key.csv` only now.

**Expected outcome**: `decision.md` signed with `GO`, `GO_WITH_RISK_FLAG` or a named fallback, and
`STATUS.md` updated. Phase 2 may start only on GO or GO_WITH_RISK_FLAG for both TTS and STT, or
after a passed fallback.

## 4. Later gates: validation scenarios (details in the tasks.md checkpoints)

| Gate | Run | Expected |
| --- | --- | --- |
| Phase 1 (T076) | `bash scripts/test.sh`; `bash scripts/latency.sh`; `bash scripts/tunnel.sh`, then `curl` from a phone hotspot with and without the secret | pytest green incl. ≥ 30 matcher pairs and `golden_spoken.csv`; 401 / 413 / 422 / 200 envelopes per [contracts/tools.openapi.yaml](contracts/tools.openapi.yaml); a duplicate `create_order` returns `duplicate: true`; p95 < 300 ms; tunnel 200 with the secret, 401 without; same suite green on the other OS |
| Phase 2 (T092) | `python -m http.server 8000` in `demo/`, then 3 voice orders (pickup, delivery, correction) + 1 English call + 1 mixed call | correct SQLite rows with `conversation_id`; `quote_order` before `create_order`; spoken read-back; digit-by-digit order id; out-of-stock spoken; E10 switches, E11 stays Arabic; `agents push --dry-run` shows no drift; minutes logged |
| Phase 3 (T109) | `bash scripts/eval.sh v1` | ≥ 20 sim scenarios × k ≥ 3; judge agreement gate; 10 real calls fetched and redacted; human verdicts on all critical flags; `git ls-files` shows no raw transcripts or audio |
| Phase 4 (T117) | `bash scripts/eval.sh v2` + `python scripts/check_frozen.py v1 v2` | frozen hashes match; ≥ 5 CHANGELOG entries; 0 critical grounding failures and 0 unconfirmed orders on dev and holdout |
| Phase 5 (T128) | fresh clone on the other OS → `bash scripts/test.sh`; `python evals/score.py --readme --check` | green; every README / QA_REPORT number matches `summary.csv`; gitleaks clean on full history |

## 5. Handing back to the laptop

```bash
git status                      # verify: no .env, phase0/samples/, audio, raw transcripts, or blind key before rating ends
git add -A && git commit -m "phase0b: …" && git push
```

On the laptop: `git pull --ff-only`. The laptop never runs a non-dry-run `push`, and the
`phase0/` SDK helpers stay Mac-only unless the venv uses a short path (research R4 caveat).
