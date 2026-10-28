# Phase 0 decision — in progress (started 2026-10-28)

Filled step by step during Phase 0b (`phase0/README.md`). Nothing below is final until signed.

TTS gate: not run yet
STT gate: not run yet
Winner: voice_id=<from API> model_id=<...> stability=<...> similarity_boost=<...> speed=<...>
asr.provider=<...>  asr.keywords=<...|none>  LLM=gemini-2.5-flash  CLI=@elevenlabs/cli 1.7.1  SDK=elevenlabs 2.74.1
Blind seed: 4821 (16 clips: voice A = Nora S `FZeLZd39ejvLgzR2gY0t` × eleven_v4_turbo, eleven_flash_v2_5 × 8 lines; 674 characters)   Raters: R1 Ahmed, R2 <city only>, R3 <city only>   STT speakers: S1 Ahmed, S2 <relation only>
Plan: started on Free, upgraded to **Starter** on 2026-10-28 for Nora S (`free_users_allowed=False`). After the
upgrade `user subscription get` shows tier starter, 40,000 character limit, 10 voice slots. Key scoped to
Text to Speech, Voices (write), User, ElevenAgents (write).
Usage: characters 0 (free, then 0 / 40,000 on Starter) -> 136 / 40,000 read right after the 16 clips (the
counter lags or bills under 1 credit per character; re-read before signing) -> <final>; call minutes UNVERIFIED
(the subscription response has no Agents-minute field) -> <after>; simulations bill minutes: <yes|no>
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
