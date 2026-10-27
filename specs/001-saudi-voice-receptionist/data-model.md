# Data Model: Saudi Voice Receptionist "Sara"

**Feature**: `specs/001-saudi-voice-receptionist` | **Date**: 2026-10-27 | **Plan**: [plan.md](plan.md)

Sources: spec Key Entities, `plan.md` §6, review amendments 3–6 and M12–M13. All data is fake demo
data (constitution IV). Field constraints are written so tasks can quote them verbatim.

Two groups of entities:

- **Phase 0 entities** (A). Files only, written in 0a (templates) and filled in 0b.
- **Product entities** (B–D). Built from Phase 1 on.

---

## A. Phase 0 entities (files under `docs/phase0/`)

The exact column contracts and the scoring CLI are in
[contracts/phase0-artifacts.md](contracts/phase0-artifacts.md).

### A1. TtsLine (`docs/phase0/tts_script.md`)

| Field | Type | Constraint |
| --- | --- | --- |
| `line_no` | int | 1–8, unique |
| `purpose` | enum | `greeting`, `price`, `total`, `total_over_100`, `phone`, `order_id`, `clarification`, `escalation_close` |
| `text_ar` | string | exact string `spoken.py` will emit; one Saudi colloquial register; plural address |
| `is_number_line` | bool | true for lines 2–6 only |
| `expected_number` | string | lines 2–6: `9.75`, `17.25`, `117`, `0551234567`, `4821`; empty otherwise |

Lines 2–4 are **pending Ahmed's register sign-off** (spec FR-053). The file carries a
`register_signed_off: no` header until he signs.

### A2. SttUtterance (`docs/phase0/stt_sheet.md` + `docs/phase0/stt_results.csv`)

| Field | Type | Constraint |
| --- | --- | --- |
| `utt_no` | int | 1–10, unique |
| `text` | string | exact text the speaker reads (UTF-8); #10 is English |
| `intent` | enum | `price`, `availability`, `order_item`, `give_phone`, `order_status`, `delivery_request`, `hours`, `escalate` |
| `expected_entities` | map | keys from: `product`, `product_alias`, `qty`, `phone`, `order_id`, `area`, `slot`, `day`, `language` |
| `scored_dimensions` | list | which gate rule (a)–(e) the utterance feeds |

Product clips are #1–#3, phone clips #4–#5, the order-id clip is #6, and the English clip is #10.

### A3. VoiceCandidate (`docs/phase0/voice_selection.md` §2 table, IDs filled in 0b only)

| Field | Type | Constraint |
| --- | --- | --- |
| `slot` | enum | `A`, `B`, `C` (retry adds `D`–`F`) |
| `voice_id` | string | **copied only from an API response**; never typed from memory; empty in 0a |
| `name` | string | as returned by the API |
| `accent`, `gender`, `use_case` | string | as returned by the API; `gender` must be female |
| `source_command` | string | the exact CLI command that returned it |
| `retrieved_at` | ISO 8601 | Asia/Riyadh |

### A4. BlindKey (`phase0/samples/blind_key.csv`; copied to `docs/phase0/clip_key.csv` after rating)

| Field | Type | Constraint |
| --- | --- | --- |
| `seed` | int | the recorded shuffle seed; same on every row |
| `blind_id` | string | numeric blind label `<nnn>` |
| `voice_label` | enum | `A`…`F` |
| `voice_id` | string | from `docs/phase0/voice_selection.md` §2 (API-sourced) |
| `model_id` | string | `eleven_v4_turbo`, `eleven_flash_v2_5`, or (retry only) `eleven_v3_conversational` |
| `line` | int | 1–8 |
| `file` | string | clip path under `phase0/samples/` |

### A5. TtsRating (`docs/phase0/tts_ratings.csv`)

| Field | Type | Constraint |
| --- | --- | --- |
| `rater_id` | enum | `R1` (Ahmed), `R2`, `R3`; no real names |
| `blind_id` | string | a `blind_id` in BlindKey (the on-disk header and `phase0/tts_score.py` use this name) |
| `naturalness` | int | 1–5 (1 foreign/broken, 2 MSA newsreader, 3 Gulf-ish with obvious errors, 4 Saudi receptionist with a slip, 5 indistinguishable from native) |
| `number_correct` | enum | `y` / `n` on number lines (2–6), empty otherwise |
| `note` | string | optional, ≤ 200 chars |

Unique key: (`rater_id`, `blind_id`).

### A6. SttResult (logical fields; stored in `docs/phase0/stt_results.csv`, see contracts/phase0-artifacts.md §3)

