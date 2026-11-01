# Phase 0 decision — signed 2026-11-01 (started 2026-10-28)

Filled step by step during Phase 0b (`phase0/README.md`). Final: signed by Ahmed 2026-11-01.

TTS gate: **GO by Ahmed's decision (2026-10-28), 1 rater instead of 3.** R1 (Ahmed) blind ratings, seed 4821:
  A/eleven_v4_turbo mean 4.38, numbers 5/5 · A/eleven_flash_v2_5 mean 4.25, numbers 5/5
  (`docs/phase0/tts_ratings_R1.csv`, scored by `phase0/tts_score.py`, which reports INCOMPLETE for 1 rater).
  Ahmed waived raters R2/R3 and chose eleven_v4_turbo. Risk: no second Saudi / Al-Ahsa ear on the voice;
  re-open the TTS gate if callers in Phase 2–3 call the voice non-Saudi (R1 noted clip 010 sounded non-Saudi).
STT gate: **PASS — single-provider run accepted by Ahmed (2026-11-01)**; S2 waived by Ahmed (2026-11-01);
  `stt_score.py --waive-speaker S2 --allow-single-provider` → STT GATE: PASS (G.3 counts scaled to 1 speaker, rounded up).
  Second provider not possible: on 2026-11-01 the API kept `scribe_realtime` when pushed `scribe_v2_turbo`
  (CLI 1.7.1 enum value, silently not stored) and rejected `elevenlabs` («Original ASR has been removed …
  Use 'scribe_realtime' instead»). `scribe_realtime` is the only Agents ASR provider.
  S1 (Ahmed, iPhone mic, 2026-11-01) on `scribe_realtime`: one call `conv_4001m6bfswbefw7byfw9bq2j8bqr`, 10 cards
  (`conv_id#n` rows in `docs/phase0/stt_results.csv`). 8/10 cards fully right; entity accuracy 83.3%, intent 9/10.
  Misses: #5 phone heard «05587834567» (one extra digit; the paired form «خمسة وخمسين، ثمانية وسبعين»);
  #10 «الهفوف» heard «للفوف» (retakes: «للحفوف») → candidate for `asr.keywords`.
  Scorer override on #3: «اثناعشر» = 12 (stt_score.py does not parse the one-word spelling).
  Earlier attempts on the Mac mini (Bluetooth WH-1000XM5 mic) returned empty «...» turns and were discarded.
Winner: voice_id=FZeLZd39ejvLgzR2gY0t (Nora S - Saudi Natural & Calm) model_id=eleven_v4_turbo stability=0.5 similarity_boost=0.8 speed=1.0
asr.provider=scribe_realtime (only option)  asr.keywords=none  LLM=gemini-2.5-flash  CLI=@elevenlabs/cli 1.7.1  SDK=elevenlabs 2.74.1
Blind seed: 4821 (16 clips: voice A = Nora S `FZeLZd39ejvLgzR2gY0t` × eleven_v4_turbo, eleven_flash_v2_5 × 8 lines; 674 characters)   Raters: R1 Ahmed (R2/R3 waived)   STT speakers: S1 Ahmed (S2 waived)
Plan: started on Free, upgraded to **Starter** on 2026-10-28 for Nora S (`free_users_allowed=False`). After the
upgrade `user subscription get` shows tier starter, 40,000 character limit, 10 voice slots. Key scoped to
Text to Speech, Voices (write), User, ElevenAgents (write).
Usage: characters 0 (free, then 0 / 40,000 on Starter) -> 136 / 40,000 read right after the 16 clips (the
counter lags or bills under 1 credit per character; re-read before signing) -> 6,250 / 40,000 on 2026-11-01 (all Phase 0 TTS, calls and the simulation); call minutes UNVERIFIED
(the subscription response has no Agents-minute field); conversation durations sum to 290 s = 4.8 min over 5 probe calls (budget 10); simulations bill minutes: **no call minutes, but credits** — the step-8 simulation
(test `test_3901m61c8shjex3semfgc18jadpd`, run `trun_4001m61c8xqff8r8snb70n526v1g`, 3 turns, config
`agent/test_configs/phase0_simulation.json`) reported credits_used 199 = platform 60 (text_message ×4) +
LLM 139 (simulated user and judge on claude-sonnet-4-6, agent on gemini-2.5-flash); free_minutes_consumed 0.
Result: passed (no price given, Saudi Arabic only). Note: one agent turn began with a literal «[أبشروا]» tag;
check in Phase 2 whether TTS speaks bracketed text
Voice slots: 0 used; the library voice worked in TTS without being added to My Voices (settles that UNVERIFIED item). Library voices with `free_users_allowed=False` cannot be used on this plan.
Thresholds confirmed by Ahmed: yes, as proposed in plan-review §G.2–G.3, except (a) has no English part
(project is Arabic only, 2026-10-28). TTS lines 2–4 register: approved as written. Trap item #3: أكياس زبالة → أكياس نفايات.
UNVERIFIED items settled (2026-10-28, `agents push` 1.7.1 + GET /v1/convai/agents/{id}):
- push creates agents from id-less configs: **yes** (Sara `agent_8601m61c0e71fyca17s7cvytjs8s`, probe `agent_0401m61c0gnxfvkaa3g0ky765ryb`)
- ids written to agents.json: **yes**
- language ar + eleven_v4_turbo accepted: **yes** (read back: language ar, tts eleven_v4_turbo, asr scribe_realtime, llm gemini-2.5-flash)
- voice while voice_id is absent: platform default `cjVigY5qzO86Huf0OWal` (not the Saudi voice; replaced by the TTS winner)
- library voice must be in My Voices for TTS: **no** (Nora S clips worked without adding)
Sara's prompt (system_v0.md) changed before the push: the English-reply line became Arabic-only.
Signed: Ahmed Ghazi, 2026-11-01 (in chat: «Accept and sign»)

Phase 2 carry-overs: Sara reads back every phone number (STT #5 added a digit); add الهفوف and the
catalog names to `asr.keywords` and re-check card 10; watch for bracketed tags like «[أبشروا]» being spoken;
re-open the TTS gate if callers say the voice sounds non-Saudi.
