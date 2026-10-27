# Draft catalog trap items (Phase 0a)

Status: **draft, names only.** These are the items the STT sheet and the TTS script already depend
on, fixed now so Phase 1's `products.json` (plan.md §6: 30 items, 2 out-of-stock, 2 near-duplicate
pairs, 3 shelf≠common items) is built around them. All demo data is fake. No prices are assigned
here: Phase 1 picks them from the fixed-price set in plan.md §6 (5.75 / 9.75 / 14.75), except the
two example prices plan.md §7 already fixes (صحون زجاج 9.75, صحون بلاستيك 5.75).

## Near-duplicate pairs (clarify with ≤ 2 options, amendment 5)

| Pair | Shelf name A | Shelf name B | Used by |
| --- | --- | --- | --- |
| 1 | صحون زجاج | صحون بلاستيك | STT #1 (fails on «بلاستيك»), TTS line 7 |
| 2 | أكواب ورق | أكواب زجاج | STT #2 (fails on «زجاج») |

## Shelf name ≠ common (dialect) name

| # | Shelf name (`name_ar`) | Common names (`aliases_ar`) | Unit | Used by |
| --- | --- | --- | --- | --- |
| 1 | أكياس نفايات | أكياس زبالة، كيس زبالة، أكياس قمامة | علبة | STT #3 (qty 12) — **the sheet's trap item** |
| 2 | أكواب ورق | كاسات ورق، كاسة ورق، كاس ورق، كوب ورق | علبة | STT #2 |
| 3 | مناشف مطبخ | فوط مطبخ، فوطة مطبخ، فوط | حبة | Phase 1 golden table |

## Out-of-stock (2, Phase 1 decides which)

Proposal: one from the near-duplicate pairs (أكواب زجاج) and one unrelated item, so scenario E2
(out-of-stock) and E3 (ambiguous product) can be tested separately.

## Rules

- If Phase 1 changes trap item 1, update both #3 rows in `docs/phase0/stt_results.csv`
  (`utterance`, `critical_entities`, `acceptable_variants`) and `docs/phase0/stt_sheet.md`.
- Plural and dialect forms are aliases (amendment 5), matched after the B4 normalization that
  `phase0/stt_score.py` already implements.
