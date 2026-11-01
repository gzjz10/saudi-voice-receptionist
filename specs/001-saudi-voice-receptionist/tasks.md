---
description: "Task list for the Saudi Voice Receptionist, grouped by gated delivery phases 0-5"
---

# Tasks: Saudi Voice Receptionist "Sara"

**Input**: Design documents from `specs/001-saudi-voice-receptionist/`: [plan.md](plan.md),
[spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md),
[contracts/](contracts/) and [quickstart.md](quickstart.md).

**Prerequisites**: constitution v1.0.0 and `reviews/plan-review.md` sections E–G. The review
overrides root `plan.md` where they conflict.

**Tests**: included. The spec and the gates require them: the scoring script on fake data, golden
matcher and spoken tables, contract tests, the agent-config validator, and eval scorers.

**Organization**: tasks are grouped by **delivery phase 0–5** (review section F), because every
phase ends in a hard gate. Inside each phase, tasks carry the user-story label they serve:

| Label | User story |
| --- | --- |
| US0 | Dialect go/no-go |
| US1 | Grounded answers |
| US2 | Voice order |
| US3 | Status and escalation |
| US4 | English and adversarial callers |
| US5 | v1 eval |
| US6 | v2 fix loop |
| US7 | Ship |

Shared setup and foundational tasks carry no story label. **Every phase ends with an explicit
`CHECKPOINT` task, the gate. The next hard-gated phase does not start until that box is ticked
with evidence.**

## Format: `- [ ] T### [P?] [US?] Description with file path`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task).
- **[USn]**: the user story from spec.md that the task serves.
- **EXECUTING NOW (0a, 2026-10-27)** at the end of a description means the Phase 0a team is
  producing that item in the current session. Tick it only when the file exists and the 0a
  checkpoint (T024) passes.
- **HUMAN** marks a step only Ahmed or the raters can do. **KEY** marks a step that needs
  `ELEVENLABS_API_KEY` on the Mac.

## Path conventions

These follow plan.md "Project Structure":

- `agent/`: CLI `init` layout, with the CLI pinned in `agent/package.json`.
- `prompts/`; `phase0/` (0b helper scripts and STT/voice sheets; `phase0/samples/` and
  `phase0/recordings/` are git-ignored); `docs/phase0/` (gate-named documents and the decision).
- `scripts/` (bash + Python, cross-platform), `backend/app/`, `backend/tests/`, `data/`,
  `evals/`, `reports/`, `demo/`.

---

## Delivery Phase 0: Dialect go/no-go (US0, Priority P0)

**Goal**: know, before backend or prompt work is wired to a runtime, whether ElevenLabs can speak
and hear natural Saudi receptionist Arabic. The output is a signed GO / GO WITH RISK FLAG / NO-GO.

**Independent test**:

- 0a: `bash scripts/check_phase0a.sh` passes offline.
- 0b: the scoring verdicts on real ratings and transcripts, plus Ahmed's signature in
  `docs/phase0/decision.md`.

