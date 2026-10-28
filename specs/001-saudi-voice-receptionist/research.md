# Research: Saudi Voice Receptionist "Sara"

**Feature**: `specs/001-saudi-voice-receptionist` | **Date**: 2026-10-27 | **Plan**: [plan.md](plan.md)

Every platform, SDK, CLI and package decision below has its source, the version pinned and the
date it was checked. Two kinds of evidence are used:

- **Leader spot-check**: verified on 2026-10-27 by the plan-review leader (`reviews/plan-review.md`,
  section A table). Re-used here, not re-fetched.
- **Planner check**: re-run by the planning agent on 2026-10-27 on the Windows laptop with
  `@elevenlabs/cli` 1.7.1 (no API key: offline `--help`, `--schema` and `--dry-run` only), `npm view`,
  `pip index versions` and the PyPI JSON API.

Anything not confirmed by either is marked **UNVERIFIED** and has a named check in `tasks.md`.

---

## R1. Voice runtime

- **Decision**: ElevenLabs Agents Platform (hosted ASR + LLM + TTS, webhook tools, `end_call`,
  agent tests, embeddable widget). Config as code via the CLI (R2).
- **Rationale**: every feature the plan needs exists today (leader spot-check, review section B).
  Phase 0b decides whether the runtime stays.
- **Alternatives**: Vapi + Azure `ar-SA` (kept only as the fallback, R10); self-hosted pipeline
  (out of scope: "no custom STT/TTS models").
- **Sources**: https://elevenlabs.io/docs/eleven-agents/customization/widget ,
  https://elevenlabs.io/docs/eleven-agents/customization/agent-testing ,
  https://elevenlabs.io/docs/eleven-agents/customization/tools/server-tools (leader, 2026-10-27).

## R2. Agent configuration as code: `@elevenlabs/cli`

- **Decision**: pin `"@elevenlabs/cli": "1.7.1"` as an exact devDependency in
  **`agent/package.json`** (where the 0a run placed it), commit `agent/package-lock.json`, run
  `npm ci` in `agent/`, and invoke as `npx elevenlabs …` from `agent/` on both machines.
  - Warning from the 0a run: without the local install, `npx elevenlabs` fetches the unrelated
    npm package `elevenlabs` (1.59.0, an old JS SDK).
  - The CLI walks up parent folders to find `.env`, so the repo-root `.env` works from `agent/`
    (0a run, checked with `voices accents get --dry-run`).
- **Layout**: `agent/` is the `agents init` layout (`agents.json`, `tools.json`, `tests.json`,
  `agent_configs/`, `tool_configs/`, `test_configs/`). Push order:
  `agents push && tools push && tests push`; tests attach via
  `platform_settings.testing.attached_tests` (leader).
- **Do not use** `agents add` (it uploads immediately; no `--skip-upload`) (leader).
- **Laptop** runs only `agents push --dry-run`; **Mac** is the single push owner and runs
  `agents pull` before every push (review M1).
- **API key**: the CLI reads `ELEVENLABS_API_KEY` (planner check: `npx elevenlabs --help` prints
  "`--api-key` … Env: ELEVENLABS_API_KEY"). `auth login --with-token` stores a key in the OS
  keyring instead; this project uses `.env` only (constitution V).
- **Version/date**: 1.7.1, published 2026-10-22 (`npm view @elevenlabs/cli`, planner re-check
  2026-10-27: still latest). Releases are frequent (1.4.0 → 1.7.1 in four weeks), so the pin is
  re-checked at the start of each phase and changed only by a deliberate commit.

### R2.1 Finding: `agents push --dry-run` does not validate field values (NEW)

