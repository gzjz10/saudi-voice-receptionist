# Contract: Phase 0 artifacts and the gate scorers

**Feature**: `specs/001-saudi-voice-receptionist` | **Date**: 2026-10-27 (paths corrected by the
leader analysis the same day to the files the 0a run produced)

This file is the interface between the people who fill the Phase 0 sheets (Ahmed, raters, Claude
on the Mac) and the scoring scripts that decide the gate: `phase0/tts_score.py` (G.2) and
`phase0/stt_score.py` (G.3), with `scripts/score_phase0.py` as a thin wrapper (tasks T021). The
gate rules come from `reviews/plan-review.md` section G. Thresholds are proposals until Ahmed
confirms them (spec FR-008). After T021 both scorers read them from `docs/phase0/thresholds.json`,
so a change he makes is data, not code.

All CSV files are UTF-8 (no BOM), comma-separated, LF line endings, with a header row exactly as
below. Empty means "not applicable".

## 1. `docs/phase0/tts_ratings.csv` (template committed in 0a with the header only)

```
rater_id,blind_id,naturalness,number_correct,note
```

| Column | Rule |
| --- | --- |
| `rater_id` | `R1` (Ahmed), `R2`, `R3`; raters 2–3 are native Saudi, ≥ 1 from Al-Ahsa; no real names in git |
| `blind_id` | the `blind_id` from `phase0/samples/blind_key.csv` (numeric `<nnn>`, 001–048, as written by `phase0/tts_samples.py --blind`); retry and Azure-fallback rounds use their own key files |
| `naturalness` | integer 1–5 |
| `number_correct` | `y` or `n` when the clip's line is 2–6, empty otherwise |
| `note` | free text ≤ 200 chars, no commas unless quoted |

Each rater fills a separate copy (`docs/phase0/tts_ratings_R1.csv` …) blind, without seeing the
key. The three copies are concatenated (one header) into `docs/phase0/tts_ratings.csv` before
scoring; `phase0/tts_score.py` takes that one file plus the key.

## 2. Blind key: `phase0/samples/blind_key.csv` (written by `phase0/tts_samples.py --blind --seed N`)

```
seed,blind_id,voice_label,voice_id,model_id,line,file
```

The key comes from the 0a run's `tts_samples.py`; this contract adopts that format. It stays in
git-ignored `phase0/samples/` until all ratings are in. Then it is copied to
`docs/phase0/clip_key.csv` and committed (tasks T042). `voice_label` is the slot (A, B, C; retry
D–F). `line` is 1–8 from `docs/phase0/tts_script.md`, whose list format is `N. label: text`, as
parsed by `tts_samples.py --script`.

## 3. STT sheet and results: `docs/phase0/stt_sheet.md` + `docs/phase0/stt_results.csv` (written by the 0a run)

```
id,speaker,asr_provider,utterance,intent,critical_entities,acceptable_variants,speaker_notes,conversation_id,transcript_heard,entities_correct,intent_ok,notes
```

- 10 utterances × speakers S1/S2 = 20 rows per provider. `phase0/stt_score.py --add-run <provider>`
  appends 20 rows for the second provider. `asr_provider` holds the value actually set in
  `sara_stt_probe.json` for that pass (the template says `default`; replace it).
- `conversation_id` is written by the person running the session. `transcript_heard` is filled
  by `stt_score.py --fetch` from `GET /v1/convai/conversations/{id}` (`transcript[].message` where
  `role == "user"`; field names re-checked against the API reference on 2026-10-27, research R6).
  `entities_correct` and `intent_ok` are filled by the scorer and confirmed by Ahmed; human values
  win.
- **Utterance 5** reads «… ثلاثة أربعة خمسة ستة سبعة» (10 digits = 0557834567). This is an
  accepted correction of review G.1, whose wording had 9 digits.
- **Encoding**: the 0a file currently starts with a UTF-8 BOM. Save it without one (tasks T014);
  every reader already uses `utf-8-sig`.
