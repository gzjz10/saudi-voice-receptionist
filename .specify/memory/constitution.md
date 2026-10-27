<!--
Sync Impact Report (scratch for review; remove before or at commit)
- Version change: template (unversioned) -> 1.0.0 (initial ratification)
- Principles defined (template had 5 slots; 9 principles requested):
  I. Grounded Facts Only (NON-NEGOTIABLE)
  II. Voice Brevity
  III. Read-Back Before Commit (NON-NEGOTIABLE)
  IV. Fake Demo Data and Private Real Calls
  V. Secrets Only in .env
  VI. Verify Docs Before Any API, SDK or CLI Use
  VII. Phase Gates, Never Faked (NON-NEGOTIABLE)
  VIII. Eval-Driven Prompt Changes
  IX. English Code, Saudi Arabic Speech
- Added sections: "Platform and Environment Constraints", "Development Workflow and Quality Gates"
- Removed sections: none
- Templates: plan-template.md "Constitution Check" reads this file at runtime; no template edits
  made (constitution skill scope). spec-template.md, tasks-template.md: no changes required.
- Deferred TODOs: none. Phase 0 thresholds are governed by reviews/plan-review.md section G and
  remain proposals until Ahmed confirms them (tracked in the feature spec, not here).
-->

# Saudi Voice Receptionist Constitution

