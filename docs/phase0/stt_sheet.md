# Phase 0 STT sheet (10 utterances × 2 speakers)

Status: **template, not run.** No transcript, score or minute in this repo comes from a real call yet. It needs the ElevenLabs API key, the minimal Arabic agent pushed from the Mac, and two speakers (Phase 0b).

Source of truth: `reviews/plan-review.md` §G.1 (sheet) and §G.3 (gate). Machine-readable copy: `docs/phase0/stt_results.csv`. Scorer: `phase0/stt_score.py`.

## What this tests

The agent's own realtime ASR (`agent.language: ar`) on the words where the real receptionist will fail:

| Stress | Clip(s) |
| --- | --- |
| Near-duplicate products (صحون زجاج / صحون بلاستيك, أكواب ورق / أكواب زجاج) | 1, 2 |
| Dialect alias that differs from the shelf name (كاسات → أكواب ورق, أكياس زبالة → أكياس نفايات) | 2, 3 |
| Quantity above 10 with a unit (اثنعش علبة) | 3 |
| 10-digit Saudi mobile, grouped and with paired numbers | 4, 5 |
| Numeric order id read digit by digit | 6 |
| Al-Ahsa place names (المبرز, الهفوف) and a time slot (بكرة العصر) | 7, 10 |
| A common English word inside Arabic speech (delivery) | 7 |
| Fast / elided speech | 3, 5, 6 |
| Angry escalation | 9 |

## The 10 utterances

`critical_entities` are the exact tokens the transcript must contain. Variants are alternatives separated by `;`; `a+b` means both parts must appear; `!x` means the clip fails if `x` appears (near-duplicate trap). Matching is done after normalization (tashkeel/tatweel removed, ال/لل clitics stripped, أإآٱ→ا, ة→ه, ى→ي, ؤ→و, ئ→ي, Arabic-Indic digits → 0-9). Spoken numbers (صفر خمسة وخمسين, اثنعش) are converted to digits before comparing.

| # | Utterance (say exactly) | Intent | Critical entities | Acceptable variants | Speaker notes |
| --- | --- | --- | --- | --- | --- |
| 1 | بكم الصحون الزجاج؟ | price_check | product = صحون زجاج | صحن زجاج · صحون زياي · أطباق زجاج · طبق زجاج · fails on «بلاستيك» | Normal pace, quiet room. S2: Hasawi ج→ي (الزياي) if natural |
| 2 | عندكم كاسات ورق؟ | availability | product = أكواب ورق | كاسات ورق · كاسة ورق · كاس ورق · كوب ورق · أكواب ورقية · fails on «زجاج» | Casual, slightly fast, TV or fan on low |
| 3 | أبي اثنعش علبة من أكياس الزبالة | order_item | qty = 12 · product = أكياس نفايات | qty: any form of 12 · product: أكياس زبالة · كيس زبالة · أكياس قمامة | Fast, elided. **Trap item is a proposal** (see below) |
| 4 | رقمي صفر خمسة خمسة، واحد اثنين ثلاثة، أربعة خمسة ستة سبعة | give_phone | phone = 0551234567 | digits or words | Grouped 3·3·4, short pauses |
| 5 | جوالي صفر خمسة وخمسين، ثمانية وسبعين، ثلاثة أربعة خمسة ستة سبعة | give_phone | phone = 0557834567 | digits or words | Paired numbers, fast, like reading off a card |
| 6 | وين وصل طلبي؟ رقمه أربعة ثمانية اثنين واحد | order_status | order_id = 4821 | digits or words | First half fast and run together (وينوصل طلبي), then digits one by one |
| 7 | أبي delivery للمبرز بكرة العصر | delivery_order | area = المبرز · slot = بكرة + العصر | Mubarraz · Al Mubarraz · بكره/باكر/بكرا + عصر | Say *delivery* in English, rest Saudi Arabic |
| 8 | متى تفتحون يوم الجمعة؟ | store_hours | day = الجمعة | جمعة · Friday | Kitchen or street noise, not loud |
| 9 | أبي أكلم موظف | escalate | escalate = موظف | موظفين · أحد من الموظفين · مسؤول · مدير | **Angry**: raised, clipped, a bit fast. No extra words |
| 10 | توصلون للهفوف؟ | delivery_area_question | area = الهفوف | هفوف · Hofuf · Hufuf · Al Hofuf | Normal pace, Saudi Arabic |

Deviations from `plan-review.md` §G.1, for the leader to confirm:

- **#5 gains a final «سبعة».** The review's text (صفر خمسة وخمسين، ثمانية وسبعين، ثلاثة أربعة خمسة ستة) is 055·78·3456 = 9 digits and cannot equal its own target 0557834567. Adding «سبعة» makes it 055·78·34567 = 0557834567.
- **#3 trap item = أكياس زبالة (common) for shelf name أكياس نفايات.** Confirmed by Ahmed 2026-10-28. If a later trap-items file trap-items file picks another item, change the utterance, `critical_entities` and `acceptable_variants` for both #3 rows in the CSV.
- **#6 order id is numeric (4821), no «MG».** Plan amendment 4 replaces `MG-4821` with numeric ids.
- #9 keeps the review's wording; the "angry" stress is in the delivery, not extra words.
- **#10 is Arabic («توصلون للهفوف؟»), not English.** Ahmed decided on 2026-10-28 that the project is
  Arabic only: Sara never switches to English, so there is no English clip and no English check.

