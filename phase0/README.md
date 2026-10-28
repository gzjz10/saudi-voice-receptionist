# Phase 0 runbook — dialect go/no-go on the Mac Mini

For Ahmed. Phase 0a (offline files) is done on the Windows laptop; this file takes you through
Phase 0b on the Mac with the API key and the raters. The gate is `reviews/plan-review.md` §G; the
live status is `docs/STATUS.md`. Nothing below is a result until a real API call or a real human
score produces it.

Rule of the phase: **never write a voice ID, score or minute count that did not come from the API
response, the raters' sheets or the usage counter.**

## Files

| File | Role |
| --- | --- |
| `agent/agent_configs/sara.json` | minimal Arabic agent (persona, no tools) |
| `agent/agent_configs/sara_stt_probe.json` | STT probe agent: same settings, answers only «تمام» |
| `agent/validate_configs.py` | offline config check against the CLI 1.7.1 schema |
| `docs/phase0/tts_script.md` | the 8 gate lines (Ahmed signs off register of lines 2–4) |
| `docs/phase0/voice_selection.md` | how the 3 female Saudi/Gulf voices are chosen, rating form |
| `phase0/find_voices.py` | voice library search; the only source of voice IDs |
| `phase0/tts_samples.py` | 48 clips + blind shuffled copies + key |
| `docs/phase0/tts_ratings.csv` | raters' sheet (template, header only) |
| `phase0/tts_score.py` | TTS gate verdict (G.2) |
| `docs/phase0/stt_sheet.md`, `docs/phase0/stt_results.csv` | 10 utterances × 2 speakers, cards, result columns |
| `phase0/stt_score.py` | STT gate verdict (G.3), `--fetch` transcripts, `--add-run` |
| `docs/phase0/catalog_traps.md` | draft trap items the sheet depends on |
| `phase0/test_phase0.py` | offline checks on fake data (`pytest` or plain `python`) |
| `docs/phase0/decision.md` | **written in 0b**, signed by Ahmed |

## Budget

- **Call minutes: ≤ 10 for all of Phase 0** (plan.md §10 gives the spike 10 of ~60–110).
  40 STT calls (20 clips × 2 providers) must average ≤ 12 s each (hang up right after «تمام») = 8 min,
  plus one Simulation test (~1 min; whether simulations bill minutes is UNVERIFIED, see step 9).
  Read the usage counter before and after and write both numbers into `decision.md`.
