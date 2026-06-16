# Mandarin Chinese schema (deep)

Rules for generating Mandarin vocabulary cards. These exist because the most common public failures of LLM-generated Chinese decks are wrong pinyin, wrong 多音字 readings, and stilted example sentences. Every rule below closes one of those holes.

## Script and variant

- Ask Simplified (`zh-CN`) or Traditional (`zh-TW`) during planning; default Simplified.
- Never mix scripts inside one deck. 头发/頭髮 class differences mean conversion is not 1:1 — generate natively in the chosen script, don't transliterate between them.

## Pinyin

- **Tone marks, not tone numbers**: `tèbié`, never `te4bie2`. Tone marks go on the correct vowel (a > o = e > i = u = ü; for `iu`/`ui` the mark goes on the second vowel).
- `ü` is written `ü` (lǜ, nǚ) — except after j/q/x/y where it's plain `u` (jù, qù, xū, yǔ).
- **Neutral tone** syllables get no mark: `xiéhe` wrong → `xiéhé` or neutral `de`, `ma`, `le`, `zi`, `men`, `lia` etc. written bare: `háizi`, `māma`.
- **Tone sandhi is NOT written**: 不 is always `bù`, 一 is always `yī` in the reading field, third-tone pairs keep their citation tones (`nǐ hǎo`, not `ní hǎo`). Readings record citation form; pronunciation rules live in the learner's head.
- `reading` field: syllables of one word run together (`tèbié`), spaces between words in multi-word entries.

## 多音字 (polyphonic characters) — the #1 hallucination class

Before finalizing any card whose word contains 得, 了, 着, 长, 行, 重, 还, 觉, 教, 便, 地, 都, 乐, 数, 切, 发, 当, 假, 间, 倒, 好, 为 — stop and verify the reading matches *this word's* pronunciation, not the character's most common one. Examples: 觉得 `juéde` but 睡觉 `shuìjiào`; 银行 `yínháng` but 行为 `xíngwéi`; 长城 `Chángchéng` but 长大 `zhǎngdà`. The ruby in the example sentence must also use the in-context reading (e.g. 了 as `le` aspect marker vs `liǎo` in 了解).

## Ruby format

Per character: `<ruby>特<rt>tè</rt></ruby><ruby>别<rt>bié</rt></ruby>`. One hanzi per `<ruby>` element so readings align visually.

- In `sentence_ruby`, give **every** hanzi its ruby (learners at the deck's level still get full readings on the back, matching Kaishi style). Punctuation and Latin text stay outside ruby tags.
- The target word inside `sentence_ruby` keeps its highlight: `<span class="t"><ruby>特<rt>tè</rt></ruby><ruby>别<rt>bié</rt></ruby></span>`.
- Neutral-tone characters get their bare-vowel pinyin in `<rt>` (`<ruby>子<rt>zi</rt></ruby>`).
- Erhua: attach `r` to the syllable it modifies: `<ruby>玩儿<rt>wánr</rt></ruby>` (儿 may share the ruby element with its host).

## Example sentences

- Natural spoken-register Mandarin unless the word itself is formal/written register (then say so in `notes`).
- **i+1**: every other word in the sentence should be at or below the deck's level. For HSK4 cards, the sentence frame should be HSK1–3 vocabulary.
- 8–20 characters. Long enough for context, short enough to drill.
- The target word appears exactly once, wrapped in `<span class="t">`.
- Don't reuse sentence frames ("我觉得X很Y") across many cards — variety is what makes sentences memorable.

## Levels and tags

- Tag with HSK level when known (`HSK4`); use HSK 3.0 band if user asks for the new standard, otherwise classic HSK 1–6 is the convention learners expect.
- Frequency ordering: when the user wants "most useful first", order by corpus frequency (SUBTLEX-CH intuition), not HSK list order.

## Voices (edge-tts)

| Variant | Word voice | Sentence voice |
|---|---|---|
| zh-CN | `zh-CN-XiaoxiaoNeural` (f) | `zh-CN-YunxiNeural` (m) |
| zh-TW | `zh-TW-HsiaoChenNeural` (f) | `zh-TW-YunJheNeural` (m) |

Two different voices on purpose: the learner hears the word in isolation and the sentence from a different speaker, which aids generalization.

## Validation specifics (what validate.py checks for zh)

- Every `<rt>` is a structurally valid pinyin syllable (tone-mark normalized).
- Ruby base characters re-joined equal `word` exactly.
- `sentence` contains `word` (tags stripped).
- `reading` ≈ concatenation of the word's `<rt>` syllables.

What it **cannot** check: whether a valid syllable is the *correct* reading for this word, and whether the sentence is natural. That is the Phase 4 self-check's job — do it character by character for the 多音字 list above.
