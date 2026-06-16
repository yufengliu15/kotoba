# deck.json contract

The single file `scripts/build_deck.py` and `scripts/validate.py` consume. Everything the scripts need lives here; the scripts never invent content.

## Top level

```json
{
  "deck_name": "Mandarin HSK4 — Travel Vocabulary",
  "language": "zh-CN",
  "voice_word": "zh-CN-XiaoxiaoNeural",
  "voice_sentence": "zh-CN-YunxiNeural",
  "tags": ["HSK4", "travel", "ankigen"],
  "cards": [ ... ]
}
```

| Key | Required | Notes |
|---|---|---|
| `deck_name` | yes | Shown in Anki. Also seeds the stable deck/model IDs, so re-building the same name updates rather than duplicates on re-import. |
| `language` | yes | BCP-47-ish code (`zh-CN`, `zh-TW`, `ja-JP`, `fr-FR`...). Picks default TTS voices if the voice keys are omitted. |
| `voice_word` / `voice_sentence` | no | edge-tts voice names. Use two different voices so word and sentence are audibly distinct. `edge-tts --list-voices` shows options. |
| `tags` | no | Applied to every card, plus any per-card tags. |

## Card object

```json
{
  "word": "特别",
  "word_ruby": "<ruby>特<rt>tè</rt></ruby><ruby>别<rt>bié</rt></ruby>",
  "reading": "tèbié",
  "definition": "special, particularly",
  "pos": "adj / adv",
  "sentence": "你对我来说是<span class=\"t\">特别</span>的人。",
  "sentence_ruby": "<ruby>你<rt>nǐ</rt></ruby><ruby>对<rt>duì</rt></ruby>...<span class=\"t\"><ruby>特<rt>tè</rt></ruby><ruby>别<rt>bié</rt></ruby></span>...",
  "sentence_meaning": "You're someone special to me.",
  "image_query": "star sky",
  "notes": "",
  "tags": ["HSK4"]
}
```

| Field | Required | Rules |
|---|---|---|
| `word` | yes | Target word in native script. Unique across the deck. |
| `word_ruby` | scripts with readings | Per-character `<ruby>字<rt>reading</rt></ruby>` HTML. Empty string for Latin-script languages — the template falls back to showing `reading` as a plain line. |
| `reading` | yes for non-Latin L2 | Plain transliteration (pinyin with tone marks, romaji, etc.). Searchable in Anki. |
| `definition` | yes | L1 meaning. 1–3 senses, comma-separated, concise. |
| `pos` | no | Part of speech, short form. |
| `sentence` | yes | Natural L2 sentence containing the word, with the target occurrence wrapped in `<span class="t">…</span>`. No ruby here — the front shows the sentence bare. |
| `sentence_ruby` | non-Latin L2 | Same sentence with ruby on every character/word that needs a reading, target still wrapped in the span. Shown on the back. |
| `sentence_meaning` | yes | L1 translation of the sentence. |
| `image_query` | no | Short **English** keyword(s) for the CC image lookup. Pick concrete, imageable nouns ("airport", "red apple") — abstract words usually return noise, leave them imageless. Only used when images are enabled. |
| `notes` | no | Usage notes, register warnings, mnemonics. Rendered small on the back. |
| `tags` | no | Per-card Anki tags (level, theme). |

## What the build script does with this

- **Audio**: synthesizes `word` → word audio, and `sentence` (HTML stripped) → sentence audio. Filenames are content-hashed, so re-runs reuse identical audio.
- **Images**: for cards with `image_query`, downloads the best CC-licensed thumbnail from Openverse; skips quietly on no result. Attribution lines go to `<out>-image-credits.txt`.
- **Packaging**: genanki note per card, fields in template order, `deck.json` order preserved as the new-card order.

## Preview mode

`--preview preview.html` renders every card front + back with the production CSS, audio buttons as static glyphs, images inline if already fetched. Use it for the Phase 2 approval gate.
