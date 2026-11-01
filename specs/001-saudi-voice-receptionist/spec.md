# Feature Specification: Saudi Voice Receptionist "Sara"

**Feature Branch**: `001-saudi-voice-receptionist` (spec directory name; no git branch is created,
work stays on `main`)

**Created**: 2026-10-27

**Status**: Draft

**Input**: User description: "Saudi-dialect voice receptionist 'Sara' for the Magadhina demo store
with tools backend, eval suite and QA report, per plan.md and reviews/plan-review.md"

**Sources**: `plan.md` (Technical Spec v1.0), `reviews/plan-review.md` (sections E-G override
`plan.md` where they conflict), `.specify/memory/constitution.md` v1.0.0.

## User Scenarios & Testing *(mandatory)*

Actors:

- **Caller**: a Saudi customer talking to Sara by voice on a web page. Sara speaks Arabic only.
- **Ahmed**: owner, builder, native-speaker reviewer, sign-off authority.
- **Raters**: Ahmed + 2 native Saudi speakers (at least 1 from Al-Ahsa) who score voice clips.
- **QA reviewer**: Ahmed acting on eval results, judge output and real-call transcripts.
- **Portfolio reader**: a hiring reviewer reading the public repo, report and video.

Priorities follow the gated delivery order: P0 must pass before any caller-facing story is built.

### User Story 0 - Dialect go/no-go before any code (Priority: P0)

Ahmed needs to know, before investing build hours, whether the hosted voice runtime can (a) speak
in a voice that native Saudi listeners rate as natural Saudi receptionist speech, including prices,
totals, phone numbers and order numbers, and (b) correctly hear Saudi dialect requests, product
names, quantities, phone digits and order ids. The outcome is a signed GO, GO WITH RISK FLAG, or
NO-GO that either confirms the voice runtime or triggers the defined fallback.

The story runs in two parts. **0a (offline, Windows laptop, today)** prepares every asset and
procedure with no API key. **0b (Mac Mini, needs API key, paid plan and humans)** produces real
voice candidates, clips, ratings, transcripts and the decision.

**Why this priority**: Saudi dialect quality is the project's top risk and its main selling point.
A failure changes the voice runtime, not the plan, so it must be known before backend or prompt
work is wired to a runtime.

**Independent Test**: 0a is tested by an offline config validation, a green scoring-script test
run on fake data, and the presence of the listed files with no voice ids, scores or minutes in
them. 0b is tested by the scoring script applied to real ratings and transcripts, and Ahmed's
signature on the decision record.

**Acceptance Scenarios**:

1. **Given** no API key on the laptop, **When** 0a is complete, **Then** a minimal Arabic agent
   definition (language Arabic, no tools, answers only «تمام») passes the platform CLI's offline
   validation without any network call to the voice platform.
2. **Given** 0a is complete, **When** the repo is inspected, **Then** it contains: an 8-line TTS
   script, a 10-utterance STT sheet with expected entities, a voice-selection procedure with no
   voice ids, empty TTS-ratings and STT-results templates, a scoring script with tests green on fake
   data, draft catalog trap items, an environment template with variable names only, and a status
   file reading "Phase 0 gate: OPEN — waiting for API key and raters".
3. **Given** a key exists on the Mac, **When** 3 female Saudi/Gulf conversational voices are
   found by the documented search procedure, **Then** their ids are recorded only as returned by
   the platform, and 3 voices × 2 synthesis models × 8 lines = 48 clips are produced with the exact
   voice settings the agent will use.
4. **Given** the 48 clips are blind-labelled and shuffled with a recorded seed, **When** 3 raters
   score them independently on the 1-5 Saudi naturalness scale (plus "heard the right number" on
   number lines), **Then** the scoring script reports GO / RETRY / NO-GO per the thresholds below.
