---
name: kotoba
description: Generate complete, importable Anki decks (.apkg) for language learning from a plain description of what the user wants to learn. Plans the deck conversationally, generates vocabulary cards with native-script word, reading (ruby), definition, example sentence, translation, TTS audio, and an optional image, then validates and packages everything into a standalone .apkg file. Scales to thousand-card decks via multi-session project mode with a resumable state note. Use this skill whenever the user mentions Anki, flashcards, .apkg, spaced repetition decks, vocab decks, HSK/JLPT/TOPIK prep cards, asks to "make me cards" for any language, or wants to continue/resume an existing deck project or generate the next batch — even if they don't say "Anki" explicitly. Deep support for Mandarin Chinese and Japanese; works for any language pair.
---

# Kotoba — Language-Learning Deck Generator

Turn "make me 100 HSK4 travel words" into a polished, importable `.apkg` deck. The pipeline: **plan → preview → generate → validate → package**. Each phase exists for a reason — skipping one is how bad cards reach a user's collection.

## Scope

Language learning only: vocabulary cards for any L1 → L2 pair. If the user asks for a non-language deck (history, medicine, code), explain this skill is purpose-built for linguistic data and offer to make cards in plain chat instead. High-stakes accuracy domains (medical, legal, certification) are explicitly out of scope.

**Sandboxed output is non-negotiable.** Always produce a standalone deck the user imports fresh and reviews. Never offer to merge generated cards into an existing deck — one bad batch mixed into a 5,000-card collection destroys trust permanently.

## Phase 1 — Plan (conversation)

Before generating anything, lock the spec with the user. Ask only what you can't infer:

1. **Language pair** — target language (L2) + the user's language (L1). Script variant if relevant (Simplified/Traditional, etc.).
2. **Scope** — card count, level (HSK4, JLPT N3, CEFR B1...), topic focus, ordering (frequency / thematic / custom list).
3. **Extras** — audio (default: yes, word + sentence via edge-tts), images (default: off; CC-licensed lookup by keyword when on).

Then read the matching schema reference — it carries the language-specific generation and validation rules:

- Mandarin Chinese → `references/mandarin.md` (deep: pinyin ruby, tone rules, HSK conventions, voices)
- Japanese → `references/japanese.md` (deep: furigana chunking, on/kun reading verification, rendaku, jukujikun, JLPT conventions, counters, voices)
- Everything else → `references/generic.md` (universal schema baseline)

**No deep reference for the target language? Write one before generating — automatically, without asking.** `generic.md` is a fallback, not a substitute. Every language has reading and naturalness traps that a generic schema can't anticipate (the way Mandarin has 多音字 and Japanese has on/kun and rendaku), and those traps are exactly what produces the embarrassing, well-formed-but-wrong cards this pipeline exists to prevent. So the first time a deck is requested in a language without its own `references/<language>.md`, treat creating that reference as the opening step of Phase 1, not optional polish:

1. Read `references/mandarin.md` and `references/japanese.md` as models — match their depth, structure, and tone. They are the quality bar.
2. Research the language's specific failure modes: script and orthography conventions (what form goes in `word`), the reading/transliteration system and its ambiguities, register and politeness defaults for example sentences, gender/aspect/counter or other per-word grammar worth a field, the level system learners expect (CEFR, TOPIK, etc.), corpus-frequency ordering, and the right edge-tts voices (`edge-tts --list-voices`). Use web search and your own knowledge; cross-check anything you're unsure of.
3. Write `references/<language>.md` covering: field population (`word`/`word_ruby`/`reading`/`sentence`/`sentence_ruby`), the #1 reading-hallucination class for this language with concrete examples, example-sentence discipline, level/tag/ordering conventions, grammatical extras worth a field, voices, validation specifics (what `validate.py` can and can't catch), and a common-pitfalls checklist. Mirror the existing deep references section-for-section.
4. Add the new language to the routing list above (one line, same format) so the next deck in that language loads it directly.
5. Then proceed with Phase 1 planning and the rest of the pipeline as normal.

