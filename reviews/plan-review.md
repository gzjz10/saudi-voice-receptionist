# Plan review — Saudi Voice Receptionist, Technical Spec v1.0

Leader: Fable 5.1. Reviewers: three Opus lenses (`reviews/raw/platform.md`, `reviews/raw/delivery.md`, `reviews/raw/quality.md`). Date: 2026-10-27. Owner: Ahmed (gzjz10).

This file is the consolidated review. Where it conflicts with `plan.md`, the decisions in section E ("Plan amendments") win (per `CLAUDE.md`). `plan.md` itself is not edited.

---

## A. Is this plan perfect?

**No.** It is a strong, buildable spec with one hole that makes it un-executable as written: the gates it depends on (§11) and the architecture diagram (§3) never exported, so no phase, Phase 0 included, has an acceptance check. Around that hole there are three design defects that would fail the plan's own critical metric (read-back total cannot be grounded; the Arabic matcher fails its own test words; real-call transcripts would land in the public repo) and a dozen platform details that are stale or unspecified.

**Overall verdict: `good_with_fixes`.** Adopt sections E–G below and the plan is ready to build. Nothing requires a re-architecture.

Reviewer verdicts: platform `ready_with_fixes`, delivery `not_ready` (because the gates are missing), quality `ready_with_fixes`. The leader agrees with all three once the gates in section F/G are adopted, which turns delivery's `not_ready` into `ready_with_fixes`.

### How claims were checked (leader spot-check, 2026-10-27)

| Claim | Result | Evidence |
| --- | --- | --- |
| CLI latest is `@elevenlabs/cli` 1.7.1 (2026-10-22); rapid releases | **Confirmed** | `npm view @elevenlabs/cli time`: 1.4.0 09-25, 1.5.0 10-13, 1.6.0 10-16, 1.7.0 10-20, 1.7.1 10-22 |
| `agents add --dry-run` still calls the API and returns 401 without a key | **Confirmed** | Ran 1.7.1 in scratch dir without `ELEVENLABS_API_KEY`: `"code": 401, "unauthorized"` |
| `agents init` layout (agents.json, tools.json, tests.json, agent_configs/, tool_configs/, test_configs/, .env.example, .gitignore); push order `agents push && tools push && tests push`; tests attach via `platform_settings.testing.attached_tests` | **Confirmed** | `npx elevenlabs agents init --yes` output |
| `agents push --dry-run` works offline | **Confirmed** | ran without key: "Pushing 0 agent(s)" |
| `agents add` has no `--skip-upload`; `simulate_conversation` is `[DEPRECATED]` | **Confirmed** | `agents add --help`, `agents --help` |
| Minimal template defaults: `eleven_v4_turbo`, `gemini-2.5-flash`, `language: "en"` | **Confirmed** | `agents templates show minimal` |
| Schema fields exist: `tts.model_id` enum (incl. `eleven_v4_turbo`, `eleven_flash_v2_5`, `eleven_v3_conversational`, `eleven_turbo_v2_5`), `asr.provider` ∈ {elevenlabs, scribe_realtime, scribe_v2_turbo}, `asr.keywords`, `language_presets`, `turn.turn_timeout`, `turn.silence_end_call_timeout`, `conversation.max_duration_seconds`, `platform_settings.auth.allowlist / enable_auth / require_origin_header`, `call_limits.daily_limit / agent_concurrency_limit`, `privacy.retention_days / record_voice`, `guardrails.prompt_injection`, `tts.text_normalisation_type` | **Confirmed** | `agents create --schema` (42.9 KB) grep |
| Tool schema: `request_headers` with `secret_id`, `response_timeout_secs`, `pre_tool_speech`, `force_pre_tool_speech`, `tool_call_sound`, `dynamic_variables` | **Confirmed** | `agents tools create --schema` |
| Widget requires public agent with auth disabled; unpkg script unversioned; widget-embed at 0.21.5 | **Confirmed** | https://elevenlabs.io/docs/eleven-agents/customization/widget ; `npm view` |
| Pricing: Free 15 min, Starter $6/75 min ($1 first month), Creator $22/275 min ($11 first month), overage $0.080/min, burst $0.160, LLM billed by usage, Twilio bills directly | **Confirmed** | https://elevenlabs.io/pricing/agents |
| Agent tests: Simulation / Next Reply / Tool Call, `repeat_count` 2–20, mocking none/all/selected, `elevenlabs agents test <agent>`; billing not stated | **Confirmed** (billing **UNVERIFIED**) | https://elevenlabs.io/docs/eleven-agents/customization/agent-testing |
| `language_detection` needs languages defined first; switches "voice and responses"; config under `agent.prompt.built_in_tools.language_detection`; `only_at_conversation_start` | **Confirmed**; whether ASR also switches **UNVERIFIED** | https://elevenlabs.io/docs/eleven-agents/customization/tools/system-tools/language-detection |
| Retention default 2 years; `retention_days` N / -1 / 0 | **Confirmed** | https://elevenlabs.io/docs/eleven-agents/customization/privacy/retention |
| Quick tunnel: hostname changes each time, no uptime guarantee, 200 in-flight requests, `cloudflared tunnel --url http://localhost:8080` | **Confirmed** | https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/ |
| TTS models: `eleven_v4_turbo` lists Arabic, ~100 ms, recommended for Agents; `eleven_flash_v2_5` Arabic ~75 ms; `eleven_multilingual_v2` "Arabic (Saudi Arabia, UAE)", higher latency; `eleven_v3_conversational` ~280 ms; `eleven_turbo_v2_5` deprecated | **Confirmed** — resolves delivery's "v4 Turbo Arabic UNVERIFIED" | https://elevenlabs.io/docs/overview/models |
| Dynamic variables `system__conversation_id`, `system__time`, usable in tool parameters and headers; `secret__` header-only | **Confirmed** | https://elevenlabs.io/docs/eleven-agents/customization/personalization/dynamic-variables |
| Auth: allowlist ≤ 10 hostnames, exact match, ports allowed; signed URLs expire 15 min; do not combine | **Confirmed** | https://elevenlabs.io/docs/eleven-agents/customization/authentication |
| STT: Arabic in "Good (>10% to ≤20% WER)" tier, no dialect info | **Confirmed** | https://elevenlabs.io/docs/capabilities/speech-to-text |
| Server tools: header type **Secret**; page does not mention timeout/retry | **Confirmed** | https://elevenlabs.io/docs/eleven-agents/customization/tools/server-tools |
| Vapi Azure transcriber lists `ar-SA`; Azure STT `ar-SA`; Azure TTS `ar-SA-ZariyahNeural` (F), `ar-SA-HamedNeural` (M) | **Confirmed** | https://docs.vapi.ai/providers/transcriber/azure ; https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support |
| rapidfuzz 3.14.6 on the §7 pipeline: صحن/صحون زجاج = 50, كوب/أكواب ورق = 50, كاسات/أكواب زجاج = 40, والصحون = 62.5, بالصحون = 62.5, any shared token = 100 (ties), آلة → ه | **Confirmed** by re-running the exact pipeline | local run, `rapidfuzz==3.14.6` |
| PyPI latest: fastapi 0.162.0, pydantic 2.14.1, rapidfuzz 3.14.6, uvicorn 0.54.0, pytest 9.1.1, litellm 1.106.4, elevenlabs 2.74.1, httpx 0.28.1 | **Confirmed** | `pip index versions` |

