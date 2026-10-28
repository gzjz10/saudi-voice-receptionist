# STATUS — Saudi Voice Receptionist

**Phase 0 gate: OPEN — waiting for API key and raters.**

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
| 3 independent blind raters (Ahmed + 2 native Saudi, ≥ 1 Al-Ahsa), 1–5 scale + number y/n | BLOCKED-human |
| Best pair mean ≥ 4.0, every rater ≥ 3.0 on it, all number lines right → GO | not evaluated |
| RETRY (3.5–3.99, once, 45 min) / NO-GO (< 3.5 or a number line wrong on all voices) / Azure fallback | not evaluated |

### 0b — STT gate (reviews §G.3)

| Criterion | State |
| --- | --- |
| Minimal agent pushed (`language: ar`, answers «تمام») | BLOCKED-key |
| 20 clips (10 × S1 Ahmed + S2) spoken live, per provider; 2 providers | BLOCKED-key + BLOCKED-human (S2) |
| Transcripts from `GET /v1/convai/conversations/{id}` (realtime ASR) | BLOCKED-key (`--fetch` never run live) |
| (a) ≥ 18/20 intents | not evaluated |
| (b) product ≥ 5/6 · (c) qty 2/2, order id 2/2 · (d) ≤ 2/40 phone digits wrong, ≥ 2/4 exact · (e) #7 #8 #9 all 2/2 | not evaluated |
| RETRY (30 min: provider switch + `asr.keywords`) / NO-GO → Vapi + Azure ar-SA STT | not evaluated |

### 0b — also required

| Item | State |
| --- | --- |
| One Simulation test; does it bill minutes? | BLOCKED-key, UNVERIFIED |
| `docs/phase0/decision.md` with LLM, asr.provider, tts.model_id, voice_id, settings, CLI 1.7.1, seed, minutes | BLOCKED (0b output) |
| Ahmed signs `decision.md`; STATUS updated with minutes | BLOCKED-human |

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