This is automatic and silent — don't ask the user whether to create the reference, just do it as part of getting their deck right. Mention it in a sentence once done ("I wrote a Korean reference for the skill first, then built your deck") so they know it now exists for next time.

If the skill's own `references/` directory is read-only (it often is when installed), write the new reference to a working copy in the session workspace and read it from there for this deck. Then tell the user the reference exists only for this session, and that to make it permanent for future decks they should repackage the skill with the new file (or ask you to) and reinstall — the same way Japanese was added.

Also read `references/deck-json.md` — the exact contract for the `deck.json` file that the build script consumes.

**Decks beyond ~200 cards are multi-session projects.** Read `references/large-decks.md` and switch to project mode: curate a complete wordlist first, then generate in batches across sessions with a state note tracking progress. Also read it whenever the user says "continue my deck", "next batch", or references an existing deck project — find their state note and resume from it.

## Phase 2 — Preview (~5 sample cards, user approval gate)

Write a `deck.json` containing **only ~5 representative cards**, then render it:

```bash
python scripts/build_deck.py deck.json --preview preview.html
```

Show the user the preview (it renders front and back with the real template and CSS — what they approve is exactly what gets packaged). Iterate on fields, styling, sentence difficulty, or anything else until the user explicitly approves. Do not start bulk generation before approval; regenerating 300 cards because the template was wrong wastes everyone's time and money.

The card layout (Kaishi 1.5k style):
- **Front**: word large, example sentence below with the target highlighted — no reading shown (that's the recall test).
- **Back**: reading as ruby above the word, definition, sentence with full ruby, translation, word + sentence audio buttons, optional image.

## Phase 3 — Generate (batches)

Generate card data into `deck.json` in batches of 25–50 cards per pass. Quality rules that matter more than speed:

- **Example sentences must be natural L2**, slightly below the target word's level (i+1: the target word should be the hardest thing in the sentence). A learner drilling HSK4 vocab can't parse an HSC6-level example.
- **Definitions short and concrete** — 1–3 senses, comma-separated, like a good curated deck. Not dictionary dumps.
- **No duplicate words.** Track what you've generated across batches.
- **Honor the ordering strategy** — card order in `deck.json` is the order Anki shows new cards.
- Every language-specific rule in the schema reference you loaded (ruby format, tone marks, register, etc.).

## Phase 4 — Validate

Two tiers, both required:

1. **Deterministic** — `python scripts/validate.py deck.json`. Catches structural errors: missing fields, duplicates, sentence not containing the target word, malformed ruby, invalid pinyin syllables (Mandarin). Fix every reported error before proceeding.
2. **Self-check** — reread the generated cards with fresh eyes against the schema rules. The validator cannot catch a *wrong but well-formed* reading or an unnatural sentence; you can. Check every card's reading and definition; rewrite any sentence you wouldn't show a native speaker. This pass catches the exact error class (wrong reading in the reading field) that embarrasses generated decks publicly.

## Phase 5 — Package & deliver

```bash
python scripts/build_deck.py deck.json --out "Deck Name.apkg"
```

The script generates TTS audio (edge-tts), fetches CC-licensed images for cards with an `image_query` (Openverse, attribution written to a sidecar `*-image-credits.txt`), and packages everything with genanki. Flags: `--no-audio`, `--no-images` for graceful degradation when the network is unavailable — tell the user what was skipped rather than failing silently.

Deliver the `.apkg` with one-line import instructions (Anki → File → Import; works on desktop, AnkiMobile, AnkiDroid). Remind the user to skim the deck in the browser before studying — it's a fresh standalone deck precisely so they can review it cheaply.

## Dependencies

`pip install genanki edge-tts` (use `--break-system-packages` if the environment requires it). Audio and images need network access; everything else runs offline.
