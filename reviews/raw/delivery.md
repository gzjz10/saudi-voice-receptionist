# Plan review: delivery plan, phases and gates

Reviewer lens: delivery plan, phases, gates, schedule, dependencies, budget.
Source: `plan.md` (Saudi Voice Receptionist, Technical Spec v1.0), `CLAUDE.md`.
Date: 2026-10-27.

**Verdict: not_ready.** The plan says each phase is gated, but the gates were never written. §11 (the delivery table) and §3 (the architecture diagram) were embedded content that did not export, so no acceptance check exists for any phase, Phase 0 included. The rest of the spec is strong: scope, data model, tool contracts, rubric and scenarios are specific enough to build from. It becomes ready_with_fixes once the phase table below, or an amended version of it, is adopted into the spec and `docs/STATUS.md`, and once findings 3–8 are resolved.

---

## A. Reconstructed delivery plan (proposal for the missing §11)

The phases come from the §14 prompts. Hours are a proposal: one column fits the plan's 20 hours, the other is a realistic estimate. "Human" means Ahmed or the family raters and callers. That time is not in the 20 hours, and it should be.

| Phase | Name | Budget (fit 20 h) | Realistic | Human time (not in 20 h) |
|---|---|---|---|---|
| 0 | Dialect spike (go/no-go) | 2.0 h | 2.5 h | ~1 h Ahmed + 2 raters × 20 min |
| 1 | Tools backend + tunnel | 4.0 h | 4.0 h | 10 min (run tests on the second machine) |
| 2 | Prompt v1 + agent + widget | 3.5 h | 4.0 h | 30 min (test calls) |
| 3 | Eval suite + v1 run | 5.5 h | 6.5 h | ~1.5 h (10 calls with family + critical-flag review) |
| 4 | Fixes → v2 + rerun | 3.0 h | 3.0 h | ~1.5 h (approve fixes, 10 calls again) |
| 5 | README, QA report, diagrams, video | 2.0 h | 3.0 h | 30 min (record video) |
| **Total** | | **20.0 h** | **23.0 h** | **~5 h** |

20 hours is possible only with zero rework and zero fallback. A Vapi fallback after Phase 0 alone would add about 3–4 hours (finding 3). Ahmed should either agree to ~23 hours plus a 3-hour contingency, or approve the cut list in finding 5 in advance.

### Phase 0: Dialect spike (no backend code)

- **Inputs:** an ElevenLabs account and paid plan, and an `ELEVENLABS_API_KEY` in `.env` on the machine running the spike; `@elevenlabs/cli` at a pinned version; 2 native Saudi raters (at least one from Al-Ahsa, to match the persona); 1 extra speaker for STT; the draft catalog trap items from §6 (see finding 11).
- **Outputs (committed):**
  - `agent/`: minimal Arabic agent config with a 3-line prompt, the §8 first message and no tools.
  - `docs/phase0/tts_script.md`: 8 fixed lines. They are greeting, price (`تسعة ريال وخمسة وسبعين هللة`), total (`سبعطعش ريال وخمسة وعشرين هللة`), phone digits grouped, order ID (`إم جي، أربعة، ثمانية، اثنين، واحد`), a clarification question, an escalation line and a closing.
  - `docs/phase0/voices.md`: 3 candidate voice IDs with name, source, TTS model ID and settings. The IDs are taken from the account and never written from memory.
  - `docs/phase0/tts_ratings.csv`: rater × clip × score, with clips blind-labelled A/B/C.
  - `docs/phase0/stt_sheet.md`: 10 utterances, each with expected entities.
  - `docs/phase0/stt_results.csv` and `scripts/score_phase0.py` (cross-platform Python).
  - `docs/phase0/decision.md`: go / retry / fallback, pinned CLI version, TTS model, ASR setting, LLM pick, minutes used.
  - `docs/STATUS.md` updated.