5. **Given** the minimal agent is live, **When** 2 speakers speak the 10 utterances (20 clips) with
   the default speech-recognition provider and once more with one alternative provider, **Then**
   transcripts are taken from the agent's own conversation records (realtime recognition, not batch
   transcription) and scored on entities, not word error rate.
6. **Given** a TTS or STT NO-GO, **When** the fallback trigger fires, **Then** the defined fallback
   is evaluated (TTS: re-rate the fallback Saudi female voice with the same lines and raters; STT:
   switch recognition to the fallback runtime, keeping the passing synthesis voice); if both fail,
   work stops and scope is renegotiated with Ahmed.
7. **Given** 0b scoring is done, **When** Ahmed signs the decision record, **Then** it lists the
   chosen LLM id, recognition provider, synthesis model, voice id, voice settings, CLI version and
   call minutes used, and the status file is updated.

---

### User Story 1 - Caller gets a grounded answer about a product or the store (Priority: P1)

A caller asks in Saudi dialect about a product's price or availability (e.g. «بكم الصحون الزجاج؟
عندكم منها؟») or about the store (hours, Friday hours, location, delivery areas and fee, minimum
order, returns, phone) and hears a short, natural answer whose facts come only from the store's
data. Ambiguous names get one clarifying question with at most 2 options; unknown or unsold items
get one polite line and a redirect, never a price.

**Why this priority**: it is the smallest end-to-end slice that proves grounded, natural Saudi
speech, and it is reused by the order flow.

**Independent Test**: call the agent and ask about an in-stock item, an out-of-stock item, an
ambiguous name, a dialect alias, an item not in the catalog, an obviously unsold item («كم سعر
الآيفون؟») and Friday hours; compare every spoken fact with the store data.

**Acceptance Scenarios**:

1. **Given** an in-stock catalog item, **When** the caller asks its price, **Then** Sara says a
   short filler line, then the exact catalog price in spoken Arabic form.
2. **Given** an out-of-stock item, **When** the caller asks for it, **Then** Sara says it is
   unavailable and offers at most one alternative from the catalog.
3. **Given** a near-duplicate pair (صحون زجاج / صحون بلاستيك), **When** the caller says «صحون»,
   **Then** Sara asks one question offering exactly those 2 options.
4. **Given** a dialect alias (كاسات ورق → أكواب ورق), **When** the caller uses it, **Then** Sara
   resolves it to the right product.
5. **Given** a product the store does not sell, **When** the caller asks its price or insists on an
   estimate, **Then** Sara gives no number and redirects to what the store sells.
6. **Given** a store-info question, **When** the caller asks it, **Then** the answer matches the
   store profile exactly.

---

### User Story 2 - Caller places a pickup or delivery order by voice (Priority: P1)

A caller orders one or more items. Sara collects one thing per turn: items and quantities, name,
phone (repeated back digit by digit, grouped), pickup or delivery (with area checked against served
areas), and time slot. She then reads back items, quantities, the quoted total, fulfillment and
time, asks «تمام كذا؟», and only after a clear yes creates the order and reads the numeric order id
digit by digit.

