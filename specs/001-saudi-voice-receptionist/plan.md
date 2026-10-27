# Implementation Plan: Saudi Voice Receptionist "Sara"

**Branch**: `001-saudi-voice-receptionist` (Spec Kit feature id only; work stays on `main`, no git
branch is created) | **Date**: 2026-10-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-saudi-voice-receptionist/spec.md`. Sources of truth,
in order: `.specify/memory/constitution.md` v1.0.0, `reviews/plan-review.md` sections E–G, then the
root `plan.md` (Technical Spec v1.0).

## Summary

Sara is a Saudi-dialect voice receptionist for a fake-data home-goods store. ElevenLabs Agents
hosts the voice loop (ASR → LLM → TTS). A FastAPI + SQLite tools backend is the only source of
prices, stock, totals and orders, and a QA pipeline scores v1 and v2 against a rubric. The
deliverables are D1–D6 from the root `plan.md` §1.

Work is gated in six delivery phases (review section F). **This session stops at the Phase 0
gate.** Phase 0 is split:

- **0a**: offline on the Windows laptop today. It produces the minimal Arabic agent, the voice
  selection procedure for 3 candidates, the 8-line TTS script, the 10-utterance STT sheet,
  templates, the scoring script and STATUS.
- **0b**: on the Mac Mini with an API key, a paid plan and human raters. It produces the real
  voice IDs, 48 clips, ratings, STT transcripts and the signed decision.

Nothing in 0b is written before a real API result or human score exists.

## Technical Context

**Language/Version**: Python 3.12 (`.python-version`; laptop 3.12.10). Bash for task scripts
(Git Bash on Windows, bash/zsh on macOS). Node ≥ 20 only to run the pinned CLI via `npx`.

**Primary Dependencies**:

- `@elevenlabs/cli` **1.7.1** (exact devDependency) for agent config as code.
- 0a: stdlib-only scripts plus `pytest==9.1.1`.
- Phase 1: FastAPI (pin chosen at the Phase 1 start by the ≥ 14-day rule, research R11),
  `pydantic==2.14.1`, `rapidfuzz==3.14.6`, `uvicorn==0.54.0`, `httpx==0.28.1`, `PyYAML==6.0.3`,
  `jsonschema==4.26.0`.
- Phase 2: `@elevenlabs/convai-widget-embed`, version chosen at build by the ≥ 14-day rule
  (0.19.1 qualifies today).
- Phase 3: judge SDK, pending decision R16.

**Storage**: SQLite (stdlib), with money as integer halalas. JSON data files (`data/`). CSV and
Markdown sheets for Phase 0 (`docs/phase0/`). JSONL tool log (git-ignored).

**Testing**: pytest (`phase0/test_phase0.py` also runs as a plain script, since pytest is not
installed on the laptop yet). Golden tables (≥ 30 matcher pairs, `golden_spoken.csv`); contract
tests validate responses against [contracts/tools.openapi.yaml](contracts/tools.openapi.yaml)
schemas; the two Phase 0 scorers are tested on fake data; agent configs are validated against the
CLI's own spec (research R2.1).

**Target Platform**:

- Dev machines: Windows 11 (Git Bash) and macOS (Mac Mini).
- Voice: ElevenLabs hosted agent.
- Tools: FastAPI on the Mac behind a cloudflared quick tunnel.
- Demo: static page on GitHub Pages.

**Project Type**: web service (tools backend), plus agent config as code, an eval CLI and a
static demo page.

**Performance Goals**: tool p95 < 300 ms locally over 100 calls per tool (Phase 1 gate). No dead
air: a filler pool before tools with p95 > ~700 ms.

**Constraints**:

- ≤ 2 short sentences per turn.
- ~110 call minutes in total on Starter, with a 15-minute Phase 0 spike.
- 23 h build + 3 h contingency.
- Public repo: no secrets, raw transcripts or audio in git.
- The laptop never pushes the agent.
- Every API/CLI shape must be verified (constitution VI).

**Scale/Scope**: 1 agent, 6 tools, 30 products, 1 store, ~26 sim scenarios × k = 5 (floor 3), 10
real call cards × 2 versions, 2 concurrent calls max, 20 calls/day limit.

**NEEDS CLARIFICATION**: none that blocks 0a. Three of Ahmed's decisions carry over from the
spec: FR-008 thresholds, FR-053 register and FR-073 store name. One technical item is deferred
with a decision rule: R16 judge provider (Phase 3). Every other unknown is resolved or labelled
UNVERIFIED in [research.md](research.md), with a named check task.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | How this plan complies | Pre-design | Post-design |
| --- | --- | --- | --- |
| I. Grounded Facts Only | `quote_order` is the only source of read-back totals; every spoken number comes from a `*_spoken_ar` field; the envelope carries `say_ar` for failures ([contracts/tools.openapi.yaml](contracts/tools.openapi.yaml)) | PASS | PASS |
| II. Voice Brevity | prompt rules + brevity metric (≤ 2 segments, ≤ 30 words) in the rubric; ≤ 2 clarification options in the contract | PASS | PASS |
| III. Read-Back Before Commit | `create_order` requires `quote_id`, is idempotent on (`conversation_id`, `quote_id`) with a UNIQUE constraint ([data-model.md](data-model.md) C2) | PASS | PASS |
| IV. Fake Data, Private Calls | seed phones `05000000xx`; Phase 0 clips in git-ignored `phase0/samples/` (T003 adds the ignore rule), raw transcripts in `phase0/recordings/` per the T038 decision; `redact.py` and consent from Phase 1/3 | PASS | PASS |
| V. Secrets Only in .env | `.env.example` names only; `X-Tool-Secret` as an ElevenLabs Secret via `secret_id` (R12); gitleaks pre-commit from Phase 1 | PASS | PASS |
| VI. Verify Docs Before Use | every CLI/API shape in research.md cites a URL or a 1.7.1 `--help` / `--schema` / `--dry-run` output; UNVERIFIED items are labelled with a check task; all pins exact | PASS | PASS (new finding R2.1 handled by an added validator) |
| VII. Phase Gates, Never Faked | 0a/0b split; 0a writes no voice id, score or minute; every phase ends with an explicit checkpoint task in tasks.md; this session stops at the Phase 0 gate | PASS | PASS |
| VIII. Eval-Driven Changes | CHANGELOG format, frozen run metadata ([data-model.md](data-model.md) D2), deterministic tool-log assertions first, human override | PASS | PASS |
| IX. English Code, Saudi Speech | docs and code in English; prompts, `say_ar`, TTS lines and utterances in Saudi Arabic UTF-8 with plural address; `match_key` never overwrites `name_ar` | PASS | PASS |

There are no violations, so Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/001-saudi-voice-receptionist/
├── spec.md                 # /speckit-specify output (step 1)
├── checklists/requirements.md
├── plan.md                 # this file
├── research.md             # R1–R18 decisions with sources, pins, UNVERIFIED items
├── data-model.md           # Phase 0 entities + catalog, quote, order, ticket, eval entities
├── quickstart.md           # Mac Mini setup + Phase 0b runbook + later gate scenarios
├── contracts/
│   ├── tools.openapi.yaml  # 6 webhook tools, envelope, errors
│   └── phase0-artifacts.md # CSV columns, thresholds.json, score_phase0.py CLI, sara.json profile
└── tasks.md                # /speckit-tasks output
```