- **Characters:** 2,022 for the 48 clips (`tts_samples.py --dry-run`). Starter shows 30,000
  credits/month (https://elevenlabs.io/pricing, read 2026-10-27); Flash/Turbo v2.5 cost 0.5–1
  credit/character via API, the v4 cost per character is **UNVERIFIED**. A RETRY round adds up to
  ~2,000 more.
- **People:** Ahmed; 2 native Saudi raters (≥ 1 from Al-Ahsa), ~20 min each; 1 extra STT speaker
  (S2, different gender or age), ~10 min.

## Step 0 — resume on the Mac (no key yet)

```bash
git clone https://github.com/gzjz10/saudi-voice-receptionist.git ~/Desktop/saudi-voice-receptionist
cd ~/Desktop/saudi-voice-receptionist
cat docs/STATUS.md                       # must still say the gate is OPEN
python3 --version                        # 3.12
python3 -m venv .venv && source .venv/bin/activate
pip install -r phase0/requirements.txt   # elevenlabs 2.74.1, python-dotenv 1.2.4, pytest 8.4.2
(cd agent && npm ci)                     # @elevenlabs/cli 1.7.1 (never bare `npx elevenlabs` without this)
python phase0/test_phase0.py             # or: python -m pytest phase0/test_phase0.py -q
python agent/validate_configs.py         # OK x3
```

If `pip install` fails or the SDK's method names changed, stop and say so; do not patch the
scripts to guess.

## Step 1 — confirm inputs (Ahmed, human)

1. Read `docs/phase0/tts_script.md`. Fix the register of lines 2–4 if a Hasawi receptionist would
   say them differently, then set `register_signed_off: yes`. If you change a line, also change
   `LINES` in `phase0/tts_samples.py` (the test keeps them equal).
2. Confirm or change every threshold in `reviews/plan-review.md` §G.2–G.3. They are proposals.
   If you change one, change the `GATE` dict at the top of `phase0/tts_score.py` /
   `phase0/stt_score.py` and note it in `decision.md`.
3. Read `docs/phase0/catalog_traps.md`; confirm «أكياس نفايات / أكياس زبالة» as the #3 trap item.

## Step 2 — plan and key (Ahmed, payment)

1. Buy the ElevenLabs **Starter** plan. Note the price and the credit and Agents-minute allowances
   you see at purchase; the pricing page did not state Starter's Agents minutes (UNVERIFIED).
2. Create an API key in the dashboard and put it in the repo-root `.env`:
   ```
   ELEVENLABS_API_KEY=<key>
   ```
   `.env` is git-ignored. Never paste the key into chat, a commit or a doc.
3. Check it and read the counters:
   ```bash
   cd agent && npx elevenlabs user subscription get && cd ..
   ```
   Write the starting character and minute usage into `docs/phase0/decision.md` (create it now
   from the template at the end of this file).

## Step 3 — find the 3 voices (key)

```bash
python phase0/find_voices.py                 # prints real accent values, then female ar voices
python phase0/find_voices.py --search "Heba" # leads named in docs/phase0/voice_selection.md
python phase0/find_voices.py --search "Hana"
python phase0/find_voices.py --search "Amal"
```

- Listen to the `preview_url`s. Shortlist 5, keep 3 **female** voices with a Saudi/Gulf accent label
  and Arabic in `verified_languages`; drop custom-rate voices (the script already does).
- Copy their IDs **from the script output** into the ID table of `docs/phase0/voice_selection.md`.
- If a voice needs to be in My Voices first (UNVERIFIED), `python phase0/find_voices.py --add <id> --name "Sara A"`.
- If the catalog leads are not found or are not female/Saudi, take the next-best API results and say
  so in `decision.md`. Do not keep a voice because a third-party site listed it.

## Step 4 — synthesize and blind the 48 clips (key, characters)

```bash
python phase0/tts_samples.py --dry-run                                # 48 clips, 2,022 characters
python phase0/tts_samples.py --voice A=<id> --voice B=<id> --voice C=<id> --blind --seed 4821
```

Output in git-ignored `phase0/samples/`: `A__eleven_v4_turbo__L01.mp3` …, `manifest.csv`,
`blind/001.mp3 … 048.mp3`, `blind_key.csv`. Use any seed, but write it in `decision.md`.
If `eleven_v4_turbo` rejects `language_code=ar`, rerun with `--no-language-code` and record that.

## Step 5 — rate (3 humans, ~20 min each)

- Give each rater **only** `phase0/samples/blind/` and the rating form in
  `docs/phase0/voice_selection.md` §5. They never see `blind_key.csv`, `manifest.csv` or the voice names.
- Each rater fills rows in `docs/phase0/tts_ratings.csv`: `rater_id` R1 (Ahmed), R2, R3;
  `blind_id` 001–048; `naturalness` 1–5 (1 foreign/broken · 2 MSA newsreader · 3 Gulf-ish with
  errors · 4 Saudi receptionist with a slip · 5 native); `number_correct` y/n on lines 2–6 only.
  Blind ids of number lines are known only from the key, so raters mark `number_correct` on every clip
  that contains a number; the scorer ignores it elsewhere.
- Alone, headphones, one pass, no replay discussion. Real names never go in the CSV.

```bash
python phase0/tts_score.py docs/phase0/tts_ratings.csv phase0/samples/blind_key.csv
```

| Verdict | Meaning | Next |
| --- | --- | --- |
| GO | best pair mean ≥ 4.0, every rater ≥ 3.0 on it, all number lines right by all raters | set `tts.model_id` + `voice_id` of that pair in both agent configs |
| RETRY | best mean 3.5–3.99 (or GO blocked by a rater/number rule) | **once, 45 min:** `tts_samples.py --stability 0.6 --speed 0.95` or `--similarity-boost 0.9`, ≤ 3 extra voices, `--model eleven_v3_conversational`; new blind set; re-rate; `tts_score.py --round retry` (≥ 4.0 GO · 3.8–3.99 GO_WITH_RISK_FLAG, write the flag into STATUS · < 3.8 NO_GO) |
| NO_GO | best mean < 3.5, or a number line wrong on every voice | **TTS fallback:** synthesize the same 8 lines with Azure `ar-SA-ZariyahNeural`, same raters and scale; pass → voice runtime becomes Vapi (+3–4 h); fail → stop and re-scope with Ahmed |

## Step 6 — push the agents (key)

```bash
cd agent
python ../agent/validate_configs.py --allow-voice-id    # after the winner is set; without flag before
npx elevenlabs agents push --dry-run
npx elevenlabs agents push --version-description "phase0 minimal arabic"
npx elevenlabs agents status                              # expect two agent ids
git status                                                # commit agents.json if push wrote ids into it
cd ..
```

UNVERIFIED and to be recorded: whether `push` creates agents from a config with no id; whether it
writes the ids into `agents.json`; whether `language: ar` is accepted with `eleven_v4_turbo`.
If the push fails, paste the exact error into `decision.md` and stop.

## Step 7 — STT clips: 20 per provider, two providers (key, ≤ 8 call-minutes)

1. Open the **STT probe** agent in the dashboard (Test agent) or the widget. It greets «هلا، تفضلوا»
   and answers only «تمام».
2. Print the cards in `docs/phase0/stt_sheet.md`. S1 = Ahmed reads cards 1→10, S2 reads 10→1.
   One call per card: wait for the greeting, read the card once, wait for «تمام», **hang up**
   (target ≤ 12 s per call). First take is the data; retake only if the call itself failed.
3. Write each `conversation_id` into the row in `docs/phase0/stt_results.csv`; set `asr_provider`
   on all 20 rows to the agent's actual value (`scribe_realtime` as configured).
4. Fetch transcripts (first live use of `--fetch`; check one by hand against the dashboard):
   ```bash
   python phase0/stt_score.py docs/phase0/stt_results.csv --fetch
   ```
   or `cd agent && npx elevenlabs agents conversations get --conversation-id <id>`.
5. Second provider: `python phase0/stt_score.py docs/phase0/stt_results.csv --add-run elevenlabs`
   (or `scribe_v2_turbo`), change `asr.provider` in `sara_stt_probe.json`, `agents push`, repeat 2–4.
6. Ahmed fills `intent_ok` (y/n: could a receptionist act on this transcript?) for every row; add
   `entities_correct` (`product=1;qty=0` form) only where the scorer is wrong. Delete anything in
   a transcript that is not the scripted card (a name, a side conversation) before committing.
7. Score:
   ```bash
   python phase0/stt_score.py docs/phase0/stt_results.csv
   ```

| Verdict | Next |
| --- | --- |
| PASS (best provider: (a) ≥ 18/20 intents, (b) ≥ 5/6 products, (c) qty 2/2 + order id 2/2, (d) ≤ 2/40 phone digits wrong + ≥ 2/4 exact, (e) #7, #8, #9 all 2/2) | record `asr.provider` winner in both agent configs |
| FAIL | **once, 30 min:** switch `asr.provider` to the third value, add product names to `asr.keywords`, re-run only the failing clips, re-score |
| still FAIL → NO-GO | **STT fallback:** Vapi + Azure `ar-SA` STT, keep ElevenLabs `eleven_flash_v2_5` TTS (+3–4 h). Both TTS and STT NO-GO → stop and re-scope |

## Step 8 — one Simulation test (key)

Run one simulation against the Sara agent from the dashboard (Tests) or
`npx elevenlabs agents tests --help` for the CLI route. Read `user subscription get` before and
after: if the minute counter moved, simulations bill minutes (write the answer in `decision.md`).

## Step 9 — decide and record

Create `docs/phase0/decision.md` with, at minimum:

```
# Phase 0 decision — <date>
TTS gate: GO | GO_WITH_RISK_FLAG | NO_GO   (paste tts_score.py output)
STT gate: PASS | FAIL | NO_GO              (paste stt_score.py gate block)
Winner: voice_id=<from API> model_id=<...> stability=<...> similarity_boost=<...> speed=<...>
asr.provider=<...>  asr.keywords=<...|none>  LLM=gemini-2.5-flash  CLI=@elevenlabs/cli 1.7.1  SDK=elevenlabs 2.74.1
Blind seed: <n>   Raters: R1 Ahmed, R2 <city only>, R3 <city only>   STT speakers: S1 Ahmed, S2 <relation only>
Usage: characters <before> -> <after>; call minutes <before> -> <after>; simulations bill minutes: yes|no
Thresholds confirmed by Ahmed: yes (changes: ...)
UNVERIFIED items settled: language ar + v4 turbo = ...; push creates agents = ...; ids written to agents.json = ...
Signed: Ahmed, <date>
```

Then update `docs/STATUS.md` (gate PASSED / FAILED, minutes used, risk flag if any), commit the
docs and CSVs (never `phase0/samples/` or recordings), push. **Phase 1 starts only after the gate is
PASSED and signed.** If the voice runtime switched to Vapi, say so in STATUS before Phase 1.

## Privacy

- Audio stays in `phase0/samples/` or `phase0/recordings/` (git-ignored) and is deleted after
  `decision.md` is signed.
- No real names or phone numbers in the repo: raters are R1–R3, speakers S1–S2; card numbers are fake.
- Each speaker/rater agrees to «أوافق على استخدام صوتي لاختبار تجريبي، ولن يُنشر التسجيل.» (kept off the repo).
- Delete the test conversations in the dashboard once the transcripts are in the CSV.