- **Privacy**: `transcript_heard` is raw ASR text. Before committing a filled sheet, apply the
  T038 decision. The default is to move the filled copy to git-ignored `phase0/recordings/` and
  commit the sheet with that column blanked.

The entity rules (a)–(e) are the ones in §5 below. They are implemented in `phase0/stt_score.py`,
which reads its thresholds from `docs/phase0/thresholds.json` after T021 (today they are a
hard-coded `GATE` dict with the same values).

## 4. `docs/phase0/thresholds.json` (committed in 0a; values = review G proposals)

```json
{
  "status": "PROPOSED - not yet confirmed by Ahmed",
  "tts": {
    "go_mean": 4.0, "retry_low": 3.5, "risk_flag_low": 3.8, "min_rater_mean": 3.0,
    "number_lines": [2, 3, 4, 5, 6], "number_lines_all_correct": true
  },
  "stt": {
    "intent_min": 18, "intent_of": 20, "english_clips_must_be_english": true,
    "product_min": 5, "product_of": 6,
    "qty_exact": 2, "orderid_exact": 2,
    "phone_digit_accuracy_min": 0.95, "phone_exact_min": 2,
    "area_slot_min": 2, "hours_day_min": 2, "escalation_min": 2
  }
}
```

## 5. Scorer CLIs

Python ≥ 3.12, stdlib only. They run the same way on Windows Git Bash (`python`) and macOS
(`python3`) through `scripts/py.sh`.

| Command | Input | Output |
| --- | --- | --- |
| `python phase0/tts_score.py docs/phase0/tts_ratings.csv phase0/samples/blind_key.csv [--round initial\|retry]` | ratings + blind key + thresholds | per-pair table (mean, rater means, number lines) and one verdict line `TTS GATE (...): GO \| RETRY \| GO_WITH_RISK_FLAG \| NO_GO` |
| `python phase0/stt_score.py docs/phase0/stt_results.csv [--fetch] [--add-run <provider>]` | STT sheet + thresholds | per-provider rules (a)–(e) with value, threshold and pass, and one verdict line `STT GATE: PASS \| FAIL \| INCOMPLETE` (INCOMPLETE until two providers have 20 transcribed clips) |
| `python scripts/score_phase0.py tts \| stt` (T021 wrapper) | the same files | the same verdicts as JSON `{verdict, best_pair \| best_provider, …}` |

`--selftest` on either scorer runs synthetic data and prints "not a Phase 0 result".

**Verdict rules (encoded exactly; see review G.2–G.3)**

- TTS, round `initial`:
  - Pick the best (voice, model) pair by mean naturalness over its ratings.
  - `GO` if mean ≥ `go_mean`, every rater's mean for that pair ≥ `min_rater_mean`, and every
    number-line rating is `y`.
  - `NO_GO` if mean < `retry_low`, or if some number line has no pair where all raters said `y`.
  - Otherwise `RETRY`.
  - If the best pair's mean ≥ `go_mean` but its rater-mean or number rule fails, the script
    evaluates the next pair. If no pair passes, the verdict is `RETRY` when best mean ≥
    `retry_low`, else `NO_GO`. This tie-handling is our interpretation, and the review is silent
    on it, so Ahmed should confirm it with the thresholds.
- TTS, round `retry`:
  - `GO` at ≥ `go_mean` with the same rater and number rules.
  - `GO_WITH_RISK_FLAG` at ≥ `risk_flag_low`.
  - Otherwise `NO_GO`.
