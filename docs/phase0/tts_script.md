# Phase 0 TTS listening script (8 gate lines)

Source: `reviews/plan-review.md` §G.1. One Saudi colloquial register, spoken strings exactly as
`spoken.py` (Phase 1) will emit them. Sara addresses the caller in the plural (معكم، رقمكم) and
speaks of herself in the feminine.

`register_signed_off: yes` (Ahmed, 2026-10-28, approved as written) — Ahmed confirms or corrects the register of lines 2–4 (and line 4's
"مية وسبعطعش") before 0b. Whatever he fixes here becomes Phase 1's `golden_spoken.csv`.

`phase0/tts_samples.py` reads this list with `--script docs/phase0/tts_script.md`; its built-in
default is the same 8 lines, and `phase0/test_phase0.py` fails if the two ever differ.
Format of each line is `N. label: text` (the script's parser depends on it).

1. greeting: هلا والله، معكم سارة من مقاضينا، كيف أقدر أخدمكم؟
2. price_9_75: الصحون الزجاج بتسعة ريال وخمسة وسبعين هللة
3. total_17_25: المجموع سبعطعش ريال وخمسة وعشرين هللة
4. total_117: المجموع مية وسبعطعش ريال
5. phone_3_3_4: رقمكم صفر خمسة خمسة، واحد اثنين ثلاثة، أربعة خمسة ستة سبعة، صح؟
6. order_id: رقم طلبكم أربعة، ثمانية، اثنين، واحد
7. clarify_2_options: تقصدون صحون زجاج أو صحون بلاستيك؟
8. escalate_close: أعتذر منكم، بحوّلكم لموظف يتواصل معكم، شكراً لاتصالكم

Lines 2–6 are the **number lines**: raters also mark "heard the right number" (y/n) on them.
The project is Arabic only (Ahmed, 2026-10-28): there is no English line.

Characters: 337 per voice × model pass; 3 voices × 2 models = 2,022 characters for 48 clips
(check with `python phase0/tts_samples.py --dry-run`).
