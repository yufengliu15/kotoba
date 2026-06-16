# Japanese schema (deep)

Rules for generating Japanese vocabulary cards. These exist because the most common public failures of LLM-generated Japanese decks are **wrong kanji readings (on/kun confusion)**, **furigana that doesn't align with its kanji**, **unnatural textbook sentences**, and **pitch/register mismatches**. Every rule below closes one of those holes. This is the Japanese analog of `mandarin.md`; read it instead of (not in addition to) the generic Japanese notes when building a Japanese deck.

## Script: kanji, kana, and what goes in `word`

- `word` holds the **standard written form** the learner will actually meet, not an artificially kana-fied or kanji-fied version. 食べる, not たべる. 綺麗 is usually written 綺麗 or きれい depending on register — prefer the form that dominates in real text (here, きれい is more common; note the kanji in `notes`).
- **Don't over-kanjify.** Many words are conventionally written in kana: ある, いる, こと, もの, できる, とても, きれい, ください, よろしく. Forcing 有る/居る/出来る onto these produces text no native writes. When unsure, default to the more common kana form and mention the kanji form in `notes`.
- **Don't under-kanjify either.** 学校 should be 学校, not がっこう. The target written form is the one in newspapers and novels.
- Okurigana (trailing kana) are part of the word: 食べる, 新しい, 飲み物. Conjugation lives in example sentences, not in `word` (cite verbs in dictionary form, i-adjectives in plain form).

## Readings — the #1 hallucination class (on'yomi vs kun'yomi)

This is Japanese's equivalent of 多音字. The same kanji has multiple readings, and the LLM's instinct is to pick the most frequent one rather than the correct one for *this* compound. **Before finalizing any card, verify the reading is correct for the specific word, not the character's default.**

Highest-risk patterns:

- **Compounds (熟語) usually take on'yomi; standalone kanji + okurigana usually take kun'yomi.** 生 reads せい in 学生 (がくせい), なま in 生 (なま, "raw"), い in 生きる (いきる), う in 生まれる (うまれる), き in 生地, お in 生い立ち. One kanji, six+ readings — the compound decides which.
- **Same compound, two valid readings, different meaning.** 上手 = じょうず ("skilled") but かみて ("stage left"); 一日 = いちにち ("one day, duration") but ついたち ("the 1st of the month"); 日本 = にほん / にっぽん; 何 = なに / なん (何人 なんにん, 何が なにが).
- **Rendaku (連濁): the second element voices.** 手紙 = てがみ (not てかみ); 時計 = とけい; 花火 = はなび; 人々 = ひとびと. The reading field and furigana must show the voiced form.
- **Irregular / 熟字訓 readings that map to the whole word, not character-by-character.** 今日 きょう, 明日 あした/あす, 昨日 きのう, 大人 おとな, 一人 ひとり, 二人 ふたり, 果物 くだもの, 部屋 へや, 上手 じょうず, 下手 へた, 田舎 いなか, 眼鏡 めがね, 時雨 しぐれ. For these you **cannot** split furigana per kanji sensibly — put the whole reading on the whole kanji block (see Furigana, "jukujikun" below).
- **Numbers and counters mutate.** 一 changes across 一本 (いっぽん), 一杯 (いっぱい), 一匹 (いっぴき), 一回 (いっかい). 三 + 百 = さんびゃく, 六 + 百 = ろっぴゃく, 八 + 百 = はっぴゃく. Verify the counter reading, don't assume いち/に/さん stay clean.

When in doubt, the reading is the thing to verify character by character in the Phase 4 self-check. A well-formed but wrong reading is exactly the error class that gets a public deck mocked.

## Furigana format (`word_ruby` and `sentence_ruby`)

The renderer uses `<ruby>漢字<rt>かな</rt></ruby>`. Two rules govern how to chunk it:

- **Group a kanji block into one ruby element with its full kana reading; keep okurigana outside.**
  - 特別 → `<ruby>特別<rt>とくべつ</rt></ruby>`
  - 食べる → `<ruby>食<rt>た</rt></ruby>べる` (the べる is kana, stays bare)
  - 新しい → `<ruby>新<rt>あたら</rt></ruby>しい`
  - 飲み物 → `<ruby>飲<rt>の</rt></ruby>み<ruby>物<rt>もの</rt></ruby>` (the み between two kanji stays bare; each kanji gets its own ruby because they read independently)
