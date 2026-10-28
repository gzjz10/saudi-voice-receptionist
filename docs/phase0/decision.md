# Phase 0 decision — in progress (started 2026-10-28)

Filled step by step during Phase 0b (`phase0/README.md`). Nothing below is final until signed.

TTS gate: **GO by Ahmed's decision (2026-10-28), 1 rater instead of 3.** R1 (Ahmed) blind ratings, seed 4821:
  A/eleven_v4_turbo mean 4.38, numbers 5/5 · A/eleven_flash_v2_5 mean 4.25, numbers 5/5
  (`docs/phase0/tts_ratings_R1.csv`, scored by `phase0/tts_score.py`, which reports INCOMPLETE for 1 rater).
  Ahmed waived raters R2/R3 and chose eleven_v4_turbo. Risk: no second Saudi / Al-Ahsa ear on the voice;
  re-open the TTS gate if callers in Phase 2–3 call the voice non-Saudi (R1 noted clip 010 sounded non-Saudi).
STT gate: not run yet
Winner: voice_id=FZeLZd39ejvLgzR2gY0t (Nora S - Saudi Natural & Calm) model_id=eleven_v4_turbo stability=0.5 similarity_boost=0.8 speed=1.0
asr.provider=<...>  asr.keywords=<...|none>  LLM=gemini-2.5-flash  CLI=@elevenlabs/cli 1.7.1  SDK=elevenlabs 2.74.1
Blind seed: 4821 (16 clips: voice A = Nora S `FZeLZd39ejvLgzR2gY0t` × eleven_v4_turbo, eleven_flash_v2_5 × 8 lines; 674 characters)   Raters: R1 Ahmed, R2 <city only>, R3 <city only>   STT speakers: S1 Ahmed, S2 <relation only>
Plan: started on Free, upgraded to **Starter** on 2026-10-28 for Nora S (`free_users_allowed=False`). After the
upgrade `user subscription get` shows tier starter, 40,000 character limit, 10 voice slots. Key scoped to
Text to Speech, Voices (write), User, ElevenAgents (write).
Usage: characters 0 (free, then 0 / 40,000 on Starter) -> 136 / 40,000 read right after the 16 clips (the
counter lags or bills under 1 credit per character; re-read before signing) -> <final>; call minutes UNVERIFIED
(the subscription response has no Agents-minute field) -> <after>; simulations bill minutes: **no call minutes, but credits** — the step-8 simulation
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
Signed: <Ahmed, date>
