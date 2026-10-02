# Lyrics notes — decisions

Your 12 original lines (`original_lines.txt`) are kept as you wrote them, with **one**
spelling change you approved: "Rap sikhane wale" → "Rap sikhane **waale**". The automated tests check that every one of these lines appears word-for-word in
`final_lyrics.txt` and in `subtitles.srt`.

## Decisions

Items 1, 3 and 6 were decided by Rishi; the rest are kept as written.

| # | Line | Question | Decision / assumption |
|---|------|----------|----------------|
| 1 | "Zaban inki **mitthi**" | *meethi* (sweet) or *mitti* (soil/dirt)? | **DECIDED: meethi (sweet).** Spelling "mitthi" kept on screen; the AI singer is sent "meethi" (`pronunciation_overrides`) so it isn't sung as *mitti*. |
| 2 | "**Q ki**" (×2) | Texting shorthand for *kyunki* (because). | Kept on screen as "Q ki". **For AI vocals only**, it is sent as "kyunki" (see `pronunciation_overrides` in `config/project.json`) so the singer doesn't say "queue ki". |
| 3 | "What the fuck he has **wrote**?" | Grammatically "has written". Explicit word. | **DECIDED: keep as is (explicit).** The track is marked explicit. |
| 4 | "Jab tak inki badal **jaati** soch" | Strict grammar would be "badal na jaaye". | Meaning: "until their mindset changes". Kept. |
| 5 | "Ab bhi hum shine karte mere school waale dost" | Who shines — "we (me + my school friends) still shine", or "my school friends still make us shine"? | "We still shine together — my school friends." Kept. |
| 6 | "Rap sikhane **wale**" vs "college **waale**" | Spelling is inconsistent within the line. | **DECIDED: changed to "waale".** |
| 7 | "line **me**" vs "niyat **mein**" | Two spellings of the same word. | Kept as written. |

## What I wrote around your lines

All additional lines are new and original. Themes: fake smiles / sweet talk (V1), haters,
greed vs. hard work, live shows and cheap tickets (V2), school + college friends and loyalty (V3),
and a chantable "Soch!" call-and-response hook. No lines, flows or titles from other artists
were used or referenced.

Placement of your lines:
- Verse 1: lines 1–4 open the verse, lines 5–8 are the verse's turn.
- Verse 2: opens with the two "Q ki" show/ticket lines.
- Verse 3: opens with the school/college friends lines.
