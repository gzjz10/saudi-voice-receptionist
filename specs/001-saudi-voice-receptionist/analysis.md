# Specification Analysis Report: Saudi Voice Receptionist "Sara"

**Feature**: `specs/001-saudi-voice-receptionist` | **Date**: 2026-10-27 | **Analyst**: Spec Kit
team leader (Fable 5.1) running `.claude/skills/speckit-analyze/SKILL.md`

**Inputs**: `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `contracts/`,
`quickstart.md`, `.specify/memory/constitution.md` v1.0.0, `reviews/plan-review.md` (sections E-G
override root `plan.md`), and the Phase 0a files on disk (`agent/`, `docs/phase0/`, `phase0/`,
`prompts/`, `.env.example`, `.gitignore`).

**Pre-execution**: `.specify/extensions.yml` does not exist, so no hooks ran.
`check-prerequisites.sh --json` returned FEATURE_DIR = `specs/001-saudi-voice-receptionist` with
research, data-model, contracts, quickstart and tasks available.

The skill is read-only; this run departs from that under the orchestrator's step 2 ("fix every
CRITICAL and HIGH finding directly in the artifacts"). The findings table records the state
**before** the fixes; the Leader sign-off at the end records what changed.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation / action |
|----|----------|----------|-------------|---------|-------------------------|
| I1 | Inconsistency | **HIGH** | plan.md "Project Structure" + "Phase 0a outputs"; tasks.md T014-T016, T019-T022, T029, T033, T036-T038; research.md R4, R6, R18; data-model.md A2, A3, A6; contracts/phase0-artifacts.md §3, §5; quickstart.md §2-§3 | All planning artifacts named Phase 0 sheets that never existed (`phase0/stt_test_sheet.md/.csv`, `phase0/voice_candidates.md`, `scripts/score_phase0.py`, `scripts/tests/test_score_phase0.py`, `docs/phase0/rating_sheet.md`). On disk the 0a run used the review section F names: `docs/phase0/stt_sheet.md`, `docs/phase0/stt_results.csv`, `docs/phase0/voice_selection.md`, scorers `phase0/tts_score.py` + `phase0/stt_score.py`, tests `phase0/test_phase0.py`. A `check_phase0a.sh` written from the artifacts would have failed on files that exist, and T024 could not pass. | FIXED: every artifact now names the on-disk files; `scripts/score_phase0.py` is reduced to a thin wrapper (T021). |
| I2 | Inconsistency | **HIGH** | contracts/phase0-artifacts.md §1; data-model.md A5; tasks.md T019 | Ratings CSV column named `clip_label` in the contract but `blind_id` on disk and in `phase0/tts_score.py`. A rater file written to the contract would not score. | FIXED: contract, data model and T019 use `blind_id`. |
| C1 | Constitution (VI, exact pins) | **HIGH** | phase0/requirements.txt vs plan.md Technical Context, research.md R11, tasks.md T002 | Two different pytest pins in one repo: `requirements-dev.txt` (planned) `pytest==9.1.1` (PyPI 2026-06-19) and `phase0/requirements.txt` (on disk) `pytest==8.4.2` (2025-09-04). | FIXED in artifacts: T002 now removes the 8.4.2 line; R11 records the conflict. The file edit itself belongs to the 0a team (not this leader's file). |
| U1 | Underspecification | **HIGH** | contracts §4, tasks.md T017/T021 vs phase0/tts_score.py, phase0/stt_score.py | The contract says both scorers read `docs/phase0/thresholds.json`; the file does not exist and neither scorer reads it. Both hard-code a `GATE` dict with the G values. Ahmed's threshold confirmation (FR-008) would then be a code change, not data. | FIXED in artifacts: T017 creates the file; T021 makes both scorers read it (fallback to built-ins, source printed); T020 adds a test that a changed file changes the verdict. |
| I3 | Inconsistency | MEDIUM | tasks.md T014 "verbatim from review G.1" vs docs/phase0/stt_sheet.md #5 | Review G.1 utterance 5 has 9 spoken digits and cannot equal its own target 0557834567. The 0a sheet correctly appended «سبعة». "Verbatim" would have reverted a correct fix. | FIXED: T014, research R6 and contracts §3 record the accepted deviation (leader decision; the review was mine). |
| I4 | Inconsistency | MEDIUM | tasks.md T003; research.md R18; plan.md Constitution Check row IV | Text said `phase0/samples/` "currently NOT ignored". The 0a run already added it to `.gitignore` (uncommitted). | FIXED: wording now "confirm; uncommitted". |
| A1 | Ambiguity | MEDIUM | spec.md FR-002 | "a minimal Arabic agent definition ... replies only «تمام»" described one agent; the repo has two (persona `sara.json` and the «تمام» probe `sara_stt_probe.json`), and the persona does not reply only «تمام». | FIXED: FR-002 names both roles without file names. |
| G1 | Coverage gap | MEDIUM | spec.md SC-016 vs tasks.md | SC-016 (dialect naturalness >= 4.0, human, voice-only) had no task producing the score after Phase 0. | FIXED: T104 now gives each real call a 1-5 naturalness score. |
| G2 | Coverage gap | MEDIUM | review M16 "Book 3 family sessions now" | No task. The 0b, v1 and v2 human sessions are the schedule-critical path. | FIXED: new T133 (HUMAN, booking in STATUS blockers). |
| G3 | Coverage gap | LOW | .specify/.gitignore ignores feature.json | The Spec Kit feature pointer does not travel to the Mac through git; skills would not find the feature. | FIXED: quickstart §1 recreates it; new T134. |
| U2 | Underspecification | LOW | tasks.md T016 vs docs/phase0/voice_selection.md §2 | The on-disk ID table lacks `source_command` / `retrieved_at` columns and the retry slots D-F that data-model A3 requires. | FIXED: T016 lists exactly what to add. |
| U3 | Underspecification | LOW | tasks.md T013 vs docs/phase0/tts_script.md | The on-disk script lacks the metadata table (`is_number_line`, `expected_number`) from data-model A1; it has the equivalent prose. | FIXED: T013 lists what to add. |
| U4 | Underspecification | LOW | tasks.md T018 vs voice_selection.md §5 | Rating form exists; it lacks the no-discussion rule and the "R1-R3 only" rule. | FIXED: T018 adds the two rules, no separate file. |
| B1 | Encoding | LOW | docs/phase0/stt_results.csv | Starts with a UTF-8 BOM (`ef bb bf`); contract says no BOM. Every reader uses `utf-8-sig`, so nothing breaks today. | Kept as T014 hygiene item. |
| D1 | Duplication | LOW | spec.md FR-008/SC-002/SC-003 vs review G.2-G.3 vs contracts §4 | The thresholds are stated in four places. Acceptable because SC must be measurable and the contract is the machine form; all four agree today. | Keep; `thresholds.json` becomes the single machine source after T017. |
| A2 | Ambiguity | LOW | spec.md FR-023 "slow enough to cause dead air" | Vague in the spec; plan.md pins it (p95 > ~700 ms) and review M15 agrees. | No change; the plan carries the number. |
| R1 | Risk (constitution IV/VI) | LOW | docs/phase0/voice_selection.md §2 | Lists three third-party catalog voice names (json2video, famulor) as "leads". No IDs, marked unconfirmed, must be re-found via the API. Risk is anchoring, not a violation. | Noted in T015; no change to the file. |

No CRITICAL findings: no constitution MUST is violated by any artifact, and no requirement with
zero coverage blocks baseline functionality. The constitution was not touched.

## Coverage summary

Only requirements that need buildable work are listed (post-launch KPIs such as SC-013..SC-016
map to measurement tasks, not build tasks).

| Requirement key | Has task? | Task IDs | Notes |
|---|---|---|---|
| FR-001 (0a/0b split, no results in 0a) | yes | T022, T024, T043 | check_phase0a "no results written" |
| FR-002 (minimal agents, offline validation) | yes | T007-T011, T022 | validator + dry-run both required |
| FR-003 (8-line TTS script) | yes | T013 | on disk |
| FR-004 (10-utterance STT sheet) | yes | T012, T014 | on disk, #5 deviation accepted |
| FR-005 (voice procedure, templates, scorer tested on fake data) | yes | T015-T021 | on disk except thresholds.json + wrapper |
| FR-006 (trap items) | yes | T012 | on disk |
| FR-007 (48 clips, blind, 3 raters) | yes | T029-T032 | KEY + HUMAN |
| FR-008 (TTS thresholds) | yes | T017, T021, T025, T033-T034 | CLARIFY Q1 |
| FR-009 (STT thresholds) | yes | T017, T021, T036-T037 | |
| FR-010 (fallback triggers) | yes | T041 | adapter tasks written only if triggered |
| FR-011 (billing check) | yes | T040 | |
| FR-012 (signed decision) | yes | T042-T043 | |
| FR-020-FR-030 (conversation rules) | yes | T077, T081, T084, T090, T093-T094 | FR-030 timeouts in T081 |
| FR-040-FR-046 (order flow) | yes | T047, T058, T059, T064, T065, T078-T079, T088 | |
| FR-050-FR-055 (data/backend) | yes | T047-T057, T061-T067, T072 | FR-053 CLARIFY Q2 |
| FR-060-FR-065 (eval/report) | yes | T093-T105, T110-T119 | |
| FR-070 (no raw data in git) | yes | T003, T060, T099, T106, T123 | |
| FR-071 (consent, retention, deletion) | yes | T010, T081, T095, T125 | |
| FR-072 (allowlist, limits, disable) | yes | T081, T091, T125 | |
| FR-073 (store name) | yes | T025, T048, T084 | CLARIFY Q3 |
| FR-074 (resumable, cross-platform, STATUS) | yes | T005, T006, T023, T068, T075, T124, T134 | |
| FR-075 (secret scan) | yes | T046, T123 | |
| SC-001 (0a complete, STATUS text) | yes | T006, T024 | |
| SC-002/SC-003 (0b gates) | yes | T033, T037, T043 | |
| SC-010-SC-012, SC-017 (v2 hard gates, 3 orders) | yes | T088, T115, T117 | |
| SC-016 (naturalness human score) | yes | T032, T104 | T104 extended |
| SC-020 (hours/minutes logged) | yes | T028, T091, T107, T116, T126 | |
| SC-021 (CHANGELOG) | yes | T113, T117 | |
| SC-022 (numbers match by script) | yes | T097, T121 | |
| SC-023 (fresh clone green) | yes | T075, T124 | |
| SC-024 (no raw data/secrets at ship) | yes | T106, T123 | |
| SC-025 (video) | yes | T122 | |

**Deliverables D1-D6 (root plan.md §1)**: D1 -> T084, T088, T092; D2 -> T118, T128; D3 -> T077,
T112, T113; D4 -> T093-T109; D5 -> T119, T121; D6 -> T122. All covered.

**Review must-fixes**: B1 -> gate tasks T024/T043/T076/T092/T109/T117/T128 + T006; B2 -> 0a/0b
split T001-T043; B3 -> T064-T065; B4 -> T054-T055; B5 -> T003, T046, T060, T082, T095, T099, T125.
M1 -> T001, T007, T050, T087; M2 -> T030, T035, T081; M3 -> T036-T037; M4 -> T081, T090; M5 -> T081,
T093, T098; M6 -> T081, T084, T086, T091; M7 -> T071; M8 -> T041; M9 -> T026, T028, T091, T107, T116,
T126; M10 -> F hours in plan.md + cut order in the strategy; M11 -> "Allowed overlap"; M12 -> T047,
T051, T059, T064-T067, T078; M13 -> T048, T056-T058; M14 -> T093, T097, T098, T103; M15 -> T094, T096,
T100, T101, T105; M16 -> T093, T095, T133; M17 -> T002, T005, T068; M18 -> T052, T053, T070; M19 ->
T025, T048, T084, T127. All covered.

**Constitution alignment issues**: none remaining. C1 (two pytest pins, principle VI) is fixed at
the task level and waits on the 0a team's file edit.

**Unmapped tasks**: none. T130-T134 are cross-cutting and map to constitution VI, the Spec Kit
flow, CLAUDE.md consistency, review M16 and FR-074.

## Metrics

- Total requirements: 48 FR (FR-001..012, 020..030, 040..046, 050..055, 060..065, 070..075) + 17
  SC (SC-001..003, 010..017, 020..025) = 65
- Total tasks: 134 (T001-T134, sequential; 2 added by this analysis); 58 marked [P]
- Coverage: 100% of FR and SC have >= 1 task
- Ambiguity count: 2 (A1 fixed, A2 accepted)
- Duplication count: 1 (accepted)
- Inconsistency count: 4 (all fixed)
- Underspecification count: 4 (all fixed at the task level)
- Coverage gaps: 3 (all fixed)
- Critical issues: 0
- High issues: 4 (all fixed)

## Next actions

- No CRITICAL issue blocks `/speckit-implement` for Phase 0a. The remaining 0a work is T002,
  T003, T005, T006, T011, T013 (table), T016 (columns), T017, T018 (rules), T020-T024.
- Before 0b: run `/speckit-clarify` for FR-008, FR-053, FR-073 (the three questions below), then
  T131 (`/speckit-analyze` again).
- The 0a team should remove `pytest==8.4.2` from `phase0/requirements.txt` (C1) and strip the BOM
  from `docs/phase0/stt_results.csv` (B1); neither file belongs to the leader.
- Extension hooks: `.specify/extensions.yml` is absent, so no `after_analyze` hook runs.

## Leader sign-off (Fable 5.1, 2026-10-27, Windows laptop)

**What I fixed (in `specs/001-saudi-voice-receptionist/` only; nothing committed, no branch):**

1. Realigned plan.md, tasks.md, research.md (R4, R6, R11, R18), data-model.md (A2, A3, A5, A6, A7),
   contracts/phase0-artifacts.md (§1, §3, §5, §6) and quickstart.md (§1-§3) to the Phase 0 files
   that exist on disk, which are the review section F names (I1, I2). The planner's R18 note that
   the 0a team used `phase0/stt_test_sheet.*` and `phase0/voice_candidates.md` was wrong; those
   files never existed.
2. Rewrote tasks T002, T003, T013-T022, T029, T032, T033, T036-T038, T104 and added T133 (book the
   3 family sessions) and T134 (recreate `.specify/feature.json` on the Mac). Marked T013 as
   executing now (its file is on disk). IDs stay sequential T001-T134.
3. Turned the hard-coded thresholds into a task (T017 + T021) so Ahmed's confirmation is data.
4. Recorded the accepted G.1 deviation for STT utterance 5 (I3) in tasks, research and contract.
5. Reworded spec FR-002 for the two-agent layout (A1). No other spec change; the three
   `[NEEDS CLARIFICATION]` markers stay for `/speckit-clarify`.
6. Added research R19: a leader spot-check that re-fetched the models page and the conversations
   API reference, re-ran the CLI schema dump offline, re-read PyPI and npm, and re-ran every 0a
   offline check (validator OK, dry-run OK, both self-tests OK, `phase0/test_phase0.py` 5/5 green
   as a plain script; pytest is not installed on the laptop). Every claim checked held; nothing
   previously UNVERIFIED was upgraded without evidence.

**What remains open (not blocking 0a):**

- `docs/STATUS.md`, `scripts/`, `requirements-dev.txt`, `.python-version`,
  `docs/phase0/thresholds.json`, `agent/tests/` and the T020 test cases do not exist yet. T024
  cannot pass until they do.
- Two edits to 0a-team files: drop `pytest==8.4.2` from `phase0/requirements.txt`; save
  `docs/phase0/stt_results.csv` without a BOM.
- `.gitignore` (with `phase0/samples/`) and the constitution are modified but uncommitted; the
  orchestrator commits.
- All UNVERIFIED items in research R3, R4, R5, R7, R9, R12, R13, R15 stay UNVERIFIED until the Mac
  has a key; each has a named task.
- Phase 0 gate status: **OPEN - waiting for API key and raters.** No voice id, score, transcript or
  minute has been written anywhere.

**Open clarification questions for Ahmed (`/speckit-clarify`; detail in
`checklists/requirements.md`):**

1. **FR-008 / SC-002 / SC-003** - confirm the Phase 0 thresholds (TTS best pair mean >= 4.0, retry
   band 3.5-3.99, risk-flag band 3.8-3.99, no rater mean < 3.0, all number lines correct; STT
   >= 18/20 intents, >= 5/6 products, 2/2 qty and order id, <= 2 of 40 phone digits wrong with
   >= 2/4 exact, 2/2 area+slot, hours, escalation), or set different ones. Also confirm the
   scorer's tie rule (next-best pair when the best fails the rater or number rule). Needed before 0b.
2. **FR-053** - fix the spoken register of TTS lines 2-4 and the golden spoken table (e.g.
   «سبعطعش» vs «سبعتعش», «مية وسبعطعش ريال», «خمسة وسبعين هللة»). Needed before 0b synthesis; it
   becomes `golden_spoken.csv` in Phase 1.
3. **FR-073** - real «مقاضينا / Magadhina» name in the public demo (needs the store owner's written
   sign-off) or a fictional store name (review default). Needed before Phase 2; 0b clips use
   مقاضينا in line 1 unless he says otherwise.