- **TTS gate (proposal; Ahmed sets the final numbers):**
  - Clips: 3 voices × 8 lines = 24 clips. Each is synthesized with the same TTS model ID and settings the agent will use. Order is randomized and voice names are hidden.
  - Raters: Ahmed plus 2 native Saudi speakers, scoring independently.
  - Scale: 1–5 Saudi naturalness. 1 = foreign or broken, 2 = MSA newsreader, 3 = Gulf-ish with obvious errors, 4 = sounds like a Saudi receptionist with a slip or two, 5 = indistinguishable from a native Saudi speaker. Each number line also gets a binary "heard the right number" check.
  - **GO** if the best voice has a mean ≥ 3.8 over its 24 ratings (3 raters × 8 lines), no rater's mean for that voice is below 3.0, and 100% of its number lines are judged correct by all raters. Rationale: the §1 v2 target for dialect naturalness is ≥ 4.0, and prompt work changes wording but not accent, so the voice has to start near that ceiling.
  - **RETRY** (once, timebox 45 min) if the best mean is 3.0–3.79: try voice settings (stability), 3 more voices, and the other Arabic-capable TTS model (finding 12).
  - **NO-GO** if the score is still under 3.8 after the retry, or under 3.0 at the start.
  - Checker: `score_phase0.py` computes the result and Ahmed signs it off in `decision.md`.
- **STT gate (proposal):**
  - Samples: 10 utterances × 2 speakers (Ahmed plus one other, ideally a different gender or age) = 20 samples. They are spoken into the minimal agent through the dashboard or the widget. The prompt tells the agent to answer only `تمام`, which keeps TTS minutes low. Transcripts are taken from the agent's own conversation transcripts, because a batch Scribe run on recorded WAVs uses a different model from the realtime agent ASR. A batch run is fine as a secondary, re-runnable check.
  - Suggested utterances. Product names must come from the draft catalog.
    1. بكم الصحون الزجاج؟
    2. عندكم كاسات ورق؟ (alias → أكواب ورق)
    3. أبي ثلاث علب مناديل (quantity + product)
    4. رقمي صفر خمسة خمسة، واحد اثنين ثلاثة، أربعة خمسة ستة سبعة (phone)
    5. وين وصل طلبي؟ رقمه إم جي أربعة ثمانية اثنين واحد (order ID)
    6. أبي توصيل للمبرز بكرة العصر (area + time slot)
    7. متى تفتحون يوم الجمعة؟
    8. أبي أكلم موظف
    9. عندكم plastic containers؟ (code-switch, E11)
    10. Do you deliver to Hofuf? (English, E10)
  - **GO** if all four hold:
    - (a) Product entities: ≥ 7 of 8 product-bearing samples identify the intended product, as Ahmed judges it, through the name or a catalog alias.
    - (b) Quantities and digits: 100% of quantities correct. Phone digit accuracy ≥ 95% across both phone samples, with at least 1 of 2 exact. The read-back in §8 step 3 mitigates the rest.
    - (c) Order-ID digits exact in both samples. The letters may come back as `MG`, `ام جي` or `إم جي`.
    - (d) Intent recoverable from the transcript in ≥ 18 of 20 samples. This includes both English samples, which must be transcribed in English or as recognizable transliteration.
  - **RETRY** (once, timebox 30 min) using the agent's ASR options, for example the Scribe v2 Realtime toggle the vendor says is available in Advanced settings (https://elevenlabs.io/blog/scribe-v2-realtime-in-elevenlabs-agents). Keyword boosting or a custom vocabulary is **UNVERIFIED**. Check the docs before relying on it.
  - **NO-GO** otherwise.
  - Checker: `score_phase0.py`, with Ahmed confirming the entity judgments.
- **Fallback trigger (must be split, see finding 3):**
  - STT no-go → Vapi with Azure STT `ar-SA`.
  - TTS no-go → a different TTS, for example Azure `ar-SA-ZariyahNeural` / `ar-SA-HamedNeural`, after a 3-clip re-rating.
  - Both fail → stop and re-scope with Ahmed.
- **Without the key (Claude can do now):**
  - the TTS script, STT sheet, expected-entity annotations, rating CSV template with the randomization seed, and `score_phase0.py` with unit tests on fake data
  - the gate definitions, `docs/STATUS.md`, `.env.example` with names only (`ELEVENLABS_API_KEY`, `TOOL_SECRET`, the judge LLM key)
  - the minimal agent prompt text
  - CLI install and `--help` capture at a pinned version
  - draft trap items for the catalog
  - **No** voice IDs and no agent JSON fields until they are checked against the real CLI output.