| Field | Type | Constraint |
| --- | --- | --- |
| `pass` | enum | `p1` (default provider), `p2` (alternative), `retry` |
| `asr_provider` | string | value actually set in `sara.json` for that pass |
| `utt_no` | int | 1–10 |
| `speaker_id` | enum | `S1` (Ahmed), `S2` |
| `conversation_id` | string | from the platform; never invented |
| `intent_ok` | enum | `y` / `n` |
| `language_ok` | enum | `y` / `n` / empty; #7 must stay Arabic, #10 must be English |
| `product_ok` | enum | `y` / `n` / empty (#1–#3 only) |
| `qty_heard` | string | digits, #3 only |
| `orderid_digits_heard` | string | digits, #6 only |
| `phone_digits_heard` | string | digits, #4–#5 only |
| `area_ok`, `slot_ok`, `day_ok` | enum | `y` / `n` / empty |
| `escalation_ok` | enum | `y` / `n` / empty (#9) |
| `checked_by` | enum | `R1` |

The 0a sheet stores these as `asr_provider`, `id`, `speaker`, `conversation_id`, `transcript_heard`,
`entities_correct`, `intent_ok` and `notes`. The per-entity fields above are what
`phase0/stt_score.py` derives. Raw `transcript_heard` text follows the tasks T038 privacy decision.

### A7. Phase0Decision (`docs/phase0/decision.md`)

The fields come from FR-012, plus the outcomes:

- `tts_verdict` ∈ {`GO`, `GO_WITH_RISK_FLAG`, `RETRY`, `NO_GO`}
- `stt_verdict` ∈ {`GO`, `RETRY`, `NO_GO`}
- `fallback_triggered` ∈ {`none`, `tts`, `stt`, `both`}
- `llm_id`, `asr_provider`, `tts_model_id`, `voice_id` and `voice_settings` (stability,
  similarity_boost, speed)
- `cli_version` (1.7.1) and `minutes_used` (read from the usage counter)
- `simulation_bills_minutes` ∈ {`yes`, `no`, `unknown`}
- `signed_by` (Ahmed) and `signed_at`

**State transitions** (gate): `OPEN` → (0b scored) → `GO` | `GO_WITH_RISK_FLAG` | `RETRY` → (one
retry) → `GO` | `GO_WITH_RISK_FLAG` | `NO_GO` → (NO_GO) `FALLBACK_EVAL` → `GO` | `STOP`. Only
the output of `phase0/tts_score.py` and `phase0/stt_score.py` plus Ahmed's signature may move it
out of `OPEN`.

### A8. StatusFile (`docs/STATUS.md`)

Fields: `phase`, `gate` (e.g. "Phase 0 gate: OPEN — waiting for API key and raters"), `blockers[]`,
`minutes_used` (blank until read from the platform), `last_updated`, `machine`. The 0a value is
fixed by the gate text.

---

## B. Catalog and store (Phase 1; trap items drafted in 0a)

### B1. Product (`data/products.json`, 30 items)

| Field | Type | Constraint |
| --- | --- | --- |
| `id` | string | `^(KIT|CLN|PLA|GFT|STA)-\d{3}$`, unique, stable |
| `name_ar` | string | display name; never normalized |
| `aliases_ar` | string[] | how callers say it, incl. broken plurals and dialect words; **no alias shared by two products; no bare category word** |
| `category` | enum | `kitchen`, `cleaning`, `plastics`, `gifts`, `stationery` |
| `price_halalas` | int | one of `575`, `975`, `1475` (fixed-price theme) |
| `in_stock` | bool | exactly 2 items `false` |
| `unit` | string | singular unit, e.g. حبة / علبة / طقم |
| `unit_dual_ar` | string | e.g. علبتين |
| `unit_plural_ar` | string | e.g. علب |
| `unit_gender` | enum | `m`, `f` |
| `trap` | enum? | `out_of_stock`, `near_duplicate`, `shelf_vs_common`, or absent |

Derived internally: `match_key` (normalized), which is never stored over `name_ar`.

Trap set: 2 out-of-stock items; the pairs صحون زجاج / صحون بلاستيك and أكواب ورق / أكواب زجاج;
and 3 shelf ≠ common-name items, one of them used in STT utterance 3. The 0a draft is in
`docs/phase0/catalog_traps.md`.

### B2. StoreProfile (`data/store.json`)

- `store_name_ar` and `store_name_en`: pending FR-073; default fictional.
- `hours`: `{sat_thu: {open, close}, fri: {open, close}}` in Asia/Riyadh `HH:MM`.
- `location_ar` and `map_url`.
- `delivery`: `{areas_ar: string[], fee_halalas: int, min_order_halalas: int}`.
- `returns_ar` and `phone` (non-real).
- `time_windows`: `{morning, noon, afternoon, evening, night}`, each `{from, to, spoken_ar}`.
- `demo_disclaimer_ar`: «نسخة تجريبية، الأسعار غير حقيقية».

---

## C. Transactional (SQLite, Phase 1)

### C1. Quote (`quotes` table, new per amendment 6)

| Column | Type | Constraint |
| --- | --- | --- |
| `quote_id` | TEXT PK | server-generated, opaque |
| `conversation_id` | TEXT | from `system__conversation_id`; nullable only in tests |
| `body_json` | TEXT | `{items:[{product_id, qty}], fulfillment, area?, time_slot}` as received |
| `lines_json` | TEXT | `[{product_id, name_ar, qty, qty_spoken_ar, unit_price_halalas, line_total_halalas}]` |
| `subtotal_halalas` | INTEGER | ≥ 0 |
| `delivery_fee_halalas` | INTEGER | 0 for pickup |
| `total_halalas` | INTEGER | subtotal + fee |
| `below_minimum` | INTEGER (bool) | delivery only |
| `created_at` | TEXT | ISO 8601, Asia/Riyadh |

A quote is side-effect free toward orders and immutable once written.

### C2. Order (`orders` table; replaces `plan.md` §6 DDL per amendments 4 and 6)

| Column | Type | Constraint |
| --- | --- | --- |
| `order_id` | TEXT PK | **4 numeric digits**, unique (`^\d{4}$`) |
| `created_at` | TEXT | ISO 8601, Asia/Riyadh |
| `customer_name` | TEXT | 1–40 chars |
| `phone` | TEXT | normalized `^05\d{8}$` |
| `fulfillment` | TEXT | `pickup` \| `delivery` |
| `area` | TEXT | required when `delivery`; must be in `store.delivery.areas_ar` |
| `slot_date` | TEXT | `YYYY-MM-DD` resolved server-side |
| `slot_window` | TEXT | key of `store.time_windows` |
| `items_json` | TEXT | `[{product_id, qty, unit_price_halalas}]`, qty 1–20 |
| `total_halalas` | INTEGER | copied from the quote |
| `status` | TEXT | `received`, `preparing`, `ready`, `out_for_delivery`, `delivered`, `cancelled`; default `received` |
| `quote_id` | TEXT | FK → quotes |
| `conversation_id` | TEXT | from `system__conversation_id` |
| — | UNIQUE | (`conversation_id`, `quote_id`) → idempotency |

Seed: 3 orders, one per status group, with phones in an obviously fake pattern (e.g. `0500000001`).

**State transitions**: `received → preparing → ready → (out_for_delivery → delivered | delivered)`,
and any state except `delivered` → `cancelled`. Only the seed script changes status. Tools never
update or delete rows.

### C3. Ticket (`tickets` table)

| Column | Type | Constraint |
| --- | --- | --- |
| `ticket_id` | TEXT PK | server-generated |
| `created_at` | TEXT | ISO 8601, Asia/Riyadh |
| `reason` | TEXT | `asked_for_human`, `angry`, `not_understood`, `cancel_request`, `other` |
| `summary` | TEXT | 1–300 chars |
| `customer_name` | TEXT? | ≤ 40 |
| `phone` | TEXT? | normalized `^05\d{8}$` if given |
| `conversation_id` | TEXT | from `system__conversation_id` |

### C4. ToolCallLog (JSON lines, `backend/logs/tool_calls.jsonl`, git-ignored)

The fields are `ts`, `tool`, `conversation_id`, `request_body` (no headers),
`status`, `error_code`, `latency_ms` and `http_status`. Header values are never logged.

---

## D. Evaluation (Phase 3–4)

### D1. Scenario (`evals/scenarios.yaml`)

- `id` (e.g. `H1`, `E13`, `N1`…) and `type` (`happy` | `edge`).
- `mode` (`sim` | `voice` | `both`) and `split` (`dev` | `holdout`, fixed before v1).
- `persona`, `caller_goal` and `script_hints[]`.
- `expected_tools[]` (with argument assertions), plus `must_say_re[]` and `must_not_say_re[]`
  (normalized regex).
- `pass_criteria`.

E7–E9 are `voice` only.

### D2. RunMetadata (`evals/results/<version>/run.json`)

`agent_config_sha`, `llm_model_id`, `voice_id`, `tts_model_id`, `asr_provider`, `catalog_sha`,
`simulator_model`, `judge_config_sha`, `k`, `started_at`, `cli_version`.

### D3. RunResult (`evals/results/<version>/summary.csv` + per-scenario JSON)

- Key: scenario × repeat.
- Verdicts per rubric dimension: `pass` / `fail` / `na`, or a count or percentage.
- `judge_verdict`, `human_verdict` (which overrides), `critical_flags[]`.
- Summary rows: pass rate, Wilson 95% CI and pass^k per dimension.

### D4. CallCard (`evals/call_cards/*.md`)

10 cards (H1, H2, H5, H6, E3, E5, E6, E10/E11, E12, E14) with a fake name and an obviously fake
phone (`0500000001`…). The same cards and callers are used for v1 and v2.
