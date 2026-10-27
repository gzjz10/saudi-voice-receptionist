# Specification Quality Checklist: Saudi Voice Receptionist "Sara"

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-10-27
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [ ] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Validation iteration 1 (2026-10-27): all items pass except the open clarification markers.
- "No implementation details" passes with a recorded exception: the feature's P0 story is a
  go/no-go on a specific hosted voice platform, so vendor, CLI, model and provider names appear
  only in the Assumptions section (as dependencies decided by `reviews/plan-review.md`) and as
  "the CLI's offline validation" in FR-002. Requirements and success criteria otherwise describe
  behaviour, not code. Exact config fields stay in review section G and belong in `/speckit-plan`.
- Prices (5.75 / 9.75 / 14.75 SAR) and test numbers in the spec are fake demo data from `plan.md`,
  not real store data.
- 3 [NEEDS CLARIFICATION] markers remain, all decisions only Ahmed can make (questions below).
  They do not block Phase 0a; Q1 and Q2 must be answered before Phase 0b runs; Q3 before the
  Phase 1 golden tables and the public demo.

### Open questions for Ahmed (resolve with `/speckit-clarify`)

#### Question 1: Phase 0 gate thresholds (FR-008, SC-002, SC-003)

**Context**: Review section G: "All thresholds are proposals for Ahmed to confirm before 0b runs."

**What we need to know**: Confirm the proposed thresholds or set different ones.

| Option | Answer | Implications |
|--------|--------|--------------|
| A | Accept as proposed (TTS ≥ 4.0, retry 3.5-3.99, risk flag 3.8-3.99; STT ≥ 18/20 intent, ≥ 5/6 product, 2/2 qty and id, ≥ 95% phone digits) | 0b can run as soon as key and raters exist |
| B | Stricter TTS bar (e.g. ≥ 4.3) | Higher chance of retry or fallback (+3-4 h) |
| C | Looser TTS bar (e.g. ≥ 3.8 GO) | Faster GO; v2 naturalness target ≥ 4.0 more likely missed |
| Custom | Give your own numbers | Recorded in `docs/phase0/decision.md` before rating |

#### Question 2: Spoken register of number lines (FR-053, TTS lines 2-4)

**Context**: Review G.1: "Line 4 and the register of lines 2-4 are Ahmed's native-speaker call."

**What we need to know**: The exact spoken forms that become the golden spoken table.

| Option | Answer | Implications |
|--------|--------|--------------|
| A | Keep review forms: «تسعة ريال وخمسة وسبعين هللة», «سبعطعش ريال وخمسة وعشرين هللة», «مية وسبعطعش ريال» | TTS script used as drafted |
| B | Use «سبعتعش» spelling and «ميّة» for 100 | Script and golden table updated before 0b |
| Custom | Dictate your own forms | Recorded as the golden table, signed by Ahmed |

#### Question 3: Store name in the public demo (FR-073)

**Context**: Review M19: "default to a fictional store name ... unless the store owner signs off
in writing."

**What we need to know**: Real brand or fictional name for the public repo and demo page.

| Option | Answer | Implications |
|--------|--------|--------------|
| A | Fictional store name (review default) | No brand risk; persona swap via store profile |
| B | Real «مقاضينا / Magadhina» with written owner sign-off | Stronger story; sign-off file needed before Phase 2 |
| Custom | Other | Recorded in the store profile and README |