**Dropped or downgraded reviewer claims**

- Quality §10: "Simulation evaluator default model is claude-sonnet-4-6" — the testing page does not name a model. **Dropped**; treat the platform evaluator as a separate, unnamed judge and do not mix it with `judge.py` numbers.
- Platform §6 / quality §15: `language_detection` also switches ASR — the page says "voice and responses" only. **UNVERIFIED**; E10 must be verified by a real voice call in Phase 2.
- Platform §17: LiteLLM PyPI compromise in March 2026 — not re-verified by the leader. The recommendation (call the judge provider's SDK directly, or pin with hashes) stands on its own merits regardless.
- Delivery §13: Lucidchart free-tier limits — third-party only, **UNVERIFIED**; the Mermaid decision below does not depend on it.
- Whether Simulation tests consume call minutes; whether Free-tier keys can use library voices; valid `voices accents get` values; whether library voices must be added to "My Voices" first — all **UNVERIFIED**, to be settled on the Mac in Phase 0b with a key.

---

## B. What is strong

- The architecture is right: hosted voice loop, our FastAPI backend as the only source of truth, QA loop reading every call. All named platform features exist today (widget, webhook tools with secret headers, `end_call`, Simulation/Tool Call tests with `repeat_count`, conversation transcript API, CLI config-as-code).
- The scope is honest and small: 5 intents, 30-item catalog, 20 scenarios, pickup/delivery, fake data, explicit non-goals.
- The spoken-field design (`*_spoken_ar` from the backend, never raw digits to TTS) is the correct way to make Arabic numbers survive TTS.
- The catalog is built as a test fixture (out-of-stock items, near-duplicate pairs, shelf-vs-common names), which is exactly what a QA-first portfolio project needs.
- The rubric separates critical / major / minor and puts humans above the LLM judge.
- Risk register (§12) already names the right top risk (dialect quality) and puts it first.
- Python stack (FastAPI, Pydantic v2, SQLite, rapidfuzz, pytest) is sound and cross-platform.
- The Sarj mapping (§13) keeps every artifact tied to a job requirement.

---

## C. MUST-FIX (prioritized)

### Blockers

**B1. No acceptance gate exists for any phase (§11 and §3 lost in export).** All three reviewers.
Fix: adopt section F (phase table) and section G (Phase 0 gate) as the new §11. Copy them into `specs/` via Spec Kit and `docs/STATUS.md`. Every gate below is pass/fail with a named checker.

**B2. Phase 0 cannot be executed on this laptop and must not be faked.** Platform §1, delivery §2.
Fix: split Phase 0 into **0a (offline, today)** and **0b (needs API key + raters, on the Mac)**. `docs/STATUS.md` reads "Phase 0 gate: OPEN — waiting for API key and raters" until 0b is scored. Details in section G.

**B3. The read-back total cannot be grounded (§7/§8 step 6).** Quality §2.
`total_spoken_ar` only comes from `create_order`, which may run only after the read-back, so the LLM would compute totals itself and violate rule 1.
Fix: add a side-effect-free `quote_order` tool (6 tools total) returning `subtotal_sar`, `delivery_fee_sar`, `total_sar`, `total_spoken_ar`, `lines[]` (with `qty_spoken_ar`, `line_total_sar`), `below_minimum`, `quote_id`. `create_order` takes `quote_id` and is idempotent on (`conversation_id`, `quote_id`). The read-back may only speak values from `quote_order`.

**B4. The §7 Arabic matcher fails the plan's own test words.** Quality §3, re-run and confirmed by the leader.
Fix: (1) normalize in this order: strip tashkeel/tatweel → strip clitics on the original text (`^(و|ف)?(ب|ل|ك)?ال`, `^لل`) with minimum stem 3 → unify letters (أإآٱ→ا, ة→ه, ى→ي, ؤ→و, ئ→ي) → convert Arabic-Indic digits → strip punctuation; (2) remove filler words (بكم، كم، عندكم، فيه، أبي، ابغى، ممكن); (3) broken plurals and dialect words are **aliases (data)**, not fuzz, with a lint test that no alias is shared by two products or is a bare category word; (4) score with `WRatio` or `max(token_sort_ratio, 0.9·partial_ratio)`, use `token_set_ratio` only to detect ambiguity, return ≤ 2 options when `needs_clarification`; (5) golden table ≥ 30 query→id pairs in `test_arabic.py`; (6) pin `rapidfuzz==3.14.6`; (7) normalization applies only to an internal `match_key`, never to `name_ar` or spoken fields.

**B5. Real-call transcripts, family data and possibly the tool secret would be committed to the public repo.** Quality §4.
Fix: git-ignore `evals/results/**/raw/` and `evals/results/**/real_calls/`; commit only `summary.csv`, verdict JSON and `redact.py`-processed excerpts (mask `05\d{8}`, `9665\d{8}`, digit runs ≥ 7, Arabic-Indic digits, caller name). Set `platform_settings.privacy.retention_days: 30`. Store `TOOL_SECRET` only as an ElevenLabs Secret referenced by `secret_id` in `request_headers`, never literal in `tool_configs/`. Add a gitleaks (or equivalent) pre-commit scan. Written consent (short Arabic line) from each family caller.

### Majors

**M1. CLI unpinned and under-described.** Platform §2–§3.
Fix: `package.json` devDependency `"@elevenlabs/cli": "1.7.1"`, invoked as `npx elevenlabs` on both machines. Commit the `agents init` layout under `agent/`. Do **not** use `agents add` (it uploads immediately); hand-write `agent_configs/sara.json` generated from `prompts/system_v*.md` by `scripts/build_agent_config.py`, validate with `agents push --dry-run`, push from the Mac. Push order: `agents push && tools push && tests push`. Attach tests via `platform_settings.testing.attached_tests`. Mac is the single push owner; always `agents pull` before `push`.

**M2. TTS model never named; agent default differs from what would be rated.** Platform §4, delivery §12.
Fix: Phase 0 compares `eleven_v4_turbo` and `eleven_flash_v2_5` on 3 female voices (v3_conversational optional). The agent runs the exact winning (voice, model, settings) triple; any later change re-opens the TTS gate. Drop `eleven_turbo_v2_5` (deprecated).

**M3. ASR treated as a black box.** Platform §5.
Fix: `agent.language: "ar"`; Phase 0b tests ≥ 2 of `asr.provider` ∈ {elevenlabs, scribe_realtime, scribe_v2_turbo} on the same 20 clips; put catalog product names in `asr.keywords`; results read from the agent's own conversation transcripts (realtime ASR), not batch Scribe.

**M4. English switching (rule 9 / E10) needs platform config.** Platform §6.
Fix: add `en` to `language_presets`, enable `built_in_tools.language_detection` with a description: switch only on English-only speech; stay in Arabic for mixed Arabic–English (E11). Define the trigger as 2 consecutive English-only caller turns. Whether ASR switches with it is UNVERIFIED → verify in Phase 2 by voice.

**M5. E7/E8/E9 cannot run in text simulation; `simulate-conversation` is deprecated.** Platform §7, quality §8, delivery §10.
Fix: tag every scenario `mode: sim | voice | both`. E7, E8, E9 and dialect naturalness are `voice`-only (real call cards). Use Simulation and Tool Call tests with `repeat_count`. Put `turn.turn_timeout` and `turn.silence_end_call_timeout` in the agent config. Enable `end_call`.

**M6. Widget exposes a public agent in a public repo.** Platform §8, quality §12.
Fix: host `demo/` on GitHub Pages; `auth.allowlist` = Pages host + `localhost:8000`; `require_origin_header: true`; `call_limits.daily_limit` (e.g. 20), `agent_concurrency_limit: 2`; `conversation.max_duration_seconds: 240`; pin `@elevenlabs/convai-widget-embed` to a version ≥ 2 weeks old at build time (0.19.1 from 2026-10-13 qualifies today); serve locally with `python -m http.server 8000`, never `file://`. Disable the agent between demo sessions.

**M7. Quick tunnel hostname changes every run; webhook URLs live on ElevenLabs.** Platform §9, delivery §8.
Fix: `scripts/tunnel.sh` starts `cloudflared tunnel --url http://localhost:8000`, captures the hostname into `.env` as `TOOLS_BASE_URL`, renders `tool_configs/*.json` from `tool_configs/*.json.tmpl`, then runs `npx elevenlabs tools push`. Named tunnel only if Ahmed has a Cloudflare domain (his call). Windows: `winget install Cloudflare.cloudflared`. Keep the Mac awake during call sessions.

**M8. Fallback claim "eval suite unchanged" is false and does not fix a TTS failure.** Platform §11, delivery §3.
Fix: split the trigger — STT no-go → Vapi + Azure `ar-SA` STT (keep ElevenLabs `eleven_flash_v2_5` TTS, not multilingual_v2); TTS no-go → re-rate Azure `ar-SA-ZariyahNeural` (female, matches سارة) with the same Phase 0 protocol; both fail → stop and re-scope. Fallback cost: +3–4 h (runtime adapter, transcript fetcher, simulator, widget), paid from the pre-approved cut list (section F).

**M9. Call-minute budget is ~2× short and no plan is chosen.** Platform §12, delivery §4, quality §12.
Fix: re-baseline to **~110 minutes** (spike 15, dev 30, real calls 45, demo 15, slack 5). Ahmed buys **Starter** ($6/mo, $1 first month, 75 min) before Phase 0b; the ~35-min overage is ≈ $2.80 at $0.08/min. Creator ($22, 275 min) only if he wants headroom. Run one Simulation test in Phase 0b and read the usage counter to learn whether tests bill minutes. Log minutes in `docs/STATUS.md` after every phase.

**M10. 20 hours has no buffer and omits ~5 h of human time; deliverables D6, `flow.png`, `architecture.png`, Makefile, `.env.example` have no owning phase.** Delivery §5–§6.
Fix: adopt 23 h + 3 h contingency (section F) and the pre-approved cut order: (1) drop Twilio, (2) real calls 6 cards × 2 versions, (3) repeats 3 instead of 5, (4) Mermaid instead of Lucidchart. Phase 2 owns `flow.mmd`, scripts, `.env.example`; Phase 5 owns `architecture.mmd`, the video and `score.py --readme`.

**M11. Strict serialization + missing key idles the project.** Delivery §7.
Fix: Phase 1 and the offline parts of Phase 3 (scenarios.yaml, rubric, judge/score on fixtures) may start while the Phase 0b gate waits. Hard serialization stays for Phase 2, the Phase 3 run and Phase 4. **This session still stops at the Phase 0 gate as Ahmed asked.**

**M12. Tool contracts: `conversation_id` LLM-filled, no idempotency, no error envelope, money as floats, missing errors.** Quality §5, platform §10.
Fix: bind `conversation_id` to `{{system__conversation_id}}` and time to `{{system__time}}` as dynamic variables on every tool (exact binding syntax to confirm in Phase 2 against the tool schema); one envelope `HTTP 200 {status: ok|error|needs_clarification|not_found, error_code, say_ar, say_en, ...}` (401 for auth, 422 for schema only); add `unknown_product`, `invalid_qty` (1–20), `below_minimum`, `outside_hours`, `area_not_served` (with `served_areas_ar[]`); resolve `time_slot` server-side to `{date, window}` Asia/Riyadh with `time_slot_spoken_ar`; `escalate_to_human` takes `customer_name?`, `phone?`; status-by-phone returns ≤ 2 latest orders; money as **integer halalas** in SQLite.

**M13. Spoken Arabic data is incomplete and mixes registers.** Quality §6.
Fix: add `unit_dual_ar`, `unit_plural_ar`, `unit_gender` to products.json; `tests/golden_spoken.csv` signed off by Ahmed (one register: white Saudi colloquial) covering 1, 2, 3, 10, 11, 17, 25, 99, 100, 117, 200 riyals; 25/50/75 halalas; qty 1/2/3/11 per unit; one phone; one order id; order ids **numeric only** (4 digits, unique); `normalize_phone()` accepting +966 / 966 / 5XXXXXXXX / Arabic-Indic / paired numbers → `05XXXXXXXX`; the actual spoken strings are auditioned in Phase 0b.

**M14. Eval statistics and method cannot support the planned claims.** Quality §7, §9–§11; delivery §10.
Fix: each sim scenario runs **k = 5** (floor 3 if cost forces it) per version; report pass rate with Wilson 95% CI and pass^k; paired per-scenario comparison; split scenarios dev/holdout (~70/30) **before** v1; freeze and log `agent_config_sha`, `llm_model_id`, `voice_id`, `tts_model_id`, `asr_provider`, `catalog_sha`, `simulator_model`, `judge_config_sha` per run; reset the SQLite DB per run (or mock tools and say so); real calls reported descriptively, not as a v1→v2 delta; interview line becomes "grounding failures went from X/100 to Y/100 simulated runs".

**M15. Rubric/judge: brittle string checks, missing critical rows, uncalibrated judge.** Quality §9–§10.
Fix: deterministic tool-log assertions are the primary scorer; `must_say`/`must_not_say` become normalized regex lists; add 3 critical rows (phantom confirmation, spoken number ≠ tool output, prompt/secret disclosure); define brevity (≤ 2 segments on `[.!?؟]` and ≤ 30 words, filler counted separately), missed cue, escalation trigger (asks for human, anger keyword ×2, or 2 consecutive "ما فهمت"); hand-label ~30 gold transcripts, accept automatic scoring only at agreement ≥ 0.9 and κ ≥ 0.7 (proposed); freeze judge model + prompt hash + temperature 0 in `evals/judge_config.yaml`; judge from a different model family than the agent LLM; spot-check 20% of judge passes; delimit transcripts as data; give the judge catalog + store.json + tool log. Replace the single filler with a pool of 4–5 variants used only before tools whose p95 > ~700 ms.

**M16. Scenario coverage gaps.** Quality §8, delivery §9.
Fix: add pickup order, area not served, below minimum, out-of-stock inside the order, "no" at read-back, status by id / not found, returns policy, alias trap, qty ≥ 11, Friday hours, injection via `customer_name`, cancel request (Sara: explain she cannot cancel, escalate). Suite grows to ~26 sim scenarios; E7–E9 voice-only. Define the **10 call cards** as the first Phase 3 output: H1, H2, H5, H6, E3, E5, E6, E10/E11, E12, E14, each with a fake name and an obviously fake phone (0500000001…). Book 3 family sessions (P0b rating, v1 calls, v2 calls) now; same callers and cards for v1 and v2.

**M17. Cross-platform setup.** Platform §16–§17, delivery §8d.
Fix: all tasks as bash scripts in `scripts/` (Git Bash + macOS) with Python entry points; optional thin Makefile for the Mac; `.python-version` = `3.12`; `requirements.txt` with exact pins (fastapi 0.162.0 or 0.161.x if < 2 weeks old at Phase 1, pydantic 2.14.1, rapidfuzz 3.14.6, uvicorn 0.54.0, pytest 9.1.1, httpx 0.28.1); judge via the provider SDK directly (or LiteLLM pinned with `--require-hashes`); `python` not `python3` on Windows; venv activate path documented for both OSes.

**M18. Tool endpoint hardening and latency measurement.** Quality §13.
Fix: `hmac.compare_digest`; never log header values; 8 KB body cap; per-IP rate limit (~30 req/min); `max_length` on every string (`query` ≤ 120, `customer_name` ≤ 40, `summary` ≤ 300); rotate `TOOL_SECRET` per demo session and after any dashboard screen recording; log `latency_ms` per tool call; report p50/p95 end-to-end from conversation metadata in QA_REPORT.

**M19. Real brand with fake prices in a public demo.** Quality §14.
Fix (Ahmed decides): default to a fictional store name in `store.json` for the public demo (the persona is swappable by design) unless the store owner signs off in writing; add an on-page banner and a first-message clause «نسخة تجريبية، الأسعار غير حقيقية»; non-real store phone; seed phones in an obviously fake pattern.

---

## D. Nice-to-have

- Turn on `platform_settings.guardrails.prompt_injection` in v2 as a CHANGELOG item (so E13 measures prompt vs prompt+guardrail).
- `tts.text_normalisation_type: "system_prompt"` so platform normalization does not fight `spoken.py`; verify by listening.
- `force_pre_tool_speech` / `tool_call_sound` as a backstop for the "لحظة أشيك لك" filler.
- Use `platform_settings.evaluation.criteria` as a free first-pass judge, reported separately.
- Shortlist LLMs from `npx elevenlabs agents llm list` (one Gemini Flash, one Claude Haiku 4.5), pick by measured latency and Arabic quality in Phase 2; record in README. Stay in Custom mode (Realtime mode's Arabic support is UNVERIFIED and removes TTS voice control).
- Plural/respectful address in the prompt («معكم سارة… كيف أقدر أخدمكم؟»), matching Ahmed's existing Maqadeena copy register; fix «جملتين قصيرة» → «جملتين قصيرتين».
- Keep `# أمثلة` prices identical to `products.json` (generate them) so the model does not learn stale prices.
- Twilio as an optional Phase 6 with 0 hours inside the 23.
- Point README setup at https://elevenlabs.io/docs/llms.txt; replace the mcpservers.org source with official URLs.
- Lucidchart only if Ahmed wants it for the application; `docs/flow.mmd` stays the source of truth.

---

## E. Plan amendments (decisions that override `plan.md`; input to Spec Kit)

1. **Gates:** section F is §11. Section G is the Phase 0 gate. `docs/STATUS.md` tracks the open gate and minutes used.
2. **Phase 0 is split** into 0a (offline, Windows, today) and 0b (API key + raters, Mac). Nothing in 0b may be reported as done without a real API result.
3. **Six tools**, not five: `get_product`, `get_store_info`, `quote_order`, `create_order`, `check_order_status`, `escalate_to_human`. Read-back uses `quote_order` only. `create_order(quote_id, …)` is idempotent.
4. **Tool envelope:** HTTP 200 `{status, error_code?, say_ar, say_en?, …}`; 401 auth; 422 schema. Money in integer halalas. Order ids numeric (4 digits). `conversation_id` and time bound from `system__conversation_id` / `system__time`.
5. **Matcher:** the B4 pipeline replaces §7 steps 1–5. Plurals/dialect words are aliases. ≤ 2 clarification options. Golden table ≥ 30 pairs. `rapidfuzz==3.14.6`.
6. **Data model additions:** `unit_dual_ar`, `unit_plural_ar`, `unit_gender`; `total_halalas INTEGER`; `quotes` table (`quote_id`, `conversation_id`, body, totals, `created_at`); orders gain `quote_id`. Seed phones obviously fake.
7. **Platform config as code:** `agent/` is the `agents init` layout; `agent_configs/sara.json` is generated from `prompts/system_v*.md`; CLI pinned 1.7.1 as devDependency, run via `npx elevenlabs`; the Mac pushes, the laptop only `--dry-run`s. Tool URLs templated from `TOOLS_BASE_URL`; `TOOL_SECRET` as an ElevenLabs Secret (`secret_id`).
8. **Agent settings baseline:** `language: ar`; `language_presets: [en]` + `language_detection` (English-only trigger); `asr.provider` and `asr.keywords` set per Phase 0b result; `tts.model_id` + `voice_id` = Phase 0b winner; `turn.turn_timeout`, `turn.silence_end_call_timeout`, `conversation.max_duration_seconds: 240`; `auth.allowlist` + `require_origin_header: true`; `call_limits.daily_limit: 20`, `agent_concurrency_limit: 2`; `privacy.retention_days: 30`; `end_call` enabled; `transfer_to_number` not used (widget cannot).
9. **Widget:** hosted on GitHub Pages; embed script pinned; local serving via `python -m http.server`.
10. **Fallback:** split trigger (STT → Vapi + Azure ar-SA STT; TTS → Azure `ar-SA-ZariyahNeural` re-rating); fallback TTS on ElevenLabs is `eleven_flash_v2_5`, not `eleven_multilingual_v2`; +3–4 h contingency.
11. **Budget:** ~110 call-minutes on Starter (Ahmed buys before 0b); 23 h + 3 h contingency; pre-approved cut order (Twilio → 6 cards → k=3 → Mermaid).
12. **Serialization:** Phase 1 and offline Phase 3 work may proceed while 0b waits; Phases 2, 3-run, 4 stay strictly gated. This session stops at the Phase 0 gate.
13. **Eval method:** `mode: sim|voice|both`; E7–E9 voice-only; ~26 sim scenarios, dev/holdout split before v1; k = 5 repeats (floor 3); Wilson CIs; frozen and hashed config per run; deterministic tool-log assertions primary; 3 new critical rubric rows; judge calibrated on ~30 gold transcripts, frozen, different model family; DB reset per run; real calls descriptive only.
14. **Privacy:** raw results and real calls git-ignored; `redact.py` before anything is committed; gitleaks pre-commit; family consent line; delete real-call conversations after the report is final.
15. **Cross-platform:** `scripts/*.sh` + Python; `.python-version` 3.12; exact pins; no `brew`/`make` assumptions.
16. **Diagrams:** Mermaid (`docs/flow.mmd`, `docs/architecture.mmd`) are the sources; PNG exports are derived. Lucidchart optional.
17. **Brand:** fictional store name by default in the public demo unless written sign-off; demo banner; the persona stays swappable via `store.json`.
18. **Owning phases for orphan deliverables:** Phase 2 → `flow.mmd`, `scripts/`, `.env.example`; Phase 5 → `architecture.mmd`, D6 video, `score.py --readme`.

---

## F. Reconstructed §11 — delivery plan

Hours are Claude Code/Ahmed build time. "Human" is rater/caller/approval time outside the build hours. Day plan: D1 Phase 0a + Phase 1 start · D2 Phases 1–2 (0b as soon as the key exists) · D3 Phase 3 build + sims · D4 real calls round 1, review, Phase 4 · D5 real calls round 2, Phase 5, video.

| Phase | Name | Hours | Human | Inputs | Outputs | Acceptance gate (pass/fail) | Checker |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **0a** | Dialect spike — offline | 1.0 | 0 | plan.md, this review, CLI 1.7.1 | `agent/` init layout + `agent_configs/sara.json` (minimal Arabic agent, no tools), `docs/phase0/tts_script.md` (8 lines), `docs/phase0/voice_selection.md` (procedure, no IDs), `docs/phase0/stt_sheet.md` (10 utterances + expected entities), `docs/phase0/tts_ratings.csv` + `stt_results.csv` templates, `scripts/score_phase0.py` + tests on fake data, draft catalog trap items, `.env.example`, `docs/STATUS.md` | `npx elevenlabs agents push --dry-run` validates the config with no API call; `pytest scripts/tests/test_score_phase0.py` green; every file above exists; `STATUS.md` says "Phase 0 gate: OPEN — waiting for API key and raters"; **no voice IDs, scores or minutes written** | Claude (automated) + Ahmed reads STATUS |
| **0b** | Dialect spike — go/no-go | 1.5 | ~1 h Ahmed + 2 raters × 20 min + 1 extra STT speaker × 10 min | API key in `.env` on the Mac, Starter plan, 2 native Saudi raters (≥ 1 from Al-Ahsa) | `docs/phase0/voices.md` (3 real voice IDs from the API), 48 clips (git-ignored), filled `tts_ratings.csv`, `stt_results.csv`, `docs/phase0/decision.md`, `STATUS.md` with minutes | **Section G** | `score_phase0.py` + Ahmed signs `decision.md` |
| **1** | Tools backend + tunnel | 4.0 | 10 min (re-run tests on 2nd OS) | §6–§7 + amendments 3–6, trap items | `backend/`, seeded SQLite, 6 tools, `arabic.py`, `spoken.py`, `redact.py`, tests, `scripts/tunnel.sh`, JSON tool log | `pytest` green incl. golden tables (≥ 30 matcher pairs, `golden_spoken.csv`); 401 without secret, 422 on oversize body, 200 envelope on every error path; `create_order` idempotent (2nd call → `duplicate: true`); p95 < 300 ms over 100 local calls per tool; from a second network a `curl` through the tunnel returns 200 with the secret and 401 without; fresh clone on the other OS runs `scripts/test.sh` green | Claude (automated), Ahmed re-runs on 2nd OS |
| **2** | Prompt v1 + agent + widget | 4.0 | 30 min test calls | green 1, Phase 0b winner, tunnel | `prompts/system_v1.md`, `scripts/build_agent_config.py`, 6 `tool_configs/*.json.tmpl`, agent pushed, `demo/index.html` on GitHub Pages, `docs/flow.mmd`, `.env.example` complete | 3 consecutive voice orders via the hosted page (1 pickup, 1 delivery, 1 mid-call correction) each create the right SQLite row with `conversation_id` from `system__conversation_id`, a `quote_order` call before `create_order`, a spoken read-back, and a digit-by-digit order id; one out-of-stock item is spoken as unavailable; one English-only call switches to English (E10) and one mixed call stays Arabic (E11); `agents push --dry-run` shows no drift; minutes logged | Ahmed makes the calls, Claude checks DB + transcripts |
| **3** | Eval suite + v1 | 6.0 | ~1.5 h (10 family calls + flag review) | green 2, judge key, 10 call cards, booked callers | `evals/scenarios.yaml` (~26, tagged mode/split), `rubric.md`, `judge_config.yaml`, `run_sims.py`, `fetch_transcripts.py`, `judge.py`, `score.py`, `results/v1/` (summary.csv, per-scenario JSON, redacted excerpts), critical-flag list, ~30 gold labels | ≥ 20 sim scenarios × k ≥ 3 completed; judge agreement on gold ≥ 0.9 / κ ≥ 0.7 per automated dimension (else that dimension is human-scored); 10 real-call transcripts fetched, redacted, joined to tool logs; 100% of critical flags and 100% of real calls have a human verdict; run metadata (all hashes/IDs) recorded; no raw transcript or audio tracked by git (`git ls-files` check) | Claude (automated) + Ahmed signs flag list |
| **4** | Fixes → v2 + rerun | 3.5 | ~1.5 h (approve fixes, 10 calls again) | v1 results, Ahmed's approval of ≥ 5 fixes | `system_v2.md`, `CHANGELOG.md` (≥ 5 entries), `results/v2/`, holdout results | each CHANGELOG entry cites scenario id + before→after metric; same suite, same k, same cards, same frozen models (hash check script passes); v2 critical grounding failures = 0 **and** orders-without-confirmation = 0 on dev and holdout (one 1-h v2.1 retry allowed, then report honestly); no critical dimension regresses | Claude (automated) + Ahmed |
| **5** | Ship | 3.0 | 30 min record video | green 4 | README (problem, architecture, setup both OSes, results table via `score.py --readme`, video link, demo-data note), `reports/QA_REPORT.md`, `docs/architecture.mmd` + PNGs, D6 video uploaded | fresh clone on the other OS reaches green `scripts/test.sh`; every number in README/QA_REPORT matches `summary.csv` by script; video 60–90 s with one order, one edge case, the results table; gitleaks clean on full history; no audio or raw transcript in git; demo banner present; `STATUS.md` shows total minutes vs budget | Claude (automated) + Ahmed |
| **6 (optional)** | Twilio number | 0 (outside budget) | — | all gates green, video published | phone number attached | one real phone call completes an order | Ahmed |
| **Total** | | **23.0 h** + 3 h contingency | **~5 h** | | | | |

Hard gates (block the next phase): 0b, 1, 2, 3, 4. Soft targets (reported, not gated): task success ≥ 85%, tools ≥ 90%, brevity ≥ 90%, naturalness ≥ 4.0.

---

## G. Phase 0 gate — precise definition

All thresholds are **proposals for Ahmed to confirm** before 0b runs; they are not from the lost table. Nothing below may be recorded as a result without a real API call or a real human score.

### G.1 Fixed assets (produced in 0a, offline)

**TTS script — 8 lines, Saudi colloquial, one register, spoken strings exactly as `spoken.py` will emit them:**

1. Greeting: هلا والله، معكم سارة من مقاضينا، كيف أقدر أخدمكم؟
2. Price 9.75: الصحون الزجاج بتسعة ريال وخمسة وسبعين هللة
3. Total 17.25: المجموع سبعطعش ريال وخمسة وعشرين هللة
4. Total over 100 (117.00): المجموع مية وسبعطعش ريال
5. Phone, grouped 3·3·4: رقمكم صفر خمسة خمسة، واحد اثنين ثلاثة، أربعة خمسة ستة سبعة، صح؟
6. Order id (numeric only): رقم طلبكم أربعة، ثمانية، اثنين، واحد
7. Clarification (≤ 2 options): تقصدون صحون زجاج أو صحون بلاستيك؟
8. Escalation + close: أعتذر منكم، بحوّلكم لموظف يتواصل معكم، شكراً لاتصالكم

(Line 4 and the register of lines 2–4 are Ahmed's native-speaker call in 0a; whatever he fixes becomes `golden_spoken.csv`.)

**STT sheet — 10 utterances, each spoken by 2 speakers (Ahmed + 1 other, different gender or age) = 20 clips, into the minimal agent whose prompt says to answer only «تمام»:**

| # | Utterance | Critical entities to score |
| --- | --- | --- |
| 1 | بكم الصحون الزجاج؟ | product = صحون زجاج (near-duplicate pair) |
| 2 | عندكم كاسات ورق؟ | product = أكواب ورق via dialect alias |
| 3 | أبي اثنعش علبة من ‹trap item› | qty = 12; product = a shelf≠common trap item drafted in 0a |
| 4 | رقمي صفر خمسة خمسة، واحد اثنين ثلاثة، أربعة خمسة ستة سبعة | phone 0551234567, grouped |
| 5 | جوالي صفر خمسة وخمسين، ثمانية وسبعين، ثلاثة أربعة خمسة ستة | phone 0557834567, paired numbers |
| 6 | وين وصل طلبي؟ رقمه أربعة ثمانية اثنين واحد | order id 4821 |
| 7 | أبي delivery للمبرز بكرة العصر | mix stays Arabic; area = المبرز; slot = بكرة العصر |
| 8 | متى تفتحون يوم الجمعة؟ | intent = hours; day = الجمعة |
| 9 | أبي أكلم موظف | intent = escalate |
| 10 | Do you deliver to Hofuf? | transcribed in English; intent = delivery; area = Hofuf |

### G.2 TTS dialect gate (needs key + raters)

- **Candidates:** 3 **female** voices (persona سارة) chosen by the 0a procedure: `voices accents get` → `voices get_shared --language ar --accent <saudi/gulf value> --use-cases conversational` (exclude custom-rate voices) → shortlist 5 → keep 3. IDs recorded only from the API response.
- **Models:** `eleven_v4_turbo` and `eleven_flash_v2_5` → 3 × 2 × 8 = **48 clips**, synthesized with the exact voice settings the agent will use. (Clips use TTS character credits, not call minutes; quota on Starter UNVERIFIED — check before synthesizing.)
- **Raters:** Ahmed + 2 native Saudi speakers (≥ 1 from Al-Ahsa), scoring independently, clips blind-labelled and shuffled with a recorded seed.
- **Scale (1–5 Saudi naturalness):** 1 foreign/broken · 2 MSA newsreader · 3 Gulf-ish with obvious errors · 4 Saudi receptionist with a slip or two · 5 indistinguishable from a native. Lines 2–6 also get a binary "heard the right number".
- **GO:** the best (voice, model) pair has mean ≥ **4.0** over its 24 ratings (3 raters × 8 lines), no rater's mean for that pair < 3.0, and 100% of its number lines are judged correct by all raters.
- **RETRY** (once, 45 min): best mean 3.5–3.99 → adjust stability/similarity, add up to 3 more voices, try `eleven_v3_conversational`. After the retry: ≥ 4.0 → GO; 3.8–3.99 → **GO with risk flag** (the v2 naturalness target may be missed; written into STATUS); < 3.8 → NO-GO.
- **NO-GO** at the start: best mean < 3.5, or any number line wrong on all voices.
- **Fallback trigger on TTS NO-GO:** re-rate Azure `ar-SA-ZariyahNeural` with the same 8 lines and raters; if it passes, voice runtime becomes Vapi (+3–4 h); if not, stop and re-scope with Ahmed.

### G.3 STT gate (needs key + 2 speakers)

- **Procedure:** 20 clips spoken live into the minimal agent (dashboard or hosted widget) with `agent.language: ar`, first with `asr.provider` default, then repeated with one other provider value; transcripts fetched from `GET /v1/convai/conversations/{id}` (realtime ASR, not batch Scribe). Score **entities, not WER**.
- **GO (all must hold, on the best provider):**
  - (a) intent recoverable in ≥ **18/20** clips, including both English clips transcribed as English;
  - (b) product entity correct (name or catalog alias) in ≥ **5/6** product clips (#1–#3 × 2);
  - (c) quantity correct in **2/2**; order-id digits exact in **2/2**;
  - (d) phone digit accuracy ≥ **95%** over the 4 phone clips (40 digits, ≤ 2 wrong) and ≥ 2/4 exactly right;
  - (e) area + time slot recoverable in **2/2** (#7), hours/day in 2/2 (#8), escalation in 2/2 (#9).
- **RETRY** (once, 30 min): switch `asr.provider` among {elevenlabs, scribe_realtime, scribe_v2_turbo}, add product names to `asr.keywords`, re-run the failing clips.
- **NO-GO** otherwise → **fallback trigger:** Vapi + Azure `ar-SA` STT, keeping ElevenLabs `eleven_flash_v2_5` TTS (+3–4 h).
- Also in 0b: run **one** Simulation test and read the usage counter to learn whether tests bill minutes; record LLM id, ASR provider, TTS model, voice id, voice settings, CLI version and minutes used in `decision.md`.

### G.4 Who does what / what needs the key

| Item | Needs API key | Needs human | Who |
| --- | --- | --- | --- |
| CLI pin, `agent/` layout, `sara.json`, `push --dry-run` | no | no | Claude (0a) |
| TTS script, STT sheet, CSV templates, `score_phase0.py` + tests, trap items, `.env.example`, STATUS | no | Ahmed fixes register of lines 2–4 | Claude (0a) |
| Plan purchase, key in `.env` on the Mac | — | **Ahmed** (payment) | Ahmed |
| Voice library search, 3 voice IDs, 48 clips | **yes** | listening to shortlist | Claude on Mac + Ahmed |
| Blind ratings | no | **3 raters** | Ahmed + 2 |
| Pushing the minimal agent, 20 STT clips × 2 providers, transcript fetch | **yes** | **2 speakers** | Claude on Mac + Ahmed + 1 |
| One Simulation test for billing check | **yes** | no | Claude on Mac |
| `decision.md` sign-off, STATUS update | no | **Ahmed** | Ahmed |

**Gate status today (2026-10-27, Windows laptop): OPEN — 0a deliverable, 0b blocked on API key, plan purchase and raters.** No result may be written until 0b runs.
