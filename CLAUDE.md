# CLAUDE.md — Saudi Voice Receptionist
Read plan.md fully before doing anything. It is the single source of truth.
- Work one phase at a time (plan.md §11). Stop at each acceptance check and report.
- Never invent prices, stock, schema changes, API/SDK/CLI shapes or eval numbers.
  Check current docs or --help first; pin versions.
- Code and comments in English. Agent speech and customer strings in Saudi Arabic (UTF-8).
- All data is fake demo data. Secrets only in .env.
- Use subagents for parallel work (backend, evals, docs) and commit after each green check.
- Keep token use low: reference plan.md sections instead of re-explaining.

## Spec Kit
- Spec Kit (`specify` CLI, skills in `.claude/skills/speckit-*`) drives the spec-first flow:
  constitution → specify → plan → tasks → implement. Feature specs live in `specs/`.
- `plan.md` (root) is the source spec; `specs/*/plan.md` is the Spec Kit implementation plan derived from it.
- Review of the source plan: `reviews/plan-review.md`. Its accepted fixes win over plan.md where they conflict.

## Machines
- Started on Windows laptop; continued on the Mac Mini. Everything needed to resume is in git.
- Status of the current phase and the open gate: `docs/STATUS.md`.