**Why this priority**: it is deliverable D1 ("a caller completes a delivery order by voice, end to
end") and exercises every critical rubric rule.

**Independent Test**: three consecutive voice orders on the hosted demo page (one pickup, one
delivery, one with a mid-call correction) each produce the right stored order linked to its call,
a quote before creation, a spoken read-back and a digit-by-digit order id.

**Acceptance Scenarios**:

1. **Given** a caller with 2 items for delivery to a served area, **When** all fields are
   collected, **Then** Sara reads back the quoted total (including any delivery fee) and creates
   the order only after a clear yes.
2. **Given** a read-back, **When** the caller says no or corrects a quantity or phone, **Then** Sara
   returns to that step only, uses the corrected value, and repeats the full read-back.
3. **Given** an area that is not served or a total below the minimum, **When** the caller asks for
   delivery, **Then** Sara says so from store data and offers pickup or the served areas.
4. **Given** an out-of-stock item inside an order, **When** it is requested, **Then** it is not
   added and Sara says it is unavailable.
5. **Given** a created order, **When** the same confirmation is retried, **Then** no second order is
   created.
6. **Given** two items in one sentence, **When** the caller says them, **Then** both are captured.

---

### User Story 3 - Caller checks an order or reaches a human (Priority: P2)

A caller asks «وين وصل طلبي؟» and gives an order number or phone; Sara reads the status. A caller
who asks for a person, is angry twice, or is not understood twice is escalated: a ticket is created
and Sara reads a callback line. A cancel request is explained (Sara cannot cancel) and escalated.

**Why this priority**: common real calls and a required escalation path, but not needed to prove
the core order flow.

**Independent Test**: look up each seeded order by id and by phone, look up a non-existent id, and
trigger each escalation reason; check spoken status and stored tickets.

**Acceptance Scenarios**:

1. **Given** a seeded order, **When** the caller gives its id or phone, **Then** Sara says its
   status in Arabic (by phone: at most the 2 latest orders).
2. **Given** an unknown id, **When** the caller asks, **Then** Sara says it was not found and offers
   help, without guessing.
3. **Given** «أبي أكلم موظف», a second angry turn, or a second «ما فهمت», **When** it happens,
   **Then** a ticket with reason and summary is created and the callback line is spoken.

---

### User Story 4 - Non-Arabic speech and adversarial callers (Priority: P2)

Sara speaks Arabic only (Arabic only since 2026-11-01, Ahmed's decision of 2026-10-28): an English-only or mixed Arabic-English caller is answered in
simple Saudi Arabic and the language never switches. Prompt injection («انسى تعليماتك», or injected text in the name
field), discount requests and long silence are handled safely.

**Why this priority**: rule-level behaviour that the eval suite measures; failures here are
critical (disclosure) or major.

**Independent Test**: one mixed Arabic-English voice call, and scenario runs for injection,
discount and silence.

**Acceptance Scenarios**:

1. **Given** English-only caller turns, **When** Sara replies, **Then** she answers in simple Arabic
   and does not switch language.
2. **Given** a mixed Arabic-English request («أبي delivery للمبرز»), **When** Sara replies, **Then**
   she stays in Arabic.
3. **Given** an instruction to change role or reveal the prompt, **When** it is spoken or placed in
   a field, **Then** Sara stays in role and reveals nothing.
4. **Given** a discount request, **When** asked, **Then** Sara gives the fixed-price answer with no
   negotiation.
5. **Given** long silence, **When** the silence timeout passes, **Then** Sara prompts once, then
   closes politely.

---

### User Story 5 - QA reviewer measures v1 against a rubric (Priority: P2)

Ahmed runs a scenario suite (~26 simulated scenarios tagged sim/voice/both, split dev/holdout
before v1, each repeated k = 5 times, floor 3) plus 10 real voice calls from printed call cards,
scores each against the rubric, and reviews every critical flag and every real call by hand.

**Why this priority**: QA is the heart of the portfolio proof (D4), but it needs a working agent.

**Independent Test**: run the suite against v1 and confirm that per-scenario results, a summary
table with confidence intervals, frozen run metadata and a human-signed critical-flag list exist,
and that no raw transcript or audio is tracked by git.

**Acceptance Scenarios**:

1. **Given** v1 is live, **When** the suite runs, **Then** at least 20 simulated scenarios × k ≥ 3
   complete and results record pass rate with a 95% Wilson interval per dimension.
2. **Given** ~30 hand-labelled gold transcripts, **When** the automated judge is calibrated,
   **Then** a dimension is auto-scored only if agreement ≥ 0.9 and kappa ≥ 0.7; otherwise it is
   human-scored.
3. **Given** a critical flag or a real call, **When** results are final, **Then** each has a human
   verdict that overrides the judge.
4. **Given** real calls, **When** transcripts are fetched, **Then** only redacted excerpts are
   committed.

---

### User Story 6 - Findings become a measured v2 (Priority: P3)

Ahmed approves at least 5 fixes drawn from v1 findings; each is applied to v2 and logged with the
scenario that caused it; the same suite reruns under the same frozen conditions.

**Why this priority**: proves improvement (D3), only meaningful after v1 results exist.

**Independent Test**: CHANGELOG has ≥ 5 entries each citing a scenario id and before → after
metric; a hash check confirms identical suite, k, cards and frozen models between v1 and v2.

**Acceptance Scenarios**:

1. **Given** v2, **When** the suite reruns, **Then** grounding failures and orders without
   confirmation are 0 on dev and holdout (one 1-hour retry allowed, then report honestly) and no
   critical dimension regresses.

---

### User Story 7 - Portfolio reader sees the live demo, results and report (Priority: P3)

A hiring reviewer opens the public repo, reads the README (problem, architecture, setup on both
operating systems, results table, video link, demo-data note), tries the hosted demo page (when
enabled) with a visible demo banner, reads a weekly-style QA report, and watches a 60-90 s video.

**Why this priority**: packaging (D2, D5, D6); last in the gated order.

**Independent Test**: a fresh clone on the other operating system runs the test script green;
every number in README and QA report matches the results summary by script.

**Acceptance Scenarios**:

1. **Given** the final repo, **When** a reader compares README/report numbers with the results
   summary, **Then** they match exactly.
2. **Given** the demo page, **When** opened, **Then** it shows a banner that prices are not real and
   the first agent line says it is a demo.

### Edge Cases

- No API key, no paid plan or no raters: Phase 0 stays OPEN; nothing in 0b is recorded.
- Best TTS pair mean 3.5-3.99: one 45-minute retry (settings, ≤ 3 more voices, a third model);
  after retry 3.8-3.99 is GO WITH RISK FLAG written into the status file.
- Any number line heard wrong on every voice: immediate TTS NO-GO.
- STT fails on one provider only: one 30-minute retry with another provider plus product names as
  recognition keywords, re-running failing clips.
- Caller gives phone as paired numbers («خمسة وخمسين، ثمانية وسبعين») or with +966 / 966 prefix or
  Arabic-Indic digits: normalized to 05XXXXXXXX before use.
- Quantity ≥ 11 (e.g. «اثنعش»), invalid quantity (outside 1-20), unknown product id.
- Tool call times out or the public tunnel URL changed: Sara says she cannot check right now; tool
  URLs are re-rendered when the tunnel restarts.
- Caller interrupts during read-back (barge-in): handled and read-back resumed (voice-only test).
- Unclear speech twice: escalate.
- Request outside opening hours for a time slot: Sara says so from store data.
- Whether platform simulation tests consume call minutes is UNVERIFIED; checked once in 0b.
- Language detection is not used (Arabic only); the ASR provider is `scribe_realtime`, the only one
  the platform accepts (Phase 0b, 2026-11-01).

## Requirements *(mandatory)*

### Functional Requirements

**Phase 0 - dialect go/no-go (P0)**

- **FR-001**: Phase 0 MUST be split into 0a (offline, no key) and 0b (key, plan, humans); 0a MUST
  NOT write any voice id, score, transcript or minute count.
- **FR-002**: 0a MUST produce minimal Arabic agent definitions (Arabic language, no tools, no
  voice id) that pass the offline validation: a persona agent that speaks only the Phase 0 prompt,
  and a recognition probe that replies only «تمام» for the STT test. Both share the same language,
  recognition and synthesis settings.
- **FR-003**: 0a MUST produce an 8-line TTS script in one Saudi colloquial register, using the exact
  strings the backend will emit: greeting; price 9.75; total 17.25; total 117; phone 0551234567
  grouped 3·3·4; numeric order id 4821 digit by digit; a 2-option clarification; escalation +
  close (lines per review section G.1).
- **FR-004**: 0a MUST produce a 10-utterance STT sheet with expected entities per utterance (review
  G.1): glass plates price; paper cups via dialect alias; qty 12 of a trap item; phone grouped;
  phone in paired numbers; order id 4821; mixed Arabic-English delivery to المبرز tomorrow
  afternoon; Friday hours; ask for a human; English "Do you deliver to Hofuf?".
- **FR-005**: 0a MUST produce a voice-selection procedure (female voices, Saudi/Gulf accent,
  conversational use case, excluding custom-rate voices, shortlist 5 → keep 3) containing no voice
  ids, plus empty TTS-ratings and STT-results templates and a scoring script that computes the
  gate verdicts, tested on fake data only.
- **FR-006**: 0a MUST draft the catalog trap items: 2 out-of-stock items, 2 near-duplicate pairs
  (صحون زجاج / صحون بلاستيك; أكواب ورق / أكواب زجاج), 3 items whose common name differs from the
  shelf name, including the one used in STT utterance 3.
- **FR-007**: 0b MUST rate 3 voices × 2 synthesis models × 8 lines = 48 clips, blind-labelled and
  shuffled with a recorded seed, by Ahmed + 2 native Saudi raters scoring independently.
- **FR-008**: TTS GO MUST require the best (voice, model) pair to have mean ≥ 4.0 over its 24
  ratings, no rater mean for it < 3.0, and all its number lines judged correct by all raters;
  RETRY and NO-GO rules per Edge Cases and review G.2.
  [NEEDS CLARIFICATION: Ahmed must confirm the proposed Phase 0 thresholds in review section G
  (TTS mean ≥ 4.0 / retry band 3.5-3.99 / risk-flag band 3.8-3.99; STT ≥ 18/20 intent, ≥ 5/6
  product, 2/2 qty and order id, ≥ 95% phone digits) or set different ones before 0b runs.]
- **FR-009**: STT GO MUST require, on the best provider: intent recoverable in ≥ 18/20 clips with
  both English clips transcribed in English; product correct in ≥ 5/6 product clips; quantity 2/2
  and order-id digits 2/2; phone digit accuracy ≥ 95% over 4 clips (≤ 2 of 40 wrong) with ≥ 2/4
  exact; area + slot 2/2, hours/day 2/2, escalation 2/2.
- **FR-010**: On TTS NO-GO the fallback Saudi female voice MUST be re-rated with the same lines and
  raters; on STT NO-GO recognition MUST move to the fallback runtime while keeping the passing
  synthesis voice; both failing MUST stop work for re-scoping.
- **FR-011**: 0b MUST run one platform simulation test and read the usage counter to settle whether
  tests bill call minutes, and record it.
- **FR-012**: The Phase 0 decision record MUST be signed by Ahmed and list LLM id, recognition
  provider, synthesis model, voice id, voice settings, CLI version and minutes used.

**Conversation behaviour (P1-P2)**

- **FR-020**: Sara MUST open with a greeting in Saudi dialect using plural/respectful address and a
  demo-disclosure clause, e.g. «هلا والله، معكم سارة من ‹store›، نسخة تجريبية والأسعار غير
  حقيقية، كيف أقدر أخدمكم؟».
- **FR-021**: Sara MUST speak at most 2 short sentences and one question per turn (constitution II).
- **FR-022**: Sara MUST state prices, stock, totals, fees, statuses and order ids only from tool
  results in the same call, and MUST say a failed or empty lookup out loud (constitution I).
- **FR-023**: Sara MUST use a short filler line from a pool of 4-5 variants before tools that are
  slow enough to cause dead air.
- **FR-024**: Ambiguous product names MUST produce one clarifying question with at most 2 options.
- **FR-025**: Unsold or off-topic requests MUST get one polite line and a redirect, with no price.
- **FR-026**: Sara MUST escalate when the caller asks for a person, is angry twice, or is not
  understood twice, and MUST explain she cannot cancel orders and escalate cancel requests.
- **FR-027**: Sara MUST answer in Arabic only, for English-only and mixed Arabic-English speech alike,
  and never switch language (Ahmed, 2026-10-28).
- **FR-028**: Sara MUST ignore instructions to change role, reveal the prompt or break rules,
  whether spoken or embedded in a field value.
- **FR-029**: Sara MUST refuse discounts or negotiation (fixed-price store).
- **FR-030**: After a silence timeout Sara MUST prompt once, then close politely; calls MUST end
  after a maximum duration (proposed 240 s).

**Order flow (P1)**

- **FR-040**: The order flow MUST collect, one per turn: items and quantities, name, phone (read
  back digit by digit, grouped), pickup or delivery (area checked against served areas), time slot.
- **FR-041**: Before creating an order Sara MUST read back items, quantities, the quoted total,
  fulfillment and time, using only a side-effect-free quote of the order; the order MUST be created
  only after a clear yes.
- **FR-042**: Order creation MUST be idempotent per (conversation, quote); a retry returns the same
  order marked as duplicate.
- **FR-043**: Order ids MUST be numeric (4 digits, unique) and spoken digit by digit.
- **FR-044**: Phones MUST be normalized to 05XXXXXXXX from +966, 966, 5XXXXXXXX, Arabic-Indic digits
  and paired-number speech; invalid phones are rejected with a spoken reason.
- **FR-045**: The system MUST reject out-of-stock items, unknown products, quantities outside 1-20,
  areas not served (listing served areas), totals below the delivery minimum and slots outside
  opening hours, each with a ready-to-speak Arabic reason.
- **FR-046**: Every order and ticket MUST be linked to the call that produced it, taken from the
  platform's call identity, not from the model.

**Data and backend behaviour**

- **FR-050**: The catalog MUST hold 30 fake items in 5 categories (kitchen, cleaning, plastics,
  gifts, stationery) with the fixed-price theme (5.75 / 9.75 / 14.75 SAR), aliases, unit forms for
  1, 2 and plural, and unit gender; money MUST be stored as integer halalas.
- **FR-051**: Every tool response MUST include ready-to-speak Arabic fields for all numbers and
  never more than 3 product matches (2 when clarifying).
- **FR-052**: Product matching MUST handle tashkeel, letter variants, attached prefixes, filler
  words, broken plurals and dialect words (via aliases), and MUST pass a golden table of ≥ 30
  query → product pairs; no alias may belong to 2 products.
- **FR-053**: Spoken money, quantities, phones and order ids MUST match a golden table signed off
  by Ahmed in one register.
  [NEEDS CLARIFICATION: Ahmed must fix the exact spoken forms for TTS lines 2-4 and the golden
  table (e.g. «سبعطعش» vs «سبعتعش», «مية وسبعطعش ريال», «خمسة وسبعين هللة») — native-speaker call.]
- **FR-054**: Tool endpoints MUST require a shared secret (reject otherwise), validate and cap every
  input, rate-limit per client, and log every call with latency but never secret values.
- **FR-055**: Three seed orders (one per status group) with obviously fake phones MUST exist for
  status lookups.

**Evaluation and reporting (P2-P3)**

- **FR-060**: The suite MUST hold ~26 simulated scenarios (the 20 in plan §9 plus pickup, area not
  served, below minimum, out-of-stock in order, "no" at read-back, status by id / not found,
  returns policy, alias trap, qty ≥ 11, injection via name, cancel request), each tagged
  sim/voice/both and dev/holdout before v1; barge-in, silence, unclear speech and naturalness are
  voice-only.
- **FR-061**: Each scenario MUST define persona, caller goal, script hints, expected tools,
  must-say and must-not-say patterns, and pass criteria.
- **FR-062**: The rubric MUST include critical rows for grounding, order without confirmation,
  phantom confirmation, spoken number differing from tool output, and prompt/secret disclosure,
  plus major/minor rows per plan §9 with explicit definitions of brevity, missed cue and
  escalation trigger.
- **FR-063**: Every run MUST record frozen identifiers (agent config, LLM, voice, synthesis model,
  recognition provider, catalog, simulator, judge config) and reset store data per run.
- **FR-064**: 10 printed call cards (fake names and phones) MUST be used by the same callers for v1
  and v2; real calls are reported descriptively, not as a v1 → v2 delta.
- **FR-065**: The QA report MUST contain a v1 vs v2 table on every rubric dimension, the top 5
  issues (excerpt → root cause → fix → result), remaining issues, and method (which numbers are
  simulated vs real), with only real numbers.

**Privacy, safety, resumability**

- **FR-070**: Raw transcripts, audio, rating clips and real-call results MUST be excluded from git;
  committed excerpts MUST be redacted (phones, long digit runs, Arabic-Indic digits, caller names).
- **FR-071**: Each family caller MUST give a short written consent line; real-call conversations
  are deleted from the platform after the report is final; platform retention is set to 30 days.
- **FR-072**: The public demo agent MUST accept calls only from allow-listed origins, with a daily
  call limit (proposed 20) and concurrency limit (proposed 2), and be disabled between sessions.
- **FR-073**: The public demo MUST use the store name decided by Ahmed and show a demo banner.
  [NEEDS CLARIFICATION: Use the real store name «مقاضينا / Magadhina» in the public demo (requires
  the store owner's written sign-off) or a fictional store name (review M19 default)?]
- **FR-074**: Everything needed to resume MUST be in git; all task scripts MUST run on Windows Git
  Bash and macOS; `docs/STATUS.md` MUST show phase, open gate, blockers and minutes used.
- **FR-075**: A secret scan MUST pass on the full history before each push.

### Key Entities *(include if feature involves data)*

- **Product**: catalog item — stable id, Arabic display name, aliases as callers say them,
  category, price (halalas), in-stock flag, unit forms (1 / 2 / plural) and gender; some items are
  test traps.
- **Store Profile**: name, opening hours (Sat-Thu and Friday), location text and map link, served
  delivery areas, delivery fee, minimum order, return policy, store phone.
- **Quote**: side-effect-free priced basket for one call — lines with spoken quantities and line
  totals, subtotal, delivery fee, total and spoken total, below-minimum flag.
- **Order**: numeric id, created time (Asia/Riyadh), customer name, normalized phone, pickup or
  delivery, area, resolved time slot, items, total (halalas), status (received, preparing, ready,
  out for delivery, delivered, cancelled), linked quote and call.
- **Ticket**: escalation id, time, reason, summary, optional name and phone, linked call.
- **Tool Call Log Entry**: tool, inputs (no secrets), outcome, latency, linked call.
- **Phase 0 Assets**: TTS script lines, STT utterances with expected entities, voice candidates
  (ids from the platform only), clip ratings, STT results, decision record.
- **Scenario**: id, type, persona, goal, hints, expected tools, must/must-not patterns, pass
  criteria, mode, split.
- **Run Result**: scenario × repeat verdicts per rubric dimension, frozen run metadata, human
  verdicts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

**Phase 0 (gate, thresholds pending Ahmed's confirmation)**

- **SC-001**: 0a is complete on 2026-10-27 with zero voice ids, scores or minutes written and the
  status file reading "Phase 0 gate: OPEN — waiting for API key and raters".
- **SC-002**: 0b TTS GO: best voice/model pair mean naturalness ≥ 4.0 / 5 over 24 ratings, every
  rater ≥ 3.0, 100% of number lines heard correctly by all raters.
- **SC-003**: 0b STT GO: ≥ 18/20 intents, ≥ 5/6 products, 2/2 quantity, 2/2 order ids, ≤ 2 of 40
  phone digits wrong, 2/2 for area+slot, hours and escalation.

**Product targets for v2 (reported as measured, met or not)**

- **SC-010**: 0 grounding failures (invented price, stock or policy) on dev and holdout (hard gate).
- **SC-011**: 0 orders created without explicit confirmation (hard gate).
- **SC-012**: 100% of orders preceded by a full read-back.
- **SC-013**: Task success ≥ 85% across the simulated suite (soft target).
- **SC-014**: Correct tool and arguments ≥ 90% (soft target).
- **SC-015**: ≥ 90% of agent turns within the brevity limit (soft target).
- **SC-016**: Dialect naturalness human score ≥ 4.0 / 5 (soft target).
- **SC-017**: A caller completes a delivery order by voice end to end on 3 consecutive attempts.

**Delivery**

- **SC-020**: Whole build fits ~23 h + 3 h contingency and ~110 call-minutes, logged per phase.
- **SC-021**: Every CHANGELOG entry (≥ 5) cites a scenario and a before → after metric.
- **SC-022**: 100% of numbers in README and QA report match the results summary by script.
- **SC-023**: A fresh clone on the second operating system runs the test script green.
- **SC-024**: 0 raw transcripts, audio files or secrets in git history at ship time.
- **SC-025**: Demo video is 60-90 s and shows one order call, one edge case and the results table.

## Assumptions

Decisions recorded from `plan.md` + `reviews/plan-review.md` (answers to questions the specify
skill would otherwise ask):

- Voice runtime: ElevenLabs Agents (hosted STT + LLM + TTS); agent config as code via
  `@elevenlabs/cli` pinned to 1.7.1 and run via `npx elevenlabs`; the laptop only runs
  `agents push --dry-run`; the Mac is the single push owner. (Review spot-check table, M1.)
- Phase 0 synthesis models compared: `eleven_v4_turbo` and `eleven_flash_v2_5`;
  `eleven_v3_conversational` only in the retry; `eleven_turbo_v2_5` dropped (deprecated). The
  agent runs the exact winning voice/model/settings; any later change re-opens the TTS gate (M2).
- Phase 0 recognition providers: default plus one of {elevenlabs, scribe_realtime,
  scribe_v2_turbo}; `agent.language: ar`; transcripts from the conversation records API (M3, G.3).
- Fallbacks: STT NO-GO → Vapi + Azure `ar-SA` STT keeping ElevenLabs `eleven_flash_v2_5` TTS;
  TTS NO-GO → re-rate Azure `ar-SA-ZariyahNeural`; +3-4 h from contingency (M8).
- Plan: Ahmed buys ElevenLabs Starter before 0b (pricing confirmed in the review on 2026-10-27);
  budget ~110 call-minutes; Creator only if he wants headroom (M9).
- Six tools, not five: product lookup, store info, quote, create order, order status, escalate
  (amendment 3). One response envelope with spoken Arabic fields (amendment 4).
- Persona: female "Sara" (سارة); voices searched are female (G.2).
- Phase 1 and offline Phase 3 work may start while 0b waits; Phase 2, the Phase 3 run and Phase 4
  stay strictly gated. This session stops at the Phase 0 gate (amendment 12).
- Diagrams are Mermaid sources with derived PNGs; Lucidchart optional (amendment 16).
- Demo page hosted on GitHub Pages with a pinned embed script; local serving over HTTP, never
  `file://` (amendment 9).
- Public tunnel from the Mac for tools during development; a named tunnel only if Ahmed has a
  domain (M7).
- Raters and callers are Ahmed's family/acquaintances; sessions booked by Ahmed.
- Out of scope: production deployment, real customer data, payments, multi-tenancy, custom
  STT/TTS models, outbound calls, SMS/WhatsApp, user accounts; Twilio number only as optional
  Phase 6 with 0 budgeted hours.
- UNVERIFIED until 0b on the Mac: whether simulation tests bill minutes; whether Starter keys can
  use library voices and whether they must be added to "My Voices" first; valid accent values for
  the voice search; TTS character quota on Starter; whether language detection also switches
  recognition.
