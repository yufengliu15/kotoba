# Generic language schema

Universal rules for any L1 → L2 pair that doesn't have its own deep reference (Mandarin and Japanese each have one). The card model is identical everywhere — what changes is how `word_ruby`, `reading`, and the sentence fields are populated. If you're building a deck in a language that *should* have its own deep reference but doesn't yet, create one first (see Phase 1 in SKILL.md) rather than leaning on these generic notes.

## Field population by script type

**Latin-script L2** (Spanish, French, German, Indonesian...):
- `word_ruby`: empty string. The template then shows the word plain and prints `reading` as a small line only if non-empty.
- `reading`: usually empty. Use it for IPA only if the user asks.
- `sentence_ruby`: empty string — the back falls back to the plain `sentence`.

**Korean**:
- `word_ruby`: empty (hangul is read directly). `reading`: revised romanization only for absolute beginners.
- Mind register: default to 해요체 in example sentences unless asked otherwise; note 한자어 vs native distinctions in `notes` when useful.
- Voices: `ko-KR-SunHiNeural` / `ko-KR-InJoonNeural`.

**Other non-Latin scripts** (Russian, Arabic, Thai, Hindi, Greek...):
- `word_ruby`: empty. Put the standard romanization in `reading` (it renders as a line above the definition on the back).
- Arabic: include full diacritics (tashkeel) in `word` and `sentence` — learners can't read undiacritized text. Thai: no spaces needed, but keep sentences short.

## Language-specific essentials worth a card field

Put these in `definition` or `notes`, whichever reads cleaner:

- **Grammatical gender** (German der/die/das, French le/la, Spanish el/la): include the article in `word` itself ("der Tisch") — gender drilled separately from the noun never sticks.
- **Verb aspect pairs** (Russian писать/написать): note the pair in `notes`.
- **Plural/principal parts** when irregular (German Häuser, English-learner irregular verbs).
- **Counters/classifiers** (Japanese, Korean, Thai): note the common counter.

## Example sentences

Same discipline as Mandarin: natural, spoken register by default, i+1 difficulty (target word is the hardest token), 5–15 words, target word exactly once wrapped in `<span class="t">`, varied sentence frames across the deck.

## Voices

Run `edge-tts --list-voices` for the full list; pick one female + one male voice of the right locale for word/sentence. If a language has no edge-tts voice, build with `--no-audio` and tell the user why.

## Validation

`validate.py` runs the structural checks (fields, duplicates, target-in-sentence, ruby well-formedness) for all languages; pinyin syllable checking is Mandarin-only. The Phase 4 self-check carries proportionally more weight for languages without deterministic reading checks — verify every reading manually.
