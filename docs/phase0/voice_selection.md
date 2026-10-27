# Phase 0 — voice selection procedure and candidates for سارة

Target voice: a young, warm, **female** Saudi receptionist (Najdi or general Gulf/"white" Saudi), natural on numbers, on a phone/web call. The gate rules are in `reviews/plan-review.md` §G.2. This file supplies the candidates, the starting settings, the listening script and the rating form.

**Status (2026-10-27): no voice ID is recorded here.**

- Voice IDs are written only from the output of `phase0/find_voices.py`, run on the Mac with a key.
- Third-party catalogs below show IDs in their page URLs. Those IDs are deliberately not copied, and their per-voice pages are not linked.

## 1. How the three are chosen (0b, needs key)

1. Run `python phase0/find_voices.py`.
   - It calls `voices.accents.get(language="ar")` and prints the accent values the API really accepts.
   - It then searches `voices.get_shared(language="ar", gender="female", accent=<each Saudi/Gulf-like value>, use_cases="conversational", include_custom_rates=False)`.
   - It drops any voice with a `fiat_rate` (custom rate) and prints ID, accent, age, use case, verified Arabic models and preview URL.
2. Look up the public leads below by name with `python phase0/find_voices.py --search "<name>"`.
3. Shortlist 5 by listening to the `preview_url`s, using the criteria below. Keep 3. Copy their IDs from the script output into the table in section 2.
4. If the API requires it (UNVERIFIED), add each one to My Voices with `python phase0/find_voices.py --add <voice_id> --name "Sara <A|B|C>"`.
5. Generate the clips:
   ```bash
   python phase0/tts_samples.py --voice A=<id> --voice B=<id> --voice C=<id> --blind --seed <n>
   ```
   This makes 48 clips (3 voices × `eleven_v4_turbo`, `eleven_flash_v2_5` × 8 lines). Before spending credits, check the character count with `--dry-run`: 2,022 characters for 48 clips.

**Selection criteria (all required, then ranked):**

- Gender female; accent label Saudi or Gulf; Arabic in `verified_languages` for at least one of the two test models.
- Use case conversational or customer service, not narration, news or audiobook. Narrator voices drift to MSA.
- No custom rate (`fiat_rate` null). `free_users_allowed` is recorded, not required, since we buy Starter.
- Preview sounds under about 35 and warm, with a moderate pace. No whisper, heavy breathiness or radio-announcer tone.
- Rank by preview impression first, then by `cloned_by_count` (more use means fewer surprises).

## 2. Candidates

All three are leads found in public third-party catalogs of the ElevenLabs voice library. None is confirmed by an official ElevenLabs source.

- Labels such as "Saudi", "middle aged" and "conversational" are those catalogs' wording.
- **Every one must be re-found via the API.** If one does not appear, or is not female/Saudi/Gulf, replace it with the next-best API result.

| Slot | Name (as listed publicly) | Source (cited) | Accent (as listed) | Why it is a lead | Main risk |
| --- | --- | --- | --- | --- | --- |
| A | Heba Mansuri — "Arabic Customer Care" | json2video Arabic voice list, page 2: https://json2video.com/ai-voices/languages/arabic/?page=2 | Saudi; conversational; professional | Built for Arabic customer care. Described as "calm, trustworthy". Closest to a receptionist. | Listed as "middle aged", so it may sound older than the target. A second "Heba Mansuri — Gentle and Calm" entry exists on the same page. Confirm which one the API returns. |
| B | Hana — "Casual & Relatable" | json2video Arabic voice list, page 3: https://json2video.com/ai-voices/languages/arabic/?page=3 | Saudi "with a light Hijazi lilt"; conversational; casual | Described as warm with a "smile", which suits the friendliest persona. | Hijazi colour, not Najdi. Al-Ahsa raters may score it lower. Also "middle aged". |
| C | Amal — "Rich & Sophisticated" | Famulor, ElevenLabs voices with a Saudi accent: https://www.famulor.io/voices/elevenlabs/languages/ar/accents/saudi (the only female among the 15 listed); also on the json2video page 3 above | Saudi | The only female Saudi voice that two independent catalogs agree on. | "Sophisticated" may read as narrator/MSA. Use case not stated. |
| reserve | Layan — "The Professional" | json2video Arabic voice list, page 3 (URL above) | Saudi on the list page; its detail page states no accent | Professional female tone. | Accent unconfirmed. |

Fallback outside ElevenLabs (only on TTS NO-GO, G.2): Azure `ar-SA-ZariyahNeural`, the Saudi female neural voice. https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support

**Voice ID fields (filled in 0b from `find_voices.py` output only):**

| Slot | voice_id | public_owner_id | accent (API) | age (API) | use_case (API) | verified Arabic models (API) |
| --- | --- | --- | --- | --- | --- | --- |
| A | | | | | | |
| B | | | | | | |
| C | | | | | | |

## 3. Models and starting settings

All three voices start with **the agent's exact settings** from `agent/agent_configs/sara.json`. The gate requires the rated clips to match what the agent will play.

