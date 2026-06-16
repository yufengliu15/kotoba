# Kotoba

*言葉 — the word. Spelled right, read right, on every card.*

![License](https://img.shields.io/badge/license-MIT-111111?style=flat-square)
![Skill](https://img.shields.io/badge/type-agent--skill-111111?style=flat-square)
![Languages](https://img.shields.io/badge/deep_support-Japanese_%26_Mandarin-111111?style=flat-square)

**Importable Anki decks for any language, with the readings actually correct.**

Most AI-generated flashcard decks look fine and are quietly wrong: the furigana is misaligned, the kanji takes its on'yomi where it should be kun'yomi, the pinyin picks the wrong reading of a 多音字, the example sentence reads like a textbook from 1987. One bad batch in your collection and you've memorized a mistake. Kotoba is built around not doing that.

---

You ask for cards. Kotoba plans the deck with you, shows you five samples to approve, then generates, validates, and hands you a standalone `.apkg` you import fresh and review before studying. Nothing is ever merged into your existing collection.

## What makes it different

**It gets the readings right.** Each supported language has a deep reference encoding its specific traps. Japanese: furigana chunking, on'yomi vs kun'yomi, rendaku, jukujikun, counters. Mandarin: pinyin tone marks, 多音字, HSK conventions. These are the exact error classes that embarrass generated decks, and they're handled per-language, not by a generic schema.

**It teaches itself new languages.** Ask for a language that doesn't have a deep reference yet (Korean, Spanish, Russian...) and Kotoba researches that language's failure modes and writes a reference first, automatically, before generating a single card. The deck you get is built on real per-language rules, and the reference is there for next time.

**Real cards, not dictionary dumps.** Natural example sentences at i+1 difficulty (the target word is the hardest thing in the sentence), concise definitions, word + sentence TTS audio in two distinct voices, optional CC-licensed images. Kaishi-1.5k-style layout.

## How it works

```
1. Plan      → language pair, count, level, topic, ordering, audio/images
2. Preview   → ~5 sample cards rendered with the real template — you approve
3. Generate  → cards in batches, honoring the per-language reference
4. Validate  → structural checks + a reading/naturalness self-check
5. Package   → a standalone .apkg, ready to import
```

## Install

### Claude Code

```
/plugin marketplace add yufengliu15/kotoba
/plugin install kotoba@kotoba
```

### Other agents (AGENTS.md)

Any host that reads `AGENTS.md` (Codex, OpenCode, and others) picks up Kotoba from a checkout of this repo with no extra setup. See [`AGENTS.md`](./AGENTS.md).

### Manual

Copy the skill into your skills directory:

```
cp -r skills/kotoba ~/.claude/skills/kotoba
```

### Dependencies

```
pip install genanki edge-tts
```

Audio (edge-tts) and CC-licensed image lookup need network access; everything else runs offline. Use `--no-audio` / `--no-images` to degrade gracefully.

## Use

Just ask, in plain language:

> make me 150 JLPT N4 vocab cards, frequency ordered, with audio

> 100 HSK4 travel words, simplified, no images

> a Korean beginner deck of the 200 most common verbs

Kotoba handles the rest, pausing once for you to approve the card design.

## Layout

```
kotoba/
├── .claude-plugin/
│   ├── plugin.json         # plugin definition
│   └── marketplace.json    # marketplace manifest (enables /plugin install)
├── skills/kotoba/
│   ├── SKILL.md            # the pipeline + language routing
│   ├── references/
│   │   ├── japanese.md     # deep: furigana, on/kun, rendaku, JLPT
│   │   ├── mandarin.md     # deep: pinyin, tones, HSK
│   │   ├── generic.md      # baseline for languages without a deep ref
│   │   ├── deck-json.md    # the deck.json contract
│   │   └── large-decks.md  # multi-session project mode
│   └── scripts/
│       ├── build_deck.py   # TTS, images, genanki packaging
│       └── validate.py     # structural validation
├── AGENTS.md               # portable instructions for AGENTS.md hosts
├── package.json
└── LICENSE
```

## License

[MIT](./LICENSE).