- **Planner check (2026-10-27)**: a copy of the minimal config with `asr.provider: "bogus"`,
  `tts.model_id: "bogus_model"`, `agent.language: "xx"` and an unknown top-level field still printed
  `[DRY RUN] Would update agent`. Only malformed JSON failed ("Invalid JSON in configuration
  file").
- **Consequence**: the 0a gate check "`push --dry-run` validates the config" proves JSON
  well-formedness and that the CLI can read the project, nothing more.
- **Decision**: validate offline with `agent/validate_configs.py`, written by the 0a run.
  - It reads every enum and range from the pinned CLI's embedded spec (`agents create --spec`),
    so nothing is hard-coded and no schema dump has to be committed.
  - It requires `tts.voice_id` to be absent in 0a mode.
  - The CLI's `--schema` output (42,929 bytes; flat dot-path properties with `enum`/`type`, e.g.
    `conversation_config.asr.provider` enum `elevenlabs | scribe_realtime | scribe_v2_turbo`) is
    an equivalent source if `--spec` changes shape.
  - The 0a gate runs both checks: the validator and `push --dry-run`.
- **Alternative rejected**: wait for a key and let the API reject bad configs. That would leave 0a
  with no real validation.

## R3. Minimal Phase 0 agent settings

- **Decision**: build `agent/agent_configs/sara.json` from `prompts/system_v0.md` (an Arabic
  prompt: answer every turn only with «تمام») with:
  - `conversation_config.agent.language: "ar"` and a first message.
  - `prompt.llm`: keep the minimal template's default, `gemini-2.5-flash` (leader: `agents
    templates show minimal`). The LLM barely matters for a «تمام»-only agent; the real pick
    happens in Phase 2.
  - No tools.
  - `tts.model_id`, `tts.voice_id`, `tts.stability`, `tts.similarity_boost` and `tts.speed` are
    left at template values in 0a. The real values are filled in 0b, only from API results.
  - `asr.provider` is the default in the first STT pass and an alternative in the second.
  - Platform settings: `privacy.retention_days: 30`, `call_limits.daily_limit: 20`,
    `call_limits.agent_concurrency_limit: 2`.
- **Field existence**: confirmed in the schema dump (planner check). Exposed paths include
  `conversation_config.agent.first_message`, `conversation_config.agent.language`,
  `conversation_config.tts.{stability,similarity_boost,speed,text_normalisation_type}`,
  `conversation_config.asr.{provider,keywords}`,
  `conversation_config.turn.{turn_timeout,silence_end_call_timeout}`,
  `conversation_config.conversation.max_duration_seconds` and `conversation_config.language_presets`.
  At platform level they include `platform_settings.privacy.{retention_days,record_voice}`,
  `platform_settings.call_limits.{daily_limit,agent_concurrency_limit}`,
  `platform_settings.auth.{allowlist,require_origin_header}`,
  `platform_settings.guardrails.prompt_injection` and `platform_settings.testing.attached_tests`.
  An offline `push --dry-run` of a scratch copy with `language: "ar"`, an Arabic prompt,
  `asr.provider: scribe_realtime` and those platform settings printed `[DRY RUN] Would update agent`.
- **UNVERIFIED**: the `language` field description says "Language of the agent - used for ASR and
  TTS". Whether `ar` makes the ASR return English text for English speech (utterance 10) is what
  STT clips 10 × 2 measure.

## R4. Voice search (3 female Saudi/Gulf candidates)

- **Implementation (0a run)**: `phase0/find_voices.py` (the Python SDK `elevenlabs==2.74.1`,
  with method names introspected on that exact version by the 0a run, plus
  `python-dotenv==1.2.4`) and the procedure in `docs/phase0/voice_selection.md`. The CLI equivalents
  below were dry-run by the planner and stay as a fallback.
  - **Windows caveat** (0a run): `elevenlabs==2.74.1` contains a 184-char file path, which fails
    in the repo `.venv` under the 260-char limit. Run the `phase0/` helpers on the Mac, or use a
    short venv path.
- **Decision**: the documented procedure, run on the Mac with a key:
  1. `npx elevenlabs voices accents get --params '{"language":"ar"}'` → `GET /v1/voices/accents`.
     Pick the Saudi/Gulf accent value from the response. Never type one from memory.
  2. `npx elevenlabs voices get_shared --params '{"language":"ar","accent":"<value>","gender":"female","use_cases":"conversational","include_custom_rates":"false","page_size":100}'`
     → `GET /v1/shared-voices`. Planner dry-run confirmed the URL and query encoding.
  3. Shortlist 5 by preview and description; Ahmed listens; keep 3.
  4. If needed, add each to "My Voices" with
     `npx elevenlabs voices share --params '{"public_user_id":"…","voice_id":"…","new_name":"…"}'`
     → `POST /v1/voices/add/{public_user_id}/{voice_id}` (planner dry-run).
  5. Record IDs only by copying from the API output into `docs/phase0/voice_selection.md` §2.
- **Params confirmed** (planner, `voices get_shared --schema`): `accent`, `gender`, `language`,
  `locale`, `use_cases`, `include_custom_rates` (string), `page_size` (≤ 100, default 30),
  `search`, `sort`, `category`.
- **UNVERIFIED** (settle in 0b):
  - the valid accent strings;
  - whether Starter keys can use library voices;
  - whether a library voice must be added to My Voices before an agent or TTS call can use it;
  - whether `include_custom_rates` takes `"false"` or another literal.

## R5. TTS models compared in Phase 0b

- **Decision**: `eleven_v4_turbo` vs `eleven_flash_v2_5`. `eleven_v3_conversational` only in the
  retry. `eleven_multilingual_v2` is not compared on the primary path. `eleven_turbo_v2_5` is
  dropped (deprecated).
- **Source**: https://elevenlabs.io/docs/overview/models (leader, 2026-10-27): v4 Turbo lists
  Arabic, ~100 ms, recommended for Agents; Flash v2.5 Arabic ~75 ms; v3 Conversational ~280 ms;
  Turbo v2.5 deprecated. Agent schema `tts.model_id` enum includes `eleven_v4_turbo`,
  `eleven_flash_v2_5`, `eleven_v3_conversational`, `eleven_multilingual_v2` and others (planner
  check).
- **Clip synthesis**: implemented by `phase0/tts_samples.py`, which uses the SDK
  `text_to_speech.convert`, `--dry-run` offline, `--blind --seed`, and writes to git-ignored
  `phase0/samples/`; `.gitignore` must add that folder (tasks T003). CLI equivalent: `npx elevenlabs text-to-speech convert --params '{"voice_id":…,"model_id":…,"text":…,"voice_settings":{…}}'`
  → `POST /v1/text-to-speech/{voice_id}` (planner dry-run). Body fields confirmed by `--schema`:
  `text`, `model_id`, `language_code`, `voice_settings.{stability,similarity_boost,style,speed,use_speaker_boost}`,
  `apply_text_normalization`, `seed`, `output_format` (query).
- **Settings parity rule**: clips use the same `stability`, `similarity_boost` and `speed` values
  that `sara.json` carries under `tts.*`. The agent schema exposes only those three, so `style` and
  `use_speaker_boost` stay at the voice's stored defaults in both. A fixed `seed` per clip makes
  re-synthesis reproducible (best effort, per the API description).
- **UNVERIFIED** (settle in 0b, before synthesizing):
  - whether `eleven_v4_turbo` is accepted by the standalone TTS endpoint and not only inside
    Agents. If it is rejected, record that line pair by having the minimal agent speak the line in
    a test conversation and downloading it via `agents conversations audio`;
  - the TTS character quota on Starter (48 clips × ~60 characters ≈ 3k characters);
  - whether the agent runtime applies the voice's stored `style` exactly as the standalone API
    does. Mitigation: before signing, Ahmed hears the winning triple inside the live minimal agent
    during the STT session and confirms it matches the rated clips.

## R6. STT test method

- **Decision**: speak the 10 utterances (× 2 speakers = 20 clips) live into the minimal agent.
  Pass 1 uses the default `asr.provider`; pass 2 uses one other value from
  {`elevenlabs`, `scribe_realtime`, `scribe_v2_turbo`} (schema enum, planner check). Read the
  realtime transcript via `npx elevenlabs agents conversations get --params '{"conversation_id":"…"}'`
  → `GET /v1/convai/conversations/{conversation_id}` (planner dry-run). The response has a
  `transcript` field (from `--schema`). Score entities, not WER, per `contracts/phase0-artifacts.md`.
- **Rationale**: batch Scribe measures a different model path from the realtime ASR callers will
  hit (review M3). Arabic is only in the "Good (>10% to ≤20% WER)" tier with no dialect claims
  (https://elevenlabs.io/docs/capabilities/speech-to-text, leader).
- **Retry**: add catalog product names via `conversation_config.asr.keywords` (schema field
  confirmed) and switch the provider.
- **Implementation (0a run)**:
  - `docs/phase0/stt_sheet.md` is the human sheet (utterances, entities, printable cards, run
    order) and `docs/phase0/stt_results.csv` holds the 20 result rows (the review F names).
  - `phase0/stt_score.py` scores it: `--fetch` reads `transcript[].message` where `role == "user"`
    from the conversations API, and `--selftest` runs offline.
  - **Leader re-check (2026-10-27, https://elevenlabs.io/docs/api-reference/conversations/get)**:
    `GET /v1/convai/conversations/{conversation_id}` returns `transcript[]` items with required
    `role` ∈ {`user`, `agent`}, nullable `message` and `time_in_call_secs`; `metadata` carries
    `call_duration_secs` and `start_time_unix_secs`. So `--fetch` reads the right fields, and
    `call_duration_secs` can feed the minutes log in `docs/STATUS.md` alongside the subscription
    counter.
  - **Accepted deviation from review G.1** (leader): utterance 5 gained a final «سبعة»; the
    review's wording had 9 digits and could not equal its own target 0557834567.
- **Privacy**: the sheet has a `transcript_heard` column. The utterances are scripted fake data,
  but constitution IV keeps raw transcripts out of git. The default is to keep filled transcripts
  in git-ignored `phase0/recordings/` and commit the verdict columns only. Ahmed decides (tasks
  T038).
- **Minutes**: ~40 short conversations (2 passes × 20). Estimate 10–15 call minutes inside the
  15-minute spike budget. This is an estimate, not a measured number; actual minutes come from the
  usage counter.

## R7. Agent tests and billing

- **Decision**: in 0b run exactly one Simulation test (`npx elevenlabs agents test <agent>`;
  planner `--help` check: argument is "agent ID or name") and read the subscription counter
  before and after (`npx elevenlabs user subscription get` → `GET /v1/user/subscription`, planner
  dry-run).
- **UNVERIFIED**: whether tests bill call minutes (the testing docs don't say; leader).
  `simulate_conversation` is `[DEPRECATED]` (planner `agents --help`), so it is not used.

## R8. Pricing and plan

- **Decision**: Ahmed buys **Starter** before 0b. Leader check of https://elevenlabs.io/pricing/agents
  on 2026-10-27: $6/mo with 75 min ($1 first month); Creator $22 with 275 min; overage
  $0.080/min; burst $0.160; LLM billed by usage. Budget ~110 call-minutes for the whole build
  (review M9). Re-check the page on the Mac before buying; prices are not copied anywhere else.
- **Who**: Ahmed (payment). Claude never enters payment details.

## R9. Language switching (Phase 2)

- **Decision**: `language_presets` with `en` plus the
  `agent.prompt.built_in_tools.language_detection` system tool, described as switching only on
  English-only speech (2 consecutive English-only turns).
- **Source**: https://elevenlabs.io/docs/eleven-agents/customization/tools/system-tools/language-detection
  (leader).
- **UNVERIFIED**: whether ASR switches as well as "voice and responses". Verified by a real call in
  the Phase 2 gate.

## R10. Fallback runtime

- **Decision**: split trigger (review M8).
  - **STT NO-GO**: Vapi with the Azure `ar-SA` transcriber, keeping ElevenLabs `eleven_flash_v2_5`
    TTS.
  - **TTS NO-GO**: re-rate Azure `ar-SA-ZariyahNeural` (female, matches سارة) with the same 8
    lines and raters.
  - **Both fail**: stop and re-scope with Ahmed.
  - Cost: +3–4 h from contingency.
- **Sources**: https://docs.vapi.ai/providers/transcriber/azure ,
  https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support (leader).
- **Not planned in tasks** beyond the trigger checkpoint. Adapter tasks are written only if the
  trigger fires.

## R11. Tools backend stack (Phase 1)

| Package | Pin | Latest on PyPI / release date (planner, 2026-10-27) | Note |
| --- | --- | --- | --- |
| Python | 3.12 (`.python-version`) | laptop has 3.12.10 | `python` on Windows, `python3` on macOS, via `scripts/py.sh` |
| fastapi | **decide at Phase 1 start**: newest release ≥ 14 days old | 0.162.0 (2026-10-23); 0.143.0 (2026-10-08) is the newest ≥ 14 days old today. Both dates re-confirmed by the leader from the PyPI per-version JSON on 2026-10-27 | FastAPI shipped ~20 releases between 2026-10-08 and 10-23; the review's "0.162.0 or 0.161.x" both fail the 2-week rule today |
| pydantic | 2.14.1 | 2026-10-11 | |
| rapidfuzz | 3.14.6 | 2026-08-30 | matcher pipeline re-run by the leader on this version |
| uvicorn | 0.54.0 | 2026-09-25 | |
| pytest | 9.1.1 | 2026-06-19 (leader re-check of the PyPI JSON, 2026-10-27; requires Python ≥ 3.10) | used in 0a for `phase0/test_phase0.py`. **Conflict found by the leader**: `phase0/requirements.txt` also pins `pytest==8.4.2` (2025-09-04). T002 removes that line so one pin remains |
| httpx | 0.28.1 | 2024-12-06 | FastAPI TestClient |
| PyYAML | 6.0.3 | 2025-09-25 | scenarios.yaml, judge_config.yaml |
| jsonschema | 4.26.0 | 2026-01-07 | contract tests against `contracts/tools.openapi.yaml` schemas |
| elevenlabs (Python SDK) | 2.74.1 (`phase0/requirements.txt`, with `python-dotenv==1.2.4`) | 2026-10-20 (0a run) | used by the 0b helpers `phase0/*.py`; install on the Mac (Windows long-path caveat, R4); the CLI stays the agent-config tool |

- **0a dependency set** (`requirements-dev.txt`): `pytest==9.1.1` only. `phase0/tts_score.py`,
  `phase0/stt_score.py`, `phase0/test_phase0.py` and `agent/validate_configs.py` use the stdlib
  (csv, json, random, urllib), so 0a installs fast on both OSes; `phase0/test_phase0.py` also runs
  without pytest as a plain script.
- **Storage**: SQLite (stdlib `sqlite3`), money as integer halalas, reset per eval run.
- **Arabic matching**: review B4 pipeline (normalize → strip clitics → unify letters → digits →
  punctuation; filler-word removal; aliases as data; `WRatio` or
  `max(token_sort_ratio, 0.9·partial_ratio)` for scoring; `token_set_ratio` only to detect
  ambiguity). The leader confirmed the §7 pipeline fails its own test words on 3.14.6.

- **Phase 1 decision (2026-10-28, Mac):** newest release ≥ 14 days old on PyPI that day:
  fastapi **0.143.1** (2026-10-14), pydantic 2.14.1, uvicorn 0.54.0, rapidfuzz 3.14.6, httpx 0.28.1,
  PyYAML 6.0.3, jsonschema 4.26.0, pytest 9.1.1, plus **tzdata 2026.5** so `zoneinfo` finds
  Asia/Riyadh on Windows. All in `requirements.txt`. Matcher as built: exact alias phrase first
  (longest key wins, ties → clarify), else `max(token_sort_ratio, 0.9·partial_ratio)` + 6 points
  when the head noun matches (stops «صحون» matching «صابون صحون»); ≥ 82 is a match, runner-up
  within 5 points → clarify with 2 options. 36 golden query pairs in `backend/tests/test_arabic.py`.
  cloudflared on the Mac: 2026.7.1. gitleaks pinned 8.30.1 (2026-03-21) in
  `scripts/install_hooks.sh`, not yet installed.

## R12. Webhook tool binding (Phase 2)

- **Decision**: tool configs set `request_headers.X-Tool-Secret = {"secret_id": "<ElevenLabs secret id>"}`
  and bind `conversation_id` with a body property `{"type":"string","dynamic_variable":"system__conversation_id"}`
  (and time from `system__time`).
- **Evidence** (planner, `tools_schema.json` from `agents tools create --schema`):
  - `api_schema` has `url`, `method`, `request_headers`, `request_body_schema`, `path_params_schema`,
    `query_params_schema`, `content_type` and `response_body_schema`;
  - a `request_headers` value can be a string, `{secret_id}`, `{variable_name}` or `{env_var_label}`;
  - a body property can carry exactly one of `description`, `dynamic_variable`, `constant_value`,
    `is_system_provided` or `is_omitted`;
  - `response_timeout_secs` is an integer from 5 to 300 (default 20), and `pre_tool_speech`,
    `force_pre_tool_speech` and `tool_call_sound` exist.
  - Dynamic variables `system__conversation_id` and `system__time`:
    https://elevenlabs.io/docs/eleven-agents/customization/personalization/dynamic-variables
    (leader).
- **UNVERIFIED** until Phase 2: end-to-end behaviour of the binding on a live call.

## R13. Public tunnel (Phase 1–2)

- **Decision**: `cloudflared tunnel --url http://localhost:8000` (quick tunnel; the hostname
  changes each run, no uptime guarantee, 200 in-flight requests). `scripts/tunnel.sh` captures the
  hostname into `.env` as `TOOLS_BASE_URL` and re-renders `tool_configs/*.json` from `*.json.tmpl`.
  A named tunnel is used only if Ahmed owns a Cloudflare domain.
- **Source**: https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/
  (leader).
- **Install**: macOS uses `brew install cloudflared` or the release binary from
  https://github.com/cloudflare/cloudflared/releases. Windows uses
  `winget install Cloudflare.cloudflared`. The cloudflared version is pinned in the README when
  installed (Phase 1). **UNVERIFIED** today: not installed on either machine yet.

## R14. Widget and demo page (Phase 2)

- **Decision**: `<elevenlabs-convai>` from `@elevenlabs/convai-widget-embed`, pinned to a version
  ≥ 14 days old at build time.
  - Candidate today: **0.19.1 (2026-10-13)**. Latest is 0.21.5 (2026-10-26), per a planner
    `npm view` on 2026-10-27.
  - Hosting: GitHub Pages, served locally with `python -m http.server 8000`.
  - Auth: `auth.allowlist` holds the Pages host and `localhost:8000` (≤ 10 hosts, exact match).
    Signed URLs expire after 15 min and are not combined with the allowlist.
- **Sources**: https://elevenlabs.io/docs/eleven-agents/customization/widget ,
  https://elevenlabs.io/docs/eleven-agents/customization/authentication (leader).

## R15. Privacy and retention

- **Decision**:
  - `platform_settings.privacy.retention_days: 30`;
  - git-ignore raw results, real calls and all audio;
  - run `redact.py` before committing excerpts;
  - add a gitleaks pre-commit scan, pinned version chosen in Phase 1 (**UNVERIFIED** today:
    gitleaks not installed on either machine).
- **Source**: https://elevenlabs.io/docs/eleven-agents/customization/privacy/retention (leader:
  default 2 years; N / -1 / 0).

## R16. LLM judge (Phase 3)

- **Decision rule, model deferred**: the judge comes from a different model family than the agent
  LLM. It is called through that provider's SDK directly, or LiteLLM pinned with
  `--require-hashes`. Config is frozen in `evals/judge_config.yaml` (model id, prompt hash,
  temperature 0).
- **NEEDS DECISION in Phase 3**: which judge provider key Ahmed has. No model id is written until
  it is checked against that provider's model list.
- **Judge gate**: agreement ≥ 0.9 and κ ≥ 0.7 against ~30 gold labels, otherwise that dimension is
  scored by a human.

## R17. Cross-platform scripting

- **Decision**: every task is a bash script in `scripts/` (Git Bash on Windows, bash/zsh on macOS)
  calling Python entry points. There are no `make`- or `brew`-only paths. `scripts/py.sh` picks
  `python` or `python3`. The venv activation path differs (`.venv/Scripts/activate` vs
  `.venv/bin/activate`) and the scripts handle both. `.gitattributes` already forces LF
  (`* text=auto eol=lf`), so scripts run on both OSes.

## R18. Phase 0 asset locations

Observed on disk by the leader analysis, 2026-10-27 (corrects the planner's earlier reading, which
named `phase0/stt_test_sheet.*` and `phase0/voice_candidates.md`; those files never existed).

- **Decision**: the 0a run used the review section F names. Follow them.
  - **Tooling** in `phase0/`: `find_voices.py`, `tts_samples.py` (SDK; Mac), `tts_score.py`,
    `stt_score.py`, `test_phase0.py` (stdlib) and `requirements.txt`.
  - **Sheets and gate-named documents** in `docs/phase0/`: `tts_script.md`, `stt_sheet.md`,
    `stt_results.csv`, `voice_selection.md`, `tts_ratings.csv`, `catalog_traps.md`; later
    `thresholds.json` (T017), `clip_key.csv` and `decision.md` (0b).
  - **Clips** in `phase0/samples/` (git-ignored by the 0a run's `.gitignore` edit, uncommitted).
  - **Raw transcripts** in `phase0/recordings/` (git-ignored).
  - **Agents** in `agent/agent_configs/`: `sara.json` and `sara_stt_probe.json`, plus
    `agent/validate_configs.py`.
  - **Prompt**: `prompts/system_v0.md`.
  - **Gate scorers**: `phase0/tts_score.py` and `phase0/stt_score.py`; `scripts/score_phase0.py`
    becomes a thin wrapper (T021) so the review's path exists.

## R19. Leader spot-check during `/speckit-analyze` (2026-10-27)

Re-verified, not copied from the review:

| Claim | Result | Evidence |
| --- | --- | --- |
| `eleven_v4_turbo` lists Arabic, ~100 ms, recommended for Agents; `eleven_flash_v2_5` Arabic ~75 ms; `eleven_v3_conversational` ~280 ms; `eleven_turbo_v2_5` deprecated | Confirmed | https://elevenlabs.io/docs/overview/models fetched 2026-10-27 |
| Conversations API `transcript[].role` ∈ {user, agent}, `message`, `metadata.call_duration_secs` | Confirmed | https://elevenlabs.io/docs/api-reference/conversations/get fetched 2026-10-27 |
| CLI 1.7.1 schema enums: `asr.provider` = elevenlabs / scribe_realtime / scribe_v2_turbo; `tts.model_id` includes eleven_v4_turbo, eleven_flash_v2_5, eleven_v3_conversational, eleven_turbo_v2_5; `text_normalisation_type` = system_prompt / elevenlabs | Confirmed | `npx elevenlabs agents create --schema` from `agent/` (offline) |
| `npm view @elevenlabs/cli version` = 1.7.1 | Confirmed | run 2026-10-27 |
| pytest 9.1.1 uploaded 2026-06-19; 8.4.2 uploaded 2025-09-04 | Confirmed | PyPI per-version JSON |
| fastapi 0.162.0 uploaded 2026-10-23; 0.143.0 uploaded 2026-10-08 | Confirmed | PyPI per-version JSON |
| `agent/validate_configs.py` exits 0; offline `agents push --dry-run` passes; `tts_samples.py --dry-run`, both `--selftest`s and `python phase0/test_phase0.py` green | Confirmed | run on the laptop 2026-10-27 |
| `agent/package-lock.json` holds darwin-arm64, darwin-x64, linux-arm64, linux-x64, win32-x64 binaries | Confirmed | grep of the lockfile |

Still UNVERIFIED (unchanged): everything listed in R3, R4, R5, R7, R9, R12, R13, R15.

## Open items (carried, not blocking 0a)

| Item | Owner | When |
| --- | --- | --- |
| Confirm Phase 0 thresholds (spec FR-008) | Ahmed | before 0b |
| Fix spoken register of TTS lines 2–4 and the golden table (FR-053) | Ahmed | before 0b synthesis |
| Real vs fictional store name (FR-073) | Ahmed | before Phase 2 (affects the greeting line; 0b clips use مقاضينا per G.1 unless Ahmed says otherwise) |
| All UNVERIFIED rows above | Claude on Mac with key | 0b (R4, R5, R7), Phase 1 (R11 fastapi pin, R13, R15), Phase 2 (R9, R12), Phase 3 (R16) |