### Source Code (repository root)

```text
saudi-voice-receptionist/
├── CLAUDE.md  plan.md  README.md (Phase 5)
├── .env.example            # names only (0a: ELEVENLABS_API_KEY; Phase 1+: TOOL_SECRET, TOOLS_BASE_URL, ...)
├── .python-version         # 3.12
├── requirements-dev.txt    # 0a: pytest==9.1.1 (Phase 1 adds requirements.txt)
├── agent/                  # `agents init` layout (CLI 1.7.1); run `npm ci` here first
│   ├── package.json  package-lock.json   # devDependency "@elevenlabs/cli": "1.7.1"
│   ├── agents.json  tools.json  tests.json  README.md
│   ├── agent_configs/sara.json  sara_stt_probe.json   # 0a: minimal Arabic agents, no tools, no voice id
│   ├── validate_configs.py  tests/   # offline validator reading enums/ranges from `agents create --spec`
│   ├── tool_configs/*.json.tmpl       # Phase 2, rendered by scripts/tunnel.sh
│   └── test_configs/
├── prompts/
│   ├── system_v0.md        # 0a: minimal Sara persona (the STT probe config answers only «تمام»)
│   ├── system_v1.md  system_v2.md  CHANGELOG.md   # Phases 2 and 4
├── docs/
│   ├── STATUS.md           # phase, open gate, blockers, minutes (T006, not on disk yet)
│   ├── phase0/             # review F names, all on disk from the 0a run: tts_script.md, stt_sheet.md,
│   │                       # stt_results.csv, voice_selection.md, tts_ratings.csv, catalog_traps.md;
│   │                       # added later: thresholds.json (T017), clip_key.csv + decision.md (0b)
│   ├── flow.mmd (Phase 2)  architecture.mmd (Phase 5)
├── phase0/                 # 0a/0b tooling: find_voices.py, tts_samples.py (SDK, Mac), tts_score.py,
│   │                       # stt_score.py, test_phase0.py (stdlib), requirements.txt (elevenlabs==2.74.1,
│   │                       # python-dotenv==1.2.4)
│   ├── samples/            # git-ignored: 48 clips, blind copies, blind_key.csv until rating ends
│   └── recordings/         # git-ignored: raw transcripts
├── scripts/                # bash entry points + Python tools, cross-platform (none on disk yet)
│   ├── py.sh  env.sh  check_phase0a.sh
│   ├── score_phase0.py  build_agent_config.py   # thin wrapper over phase0/*_score.py (T021); config generator (Phase 1)
│   ├── test.sh  tunnel.sh  latency.sh  eval.sh            # Phases 1–3
│   └── tests/test_build_agent_config.py
├── backend/app/{main,tools,models,envelope,db,arabic,spoken,phone,timeslot,auth,ratelimit,logging,redact}.py
├── backend/tests/{test_tools,test_contracts,test_arabic,test_spoken,test_phone,test_timeslot,test_auth}.py + golden_spoken.csv
├── data/{store.json,products.json}
├── evals/{scenarios.yaml,rubric.md,judge_config.yaml,call_cards/,run_sims.py,fetch_transcripts.py,judge.py,score.py,results/{v1,v2}/}
├── reports/QA_REPORT.md
└── demo/index.html
```