## How to run it (Phase 0b, on the Mac)

1. **Prerequisites.** API key in `.env`; the minimal agent pushed with `agent.language: ar` and a prompt that answers only «تمام». Write the agent's actual `asr.provider` value into the `asr_provider` column instead of `default`.
2. **Speakers.** S1 = Ahmed. S2 = a family member, ideally a different gender or age. Real names are never written in the repo: the sheet only says S1/S2.
3. **One call per clip.** Open the agent (dashboard test call or the local widget page), wait for the greeting, read one card once, wait for «تمام», hang up. Copy the conversation id into `conversation_id` for that row. Do not retry a clip because it sounded bad: the first take is the data. Re-take only if the call itself failed (no audio, cut off), and say so in `notes`.
4. **Order.** S1 does 1→10, S2 does 10→1, so fatigue and warm-up do not all land on the same clips.
5. **Transcripts.** Either paste the user turn into `transcript_heard` exactly as shown, or run `python phase0/stt_score.py docs/phase0/stt_results.csv --fetch` to fill it from the API (reads `transcript[].message` where `role == "user"`).
6. **Human check.** For every row, Ahmed fills `intent_ok` (`y`/`n`: could a receptionist act on this transcript?) and, if he disagrees with the scorer, `entities_correct` as `x/n` or per entity (`product=1;qty=0`). Human values win; the scorer prints every override.
7. **Second provider.** `python phase0/stt_score.py docs/phase0/stt_results.csv --add-run scribe_realtime` appends 20 blank rows; switch `asr.provider` on the agent, repeat steps 3–6. Allowed values (CLI 1.7.1 schema): `elevenlabs`, `scribe_realtime`, `scribe_v2_turbo`.
8. **Score.** `python phase0/stt_score.py docs/phase0/stt_results.csv`. Copy the gate lines into `docs/phase0/decision.md`.

## Gate (plan-review.md §G.3, thresholds confirmed by Ahmed 2026-10-28)

On the best provider, all of:

- (a) intent recoverable in ≥ 18/20 clips;
- (b) product correct (name or alias) in ≥ 5/6 clips (#1–#3);
- (c) quantity (#3) 2/2 and order-id digits (#6) exact 2/2;
- (d) phone digit accuracy ≥ 95% over the 4 phone clips (≤ 2 of 40 digits wrong) and ≥ 2/4 exactly right;
- (e) #7 area + slot 2/2, #8 hours/day 2/2, #9 escalation 2/2.

The scorer reports INCOMPLETE until two providers each have 20 transcribed clips. FAIL → one 30-minute retry (other provider, product names in `asr.keywords`, re-run failing clips) → otherwise NO-GO and the STT fallback (Vapi + Azure `ar-SA` STT, keep ElevenLabs `eleven_flash_v2_5` TTS).

## Privacy

- **Recordings never go in the repo.** If you keep audio, store it in `phase0/recordings/` (git-ignored) or outside the repo, and delete it after `decision.md` is signed.
- **No real names, no real phone numbers.** The numbers on the cards are fake; read them as written, not your own.
- Only the transcribed text of the scripted cards goes in the CSV. If a transcript catches anything else (a name, a side conversation), delete that part before committing.
- Each speaker agrees to the line: «أوافق على استخدام صوتي لاختبار تجريبي، ولن يُنشر التسجيل.» Keep the consent off the repo.

## Printable scenario cards

Print this page (A4, 2 cards per row). Cut along the lines. Speaker writes nothing on the card.

| | |
| --- | --- |
| **Card 1** · S1 / S2<br><br>**بكم الصحون الزجاج؟**<br><br>Pace: normal · Room: quiet | **Card 2** · S1 / S2<br><br>**عندكم كاسات ورق؟**<br><br>Pace: casual, a bit fast · Room: TV/fan on low |
| **Card 3** · S1 / S2<br><br>**أبي اثنعش علبة من أكياس الزبالة**<br><br>Pace: **fast**, words run together | **Card 4** · S1 / S2<br><br>**رقمي صفر خمسة خمسة، واحد اثنين ثلاثة، أربعة خمسة ستة سبعة**<br><br>Pace: steady, pause at each comma |
| **Card 5** · S1 / S2<br><br>**جوالي صفر خمسة وخمسين، ثمانية وسبعين، ثلاثة أربعة خمسة ستة سبعة**<br><br>Pace: **fast**, paired numbers | **Card 6** · S1 / S2<br><br>**وين وصل طلبي؟ رقمه أربعة ثمانية اثنين واحد**<br><br>Pace: first half **fast**, then one digit at a time |
| **Card 7** · S1 / S2<br><br>**أبي *delivery* للمبرز بكرة العصر**<br><br>Say *delivery* in English | **Card 8** · S1 / S2<br><br>**متى تفتحون يوم الجمعة؟**<br><br>Room: light kitchen or street noise |
| **Card 9** · S1 / S2<br><br>**أبي أكلم موظف**<br><br>Tone: **angry**, raised, clipped. No extra words | **Card 10** · S1 / S2<br><br>**توصلون للهفوف؟**<br><br>Pace: normal |

Operator log (fill on paper, copy into the CSV, then throw the paper away):

| Card | Speaker | asr_provider | conversation_id | Re-take? why |
| --- | --- | --- | --- | --- |
| 1–10 | S1 / S2 | | | |