Sources of truth, in order: this constitution, `reviews/plan-review.md` section E ("Plan
amendments") and sections F-G (gates), then `plan.md` (Technical Spec v1.0). Where the review and
`plan.md` conflict, the review wins.

## Core Principles

### I. Grounded Facts Only (NON-NEGOTIABLE)

- Every price, stock state, total, delivery fee, order status, order id and store policy the
  agent speaks MUST come from a tool result returned in the same call. The model MUST NOT compute,
  recall or estimate any of them.
- Read-back totals MUST come from the side-effect-free quote tool, never from model arithmetic.
- A failed, empty or timed-out tool call MUST be said out loud as a failure; the agent MUST NOT
  guess or fill the gap.
- Off-topic or unsold products get one polite line and a redirect, with no price.
- Rationale: one invented price makes the demo untrustworthy; grounding failures are the critical
  rubric dimension and the v2 target is zero.

### II. Voice Brevity

- Each agent turn MUST be at most 2 short sentences (≤ 2 segments split on `. ! ? ؟` and
  ≤ 30 words; pre-tool filler counted separately) and ask at most one question.
- Numbers MUST be spoken from the backend's ready-to-speak fields (`*_spoken_ar`), never raw
  digits, so text-to-speech never improvises number reading.
- Ambiguity gets one clarifying question with at most 2 options.
- Rationale: callers only hear the agent; long or batched turns cause missed cues and barge-in.

### III. Read-Back Before Commit (NON-NEGOTIABLE)

- An order MUST NOT be created until the agent has read back items, quantities, total,
  fulfillment (pickup/delivery + area) and time slot, and the caller has given a clear yes.
- A correction at any step returns to that step only, then the full read-back repeats.
- Order creation MUST be idempotent per (conversation, quote) so a retried call never creates a
  second order.
- Rationale: an order without explicit confirmation is a critical rubric failure.

### IV. Fake Demo Data and Private Real Calls

- All products, prices, stock, orders, store details and phone numbers in the repo MUST be fake
  demo data, and the README and demo page MUST say so. Seed phones use an obviously fake pattern.
- Real test callers use made-up names and numbers and give a short written consent.
- Raw transcripts, call audio, real-call results and rating clips MUST NOT be tracked by git; only
  redacted excerpts, summaries and verdicts may be committed. Real-call conversations are deleted
  from the platform after the report is final.
- Rationale: the repository is public; the portfolio must never leak a real person's data.

### V. Secrets Only in .env

- API keys, the tool secret and any token MUST live only in `.env` (git-ignored) on the machine
  that needs them; `.env.example` lists names with no values.
- The tool secret MUST reach the voice platform only as a platform-stored secret referenced by id,
  never as a literal in a committed config file.
- A secret scan (gitleaks or equivalent) MUST pass before every push; the tool secret is rotated
  per demo session and after any screen recording that shows the dashboard.
- Rationale: one leaked key in a public repo means billing exposure and an open tools endpoint.

### VI. Verify Docs Before Any API, SDK or CLI Use

- No API route, SDK call, CLI command or flag, config field, model id, voice id, price, quota or
  eval number may be written from memory. Each MUST be checked against current official docs or
  real `--help` / schema output first, with the URL or command cited.
- Anything that cannot be verified MUST be labelled `UNVERIFIED` where it is used.
- Every dependency MUST be pinned to an exact version (CLI, Python and npm packages, embed script).
- Rationale: the voice platform ships CLI releases every few days; stale shapes cost hours.

### VII. Phase Gates, Never Faked (NON-NEGOTIABLE)

- Work proceeds one phase at a time per the reconstructed delivery plan (review section F). A
  hard-gated phase MUST NOT start until the previous gate passes; only the parallel work the review
  explicitly allows (Phase 1 and offline Phase 3 while 0b waits) may overlap.
- Each gate is pass/fail with a named checker; the session stops at the gate and reports.
- No voice id, rating, transcript score, minute count or eval number may be recorded unless it came
  from a real API response or a real human score. Missing inputs leave the gate `OPEN`.
- `docs/STATUS.md` always states the current phase, the open gate, what blocks it and call minutes
  used.
- Rationale: Phase 0 is a go/no-go on dialect quality; a faked pass would sink every later phase.

### VIII. Eval-Driven Prompt Changes

- Every change to the system prompt, flow or tools after v1 MUST be logged in
  `prompts/CHANGELOG.md` as: date · change · scenario id that caused it · metric before → after.
- v1 and v2 MUST run on the same scenario suite, the same repeat count, the same call cards and the
  same frozen models and configs (hashes recorded per run).
- Deterministic tool-log assertions are the primary scorer; the LLM judge is a helper, and a human
  verdict overrides it on every critical flag and every real call.
- Reports state the real numbers, met or not, and say which came from simulation and which from
  real calls.
- Rationale: the project's value is proving measured improvement, not claiming it.

### IX. English Code, Saudi Arabic Speech

- Code, comments, docs, commit messages and specs MUST be in English.
- Agent speech, the system prompt, customer-facing strings and test utterances MUST be natural
  Saudi colloquial Arabic in UTF-8, one register throughout (plural/respectful address); English
  only for an English-only caller.
- Text normalization for matching MUST NOT alter display names or spoken fields.
- Rationale: the agent must sound Saudi to callers while the repo stays reviewable by anyone.

## Platform and Environment Constraints

- Two machines: Windows laptop (Git Bash) and Mac Mini. Everything needed to resume MUST be in git.
  Shell scripts are POSIX/bash; Python is cross-platform (3.12, `.python-version`); no `brew`- or
  `make`-only paths.
- The voice platform CLI is pinned as a project dev dependency and run via `npx`; the laptop only
  validates offline (`--dry-run`); the Mac is the single push owner and pulls before every push.
- The tools backend is the only source of truth and stays platform-neutral so a voice-runtime
  fallback changes the adapter, not the backend.
- Call minutes are budgeted (~110 on the chosen plan) and logged in `docs/STATUS.md` per phase.
- Tool endpoints require the secret header (401 otherwise), validate and cap every body, and log
  each call with latency but never header values.

## Development Workflow and Quality Gates

- Spec Kit flow: constitution → specify → clarify → plan → tasks → implement. Feature specs live in
  `specs/`; root `plan.md` is the source spec.
- Commit after each green check; the orchestrating session owns commits and pushes.
- A gate passes only when its checker's evidence exists in the repo (test output, STATUS entry,
  signed decision file) or the human checker records the verdict.
- Decisions only Ahmed can make (payment, brand use, thresholds, spoken register, approved fixes)
  are recorded with his sign-off, never assumed.

## Governance

- This constitution supersedes other working practices in the repo; `CLAUDE.md` is the runtime
  guidance file and MUST stay consistent with it.
- Amendments: proposed in a commit that edits this file, states the reason and is approved by
  Ahmed (owner, GitHub gzjz10). Semantic versioning applies: MAJOR for removing or redefining a
  principle, MINOR for adding a principle or section or materially expanding guidance, PATCH for
  wording fixes.
- Compliance: every `/speckit-plan` Constitution Check and every gate report MUST confirm
  principles I-IX or list the violation with justification; unjustified violations block the gate.

**Version**: 1.0.0 | **Ratified**: 2026-10-27 | **Last Amended**: 2026-10-27