**Layout used by the 0a run in progress** (observed on disk 2026-10-27; this list supersedes any
other Phase 0 path in this feature's docs):

- **Tooling** (`phase0/` at the repo root, all stdlib except the two SDK helpers):
  - `find_voices.py` (voice search, SDK);
  - `tts_samples.py` (48 clips, `--dry-run`, `--blind --seed`, `--script`, SDK);
  - `tts_score.py` (TTS gate G.2, `--round`, `--selftest`);
  - `stt_score.py` (STT gate G.3, `--fetch`, `--add-run`, `--selftest`);
  - `test_phase0.py` (offline tests on fake data; runs under pytest or as a plain script);
  - `requirements.txt` (`elevenlabs==2.74.1`, `python-dotenv==1.2.4`; see T002 for the pytest pin).
  - The review's `scripts/score_phase0.py` is realized by `tts_score.py` + `stt_score.py`; T021
    adds only a thin `scripts/score_phase0.py` wrapper so the review's path exists.
- **Sheets and gate-named documents** (`docs/phase0/`, the review section F names):
  `tts_script.md`, `stt_sheet.md` (10 utterances + cards), `stt_results.csv` (the STT results
  template, 20 blank rows), `voice_selection.md` (procedure + empty ID table + rating form),
  `tts_ratings.csv` (header only), `catalog_traps.md`; added by T017/T042: `thresholds.json`,
  `decision.md`, `clip_key.csv`.
- **Agent** (`agent/`): the CLI pin in `agent/package.json`, the configs
  `agent/agent_configs/sara.json` and `sara_stt_probe.json`, and the offline validator
  `agent/validate_configs.py`.
- **Not on disk yet** (2026-10-27 leader analysis): `docs/STATUS.md`, `scripts/`,
  `requirements-dev.txt`, `.python-version`, `docs/phase0/thresholds.json`, `agent/tests/`.
  The analysis report is `specs/001-saudi-voice-receptionist/analysis.md`.

### Phase 0a.1: Setup (offline, Windows, no key)

- [ ] T001 Pin the CLI in `agent/package.json` as the exact devDependency `"@elevenlabs/cli": "1.7.1"` and commit `agent/package-lock.json` (with the darwin/linux/win32 optional binaries). Run every CLI command from `agent/` after `npm ci`, because `npx elevenlabs` outside it fetches the unrelated npm package `elevenlabs` (research R2) — EXECUTING NOW (0a, 2026-10-27)
- [ ] T002 [P] Create `.python-version` (`3.12`) and `requirements-dev.txt` containing exactly `pytest==9.1.1` (PyPI upload 2026-06-19, re-checked 2026-10-27) for the 0a gate tests, and **remove the `pytest==8.4.2` line from `phase0/requirements.txt`** so the repo carries one pytest pin (constitution VI). Keep `phase0/requirements.txt` for the 0b SDK pins only, because `elevenlabs==2.74.1` fails to install under the laptop's 260-char path limit in the repo `.venv` (research R11). pytest is not installed on the laptop today; `python phase0/test_phase0.py` runs the same tests as a plain script
- [ ] T003 [P] Confirm `.gitignore` covers `phase0/samples/` (added by the 0a run, still uncommitted on 2026-10-27; `phase0/tts_samples.py` writes clips and `blind_key.csv` there) and extend it with `evals/results/**/raw/`, `evals/results/**/real_calls/` and `backend/logs/`. Keep `.env`, `phase0/recordings/`, `node_modules/` and `__pycache__/` (review B5, constitution IV)
- [ ] T004 [P] Create `.env.example` with names only and no values: `ELEVENLABS_API_KEY=` (read by `phase0/*.py`, and by the CLI walking up from `agent/`). Later-phase names (`TOOL_SECRET`, `TOOLS_BASE_URL`) are added in Phase 1/2 — EXECUTING NOW (0a, 2026-10-27)
- [ ] T005 [P] Create `scripts/py.sh` (choose `python` or `python3`, require 3.12) and `scripts/env.sh` (`set -a; . ./.env; set +a`, fail clearly if `.env` is missing). POSIX bash only, LF endings (research R17)
- [ ] T006 [P] Create `docs/STATUS.md` with the fields phase, gate, blockers, minutes_used (blank), last_updated and machine. The gate line must read exactly `Phase 0 gate: OPEN — waiting for API key and raters`. Blockers: API key, Starter plan, 2 raters + 1 speaker, Ahmed's decisions FR-008/FR-053/FR-073 (data-model A8)

### Phase 0a.2: Offline assets for US0

- [ ] T007 [US0] Create the agent project layout with `npx elevenlabs agents init .` inside `agent/` (`agents.json`, `tools.json`, `tests.json`, `agent_configs/`, `tool_configs/`, `test_configs/`, `.gitignore`; the generated `agent/.env.example` is removed in favour of the root one). Do NOT use `agents add` (research R2) — EXECUTING NOW (0a, 2026-10-27)
- [ ] T008 [US0] Write the offline validator `agent/validate_configs.py` (stdlib only). It reads every enum and range from the pinned CLI's own `agents create --spec`, fails on a bogus enum, an unknown field or an out-of-range value, and requires `tts.voice_id` to be absent in 0a mode (`--allow-voice-id` from 0b). It exists because `agents push --dry-run` checks only JSON parsing (research R2.1) — EXECUTING NOW (0a, 2026-10-27)
- [ ] T009 [P] [US0] Write `prompts/system_v0.md`: the minimal Sara persona prompt in Saudi colloquial Arabic with plural address, copied verbatim into `sara.json` — EXECUTING NOW (0a, 2026-10-27)
- [ ] T010 [US0] Write the two minimal Arabic agents in `agent/agent_configs/` and register both in `agent/agents.json`:
  - `sara.json`: the persona;
  - `sara_stt_probe.json`: same language, ASR and TTS settings, answers only «تمام» (review G.3).

  Required values in both: `conversation_config.agent.language` = `"ar"`; no tools; `conversation_config.tts.voice_id` **omitted**; `tts.stability`/`similarity_boost`/`speed` set (these are the values `phase0/tts_samples.py` must reuse); `platform_settings.privacy.retention_days` = 30; `platform_settings.call_limits.daily_limit` = 20; `platform_settings.call_limits.agent_concurrency_limit` = 2. Hand-written is allowed in 0a; T050 adds a generator (contracts/phase0-artifacts.md §6; depends on T007, T009) — EXECUTING NOW (0a, 2026-10-27)
- [ ] T011 [P] [US0] Add pytest coverage for the validator in `agent/tests/test_validate_configs.py`, using temp copies of the configs. Cases: the real configs pass; a bogus `asr.provider` fails; an unknown field fails; `tts.voice_id` present fails without `--allow-voice-id`. Mark the tests skipped with a clear reason when `agent/node_modules` is missing
- [ ] T012 [P] [US0] Draft the catalog trap items in `docs/phase0/catalog_traps.md`: 2 out-of-stock items; near-duplicate pairs صحون زجاج / صحون بلاستيك and أكواب ورق / أكواب زجاج; 3 items whose common name ≠ shelf name, including the STT utterance-3 item (the 0a sheet proposes shelf أكياس نفايات / common أكياس زبالة, sold by علبة; keep both files consistent); aliases as callers say them; prices only from {5.75, 9.75, 14.75}; all fake (data-model B1)
- [ ] T013 [P] [US0] `docs/phase0/tts_script.md` exists with the 8 gate lines verbatim from review G.1 as the `N. label: text` list that `phase0/tts_samples.py --script` parses, the header `register_signed_off: no`, and the 2,022-character count. Still to add: a metadata table with `line_no`, `purpose`, `is_number_line` (true for lines 2–6 only) and `expected_number` (`9.75`, `17.25`, `117`, `0551234567`, `4821`). Lines 2–4 await Ahmed (FR-053) and line 1's store name awaits FR-073. This file is the single source of truth; the embedded `LINES` in `phase0/tts_samples.py` must match it, and `phase0/test_phase0.py::test_tts_script_md_matches_builtin_lines` already checks that (data-model A1) — EXECUTING NOW (0a, 2026-10-27)
- [ ] T014 [US0] The 10-utterance STT sheet is `docs/phase0/stt_sheet.md` (utterances, entities, variants, speaker notes, printable cards, run procedure) + `docs/phase0/stt_results.csv` (10 utterances × speakers S1/S2 = 20 rows with empty `conversation_id`/`transcript_heard`/`entities_correct`/`intent_ok` cells; `phase0/test_phase0.py` checks they are blank). Utterance 3 matches T012's trap item (أكياس نفايات / أكياس زبالة). **Accepted deviation from review G.1** (leader, 2026-10-27): utterance 5 ends with an added «سبعة», because the review's text had only 9 digits and could not equal its own target 0557834567. Still to do: save the CSV as UTF-8 **without BOM** (the current file starts with one; every reader already uses `utf-8-sig`, so this is hygiene, not a blocker) — EXECUTING NOW (0a, 2026-10-27)
- [ ] T015 [P] [US0] The 3-voice-candidate procedure is `docs/phase0/voice_selection.md` §1 and §3 plus the search helper `phase0/find_voices.py`:
  - `voices.accents.get(language="ar")` → `voices.get_shared(language="ar", gender="female", accent=<value from the response>, use_cases="conversational", include_custom_rates=False)`;
  - drop custom-rate voices → shortlist 5 → Ahmed keeps 3 → optional add to My Voices (`--add`);
  - starting voice settings (0.5 / 0.8 / 1.0 = `sara.json`) and the rating form (§5).

  No voice IDs anywhere; the §2 "leads" are third-party catalog names only, marked unconfirmed, and every one must be re-found through the API or replaced. The R4 UNVERIFIED items are listed in §6 (research R4) — EXECUTING NOW (0a, 2026-10-27)
- [ ] T016 [P] [US0] The empty candidate table is `docs/phase0/voice_selection.md` §2 "Voice ID fields": slots A/B/C with `voice_id`, `public_owner_id`, accent, age, use_case and verified Arabic models, filled only from `find_voices.py` output. Still to add: a `source_command` and `retrieved_at` column and the retry slots D–F. All ID cells stay empty in 0a (data-model A3) — EXECUTING NOW (0a, 2026-10-27)
- [ ] T017 [P] [US0] Create `docs/phase0/thresholds.json` with the review G values and `"status": "PROPOSED - not yet confirmed by Ahmed"` (contracts/phase0-artifacts.md §4). Today both scorers hard-code the same values in a `GATE` dict; T021 makes them read this file, so Ahmed's changes are data
- [ ] T018 [P] [US0] The rating form is `docs/phase0/voice_selection.md` §5 (1–5 Saudi naturalness anchors, `number_correct` Y/N for lines 2–6, headphones, alone, blind ids only). Still to add there: the no-discussion rule between raters and the rule that the sheet carries rater ids R1–R3 only, never names. No separate `rating_sheet.md` is needed
- [ ] T019 [P] [US0] The header-only template `docs/phase0/tts_ratings.csv` exists with the header `rater_id,blind_id,naturalness,number_correct,note` (the column is `blind_id`, matching `phase0/tts_score.py` and `blind_key.csv`; contracts/phase0-artifacts.md §1 was corrected to this). The STT results template is `docs/phase0/stt_results.csv` (T014). UTF-8 without BOM, LF (contracts §1, §3)
- [ ] T020 [P] [US0] Extend `phase0/test_phase0.py` (today: both `--selftest`s, blank templates, header-only ratings, `LINES` == `tts_script.md`) with fake-data cases that use voice slots only, never IDs:
  - TTS GO, RETRY and NO_GO by mean;
  - NO_GO when a number line is wrong on all pairs;
  - a rater mean < 3.0 blocks GO;
  - retry → GO_WITH_RISK_FLAG;
  - STT GO, then each rule (a)–(e) failing alone;
  - phone boundary: 2 wrong digits of 40 pass, 3 fail;
  - invalid input (unknown blind_id, bad value, duplicate key) exits 2;
  - thresholds read from `docs/phase0/thresholds.json` change the verdict.

  Fixtures, if any are needed beyond in-memory data, go in `phase0/tests/fixtures/fake_*.csv` (contracts/phase0-artifacts.md §5)
- [ ] T021 [US0] Make `phase0/tts_score.py` and `phase0/stt_score.py` read `docs/phase0/thresholds.json` (falling back to the built-in G values only when the file is missing, and printing which source was used), and add the thin stdlib wrapper `scripts/score_phase0.py` with subcommands `tts` and `stt` that call the two scorers and print one JSON verdict each, never writing `decision.md`. Keep both `--selftest`s green and make T020 green (depends on T017, T020)
- [ ] T022 [US0] Write `scripts/check_phase0a.sh`, which prints one PASS/FAIL line per check:
  - `python -m pytest phase0/test_phase0.py agent/tests -q`, or `python phase0/test_phase0.py` when pytest is not installed (print which ran);
  - `python phase0/stt_score.py --selftest` and `python phase0/tts_score.py --selftest`;
  - `python phase0/tts_samples.py --dry-run` (offline plan, no key);
  - `python agent/validate_configs.py`;
  - `(cd agent && env -u ELEVENLABS_API_KEY npx elevenlabs agents push --dry-run)`, with no API call;
  - existence of every plan.md "Phase 0a outputs" file;
  - "no results written": voice ID cells empty in `voice_selection.md` §2, `tts_ratings.csv` header-only, `stt_results.csv` result cells empty, STATUS minutes blank, no `voice_id` in either agent config;
  - `git check-ignore phase0/samples/ phase0/recordings/ .env` all ignored.

  It exits non-zero on any FAIL (depends on T001–T021)
- [ ] T023 [US0] Add a short "Phase 0 on the Mac" pointer in `docs/STATUS.md` that links `specs/001-saudi-voice-receptionist/quickstart.md` §3 and lists the open Ahmed decisions with where each is recorded

- [ ] T024 [US0] **CHECKPOINT: PHASE 0a GATE.** Run `bash scripts/check_phase0a.sh` on Windows Git Bash. PASS requires all of:
  - `agents push --dry-run` succeeds offline (it proves JSON well-formedness only) **and** `agent/validate_configs.py` exits 0;
  - pytest and the `stt_score.py` self-test are green on fake data;
  - every 0a file exists;
  - no voice ID, score, transcript or minute is written;
  - `phase0/samples/` is git-ignored;
  - `docs/STATUS.md` reads `Phase 0 gate: OPEN — waiting for API key and raters`.

  Then **STOP and report to Ahmed.** The orchestrator commits and pushes to `gzjz10/saudi-voice-receptionist`. Phase 0 as a whole stays OPEN.

### Phase 0b: Go/no-go with key and humans (Mac Mini). BLOCKED on T025–T026

- [ ] T025 [US0] HUMAN: Ahmed confirms or changes `docs/phase0/thresholds.json` (sets `"status": "CONFIRMED by Ahmed <date>"`), signs the register of lines 2–4 in `docs/phase0/tts_script.md` (`register_signed_off: yes`), and decides the store name for line 1 (spec FR-008, FR-053, FR-073; resolve via `/speckit-clarify`)
- [ ] T026 [US0] HUMAN: Ahmed re-checks https://elevenlabs.io/pricing/agents, buys Starter, creates an API key and pastes it into `.env` on the Mac. Claude never handles payment or the key (research R8)
- [ ] T027 [US0] On the Mac, follow `quickstart.md` §1: clone, venv, `pip install -r requirements-dev.txt -r phase0/requirements.txt`, then `cd agent && npm ci`. Re-run `bash scripts/check_phase0a.sh` (all PASS)
- [ ] T028 [US0] KEY: record the usage baseline from `cd agent && npx elevenlabs user subscription get --format json` (character and minute counters) in `docs/STATUS.md` (research R7)
- [ ] T029 [US0] KEY + HUMAN: run `python phase0/find_voices.py`. Ahmed listens to the shortlist of 5 and keeps 3. Copy the IDs **from that output** into `docs/phase0/voice_selection.md` §2 slots A–C with source_command and retrieved_at. Write the R4 UNVERIFIED answers (accent values, Starter access, need for `--add`) into research.md R4
- [ ] T030 [US0] KEY: run `python phase0/tts_samples.py --script docs/phase0/tts_script.md --voice A=<id> --voice B=<id> --voice C=<id>` to produce 3 voices × {`eleven_v4_turbo`, `eleven_flash_v2_5`} × 8 lines = 48 clips in git-ignored `phase0/samples/`, with the `sara.json` voice settings. First settle R5 (does the TTS endpoint accept `eleven_v4_turbo`? Starter character quota?) using `--dry-run` for the character count, and record both in research.md R5
- [ ] T031 [US0] Re-run with `--blind --seed <N>` to get the shuffled copies in `phase0/samples/blind/` and `phase0/samples/blind_key.csv` (git-ignored until rating ends). Record the seed in `docs/STATUS.md`
- [ ] T032 [US0] HUMAN: Ahmed (R1) and 2 native Saudi raters (R2, R3; ≥ 1 from Al-Ahsa) rate independently using the rating form (`voice_selection.md` §5), each filling `docs/phase0/tts_ratings_R<n>.csv` with the `tts_ratings.csv` header
- [ ] T033 [US0] Merge and score: concatenate the three rater files into `docs/phase0/tts_ratings.csv` (one header), run `python phase0/tts_score.py docs/phase0/tts_ratings.csv phase0/samples/blind_key.csv` (or `python scripts/score_phase0.py tts`, T021) and paste the verdict into a draft (unsigned) `docs/phase0/decision.md`
- [ ] T034 [US0] KEY + HUMAN, only if T033 = RETRY: one 45-minute retry. Adjust stability/similarity in `sara.json`, add ≤ 3 voices (slots D–F via T029), and try `eleven_v3_conversational`. Re-synthesize, re-rate, then re-score with `--round retry` (≥ 4.0 GO; 3.8–3.99 GO_WITH_RISK_FLAG written in STATUS; < 3.8 NO_GO)
- [ ] T035 [US0] KEY: run `python agent/validate_configs.py --allow-voice-id` with the winning (voice, model, settings) triple set in `agent/agent_configs/sara.json` and `sara_stt_probe.json`. Then from `agent/` run `npx elevenlabs agents pull` and `npx elevenlabs agents push` (Mac is the single push owner). This settles the R3 UNVERIFIED item: does the server accept `language: "ar"`?
- [ ] T036 [US0] HUMAN + KEY: STT run 1 on the `asr.provider` written in `sara_stt_probe.json` (`scribe_realtime`, the schema default). S1 (Ahmed) and S2 speak the 10 utterances of `docs/phase0/stt_sheet.md` (cards; S1 in order 1→10, S2 in order 10→1) into `Sara STT probe - Phase 0`, one conversation per clip, and write each `conversation_id` and the actual provider value into `docs/phase0/stt_results.csv`. Then run `python phase0/stt_score.py docs/phase0/stt_results.csv --fetch` (realtime transcript from `GET /v1/convai/conversations/{id}`, `transcript[].message` where `role == "user"`; also note `metadata.call_duration_secs` per conversation for the minutes log)
- [ ] T037 [US0] KEY + HUMAN: run 2 with one other `asr.provider` from {`elevenlabs`, `scribe_v2_turbo`}. Run `python phase0/stt_score.py docs/phase0/stt_results.csv --add-run <provider>`, edit the probe config, push, repeat the 20 clips and fetch. Then run `python phase0/stt_score.py docs/phase0/stt_results.csv` (or `python scripts/score_phase0.py stt`). If NO_GO, do one 30-minute retry: add product names from `docs/phase0/catalog_traps.md` to `conversation_config.asr.keywords`, switch provider, and re-run only the failing clips
- [ ] T038 [US0] Privacy check before commit. Decide with Ahmed whether the filled `transcript_heard` column of `docs/phase0/stt_results.csv` may stay in git: the utterances are scripted fake data, but constitution IV says raw transcripts are not tracked. Default: move the filled copy to git-ignored `phase0/recordings/stt_results_full.csv` and commit the sheet with `transcript_heard` blanked and the verdict columns kept
- [ ] T039 [US0] HUMAN: during T036, Ahmed confirms that the live agent voice matches the rated winning clip (research R5 runtime match). Record yes/no in `docs/phase0/decision.md`
- [ ] T040 [US0] KEY: billing check. Create one Simulation test in `agent/test_configs/`, attach it via `platform_settings.testing.attached_tests`, run `npx elevenlabs agents test <agent>` once, re-read `user subscription get`, and record `simulation_bills_minutes` in `docs/phase0/decision.md` and research.md R7
- [ ] T041 [US0] Fallback trigger, only if TTS or STT is NO_GO:
  - TTS NO_GO: re-rate Azure `ar-SA-ZariyahNeural` with the same 8 lines and raters.
  - STT NO_GO: plan the Vapi + Azure `ar-SA` STT adapter, keeping `eleven_flash_v2_5` TTS.
  - Both: STOP and re-scope with Ahmed.

  Write the adapter tasks into this file only if triggered (research R10; +3–4 h from contingency)
- [ ] T042 [US0] Complete `docs/phase0/decision.md` with every FR-012 field: llm_id, asr_provider, tts_model_id, voice_id, voice_settings, cli_version 1.7.1, minutes_used read from the counter, simulation_bills_minutes, both verdicts and fallback_triggered. HUMAN: Ahmed signs. Update `docs/STATUS.md` with gate result and minutes, and commit the blind key as `docs/phase0/clip_key.csv` only now

- [ ] T043 [US0] **CHECKPOINT: PHASE 0b GATE (HARD).**
  - PASS = TTS verdict GO or GO_WITH_RISK_FLAG, **and** STT verdict GO (or a passed fallback),
    computed by the scoring scripts on real data, **and** `decision.md` signed by Ahmed, **and**
    `STATUS.md` updated with minutes.
  - Delivery Phase 2, the Phase 3 run and Phase 4 stay blocked until this box is ticked.
  - STOP and report.

---

## Delivery Phase 1: Tools backend + tunnel (foundational for US1–US3)

**Goal**: the 6 webhook tools per [contracts/tools.openapi.yaml](contracts/tools.openapi.yaml),
seeded SQLite, the Arabic matcher, spoken numbers and a tunnel.

**May start while 0b waits** (review amendment 12), but not before T024.

**Independent test**: `bash scripts/test.sh` is green, and the T076 checkpoint passes.

### Setup

- [ ] T044 Re-check package pins. Pick FastAPI as the newest release ≥ 14 days old on the Phase 1 start date (today that would be 0.143.0; 0.162.0 is too new), then write `requirements.txt` with exact pins: that fastapi, `pydantic==2.14.1`, `rapidfuzz==3.14.6`, `uvicorn==0.54.0`, `httpx==0.28.1`, `PyYAML==6.0.3`, `jsonschema==4.26.0`. Record the date and versions in research.md R11. Also re-check that `@elevenlabs/cli` in `agent/package.json` is still pinned at 1.7.1 deliberately
- [ ] T045 [P] Create the package skeleton `backend/app/__init__.py`, `backend/app/main.py` (FastAPI app, `POST /tools/<name>` routes registered from `tools.py`) and `backend/tests/conftest.py` (TestClient, temp SQLite DB, `TOOL_SECRET` fixture)
- [ ] T046 [P] Add gitleaks as a pre-commit scan in `scripts/install_hooks.sh` (with a pinned gitleaks version chosen and recorded in research.md R15) and `.gitleaks.toml`, cross-platform (constitution V)

### Foundational (blocks all tool handlers)

- [ ] T047 Implement `backend/app/db.py` with `quotes`, `orders` and `tickets` per data-model C1–C3 (DB reset helper + seed loader):
  - `order_id` TEXT PK `^\d{4}$`;
  - `phone` `^05\d{8}$`;
  - `fulfillment` IN ('pickup','delivery');
  - `status` IN ('received','preparing','ready','out_for_delivery','delivered','cancelled') DEFAULT 'received';
  - `total_halalas` INTEGER;
  - UNIQUE(`conversation_id`, `quote_id`);
  - ticket `reason` IN ('asked_for_human','angry','not_understood','cancel_request','other') and `summary` 1–300 chars.
- [ ] T048 [P] Build `data/products.json` (30 fake items, 5 categories) from `docs/phase0/catalog_traps.md` per data-model B1:
  - `id` `^(KIT|CLN|PLA|GFT|STA)-\d{3}$`;
  - `price_halalas` ∈ {575, 975, 1475};
  - exactly 2 `in_stock: false`;
  - `unit`, `unit_dual_ar`, `unit_plural_ar`, `unit_gender` ∈ {m, f}.

  Then build `data/store.json` per data-model B2 (fictional name unless FR-073 says otherwise; hours Sat–Thu and Fri; delivery areas, fee and minimum in halalas; time windows; non-real phone; `demo_disclaimer_ar`)
- [ ] T049 [P] Seed 3 orders (one per status group) with obviously fake phones `0500000001`… in `backend/app/seed.py`
- [ ] T050 [P] Implement `scripts/build_agent_config.py --prompt <file> --profile phase0|full` that renders `agent/agent_configs/sara.json` from `prompts/system_v*.md` and keeps values chosen in 0b. Add tests in `scripts/tests/test_build_agent_config.py` (the phase0 output passes `agent/validate_configs.py` and equals the hand-written 0a file)
- [ ] T051 [P] Implement `backend/app/envelope.py`: build responses `{status ∈ ok|error|needs_clarification|not_found, error_code, say_ar, say_en, …}` with the error_code enum from contracts/tools.openapi.yaml `Envelope`
- [ ] T052 [P] Implement `backend/app/auth.py` (`X-Tool-Secret` compared with `hmac.compare_digest`, 401 `{"detail":"unauthorized"}`, attempt logged without header values) and `backend/app/ratelimit.py` (~30 req/min per IP → 429). Add an 8 KB body cap (413) in `backend/app/main.py` middleware (review M18)
- [ ] T053 [P] Implement `backend/app/logging.py`: JSONL to git-ignored `backend/logs/tool_calls.jsonl` with `ts, tool, conversation_id, request_body, status, error_code, latency_ms, http_status` and never header values (data-model C4)
- [ ] T054 [P] Write the golden tests first in `backend/tests/test_arabic.py`:
  - ≥ 30 query → product_id pairs, incl. صحن/صحون, كاسات→أكواب, والصحون, بالصحون, Arabic-Indic digits and filler words;
  - an alias-lint test (no alias shared by two products, no bare category word);
  - ambiguity returns ≤ 2 options.
- [ ] T055 Implement `backend/app/arabic.py` with the review B4 pipeline (strip tashkeel/tatweel → strip clitics `^(و|ف)?(ب|ل|ك)?ال`, `^لل` with min stem 3 → unify أإآٱ→ا, ة→ه, ى→ي, ؤ→و, ئ→ي → Arabic-Indic digits → punctuation; remove filler words بكم، كم، عندكم، فيه، أبي، ابغى، ممكن; exact alias first; `WRatio` or `max(token_sort_ratio, 0.9·partial_ratio)` scoring; `token_set_ratio` only for ambiguity). `match_key` must never overwrite `name_ar`. Make T054 green
- [ ] T056 [P] HUMAN + tests first: create `backend/tests/golden_spoken.csv` covering 1, 2, 3, 10, 11, 17, 25, 99, 100, 117 and 200 riyals; 25/50/75 halalas; qty 1/2/3/11 per unit; one phone; one order id. The register follows the T025 sign-off (Ahmed signs the file header). Add `backend/tests/test_spoken.py`
- [ ] T057 Implement `backend/app/spoken.py` (money from halalas, whole amounts drop halalas, quantity–unit agreement using `unit_dual_ar`/`unit_plural_ar`/`unit_gender`, digit-by-digit order id, phone grouped 3·3·4). Make T056 green
- [ ] T058 [P] Write tests first in `backend/tests/test_phone.py`, then implement `normalize_phone()` in `backend/app/phone.py`: accepts +966 / 966 / 5XXXXXXXX / Arabic-Indic digits / paired-number speech → `^05\d{8}$`, else `invalid_phone`
- [ ] T059 [P] Write tests first in `backend/tests/test_timeslot.py`, then implement `backend/app/timeslot.py`: resolve phrases like «بكرة العصر» against `now` (Asia/Riyadh) and `store.time_windows` into `{date, window ∈ morning|noon|afternoon|evening|night, time_slot_spoken_ar}`, with `outside_hours` for closed windows (Friday hours separately)
- [ ] T060 [P] Write tests first in `backend/tests/test_redact.py`, then implement `backend/app/redact.py`: mask `05\d{8}`, `9665\d{8}`, digit runs ≥ 7, Arabic-Indic digit runs and caller names (review B5)
- [ ] T061 [P] Add `backend/tests/test_contracts.py`, which validates every tool response (ok and each error path) against the component schemas in `specs/001-saudi-voice-receptionist/contracts/tools.openapi.yaml` using `jsonschema==4.26.0`

### Tool handlers by story

- [ ] T062 [P] [US1] Write tests first in `backend/tests/test_tools.py::test_get_product_*`, then implement `get_product` in `backend/app/tools.py`. Rules: `query` 1–120 chars; ≤ 3 matches; `needs_clarification` with exactly 2 `clarify_options_ar` for near-duplicates; `suggestions` ≤ 2 in-stock alternatives for out-of-stock or not_found; `price_spoken_ar` on every match
- [ ] T063 [P] [US1] Write tests first, then implement `get_store_info` in `backend/app/tools.py`: `topic` ∈ {hours, location, delivery, returns, phone}, optional `day`, `unknown_topic` error, `served_areas_ar` for delivery, text only from `data/store.json`
- [ ] T064 [US2] Write tests first, then implement `quote_order` in `backend/app/tools.py`. Inputs: `items` 1–10 of `{product_id, qty 1–20}`, `fulfillment`, `area` (required when delivery), `time_slot` ≤ 40 chars. It writes only to `quotes` and returns `quote_id`, `lines[]` with `qty_spoken_ar`, `subtotal_halalas`, `delivery_fee_halalas`, `total_halalas`, `total_spoken_ar`, `below_minimum` and `slot`. Errors: `unknown_product`, `invalid_qty`, `out_of_stock`, `area_not_served` (with `served_areas_ar`), `below_minimum`, `outside_hours`, `missing_field`
- [ ] T065 [US2] Write tests first, then implement `create_order` in `backend/app/tools.py`. Inputs: `quote_id`, `customer_name` 1–40, `phone`, and `conversation_id` from the platform. Lines and total are copied from the quote. It returns `order_id` `^\d{4}$` unique, `order_id_spoken_ar`, `phone_spoken_ar` and `total_spoken_ar`. A second call with the same (`conversation_id`, `quote_id`) returns the same order with `duplicate: true`. Errors: `invalid_phone`, `quote_not_found`, `quote_mismatch` (depends on T064)
- [ ] T066 [P] [US3] Write tests first, then implement `check_order_status` in `backend/app/tools.py`: by `order_id` `^\d{4}$` or by `phone` (≤ 2 latest orders), `status_ar` and `order_id_spoken_ar`, `not_found` without guessing
- [ ] T067 [P] [US3] Write tests first, then implement `escalate_to_human` in `backend/app/tools.py`: `reason` enum, `summary` 1–300, optional `customer_name` ≤ 40 and `phone`; it writes a ticket and returns `ticket_id` and `callback_text_ar`. A `cancel_request` reason is supported

### Scripts and verification

- [ ] T068 [P] Write `scripts/test.sh`: venv-aware, runs `pytest backend/tests scripts/tests agent/tests -q`, and works on Git Bash and macOS
- [ ] T069 [P] Write `scripts/dev.sh`, which runs `uvicorn backend.app.main:app --port 8000`
- [ ] T070 [P] Write `scripts/latency.sh`: 100 local calls per tool, prints p50/p95, fails if p95 ≥ 300 ms
- [ ] T071 Write `scripts/tunnel.sh` (research R13). It starts `cloudflared tunnel --url http://localhost:8000`, captures the hostname into `.env` as `TOOLS_BASE_URL`, and renders `agent/tool_configs/*.json` from `*.json.tmpl`. In Phase 1 it only prints; the push comes in Phase 2. Record the installed cloudflared version in research.md R13
- [ ] T072 HUMAN: Ahmed approves or edits `backend/tests/golden_spoken.csv` (signed header)
- [ ] T073 Run `bash scripts/test.sh` and `bash scripts/latency.sh` on the Mac and commit the outputs summary to `docs/STATUS.md`
- [ ] T074 Tunnel check. From a second network (phone hotspot), `curl` each tool through the tunnel: 200 with the secret, 401 without. Record the result in `docs/STATUS.md` and stop the tunnel afterwards
- [ ] T075 HUMAN: on the other OS (Windows laptop), take a fresh clone and run `bash scripts/test.sh` until it is green, then record that in `docs/STATUS.md`

- [ ] T076 **CHECKPOINT: PHASE 1 GATE (HARD).** PASS requires all of:
  - pytest green incl. ≥ 30 matcher pairs and `golden_spoken.csv`;
  - 401 without secret, 413 on oversize body, 422 on schema violation, and a 200 envelope on every error path;
  - `create_order` idempotent (2nd call → `duplicate: true`);
  - p95 < 300 ms over 100 calls per tool;
  - tunnel 200 with secret / 401 without from a second network;
  - fresh clone green on the 2nd OS.

  STOP and report.

---

## Delivery Phase 2: Prompt v1 + agent + widget (US1–US4 live). BLOCKED on T043 and T076

**Goal**: a caller completes orders by voice on the hosted page (D1).

**Independent test**: the T092 checkpoint.

- [ ] T077 [US1] Write `prompts/system_v1.md` in Saudi Arabic with plural address, using the root `plan.md` §8 sections (# الشخصية … # أمثلة), the 10 non-negotiable rules, the order flow 1–7 with `quote_order` before read-back, a filler pool of 4–5 variants for slow tools, the Arabic-only rule (no language switch; replaces the old 2-English-turns switch), and the demo clause «نسخة تجريبية، الأسعار غير حقيقية». Fix «جملتين قصيرة» → «جملتين قصيرتين». Prices in # أمثلة are generated from `data/products.json`
- [ ] T078 [P] [US1] Write `agent/tool_configs/get_product.json.tmpl` and `agent/tool_configs/get_store_info.json.tmpl` per research R12: `api_schema.url` = `{{TOOLS_BASE_URL}}/tools/<name>`, `request_headers.X-Tool-Secret` = `{"secret_id": …}`, the `conversation_id` body property with `dynamic_variable: system__conversation_id`, `response_timeout_secs` ∈ 5–300, and `pre_tool_speech` set as decided
- [ ] T079 [P] [US2] Write `agent/tool_configs/quote_order.json.tmpl` and `agent/tool_configs/create_order.json.tmpl` (same rules as T078; `now` bound to `system__time`)
- [ ] T080 [P] [US3] Write `agent/tool_configs/check_order_status.json.tmpl` and `agent/tool_configs/escalate_to_human.json.tmpl` (same rules as T078)
- [x] T081 [US4] Extend `scripts/build_agent_config.py --profile full` with the agent settings baseline (review amendment 8):
  - ~~`language_presets` incl. `en` and `language_detection`~~ dropped: Arabic only (2026-10-28);
  - `turn.turn_timeout`, `turn.silence_end_call_timeout` and `conversation.max_duration_seconds: 240`;
  - `auth.allowlist` (Pages host + `localhost:8000`), `require_origin_header: true`;
  - `call_limits.daily_limit: 20`, `agent_concurrency_limit: 2`, `privacy.retention_days: 30`;
  - `end_call` enabled; the 0b winning voice/model/ASR; `tts.text_normalisation_type` as decided.

  Validate every field with `python agent/validate_configs.py --allow-voice-id`
- [x] T082 KEY: create the ElevenLabs secret for `TOOL_SECRET` via `npx elevenlabs agents secrets create` (check `--schema` first) and put only its `secret_id` into the templates' render input in `.env` (constitution V)
- [ ] T083 DEFERRED to Phase 4 (2026-11-01): keep `gemini-2.5-flash` (still in `agents llm list`, passed the 0b simulation) and compare models on the v1 results instead of 3 extra calls. Original: LLM shortlist via `npx elevenlabs agents llm list`. Pick one Gemini Flash and one Claude Haiku class model, measure latency and Arabic quality on 3 test calls, and record the pick and reason in research.md (new R19) and `docs/STATUS.md`
- [x] T084 [US2] Build `demo/index.html` with `<elevenlabs-convai>` from `@elevenlabs/convai-widget-embed` pinned to an exact version ≥ 14 days old (research R14), a visible demo banner (prices not real), and the store name per FR-073. Serve it with `python -m http.server 8000`, never `file://`
- [x] T085 [P] [US2] Write `docs/flow.mmd`, a Mermaid activity diagram (greeting → intent → branches → quote → read-back → confirm → create → end / escalate)
- [x] T086 [P] (Done on a Cloudflare static-assets Worker instead, 2026-11-01; see STATUS) Publish `demo/` on GitHub Pages (workflow or branch setting) and record the Pages host in the `auth.allowlist` input
- [x] T087 KEY: on the Mac, run `scripts/tunnel.sh`, then from `agent/` run `npx elevenlabs agents pull`, then `agents push && tools push && tests push`. Afterwards run `agents push --dry-run` and confirm no drift
- [x] T088 [US2] HUMAN: 3 consecutive voice orders on the hosted page (1 pickup, 1 delivery, 1 with a mid-call correction). Claude checks that each SQLite row has `conversation_id` from `system__conversation_id`, a `quote_order` call before `create_order`, a spoken read-back and a digit-by-digit order id (verifies research R12)
- [ ] T089 [US1] HUMAN: one call asking for an out-of-stock item, which must be spoken as unavailable with at most one alternative
- [x] T090 [US4] HUMAN: one mixed call «أبي delivery للمبرز» that must stay Arabic (E11). E10 (English switch) dropped: Arabic only
- [x] T091 Log the call minutes used in Phase 2 in `docs/STATUS.md` (read from the usage counter) and disable the agent or demo between sessions

- [ ] T092 **CHECKPOINT: PHASE 2 GATE (HARD).** PASS requires:
  - T088 (3/3 orders correct), T089 and T090 all pass;
  - `agents push --dry-run` shows no drift;
  - minutes logged.

  STOP and report.

---

## Delivery Phase 3: Eval suite + v1 (US5). Offline parts (T093–T101) may start while 0b waits; the run (T102+) is BLOCKED on T092

**Goal**: measured v1 quality with a human-verified critical-flag list.

**Independent test**: the T109 checkpoint.

- [ ] T093 [P] [US5] Write `evals/scenarios.yaml` with ~26 scenarios: the 20 from root `plan.md` §9 plus pickup, area not served, below minimum, out-of-stock inside an order, "no" at read-back, status by id / not found, returns policy, alias trap, qty ≥ 11, injection via `customer_name`, and cancel request. Each scenario has `id, type, mode ∈ sim|voice|both, split ∈ dev|holdout` (≈ 70/30, fixed now), `persona, caller_goal, script_hints, expected_tools` (with argument assertions), `must_say_re, must_not_say_re, pass_criteria`. E7–E9 are `voice` only
- [ ] T094 [P] [US5] Write `evals/rubric.md` with the critical rows (grounding, order without confirmation, phantom confirmation, spoken number ≠ tool output, prompt/secret disclosure), the major/minor rows, and the definitions: brevity = ≤ 2 segments on `[.!?؟]` and ≤ 30 words, filler counted separately; missed cue; escalation trigger
- [ ] T095 [P] [US5] Write `evals/call_cards/` with 10 cards (H1, H2, H5, H6, E3, E5, E6, E10/E11, E12, E14), fake names and phones `0500000001`…, plus a short Arabic consent line for family callers
- [ ] T096 [US5] Decide the judge (research R16). Ahmed names the provider key; the model comes from a different family than the agent LLM and its id is checked in that provider's model list. Write `evals/judge_config.yaml` (model id, prompt hash, temperature 0)
- [ ] T097 [P] [US5] Write tests first in `evals/tests/test_score.py`, then implement `evals/score.py` (pass rate, Wilson 95% CI, pass^k, paired per-scenario comparison, `--readme` table output, `--check` that verifies README/QA_REPORT numbers)
- [ ] T098 [P] [US5] Implement `evals/run_sims.py`. It uses platform Simulation/Tool Call tests (`test_configs/`, `repeat_count`) where they fit and an LLM caller from each persona for the rest, resets SQLite per run, and writes run metadata `agent_config_sha, llm_model_id, voice_id, tts_model_id, asr_provider, catalog_sha, simulator_model, judge_config_sha, k, cli_version` to `evals/results/<v>/run.json`
- [ ] T099 [P] [US5] Implement `evals/fetch_transcripts.py` (conversations API via the CLI, joined with `backend/logs/tool_calls.jsonl`). Raw output goes to git-ignored `evals/results/<v>/raw/` and real calls to `real_calls/`; only `redact.py` excerpts are committed
- [ ] T100 [US5] Implement `evals/judge.py`. Deterministic tool-log assertions run first, then the LLM judge on the remaining dimensions, with transcripts delimited as data and catalog + `store.json` + tool log given. It writes per-scenario JSON
- [ ] T101 [US5] HUMAN: hand-label ~30 gold transcripts in `evals/gold/`. Compute judge agreement and κ per dimension. A dimension is auto-scored only at agreement ≥ 0.9 and κ ≥ 0.7, otherwise it is human-scored
- [ ] T102 [US5] KEY: run v1 with `bash scripts/eval.sh v1` (≥ 20 sim scenarios × k = 5, floor 3) into `evals/results/v1/`
- [ ] T103 [US5] HUMAN: 10 real calls by Ahmed + family using the cards, with written consent collected. Fetch, redact and join them to the tool logs
- [ ] T104 [US5] HUMAN: Ahmed reviews 100% of critical flags and 100% of real calls, and gives each real call a 1–5 Saudi naturalness score on the Phase 0 scale (feeds SC-016, voice-only). The human verdict overrides the judge. Write the signed flag list to `evals/results/v1/critical_flags.md`
- [ ] T105 [P] [US5] Spot-check 20% of judge passes and record the result in `evals/results/v1/spotcheck.md`
- [ ] T106 Verify `git ls-files` shows no raw transcript or audio, and record the check in `docs/STATUS.md`
- [ ] T107 Log the minutes used in Phase 3 in `docs/STATUS.md`
- [ ] T108 [P] Write `scripts/eval.sh`, a cross-platform wrapper: run_sims → fetch → judge → score

- [ ] T109 **CHECKPOINT: PHASE 3 GATE (HARD).** PASS requires:
  - ≥ 20 sim scenarios × k ≥ 3 completed;
  - judge agreement gate applied per dimension;
  - 10 real-call transcripts fetched, redacted and joined;
  - 100% of critical flags and real calls carry a human verdict;
  - run metadata recorded;
  - no raw data tracked by git.

  STOP and report.

---

## Delivery Phase 4: Fixes → v2 + rerun (US6). BLOCKED on T109

**Goal**: measured improvement under frozen conditions (D3).

**Independent test**: the T117 checkpoint.

- [ ] T110 [US6] List findings from `evals/results/v1/` and propose ≥ 5 fixes, each with the scenario behind it, in `evals/results/v1/proposed_fixes.md`
- [ ] T111 [US6] HUMAN: Ahmed approves fixes (≥ 5)
- [ ] T112 [US6] Apply the approved fixes in `prompts/system_v2.md` (and tools/flow where approved). Turning on `platform_settings.guardrails.prompt_injection` counts as its own CHANGELOG item
- [ ] T113 [US6] Write `prompts/CHANGELOG.md` entries: date · change · scenario id · metric before → after (after-values are filled only from v2 results)
- [ ] T114 [P] [US6] Implement `scripts/check_frozen.py v1 v2`. It verifies the same suite, same k, same cards and same frozen model/config hashes, except for the intended prompt/config change
- [ ] T115 [US6] KEY + HUMAN: run v2 on the same suite (`bash scripts/eval.sh v2`), the same 10 cards with the same callers, and the holdout. If critical grounding or unconfirmed orders are > 0, allow one 1-hour v2.1 retry, then report honestly
- [ ] T116 Log the minutes used in Phase 4 in `docs/STATUS.md`

- [ ] T117 **CHECKPOINT: PHASE 4 GATE (HARD).** PASS requires:
  - each CHANGELOG entry cites a scenario id and a before→after metric;
  - `check_frozen.py` passes;
  - v2 critical grounding failures = 0 **and** orders-without-confirmation = 0 on dev and holdout;
  - no critical dimension regresses.

  STOP and report.

---

## Delivery Phase 5: Ship (US7). BLOCKED on T117

**Goal**: a public repo, report and video a hiring reviewer can trust (D2, D5, D6).

**Independent test**: the T128 checkpoint.

- [ ] T118 [P] [US7] Write `README.md` with:
  - problem, architecture, and setup on both OSes (links to quickstart);
  - the results table generated by `evals/score.py --readme`;
  - the video link, the demo-data note and the Sarj mapping (root `plan.md` §13);
  - pinned versions and minutes vs budget.
- [ ] T119 [P] [US7] Write `reports/QA_REPORT.md`:
  - a v1 vs v2 table on every rubric dimension with CIs;
  - the top 5 issues (redacted excerpt → root cause → fix → result);
  - remaining issues;
  - method (simulated vs real numbers, judge vs human).
- [ ] T120 [P] [US7] Write `docs/architecture.mmd` and export PNGs of `flow.mmd` and `architecture.mmd` to `docs/`
- [ ] T121 [US7] Run `python evals/score.py --readme --check`. Every number in README and QA_REPORT must match `summary.csv`
- [ ] T122 [US7] HUMAN: record the 60–90 s video (one order call, one edge case, the results table) and add the link to README
- [ ] T123 Run a gitleaks scan on the full history, and check with `git ls-files` that no audio or raw transcript is tracked
- [ ] T124 HUMAN: on the other OS, take a fresh clone and run `bash scripts/test.sh` until it is green
- [ ] T125 HUMAN: after the report is final, delete the real-call conversations from the platform, disable the demo agent between sessions, and rotate `TOOL_SECRET`
- [ ] T126 Update `docs/STATUS.md` with total minutes vs the ~110 budget and hours vs 23 h + 3 h
- [ ] T127 [P] Check that the demo banner and the first-message demo clause are present on the live page

- [ ] T128 **CHECKPOINT: PHASE 5 GATE.** PASS requires:
  - fresh clone green on the other OS;
  - numbers match by script;
  - video 60–90 s with the three required parts;
  - gitleaks clean on full history;
  - no audio or raw transcript in git;
  - banner present;
  - STATUS shows minutes vs budget.

  Final push.

### Optional Phase 6: Twilio number (0 budgeted hours)

- [ ] T129 HUMAN + KEY: only after T128 and the video are published, attach a Twilio number and complete one real phone order. Twilio bills directly, so Ahmed approves the cost first

---

## Polish and cross-cutting concerns (run at each phase start)

- [ ] T130 [P] At the start of each phase, re-check `@elevenlabs/cli` and the widget pins against `npm view` and re-run `agent/validate_configs.py` (it reads the spec from the pinned CLI) if the pin changes (constitution VI)
- [ ] T131 [P] Run `/speckit-analyze` on spec.md, plan.md and tasks.md after `/speckit-clarify` resolves FR-008, FR-053 and FR-073, and fix any inconsistency
- [ ] T132 [P] Keep `CLAUDE.md` consistent with the constitution: add the `docs/STATUS.md` + `quickstart.md` pointers and the 0a/0b split
- [ ] T133 HUMAN: Ahmed books the 3 family sessions now (0b rating + STT speaking; v1 real calls; v2 real calls with the same callers and cards) and notes the dates in `docs/STATUS.md` blockers (review M16). Names stay out of git
- [ ] T134 [P] On the Mac after `git clone`, recreate the git-ignored `.specify/feature.json` as `{"feature_directory": "specs/001-saudi-voice-receptionist"}` (quickstart §1) so the Spec Kit skills find the feature; verify with `bash .specify/scripts/bash/check-prerequisites.sh --json`

---

## Dependencies and execution order

### Gate chain (hard)

- T024 (0a) is the first gate.
- From T024: T043 (0b) → T092 (Phase 2) → T109 (Phase 3) → T117 (Phase 4) → T128 (Phase 5) →
  optional T129.
- Also from T024: T076 (Phase 1) → T092.
- Phase 2 needs **both** T043 and T076.

### Allowed overlap (review amendment 12)

- Phase 1 (T044–T076) may start after T024 while 0b (T025–T043) waits for the key and raters.
- The offline parts of Phase 3 (T093–T101) may start after T024.
  - T096 needs Ahmed's judge-provider decision.
  - T101 needs transcripts, so in practice it runs after T102.
- The Phase 3 run (T102+), all of Phase 2 and all of Phase 4 stay strictly gated.
- **This session stops at T024.**

### Within Phase 0a

- T001 → T007 → T010.
- T009 → T010.
- T012 ↔ T014 (keep the trap item consistent).
- T001 + T010 → T008 → T011.
- T013 + T017 + T020 → T021.
- Everything → T022 → T024.

### Within Phase 0b

- T025 + T026 → T027 → T028 → T029 → T030 → T031 → T032 → T033 → (T034) → T035 → T036 → T037
  → T038, then T039 and T040 → (T041) → T042 → T043.

### Within Phase 1

- T044 → T045 → foundational tasks T047–T061.
- Within the handlers: T054 → T055, T056 → T057, and T064 → T065.
- Handlers T062–T067 come after T047, T051, T052, T053, T055 and T057.
- Verification T068–T075 comes after the handlers.

### Story completion order

US0 → (US1, US2, US3 backend in parallel in Phase 1) → US1/US2/US3/US4 live in Phase 2 → US5 →
US6 → US7.

## Parallel examples

```text
# Phase 0a: after T001/T002, launch together:
T003 .gitignore · T005 scripts/py.sh+env.sh · T006 docs/STATUS.md · T009 prompts/system_v0.md
T011 validator tests · T012 catalog_traps.md · T013 tts_script.md table · T015/T016 voice_selection.md
T017 thresholds.json · T018 rating form rules · T019 tts_ratings.csv · T020 test_phase0.py cases

# Phase 1: after T047/T051-T053:
T054 test_arabic.py · T056 golden_spoken.csv · T058 phone · T059 timeslot · T060 redact · T061 contract tests
then T062 get_product [US1] · T063 get_store_info [US1] · T066 check_order_status [US3] · T067 escalate [US3]

# Phase 2: T078 [US1] · T079 [US2] · T080 [US3] tool templates, T085 flow.mmd, T086 Pages

# Phase 3 offline: T093 scenarios · T094 rubric · T095 call cards · T097 score.py · T098 run_sims · T099 fetch
```

## Implementation strategy

1. **Today (Windows)**: Phase 0a only, T001–T024, then stop at the T024 checkpoint and report.
   T001, T004, T007, T008, T009, T010, T013, T014, T015 and T016 are being executed now (files on
   disk, checked by the leader analysis on 2026-10-27). The orchestrator commits and pushes to the
   public repo, so the Mac can resume from git.
2. **Mac, with key and raters**: Phase 0b, T025–T043. This is the go/no-go, and nothing is
   recorded without real API output or human scores. While waiting for raters, start Phase 1
   (T044+) and offline Phase 3 (T093–T100).
3. **MVP**: Phase 1 + Phase 2 with US1 + US2 live (T092). This is D1: a caller completes a
   delivery order by voice.
4. **Incremental after the MVP**: US3/US4 checks in Phase 2, the measured v1 (US5) in Phase 3,
   v2 (US6) in Phase 4, and shipping (US7) in Phase 5.
5. **Cut order if time runs short** (pre-approved, review M10): drop Twilio → 6 call cards × 2
   versions → k = 3 → Mermaid instead of Lucidchart.