- **Needs the key and a human:**
  - account and plan purchase (Ahmed; this is a payment, so Ahmed does it)
  - `elevenlabs auth login` (opens a browser OAuth flow per the CLI docs) or the key in `.env`
  - adding voices from the Voice Library, synthesizing the 24 clips, pushing the agent
  - recording 20 STT samples, the 3 raters scoring, and Ahmed's sign-off

### Phase 1: Tools backend

- **Inputs:** §6–§7, the Phase 0 catalog draft, and Python 3.11+ on both machines.
- **Outputs:** `backend/`, seeded SQLite, tests, a tunnel script, and a tool-call JSON log.
- **Gate (automated; Ahmed re-runs it on the other machine):**
  - `pytest` green, with ≥ 15 Arabic variants in `test_arabic.py`.
  - The §7 money examples asserted exactly.
  - Phone grouped as 055 · 123 · 4567, and unit agreement (ثلاث علب, علبة وحدة).
  - 401 returned without `X-Tool-Secret` and 422 on an oversize `query`.
  - p95 latency under 300 ms over 100 local calls per tool (the §12 target).
  - From a second network, a `curl` through the tunnel returns 200 with the secret and 401 without it.
  - `make test`, or the equivalent, works from a fresh clone on the second OS.

### Phase 2: Prompt v1, agent, widget

- **Inputs:** a green Phase 1, the Phase 0 voice and model decision, and a stable tunnel URL (finding 8).
- **Outputs:** `prompts/system_v1.md`, agent config with 5 tools, `demo/index.html`, and `docs/flow.png` (or its Mermaid source).
- **Gate (Ahmed does the calls; Claude checks the database):**
  - 3 voice orders in a row through `demo/index.html`: 1 pickup, 1 delivery, 1 with a mid-call correction.
  - Each creates the right SQLite row with `conversation_id` filled in, a spoken read-back before `create_order`, and an order ID read digit by digit.
  - A `get_product` call for an out-of-stock item is spoken as unavailable.
  - The CLI's dry-run shows no drift between git and the platform (`elevenlabs agents push --dry-run`, per https://elevenlabs.io/docs/agents-platform/operate/cli).
  - The voice-minute count is logged.

### Phase 3: Eval suite and v1

- **Inputs:** a green Phase 2, the judge LLM key, 10 printed call cards (not yet defined anywhere, see finding 9), and scheduled callers.
- **Outputs:** `evals/*`, `results/v1/` (summary CSV, per-scenario JSON, tool logs, transcripts with no audio), and a critical-flag list.
- **Gate (Ahmed signs off):**
  - 20 scenarios × N repeats, with N ≥ 3 recommended (finding 10), completed in text simulation.
  - 10 real-call transcripts fetched and joined to their tool logs.
  - 100% of critical flags and 100% of the real calls have a human verdict recorded in the results.
  - Judge-vs-human agreement on the real calls is reported as a number.

### Phase 4: v2

- **Inputs:** the v1 results and Ahmed's approval of the fix list.
- **Outputs:** `system_v2.md`, ≥ 5 `CHANGELOG.md` entries, `results/v2/`.
- **Gate:**
  - Each changelog entry cites a scenario ID and a before → after metric.
  - Same suite, same N, same cards, same models as v1. A script checks the config hash.
  - v2 critical grounding failures = 0. If not, one v2.1 iteration is allowed, timeboxed to 1 h. After that the remaining failures are reported honestly.
  - No critical dimension regresses relative to v1.

### Phase 5: Ship

- **Outputs:** README, `QA_REPORT.md`, `docs/architecture.png`, `docs/flow.png`, video link.
- **Gate:**
  - Fresh-clone setup on the other OS reaches a green `make test`.
  - Every number in the README and QA report is checked by script against `summary.csv`.
  - The video is 60–90 s and contains an order, an edge case and the results table.
  - A secrets scan of git history is clean, and no audio is in the repo.
  - The demo-data disclaimer is present.
  - Twilio only after all of that.