- **Jukujikun / irregular whole-word readings get ONE ruby over the whole kanji span**, because the reading can't be split per character:
  - 今日 → `<ruby>今日<rt>きょう</rt></ruby>` (never 今<rt>きょ</rt>日<rt>う</rt> — that's nonsense)
  - 大人 → `<ruby>大人<rt>おとな</rt></ruby>`, 明日 → `<ruby>明日<rt>あした</rt></ruby>`
- Pure-kana words get **empty** `word_ruby` (and the template shows `reading`): ある, きれい, とても → `word_ruby: ""`.
- In `sentence_ruby`, put furigana on **every kanji** (Kaishi-style: full readings on the back). Kana, punctuation, and Latin text stay outside ruby tags.
- The target word inside `sentence_ruby` keeps its highlight wrapping the ruby:
  `<span class="t"><ruby>特別<rt>とくべつ</rt></ruby></span>`.

Validation note: the build's well-formedness check re-joins ruby **base** characters and compares to `word`. For jukujikun that's fine (base = full kanji span). What it cannot check is whether きょう is the *right* reading for 今日 — that's the self-check.

## `reading` field

- Full **kana** (hiragana for native words / kun'yomi, the conventional kana for the word). とくべつ, たべる, きょう.
- Use katakana when the word itself is katakana (コーヒー, テレビ, パソコン) — `reading` mirrors the word's own kana.
- Romaji only if the learner is an absolute beginner and explicitly asks; even then, prefer kana and treat romaji as a crutch to remove fast.
- For pitch accent: do **not** encode pitch in `reading` (it stays clean kana). If pitch matters to the user, note the accent pattern (e.g. "[0] heiban" or "は↓し vs はし↑") in `notes`.

## Example sentences

- **Natural, modern Japanese.** Default register is **polite desu/masu (丁寧体)** for standalone study sentences, because that's what a learner produces first and hears most. Switch to casual (常体) only if the word is inherently casual (やばい, すごく as an intensifier in speech) and note it.
- **i+1 difficulty**: the target word should be the hardest item in the sentence. For an N3 card, build the frame from N5–N4 grammar and vocab. Don't drop an N1 grammar point into an N4 word's example.
- **Length: roughly 8–20 characters of content** (short enough to drill, long enough to disambiguate the reading and meaning). Japanese sentences with full furigana get visually long fast — keep them tight.
- The target word appears **exactly once**, in a natural collocation, wrapped in `<span class="t">`. Show it conjugated naturally (a verb card 食べる can appear as 食べました in the sentence — the reading test is still valid because the back furigana covers it).
- **Particles must be correct and idiomatic** — は/が, に/で, を/が confusion is the fastest way to make a sentence read as machine-translated. が as subject vs は as topic; 〜に行く (destination) vs 〜で食べる (location of action).
- **Avoid the textbook smell.** これはペンです / 私は学生です-style frames are dead. Use realistic situations and natural collocations. Don't reuse one frame ("私は〜が好きです") across many cards.
- Don't drop the subject mechanically and don't over-state it either — Japanese omits 私は when obvious. Forcing 私は onto every sentence is a tell.

## Levels, tags, and ordering

- Tag with **JLPT level** when known: `N5`, `N4`, `N3`, `N2`, `N1`. This is the convention Japanese learners expect (the analog of HSK bands).
- JLPT has no official word list since 2010; use a widely-accepted community list (e.g. Jreibun / Jisho JLPT tags / the common Anki N-level decks) and say which when it matters.
- **Frequency ordering**: when the user wants "most useful first", order by corpus frequency (BCCWJ / Netflix-subtitle frequency intuition), which does **not** match JLPT order — many high-frequency words (やる, ちょっと, だから) sit oddly in the JLPT bands.
- Mark a word's typical **register/script reality** in tags or notes when it diverges from the kanji form (e.g. "usually written in kana").

## Counters and grammatical extras worth a field

Put these in `definition` or `notes`, whichever reads cleaner:

- **Counter (助数詞)** for nouns: 本 (long things), 枚 (flat things), 匹/頭 (animals), 個, 人, 台, 冊. A noun without its counter never fully sticks — note 犬 → 匹, 本(book) → 冊.
- **Transitivity pairs (自動詞/他動詞)**: 開く/開ける, 始まる/始める, 出る/出す. Note the partner in `notes`; this distinction is high-value and constantly confused.
- **する-verbs**: nouns that verbalize with する (勉強→勉強する). Note it so the learner knows the word's verbal use.
- **な-adjective vs い-adjective**: tag な-adjectives (静か[な], 綺麗[な]) so conjugation is unambiguous. i-adjectives cite in plain form (新しい).
- **Pitch accent pattern** in `notes` when the user is targeting pronunciation, and especially for minimal pairs (箸 はし[1] vs 橋 はし[2] vs 端 はし[0]).
- **Katakana loanword origin** when non-obvious or "wasei-eigo" (アルバイト from German, マンション = apartment not mansion) — note it; the false-friend meaning is a common trap.

## Voices (edge-tts)

| Role | Voice |
|---|---|
| Word | `ja-JP-NanamiNeural` (f) |
| Sentence | `ja-JP-KeitaNeural` (m) |

Two different voices on purpose: the learner hears the word in isolation from one speaker and the sentence from another, which aids generalization. `ja-JP-AoiNeural`, `ja-JP-MayuNeural`, `ja-JP-ShioriNeural` are alternatives if the user wants a different timbre.

## Validation specifics (what validate.py checks for ja)

The deterministic validator (`scripts/validate.py`) checks structure only:

- Required fields present; no duplicate `word` across the deck.
- `sentence` contains `word` (after stripping the `<span>`/ruby tags) — note this can false-fail when the target is **conjugated** in the sentence (食べる vs 食べました). If the validator flags a conjugated target, confirm by eye that the dictionary form is genuinely present in the surface form and treat it as a pass; don't de-conjugate `word` to satisfy the checker.
- Ruby well-formedness: every `<rt>` has a base, tags balanced, `word_ruby` base characters re-join to `word`.
- `reading` ≈ kana of the word.

What it **cannot** check (this is the Phase 4 self-check's whole job, and it carries more weight in Japanese than in Mandarin because there's no per-syllable reading validator):

- Whether the reading is the **correct** on/kun/jukujikun reading for this specific word (check every kanji against the on/kun risk list above).
- Whether **rendaku** was applied correctly (てがみ not てかみ).
- Whether the **counter, transitivity, and register** notes are right.
- Whether the sentence is **natural** (particles, collocation, no textbook smell) — reread every sentence as if a native were grading it; rewrite any you wouldn't say out loud.

## Common pitfalls checklist (run before packaging)

1. **Reading default-bias** — did you reflexively use the on'yomi/most-common reading instead of this word's actual reading? (生, 上, 下, 日, 人, 何, 行, 大, 中, 間, 方, 気 are repeat offenders.)
2. **Rendaku missed or over-applied** — second-element voicing present where it should be, absent where it shouldn't.
3. **Jukujikun split per kanji** — 今日 must be one ruby (きょう), not split.
4. **Over-kanjification** — forcing kanji onto words normally written in kana (ある, きれい, こと, できる).
5. **Furigana misalignment** — okurigana accidentally inside the ruby base, or a kanji block's reading not matching its characters.
6. **Particle errors** in the example sentence (は/が, に/で, を).
7. **Wrong conjugation register** — casual form where polite was expected, or vice versa.
8. **Counter omitted** for a noun where the counter is essential.
9. **Transitivity pair confused** (開く vs 開ける) in the definition or sentence.
10. **Katakana false friend** (マンション, アルバイト) left unexplained.
11. **Textbook-smell sentence** — これは〜です frames, forced 私は, no real situation.
12. **Pitch-accent minimal pairs** (箸/橋/端) not flagged when the deck targets pronunciation.