**Structure Decision**: a single repository with four parts (agent config, tools backend, eval
suite, reports), as in root `plan.md` §5 with the review amendments:

- `agent/` follows the CLI's `init` layout, with the CLI pinned inside it;
- `scripts/` replaces the Makefile (amendment 15);
- Phase 0 tooling lives in `phase0/`; every Phase 0 sheet and gate-named document lives in
  `docs/phase0/` under the review section F names (`tts_script.md`, `stt_sheet.md`,
  `stt_results.csv`, `voice_selection.md`, `tts_ratings.csv`, `catalog_traps.md`, later
  `thresholds.json`, `clip_key.csv`, `decision.md`). Clips go to git-ignored `phase0/samples/`
  and raw transcripts to `phase0/recordings/`. The review's `scripts/score_phase0.py` is realized
  as `phase0/tts_score.py` + `phase0/stt_score.py`, with a thin wrapper added in T021;
- `backend/app/` gains `envelope.py`, `phone.py`, `timeslot.py`, `ratelimit.py` and `redact.py`
  for amendments 4, 6, M12, M13, M18 and B5.

### Phase 0a outputs (the gate's file list)

Status on disk is from the leader analysis of 2026-10-27 (`analysis.md`).

1. `agent/package.json` + `agent/package-lock.json` (CLI 1.7.1, darwin/linux/win32 binaries). ON DISK.
2. The `agent/` init layout, plus `agent/agent_configs/sara.json`, `agent/agent_configs/sara_stt_probe.json` and `agent/validate_configs.py` (ON DISK; `python agent/validate_configs.py` exits 0 and the offline `push --dry-run` passes) + `agent/tests/` (T011, missing).
3. `prompts/system_v0.md`. ON DISK.
4. `docs/phase0/tts_script.md` (8 lines; equals `LINES` in `phase0/tts_samples.py`, test green). ON DISK; T013 adds the metadata table.
5. `docs/phase0/stt_sheet.md` + `docs/phase0/stt_results.csv` (10 utterances × 2 speakers + expected entities; result cells empty, test green). ON DISK; T014 removes the BOM.
6. `docs/phase0/voice_selection.md` (procedure, empty slots A–C, rating form, **no voice IDs**) + `phase0/find_voices.py`. ON DISK; T016 adds two columns and slots D–F.
7. `phase0/tts_samples.py` (`--dry-run` green offline) + `phase0/tts_score.py` and `phase0/stt_score.py` (both `--selftest` green) + `phase0/requirements.txt`. ON DISK; T002 removes its second pytest pin.
8. `docs/phase0/thresholds.json` (PROPOSED). Missing (T017); scorers read it after T021.
9. Rating form = `docs/phase0/voice_selection.md` §5. ON DISK; T018 adds two rules.
10. `docs/phase0/tts_ratings.csv` (header only, `blind_id` column). ON DISK.
11. `docs/phase0/catalog_traps.md` (draft trap items). ON DISK.
12. `phase0/test_phase0.py` (5 tests green as a plain script; pytest not installed on the laptop) + the T020 cases; `scripts/score_phase0.py` thin wrapper (T021, missing).
13. `scripts/check_phase0a.sh`. Missing (T022).
14. `.env.example` (ON DISK, names only) + `.gitignore` covering `phase0/samples/` (ON DISK, uncommitted).
15. `docs/STATUS.md` reading "Phase 0 gate: OPEN — waiting for API key and raters". Missing (T006).
16. `.python-version` + `requirements-dev.txt` (`pytest==9.1.1`). Missing (T002).