**Critical path:** API key and plan → Phase 0 raters → Phase 2 (voice + tunnel) → Phase 3 real calls (family availability) → Phase 4 real calls again → Phase 5 video. Phase 1 is off the critical path (finding 7).

---

## B. Findings

### 1. [blocker] §11 and §3 lost in export: no gate exists for any phase
- **Problem:** The plan's main control is "no phase starts until the previous gate passes", and CLAUDE.md says "stop at each acceptance check". Neither the gates nor the hour budget per phase exist in the repo, and §3, the architecture diagram, is gone too. Each Claude Code session will make up its own acceptance check, which is exactly the "never invent" failure the plan forbids.
- **Evidence:** plan.md line 385, `[embedded content: delivery plan · 6 phases, 20 hours, a gate after each]`, and line 56.
- **Fix:** Re-export §11 and §3 from the original doc if possible. Otherwise adopt section A as the new §11 and write it into `specs/` and `docs/STATUS.md`. Gates should be pass/fail and machine-checkable where possible, with a named human checker.

### 2. [blocker] The Phase 0 go/no-go has no criteria
- **Problem:** "a go/no-go on dialect quality" with no raters, scale, threshold, entity list or sample size is not a gate. With the key missing, the risk is that Phase 0 gets "passed" by impression.
- **Evidence:** plan §11 prose, §12 row 1 ("try 3+ voices"), and the §14 Phase 0 prompt. None of them defines pass/fail.
- **Fix:** Use the TTS and STT gates in section A: blind 3-rater MOS ≥ 3.8 plus 100% number intelligibility, and entity accuracy (7 of 8 products, 100% quantities, ≥ 95% phone digits, exact order-ID digits). Run STT through the agent's realtime transcripts, not batch STT. Record the result in `docs/phase0/decision.md`. Phase 0 cannot pass today: there is no key, and no result may be faked.

### 3. [major] The fallback stack does not fix a TTS failure, and the claim that "only the adapter changes" is false
- **Problem:** The §4 fallback is Vapi + Azure STT `ar-SA` + **ElevenLabs** TTS `eleven_multilingual_v2`. If Phase 0 fails on TTS dialect, the fallback keeps the same vendor's voices, so it fixes nothing. Switching to Vapi also replaces things that are ElevenLabs-specific in this plan:
  - the CLI config-as-code (`agent/`)
  - the platform simulation and agent tests (§9 step 1)
  - `fetch_transcripts.py` (the ElevenLabs API)
  - the `<elevenlabs-convai>` widget
  - the conversation-ID linkage

  That is 3–4 hours the 20-hour budget does not have.
