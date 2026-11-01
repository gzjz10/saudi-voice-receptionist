# STATUS — Saudi Voice Receptionist

**Phase 0 gate: PASSED 2026-11-01** — TTS GO (Nora S + eleven_v4_turbo, R1 only) and STT PASS (S1 only, `scribe_realtime`, the only provider); `docs/phase0/decision.md` signed by Ahmed. Next: Phase 2 (plan.md §14 row 2).

_The sections below are the history of the gate._

Updated 2026-10-27 on the Windows laptop by the Phase 0 team (leader Fable 5.1). Phase 0a (offline)
is complete. Phase 0b has not started: no API key exists on this machine, so **no voice ID, clip,
transcript, score or minute has been produced**. Call minutes used so far: **0**. Characters used: **0**.

Gate definition: `reviews/plan-review.md` §G. Runbook for the Mac: `phase0/README.md`.
**Phase 1 must not start until this gate reads PASSED and `docs/phase0/decision.md` is signed by
Ahmed** (amendment 12 allows Phase 1 offline work to proceed in parallel only with Ahmed's say-so).

## Gate checklist

States: PREPARED (file/script exists and was checked offline) · BLOCKED-key (needs
`ELEVENLABS_API_KEY` on the Mac) · BLOCKED-human (needs Ahmed, raters or speakers) · PASS · FAIL.
Nothing is PASS yet; that is correct, not a gap.

### 0a — offline (reviews §F row 0a)

| Criterion | State | Evidence |
| --- | --- | --- |
| `agent/` is the CLI `agents init` layout; `@elevenlabs/cli` pinned 1.7.1 as devDependency | PREPARED | `agent/package.json`, lockfile with darwin-arm64 binary; `--version` → `elevenlabs 1.7.1` |
| `agent_configs/sara.json`: minimal Arabic agent, `language: ar`, no tools, no `voice_id` | PREPARED | `python agent/validate_configs.py` → OK; `test_phase0.py` asserts no `voice_id`/tools and prompt == `prompts/system_v0.md` |
| `npx elevenlabs agents push --dry-run` validates with no API call | PREPARED (weak check) | exits 0 and prints "Would update agent". **Caveat:** in 1.7.1 the dry-run only parses JSON (it even exits 0 on invalid JSON); `validate_configs.py` adds enum/range checks from the CLI's own schema and is the real 0a check |
| `docs/phase0/tts_script.md` (8 lines) | PREPARED, register signed off 2026-10-28 | lines from review §G.1; `register_signed_off: no` until Ahmed reviews lines 2–4 |
| `docs/phase0/stt_sheet.md` (10 utterances + expected entities) | PREPARED | includes cards, run steps, privacy rules. #5 corrected (+«سبعة») so the spoken digits equal 0557834567; #6 numeric 4821; #3 trap = أكياس زبالة/أكياس نفايات |
| `docs/phase0/voice_selection.md` (procedure, NO voice IDs) | PREPARED | 3 leads cited by name/catalog page only; ID table empty; `test_phase0.py` greps docs for id-like tokens |
| `docs/phase0/tts_ratings.csv` + `docs/phase0/stt_results.csv` templates | PREPARED | header-only ratings sheet; 20 blank result rows (10 × S1/S2) |
| Scorers + tests on fake data | PREPARED | `phase0/stt_score.py --selftest`, `phase0/tts_score.py --selftest`, `python phase0/test_phase0.py` → 7/7 pass (also pytest-collectable) |
| Draft catalog trap items | PREPARED | `docs/phase0/catalog_traps.md` (names and aliases only, no prices) |
| `.env.example` (names only) | PREPARED | one variable, `ELEVENLABS_API_KEY=` |
| No voice IDs, scores or minutes written | PREPARED | confirmed by test + manual read of every Phase 0 file |

**0a verdict: complete.** Deviations from the spec-kit file list (`specs/001-.../plan.md` "Phase 0a
outputs"): scorers are `phase0/stt_score.py` + `phase0/tts_score.py` with `phase0/test_phase0.py`
instead of `scripts/score_phase0.py` + `scripts/tests/`; `thresholds.json` is not a file (thresholds
are the `GATE` dicts at the top of each scorer); `rating_sheet.md` and `voices.md` are sections of
`voice_selection.md`; `validate_agent_config.py` is `agent/validate_configs.py`; no
`check_phase0a.sh` (the test file is the check). The spec-kit documents should be updated to match
when Phase 1 planning starts.

### 0b — TTS dialect gate (reviews §G.2)

| Criterion | State |
| --- | --- |
| Ahmed confirms thresholds and the register of lines 2–4 | PASS (2026-10-28, approved as is) |
| Starter plan bought, key in `.env` on the Mac | PASS (2026-10-28; free key upgraded to Starter) |
| 3 female Saudi/Gulf voices found via the API, IDs recorded from the response only | DEVIATION: 1 voice (Nora S) after Ahmed rejected the other library candidates; see `voice_selection.md` |
| 48 clips (3 voices × 2 models × 8 lines) with the agent's exact voice settings, blind + seeded | DONE as 16 clips (1 voice × 2 models × 8), seed 4821; rating page `phase0/make_rating_page.py` |
| 3 independent blind raters (Ahmed + 2 native Saudi, ≥ 1 Al-Ahsa), 1–5 scale + number y/n | WAIVED: Ahmed rated alone (R1) and waived R2/R3, 2026-10-28 |
| Best pair mean ≥ 4.0, every rater ≥ 3.0 on it, all number lines right → GO | GO on R1 only: Nora S + eleven_v4_turbo 4.38, numbers 5/5; set in both agent configs |
| RETRY (3.5–3.99, once, 45 min) / NO-GO (< 3.5 or a number line wrong on all voices) / Azure fallback | not evaluated |

### 0b — STT gate (reviews §G.3)

| Criterion | State |
| --- | --- |
| Minimal agent pushed (`language: ar`, answers «تمام») | PASS (2026-10-28; ids in `agent/agents.json`) |
| 20 clips (10 × S1 Ahmed + S2) spoken live, per provider; 2 providers | S1 DONE 2026-11-01 on `scribe_realtime` (8/10 cards right; misses #5 phone, #10 الهفوف; see `decision.md`). S2 WAIVED by Ahmed 2026-11-01. Second provider IMPOSSIBLE: API keeps/forces `scribe_realtime` (see `decision.md`). Scorer: PASS with `--waive-speaker S2 --allow-single-provider`, accepted by Ahmed 2026-11-01 |
| Transcripts from `GET /v1/convai/conversations/{id}` (realtime ASR) | BLOCKED-key (`--fetch` never run live) |
| (a) ≥ 18/20 intents | not evaluated |
| (b) product ≥ 5/6 · (c) qty 2/2, order id 2/2 · (d) ≤ 2/40 phone digits wrong, ≥ 2/4 exact · (e) #7 #8 #9 all 2/2 | not evaluated |
| RETRY (30 min: provider switch + `asr.keywords`) / NO-GO → Vapi + Azure ar-SA STT | not evaluated |

### 0b — also required

| Item | State |
| --- | --- |
| One Simulation test; does it bill minutes? | PASS 2026-10-28: test passed; bills credits (199), not call minutes |
| `docs/phase0/decision.md` with LLM, asr.provider, tts.model_id, voice_id, settings, CLI 1.7.1, seed, minutes | PASS 2026-11-01 |
| Ahmed signs `decision.md`; STATUS updated with minutes | PASS 2026-11-01 — 4.8 call-min, 6,250 / 40,000 characters |

## What was produced in 0a

`prompts/system_v0.md` · `agent/` (package pin, registries, two configs, `validate_configs.py`,
README) · `docs/phase0/` (`tts_script.md`, `stt_sheet.md`, `stt_results.csv`, `voice_selection.md`,
`tts_ratings.csv`, `catalog_traps.md`) · `phase0/` (`find_voices.py`, `tts_samples.py`,
`tts_score.py`, `stt_score.py`, `test_phase0.py`, `requirements.txt`, `README.md`) · `.env.example` ·
this file.

Versions pinned: `@elevenlabs/cli` 1.7.1 · `elevenlabs` (Python) 2.74.1 · `python-dotenv` 1.2.4 ·
`pytest` 8.4.2 · Python 3.12. Agent baseline: LLM `gemini-2.5-flash`, TTS `eleven_v4_turbo` (vs
`eleven_flash_v2_5` in the test), ASR `scribe_realtime`, stability 0.5 / similarity 0.8 / speed 1.0,
max call 240 s, retention 30 d, 20 calls/day, 2 concurrent.

Doc spot-checks done by the leader on 2026-10-27: Arabic listed for `eleven_v4_turbo` (~100 ms),
`eleven_flash_v2_5` (~75 ms) and `eleven_v3_conversational` (~280 ms); `eleven_turbo_v2_5` deprecated
(https://elevenlabs.io/docs/overview/models). Conversation transcript items carry `role` ∈ {user,
agent} and optional `message` (https://elevenlabs.io/docs/api-reference/conversations/get). Starter
= 30,000 credits/month; Flash/Turbo v2.5 0.5–1 credit/char via API (https://elevenlabs.io/pricing).

## What blocks the gate

1. No ElevenLabs API key (Ahmed buys Starter and writes the key into `.env` on the Mac).
2. Raters and speakers not booked (2 native Saudi raters, 1 extra STT speaker).
3. Ahmed has not confirmed the G.2/G.3 thresholds or signed off the register of TTS lines 2–4.
4. Python SDK does not install inside this repo on Windows (path > 260 chars); run 0b on the Mac.

## UNVERIFIED (settle on the Mac, record in decision.md)

Server accepts `language: ar` with `eleven_v4_turbo` · `agents push` creates agents from id-less
configs and whether it writes ids into `agents.json` · the voice used while `voice_id` is absent ·
real accent values from `voices accents get` and whether `gender=female` / `use_cases=conversational`
filter values are accepted · whether library voices must be added to My Voices first · catalog
labels vs official library entries · `eleven_v3_conversational` on the plain TTS endpoint · whether
the agent sends `language_code`/`use_speaker_boost` like `tts_samples.py` · Starter's Agents minutes
and v4 credit cost per character · whether Simulation tests bill minutes · `--fetch` against the
live API.

## Next prompt to paste into Claude Code on the Mac

```
Read CLAUDE.md, docs/STATUS.md and phase0/README.md. Phase 0a is done; do Phase 0b only.
I have put ELEVENLABS_API_KEY in .env, bought Starter, and booked 2 raters and 1 extra speaker.
Follow phase0/README.md steps 0-9 in order. Record the usage counter before and after. Never write a
voice ID, score or minute that did not come from the API response, the raters' CSV or the counter;
mark anything you could not check UNVERIFIED. Stop and ask me at every human step (thresholds and
register sign-off, listening to the shortlist, rating, speaking the STT cards, decision.md signature).
Keep Phase 0 under 10 call-minutes. At the end, update docs/STATUS.md with the gate verdict, commit
the docs and CSVs (not phase0/samples/), push, and stop. Do not start Phase 1.
```

## History

- 2026-10-27 — repo bootstrapped; plan review (`reviews/plan-review.md`) and spec kit docs written;
  Phase 0a files written and checked offline on the Windows laptop. Gate OPEN.
- 2026-10-28 — resumed on the Mac: venv + CLI 1.7.1 installed, offline tests 7/7. Free-plan key in
  `.env` (Text to Speech, Voices, User, ElevenAgents); `user subscription get` → tier free,
  0 / 10,000 characters, 3 voice slots. **Ahmed: the project is Arabic only.** STT #10 is now
  «توصلون للهفوف؟», check (a) has no English part, TTS line 9 removed, plan.md rule 9 / E10 and
  review M4 updated. The Spec Kit docs in `specs/` still describe English switching (FR-027,
  T077, T090, phase0 contract); update them when Phase 1 planning starts.

## Phase 1 — tools backend (started 2026-10-28, in parallel with 0b by Ahmed's say-so)

Plan and task ticks: `docs/phase1/PLAN.md`. **Phase 1 gate: PASSED 2026-10-28** (Windows clone check waived by Ahmed).

| Gate check (T076) | State |
| --- | --- |
| pytest green incl. ≥ 30 matcher pairs and `golden_spoken.csv` | PASS — `bash scripts/test.sh`: 150 passed (36 matcher pairs, 37 spoken rows) + Phase 0 checks 7/7 |
| 401 without secret, 413 > 8 KB, 422 on schema, 200 envelope on every error path | PASS — `backend/tests/test_http.py`, `test_tools.py`, `test_contracts.py` (all responses validate against `tools.openapi.yaml`) |
| `create_order` idempotent (2nd call → `duplicate: true`) | PASS — with and without `conversation_id` |
| p95 < 300 ms over 100 calls per tool | PASS in-process (`bash scripts/latency.sh`): worst p95 3.2 ms. Live uvicorn: 200 with secret, 401 without, and the 30/min limiter returned 429 as designed |
| Tunnel 200 with secret / 401 without, from a second network | PASS 2026-10-28 — Ahmed started `dev.sh` + `tunnel.sh` (quick tunnel); `bash scripts/tunnel_check.sh` through the public trycloudflare URL: all 6 tools 200 with the secret, 401 without. Whether the Mac was on the phone hotspot is per Ahmed |
| Fresh clone green on Windows | WAIVED by Ahmed 2026-10-28 (T075): the project runs on the Mac only. Re-open if the Windows laptop is used again |
| `golden_spoken.csv` signed | PASS 2026-10-28 — Ahmed approved all 32 draft rows as written (T072) |

Decisions: Arabic only (`say_en`/`text_en` removed from the contract); store name مقاضينا as in
the signed TTS line 1, with the demo disclaimer; delivery fee 15 SAR and minimum 50 SAR are fake
demo values; gitleaks pinned 8.30.1 but not installed (`scripts/install_hooks.sh` refuses until it is).

## Phase 2 — prompt v1, tools, widget (started 2026-11-01)

Tasks: `specs/001-saudi-voice-receptionist/tasks.md` T077–T092. **Phase 2 gate: OPEN — everything passes except T089, fixed in the backend and waiting on one out-of-stock call after a backend restart.**

| Item | State |
| --- | --- |
| T077 `prompts/system_v1.md` (plural, Arabic only, quote → read-back → yes → create, filler pool, demo clause, no bracket tags) | DONE offline; example totals taken from the backend's own quote output |
| T078–T080 six tool templates `agent/tool_configs/*.json.tmpl` | DONE; checked by `agent/validate_configs.py` (schema) and `scripts/tests/test_tool_templates.py` (backend contract). `now` binds `system__time_utc` (ISO), not `system__time` (`%A, %H:%M %d %B %Y`) |
| T081 `build_agent_config.py --profile full` | DONE: v1 prompt, `tool_ids`, `end_call`. Kept from Phase 0: 240 s max, 20 calls/day, 2 concurrent, 30-day retention. No language presets (Arabic only). Turn timeouts left at platform defaults. `auth.allowlist` deferred until T088 passes, so dashboard and phone testing keep working |
| T082 secret | DONE 2026-11-01: `push_tools.py` created workspace secret `sara_tool_secret`; only `TOOL_SECRET_ID` is in `.env` |
| T083 LLM A/B | DEFERRED to Phase 4; `gemini-2.5-flash` still listed by `agents llm list` |
| T084 `demo/index.html` | DONE offline; widget `@elevenlabs/convai-widget-embed@0.20.0` (2026-10-13, newest ≥ 14 days old). Serve on port 8080 (the backend has 8000) |
| T085 `docs/flow.mmd` | DONE |
| T086 public demo page | DONE 2026-11-01 with Ahmed's yes, on Cloudflare instead of GitHub Pages: static-assets Worker `saudi-voice-receptionist` (`wrangler.jsonc`, serves only `demo/`) at https://saudi-voice-receptionist.maqadeena-purchase-order.workers.dev. Tools work only while `dev.sh` + the tunnel run on the Mac |
| T087 push | DONE 2026-11-01: 6 tools in `agent/tools.json`, agent renamed `Sara`; live read-back: 6 `tool_ids`, only `end_call` enabled, prompt == `system_v1.md`; tunnel 200 with secret, 401 without. `asr.keywords` = مقاضينا + the 4 towns (Phase 0 carry-over) |
| T088 three voice orders | PASS 2026-11-01. 7088 `conv_5201m6bsby18ew3rtw0wsz2b90g4` delivery الهفوف, 6 × صحون زجاج, 73.50 (recovered from `missing_field` «الحين» and `below_minimum` 48.75 → caller added one); 6248 `conv_6301m6bst7v8e7drn5b495aby1s0` delivery المبرز, 4 × ترمس قهوة, 74.00; 3437 `conv_4001m6bsxnr9f8mbb7ejtn0m5v91` pickup, 2 → 3 × قدر ضغط corrected at read-back, re-quoted 29.50 → 44.25. Every order: `quote_order` before `create_order`, `conversation_id` + `quote_id` stored, order id read digit by digit, `end_call` after. **Defect found:** call 3 read the phone back with 9 digits and the caller said yes (stored number was right). Fix: step 3 reads the phone in 3-3-4 groups and counts 10 digits; re-pushed, not yet re-tested by voice |
| T089 out of stock | FAIL → fixed, re-test pending: `conv_9301m6bt0vdpfnfv5b4scavjmjvc` said «خلصت حالياً» and placed no order, but spoke **two** alternatives (spec: at most one) because backend `say_ar` joined both. `get_product` now speaks only the first («عندنا بداله …»); `suggestions` unchanged; test tightened. Needs a backend restart and a 20 s call |
| T090 mixed-language | PASS: in `conv_6301…` and `conv_1401m6btjnt2ezqa0sdfse4w0k4z` the English words «delivery» / «pickup» came through ASR as Arabic script («بيك أب»); Sara stayed Arabic and took the right fulfilment both times. `scribe_realtime` transliterates, so the LLM never sees Latin text |
| Drift | PASS: after the last push, live prompt, `tool_ids`, `asr.keywords`, voice and LLM equal `agent/agent_configs/sara.json` (the CLI 1.7.1 dry-run always says "force override", so it is no drift check) |
| Re-test call 7806 `conv_5201m6bt596beznrdhfcrey1g6td` | 120 s; order stored right (3 × دفاتر, pickup, 17.25) but 3 defects: (1) «[لحظة] لحظة» on almost every turn: `tts.expressive_mode` was true, so the platform asked the LLM for audio tags (the Phase 0 «[أبشروا]» carry-over); now false in `sara.json`. (2) She called `quote_order` without asking pickup or delivery (assumed pickup) and before taking the phone. (3) She took the phone after the read-back and called `create_order` without reading it back. Fix: step 6 lists the 5 things needed before `quote_order`; rule 4 forbids `create_order` before a confirmed phone read-back. Re-pushed; phone grouping and T090 still not voice-tested |
| Clean call 2928 `conv_1401m6btjnt2ezqa0sdfse4w0k4z` | 95 s, PASS: phone read back as «صفر خمسة صفر، صفر صفر صفر، صفر صفر صفر واحد» and confirmed before fulfilment; asked pickup or delivery; quote → read-back → yes → create; no bracket tags |
| T081 `auth.allowlist` | DONE: only the workers.dev demo host and `localhost:8080` may start calls; `require_origin_header: true`. The elevenlabs.io talk-to link no longer works by design |
| T091 usage | Phase 2 calls on 2026-11-01: 7 calls, 681 s (11.4 min): 77 + 149 + 110 + 99 + 31 + 120 + 95 s. Between sessions: stop `dev.sh` + the tunnel (tools then fail politely); the allowlist stops strangers' calls |
| Call 1 `conv_9501m6brykn5eh8sa18rwa289t3z` | 77 s, no order: she asked for the district and refused «حي برادة» herself. Fixed in step 4 (ask for one of the 4 towns; `quote_order` decides); call 7088 then asked for the town correctly |

Deviations: CLI 1.7.1 has no `tools push` and inline `prompt.tools` is deprecated, so tools are workspace
tools upserted by name over REST (`scripts/push_tools.py`) and attached by `tool_ids`. `tunnel.sh` no longer
renders templates. Spec lines on English switching (FR-027, US4, T077, T081, T090) now say Arabic only.