## Phase 0 (research) and Phase 1 (design) results

- **Research**: [research.md](research.md), with decisions R1–R18. Notable new finding R2.1:
  `agents push --dry-run` does not validate enums or unknown fields, so 0a adds a schema validator
  against the CLI's own spec (`agent/validate_configs.py`).
- **Design**:
  - [data-model.md](data-model.md);
  - [contracts/tools.openapi.yaml](contracts/tools.openapi.yaml), with 6 tools. The orchestrator
    asked for 5, but review amendment 3 adds `quote_order`, and the review wins;
  - [contracts/phase0-artifacts.md](contracts/phase0-artifacts.md);
  - [quickstart.md](quickstart.md).
- **Re-check after design**: Constitution Check still PASS for all nine principles, see the table
  above.

## Delivery phases and gates (from review section F)

| Phase | Hours | Gate summary (full checkpoint task in tasks.md) | Machine |
| --- | --- | --- | --- |
| 0a | 1.0 | schema validation + `push --dry-run` OK offline; pytest green on fake data; all 0a files exist; no voice id / score / minute; STATUS OPEN | Windows (today) |
| 0b | 1.5 + human | review G.2 TTS gate + G.3 STT gate + billing check + signed `decision.md` | Mac |
| 1 | 4.0 | pytest + golden tables, auth/size/schema/envelope paths, idempotency, p95 < 300 ms, tunnel 200/401, green on 2nd OS | Mac (laptop may start while 0b waits) |
| 2 | 4.0 | 3 consecutive voice orders + out-of-stock + E10/E11 calls; no config drift; minutes logged | Mac |
| 3 | 6.0 | ≥ 20 sim × k ≥ 3, judge agreement gate, 10 real calls redacted, human verdicts, no raw data in git | Mac (offline parts may start while 0b waits) |
| 4 | 3.5 | ≥ 5 CHANGELOG entries with scenario + metric; frozen hashes match; 0 critical grounding / unconfirmed orders | Mac |
| 5 | 3.0 | fresh-clone green on other OS; numbers match by script; 60–90 s video; gitleaks clean; banner; minutes vs budget | either |

## Complexity Tracking

No constitution violations, so nothing is listed.