- **Evidence:** plan §4 line 75. Azure lists `ar-SA` for STT and the neural TTS voices `ar-SA-ZariyahNeural` and `ar-SA-HamedNeural` (https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts). Vapi accepts `ar-SA` for its Azure transcriber (https://docs.vapi.ai/providers/transcriber/azure). Where the language code goes in Vapi's config is **UNVERIFIED** from that page.
- **Fix:** Split the trigger. STT failure → Vapi + Azure `ar-SA` STT. TTS failure → re-rate Azure `ar-SA` voices (or another vendor) with the same Phase 0 protocol. Write a fallback impact list (the adapters for config, sims, transcript fetch and widget) and a +3–4 h contingency, paid for from the cut list in finding 5.

### 4. [major] The 60 call-minute budget cannot hold 10 real calls × 2 versions plus a demo
- **Problem:** §10 gives 20 minutes to real calls, which is 20 calls (10 cards × v1 and v2) at 1 minute each. A full order call has 7 steps, one question at a time, a read-back, a digit-by-digit phone repeat and a digit-by-digit order ID. That is realistically 2.5–4 minutes. Status and price calls take about 1 minute. A realistic mix averages about 2 minutes, so about 40 minutes for real calls alone. Phase 0's 20 STT samples plus the TTS synthesis also strain a 10-minute spike, and development gets only 20 minutes for Phase 2's end-to-end debugging. A realistic total is about 100–110 voice minutes.
- **Evidence:** the ElevenLabs Agents pricing page shows Free 15 min, Starter 75 min ($6/mo, $1 the first month), Creator 275 min ($22/mo, $11 the first month), extra minutes $0.08 each, and LLM billed separately "based on usage" (https://elevenlabs.io/pricing/agents, fetched 2026-10-27). Whether the agent-testing "Simulation" tests use call minutes or only LLM cost is **UNVERIFIED**; neither the testing docs nor the pricing page say (https://elevenlabs.io/docs/eleven-agents/customization/agent-testing).
- **Fix:** Re-baseline to about 110 minutes (spike 15, development 30, real calls 45, demo 15, slack 5). On Starter, the ~35-minute overage costs about $3 at the listed rate, so the money is small; the real risk is a hard stop on the Free tier. Ahmed picks Starter or Creator before Phase 0. In Phase 0, run one simulation test and read the usage counter to settle the billing question. Log minutes in `docs/STATUS.md` after every phase.

### 5. [major] 20 hours for D1–D6 has no buffer and leaves human time out
- **Problem:** Phase 3 alone builds 6 artifacts: scenarios, rubric, sims runner, transcript fetcher, judge and scorer. It also runs 20 or more simulations, coordinates 10 human calls and reviews flags, which realistically takes 6–6.5 hours. The 20 hours does not count rater time, caller time, flag review or fix approval (about 5 hours of humans), and it assumes zero rework and no fallback. "Five days" also says nothing about which day each phase lands.
- **Evidence:** reasoning from §9 and §14. The deliverables table lists 6 deliverables, and 3 of them (D2 README, D5 report, D6 video) all fall in the last 2 hours.
- **Fix:**
  - Adopt the realistic column (23 h) plus a 3 h fallback contingency, or pre-approve these cuts in order: (1) Twilio stretch dropped; (2) real calls cut to 6 cards × 2 versions; (3) N = 1 repeat instead of 3; (4) Lucidchart replaced by Mermaid; (5) architecture image drawn as Mermaid.
  - Day plan: Day 1 Phase 0 plus Phase 1 start; Day 2 Phases 1–2; Day 3 Phase 3 build and sims; Day 4 real calls round 1, review, Phase 4; Day 5 real calls round 2, Phase 5, video.

### 6. [major] Several deliverables are in no phase prompt: the video, `flow.png`, `architecture.png`, Makefile, `.env.example`
- **Problem:** D6 (the demo video, 60–90 s) is only referenced as a "video link" in the Phase 5 README prompt, and nothing schedules recording or editing it. §8's Lucidchart flow (`docs/flow.png`) and `docs/architecture.png` are in no phase prompt either. The §5 Makefile targets (`dev | test | tunnel | push-agent | eval | report`) and `.env.example` have no owner, and the README "results table" depends on a script nobody is asked to write.
- **Evidence:** the §14 prompts table (lines 456–461) against §1 D1–D6 and §5.
- **Fix:** Phase 2 owns the flow diagram, the Makefile skeleton and `.env.example`. Phase 5 owns the architecture diagram, the video (script, record, upload, link) and a `score.py --readme` table generator. Add these to the gates in section A.

### 7. [major] Strict serialization plus the missing API key stalls the project
- **Problem:** The rule is "no phase starts until the previous gate passes", and Phase 0 cannot pass without a key and raters. That idles Phase 1, even though §4 says the backend is platform-neutral ("The tools backend and eval suite stay unchanged" under the fallback). The plan's own logic allows Phase 1 to run in parallel.
- **Evidence:** plan §4 line 75 and §11 line 383. Today there is no key on the laptop.
- **Fix:** Allow Phase 1, and the offline parts of Phase 3 such as the scenarios YAML, the rubric, and judge/score code tested on fixtures, to start while the Phase 0 gate waits on human input. Keep the hard serialization only for Phases 2, 3-run and 4. The user asked to stop at the Phase 0 gate this session, so this is a recommendation for the next sessions, and Ahmed decides.

### 8. [major] The Mac/laptop split breaks the tunnel, the agent config and the logs
- **Problems:**
  - (a) A `cloudflared` quick tunnel gets a new random hostname on every start ("The hostname changes each time you create a Quick Tunnel"), and it has no uptime guarantee (https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/). The 5 webhook tool URLs in the agent config therefore change every session and must be re-pushed. If the Mac sleeps during family calls, they fail.
  - (b) CLI auth is per machine: an OS keyring, or `ELEVENLABS_API_KEY` in `.env` (per the CLI docs). Both machines pushing one remote agent leads to config drift.
  - (c) SQLite `*.db` is git-ignored, and the tool-call JSON log is local. If the logs that `judge.py` joins on `conversation_id` are not committed under `results/`, they are lost when switching machines.
  - (d) The §14 setup is Mac-only (`brew`, `source .venv/bin/activate`). Git Bash on Windows has no `make` by default.
  - (e) Whether the conversation ID reaches the webhook automatically is **UNVERIFIED**. The `conversation_id?` field in `create_order` depends on it.
- **Fix:**
  - Use a named Cloudflare tunnel with a fixed hostname (this needs a Cloudflare account and domain, Ahmed's call), or template the base URL from `.env` into tool configs and make re-push one command.
  - Make one machine, the Mac, the agent-push owner, and always `agents pull` before a push.
  - Commit sanitized tool logs and transcripts into `results/`.
  - Write task runners as Python scripts, with the Makefile as a thin wrapper, and document Windows equivalents.
  - Verify how the conversation ID is passed (a dynamic or system variable) in the Phase 2 docs check.
  - Disable sleep on the Mac during call sessions.

### 9. [major] The human dependencies (raters and callers) are unscheduled and the call cards are undefined
- **Problem:** Phases 0, 3 and 4 need 2–3 family members at least 3 times: Phase 0 rating, v1 calls and v2 calls. The "10 call cards" are not defined. The §9 table has 20 scenarios and nothing says which 10 become cards. Callers also need fake identities (name, fake phone) on the cards, according to §10.
- **Evidence:** §9 step 2 and the §10 Data bullet.
- **Fix:** Phase 3's first output is the 10 card subset: at least H1, H2, H5, H6, E3, E5, E6, E10 or E11, E12 and E14, each with a fake name and fake 05XXXXXXXX number. Book 3 sessions with family now. Make the same callers do the same cards for v1 and v2.

### 10. [major] The v1 → v2 comparison is statistically weak and confounded
- **Problem:** 20 LLM-simulated scenarios run once is noisy: one flip moves task success by 5 points, and the target is ≥ 85%, or 17 of 20. The LLM caller is non-deterministic. If the LLM, voice or tool code changes between runs, the delta isn't attributable to the prompt.
- **Evidence:** the agent-testing docs describe `repeat_count` (2–20) for probabilistic pass rates (https://elevenlabs.io/docs/eleven-agents/customization/agent-testing). The older simulate-conversation endpoints are marked deprecated in favour of the Simulation test type (https://elevenlabs.io/docs/eleven-agents/guides/simulate-conversation). §9's "use the platform's built-in simulation" should target the non-deprecated test type.
- **Fix:** Use N ≥ 3 repeats per scenario and report pass rates with counts. Freeze and hash the LLM, voice, TTS model, tools code and judge model for both runs. Report real calls and simulations separately, as §9 already asks. Build on the Simulation / Tool Call test types, not the deprecated endpoints.

### 11. [minor] The Phase 0 STT sheet needs catalog names that are only created in Phase 1
- **Problem:** STT entity accuracy has to be measured on the product names and aliases the catalog will actually use, especially the §6 traps (near-duplicate pairs, shelf-vs-common names). `products.json` is a Phase 1 output.
- **Fix:** Draft the trap items and their aliases in Phase 0. This is fake demo data, so it is allowed. Phase 1 completes the 30 items around them.

### 12. [minor] The TTS model and LLM picks are not pinned, and the agent default may not be the model you test
- **Problem:** The ElevenLabs help center says new agents default to **Eleven v4 Turbo**, and that agents support "every language supported by the text to speech model your agent uses" (https://elevenlabs.io/docs/help-center/product/eleven-agents/which-languages-can-i-use-with-eleven-agents). The languages page lists Arabic for Flash v2.5, Multilingual v2 and Eleven v3. Arabic support for v4 Turbo is **UNVERIFIED** there (https://elevenlabs.io/docs/help-center/other/what-languages-do-you-support.md). Rating clips made with one model while the agent runs another invalidates Phase 0. The LLM is "Gemini Flash / Claude Haiku class" and not pinned either.
- **Fix:** Phase 0 records the exact TTS model ID, voice settings, ASR setting and LLM ID used by the agent. The clips must be made with that exact combination. Any later change to these re-opens the TTS gate.

### 13. [minor] Lucidchart is an outside dependency with free-tier limits
- **Problem:** It needs an account. The free plan is commonly reported as 3 editable documents and 60 objects per document, with connectors and text counting toward that. This is **UNVERIFIED** against an official Lucid page; the sources are third-party, e.g. https://community.lucid.co/product-questions-3/free-plan-restrictions-122. A flow with branches, escalation and correction loops can hit 60 objects. The diagram is also not diffable in git.
- **Fix:** Keep a Mermaid `docs/flow.mmd` as the source of truth (it renders on GitHub and works on both machines), and export to `flow.png`. Use Lucidchart only if Ahmed wants it shown for the Sarj application, and as the last item.

### 14. [minor] The judge-LLM key and cost are missing from the secrets and budget
- **Problem:** `judge.py` uses LiteLLM against some provider, but §10 budgets only ElevenLabs minutes. The judge key isn't in the `.env` list, and the model and its cost are unpinned.
- **Fix:** Add `JUDGE_MODEL` and the provider key name to `.env.example`. Pin the model in Phase 3. Estimate cost as runs × tokens before running, and log it.

### 15. [minor] Scope-creep guardrails are fine, but "stretch after Phase 5" conflicts with §11
- **Problem:** §11 says Twilio is "in Phase 5 only after every gate is green", while §12 says stretch items come "only after Phase 5 is done". In a 5-day window either reading competes with the video.
- **Fix:** Twilio is post-gate-5 only, after the video is published and linked. Make it a separate optional Phase 6 with no hours in the 20.

### 16. [minor] The success-metric targets are not tied to gates
- **Problem:** §1 says "Targets guide the work". That is honest, but it means only grounding = 0 is a hard requirement in practice. Without a stated rule, Phase 4 could loop on the ≥ 85% task success target indefinitely.
- **Fix:** Grounding critical failures = 0 and "no order without confirmation" = 0 are hard gates, with one 1-hour v2.1 retry. All other targets are reported, not gated.

---

## C. Coverage check of D1–D6 against the phases

| Deliverable | Covered by | Gap |
|---|---|---|
| D1 live widget order | Phase 2 | Gate "works end to end" is vague. Fixed by 3 consecutive DB-verified orders |
| D2 public repo + README | Phase 5 | Architecture image and video link have no producing phase (finding 6) |
| D3 v1→v2 + CHANGELOG | Phases 2, 4 | OK |
| D4 eval suite, v1 + v2 | Phases 3, 4 | Call cards undefined (finding 9); noise (finding 10) |
| D5 QA_REPORT | Phase 5 | Needs a script check of numbers against `summary.csv` |
| D6 demo video | none | Not in any phase (finding 6) |

## D. Sources used

- ElevenLabs Agents pricing: https://elevenlabs.io/pricing/agents (fetched 2026-10-27)
- ElevenLabs CLI: https://elevenlabs.io/docs/agents-platform/operate/cli
- ElevenLabs agent testing: https://elevenlabs.io/docs/eleven-agents/customization/agent-testing
- Deprecated simulate-conversation guide: https://elevenlabs.io/docs/eleven-agents/guides/simulate-conversation
- Agent languages and default model: https://elevenlabs.io/docs/help-center/product/eleven-agents/which-languages-can-i-use-with-eleven-agents
- TTS model languages: https://elevenlabs.io/docs/help-center/other/what-languages-do-you-support.md
- Scribe v2 Realtime in Agents: https://elevenlabs.io/blog/scribe-v2-realtime-in-elevenlabs-agents
- Azure Speech language support (STT and TTS `ar-SA`): https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support
- Vapi Azure transcriber: https://docs.vapi.ai/providers/transcriber/azure
- Cloudflare quick tunnels: https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/
- Lucid free-plan limits (third-party, unverified): https://community.lucid.co/product-questions-3/free-plan-restrictions-122

All thresholds in section A are proposals for Ahmed to accept or change. They are review judgments, not measured facts.