- STT, per provider. `GO` only if all hold:
  - (a) `intent_ok` = `y` on ≥ `intent_min` of 20, and both #10 rows have `language_ok` = `y`;
  - (b) `product_ok` = `y` on ≥ `product_min` of the 6 rows for #1–#3;
  - (c) `qty_heard` = `12` on both #3 rows, and `orderid_digits_heard` = `4821` on both #6 rows;
  - (d) phone digit accuracy = 1 − (Σ Levenshtein(expected, heard) / 40) ≥
    `phone_digit_accuracy_min`, and at least `phone_exact_min` of the 4 phone rows are exact.
    Expected values: #4 `0551234567`, #5 `0557834567`;
  - (e) `area_ok` and `slot_ok` = `y` on both #7 rows, plus `day_ok` and `intent_ok` on both #8
    rows, plus `escalation_ok` on both #9 rows.

  The best provider is the one that passes, or else the one with the most rules passing. The
  verdict is `GO` or `NO_GO` per pass, and pass `retry` re-scores only the re-run clips merged
  over p1/p2.
- The exit code is 0 for any computed verdict, 2 for invalid input (unknown label, bad value,
  duplicate key). The script never writes a verdict into `decision.md`. Ahmed copies it there and
  signs.

**Tests** (`phase0/test_phase0.py`; today 5 tests, extended by T020; any fixtures in
`phase0/tests/fixtures/fake_*.csv`):

- both `--selftest`s green; templates blank; `tts_ratings.csv` header-only (on disk);
- `phase0/tts_samples.py` `LINES` equal `docs/phase0/tts_script.md` (on disk);
- TTS GO, RETRY, NO_GO by mean, and NO_GO by a number line wrong on all pairs;
- a rater mean below 3.0 blocks GO;
- GO_WITH_RISK_FLAG after retry;
- STT GO, plus each of rules (a)–(e) failing on its own;
- English clips not in English fail (a);
- the Levenshtein phone accuracy boundary: 2 wrong digits pass, 3 fail;
- invalid input returns exit code 2;
- a changed `thresholds.json` changes the verdict.

Fixture files are clearly named `fake_*.csv` and use voice slots, never voice ids.

## 6. `agent/agent_configs/sara.json` and `sara_stt_probe.json` (Phase 0 profile)

Both files are hand-written in 0a. `sara.json` embeds `prompts/system_v0.md`; the probe answers
only «تمام». From Phase 1 they are generated by `scripts/build_agent_config.py`. They are
checked by:

1. `python agent/validate_configs.py` (0a run's validator). It reads enums and ranges from the
   pinned CLI's `agents create --spec`, so no schema dump is committed. In 0a mode `tts.voice_id`
   must be absent; from 0b on, run it with `--allow-voice-id`. Exit code 0 means valid.
2. `cd agent && npx elevenlabs agents push --dry-run` must exit 0 and print
   `[DRY RUN] Would update agent` (or the create equivalent) with no API call. This proves only
   JSON well-formedness and project readability (research.md R2.1).

Required values for the Phase 0 profile:

- `conversation_config.agent.language` = `"ar"`;
- no `tools` or `tool_ids`;
- the probe's prompt says to answer only «تمام»;
- `platform_settings.privacy.retention_days` = 30;
- `platform_settings.call_limits.daily_limit` = 20;
- `platform_settings.call_limits.agent_concurrency_limit` = 2;
- `conversation_config.tts.voice_id` is **omitted** in 0a, so no voice id at all is written before
  0b. The `minimal` template's default id is not a candidate and is not kept. If validation turns
  out to require the field, the gap is reported at the 0a gate, not filled. The real id is set in
  0b from `docs/phase0/voice_selection.md` §2 (the review F table calls this file `voices.md`;
  `voice_selection.md` is the one on disk and carries both the procedure and the ID table).
- Observed 0a values (both files, validator OK): `agent.language` `ar`, `prompt.llm`
  `gemini-2.5-flash`, `asr.provider` `scribe_realtime` (schema default, written out),
  `tts.model_id` `eleven_v4_turbo`, `tts.stability` 0.5, `similarity_boost` 0.8, `speed` 1.0,
  `text_normalisation_type` `system_prompt`, `conversation.max_duration_seconds` 240.