| Setting | Start (all voices) | Source | Why |
| --- | --- | --- | --- |
| model | `eleven_v4_turbo` and `eleven_flash_v2_5`, both rated | https://elevenlabs.io/docs/overview/models: v4 Turbo "~100ms", recommended for Agents; Flash v2.5 "~75ms", "real-time voice agents" | The two Arabic-capable low-latency agent models. `eleven_v3_conversational` (~280 ms) is tried only in the RETRY step. `eleven_turbo_v2_5` is deprecated in the spec. |
| stability | 0.5 | agent spec default (range 0–1) | Balanced: lower risks odd prosody on digits, higher sounds flat. |
| similarity_boost | 0.8 | agent spec default (0–1) | Keeps the voice's own Saudi accent. The plain TTS API default is 0.75, so the agent value is passed explicitly. |
| style | 0.0 | TTS API default; the agent TTS config has no `style` field | Must be 0 so the clips equal the agent's output. |
| speed | 1.0 | agent spec default (0.7–1.2) | A neutral baseline for rating. |
| language_code | `ar` (`en` for line 9) | TTS API reference (ISO 639-1) | Sent for v4 Turbo and Flash v2.5. Whether the agent sends the same is UNVERIFIED. |

**RETRY step only** (best mean 3.5–3.99, one 45-minute attempt, G.2):

- If digits sound unclear, try stability 0.6 and speed 0.95.
- If the accent drifts to MSA, try similarity_boost 0.9.
- These are starting hypotheses, not documented recommendations.
- Apply them with `tts_samples.py --stability … --similarity-boost … --speed …`. Copy the winning values into `sara.json`.

## 4. Listening script (fixed)

Lines 1–8 are the gate script (`reviews/plan-review.md` §G.1), exactly as `spoken.py` will emit them.

- Ahmed confirms or corrects the register of lines 2–4 before 0b.
- The same 8 lines live in `docs/phase0/tts_script.md`; any correction goes there and is used via `tts_samples.py --script docs/phase0/tts_script.md`.
- Line 9 is optional (`--with-english`) and is **not** part of the gate mean.

| # | Purpose | Text |
| --- | --- | --- |
| 1 | Greeting | هلا والله، معكم سارة من مقاضينا، كيف أقدر أخدمكم؟ |
| 2 | Price 9.75 | الصحون الزجاج بتسعة ريال وخمسة وسبعين هللة |
| 3 | Total 17.25 | المجموع سبعطعش ريال وخمسة وعشرين هللة |
| 4 | Total 117 | المجموع مية وسبعطعش ريال |
| 5 | Phone 0551234567, 3·3·4 | رقمكم صفر خمسة خمسة، واحد اثنين ثلاثة، أربعة خمسة ستة سبعة، صح؟ |
| 6 | Order id 4821 | رقم طلبكم أربعة، ثمانية، اثنين، واحد |
| 7 | Clarifying question (2 options) | تقصدون صحون زجاج أو صحون بلاستيك؟ |
| 8 | Apology + escalation + close | أعتذر منكم، بحوّلكم لموظف يتواصل معكم، شكراً لاتصالكم |
| 9 | English (optional, not gated) | Thanks for calling Maqadeena. How can I help you today? |

## 5. Rating form

**Raters:** Ahmed plus 2 native Saudi speakers, at least 1 from Al-Ahsa (minimum 2 raters per the task; the gate needs 3).

**Procedure:**

- Each rater works alone with headphones.
- They hear `phase0/samples/blind/001.mp3 … 048.mp3` in that order.
- They see only the blind id, never the voice, model or `blind_key.csv`.
- Write the seed in `decision.md`.

**Per clip (gated).** Saudi naturalness uses the G.2 scale:

- 1 = foreign/broken
- 2 = MSA newsreader
- 3 = Gulf-ish with obvious errors
- 4 = Saudi receptionist with a slip
- 5 = indistinguishable from a native speaker

| Rater | blind_id | Saudi naturalness (1–5) | Heard the right number? (Y/N, lines 2–6 only) | Notes (word that sounded wrong) |
| --- | --- | --- | --- | --- |
| | 001 | | | |
| | … | | | |
| | 048 | | | |

**Per voice × model (not gated, used to break ties and pick among GO pairs).** Fill this in after unblinding. Score 1–5 each.

| Rater | Voice | Model | Saudi-ness | Naturalness | Clarity of numbers | Warmth | Would you call this store again? (Y/N) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| | A | eleven_v4_turbo | | | | | |
| | A | eleven_flash_v2_5 | | | | | |
| | B | eleven_v4_turbo | | | | | |
| | B | eleven_flash_v2_5 | | | | | |
| | C | eleven_v4_turbo | | | | | |
| | C | eleven_flash_v2_5 | | | | | |

Gated results (mean ≥ 4.0 over 24 ratings, no rater mean < 3.0, all number lines correct) are computed from `docs/phase0/tts_ratings.csv` joined with `phase0/samples/blind_key.csv` by `phase0/tts_score.py`. Nothing in this file is a result until real raters fill it in.

## 6. UNVERIFIED (settle on the Mac)

- The exact accent strings from `voices accents get`, for example whether "saudi" or "gulf"/"khaleeji" exists. The script prints them before searching.
- Whether `gender="female"` and `use_cases="conversational"` are the accepted filter values. The script retries without the use-case filter if it gets 0 results.
- Whether the catalog labels above ("Saudi", "middle aged", "conversational") match the official library entries.
- Whether a library voice must be added to My Voices before TTS or an agent can use it.
- The Starter character quota versus the 2,022 characters needed (G.2 already flags this), and the credit cost per character per model.
- Whether `eleven_v3_conversational` is accepted by the plain TTS endpoint (it is in the agent model enum). This is only needed for the RETRY step.
- Whether the agent sends `language_code` / `use_speaker_boost` the same way as `tts_samples.py`. The samples leave `use_speaker_boost` unset, so the API default applies.
