# Large decks: multi-session projects (200+ cards)

A thousand-card deck cannot be generated well in one sitting — quality drifts, words duplicate, and the session ends before the deck does. For anything beyond ~200 cards, switch to **project mode**: split the work into two phases with durable files between them, so any future session can resume exactly where the last one stopped.

## The two phases

**Phase A — Curate (once).** Produce the complete wordlist *before any cards are generated*:

1. Lock the deck spec with the user as usual (Phase 1 of SKILL.md), plus the template approval gate with ~5 sample cards.
2. Build `wordlist.json`: every target word the deck will contain, in final order, each entry `{"word": ..., "hint": "<level/frequency/theme note>", "status": "todo"}`. Source it from a real inventory (official HSK/JLPT lists, a frequency corpus, the user's own list) rather than improvising — improvised lists drift toward common words and repeat themselves.
3. Have the user review the wordlist (or at least its size, ordering, and a sample). This is cheap to fix now and expensive to fix after 800 cards exist.

**Phase B — Generate (many sessions).** Burn down the wordlist in batches:

1. Read the state note (below) and `wordlist.json`; take the next 25–50 `"todo"` words.
2. Generate full card objects, append to `deck.json`, run `validate.py`, do the self-check, mark those words `"done"`.
3. Update the state note (batches completed, decisions made, anything irregular).
4. At any point, `build_deck.py` can package the partial deck — stable deck IDs mean re-importing a newer build updates the deck in place instead of duplicating it. Encourage the user to import early and start studying while the rest generates.

## The state note

Keep a markdown note per deck project — the kickoff document for future sessions. Where it lives is the user's choice (their notes vault, the project folder, anywhere durable). It should contain:

- **Spec**: language pair, level, ordering strategy, fields, voices, images on/off, anything the user decided during planning.
- **Files**: paths to `wordlist.json`, `deck.json`, media dir, latest `.apkg`.
- **Progress**: words done / total, last batch date, last validation result.
- **Decisions log**: one line per session — rulings made mid-generation ("X uses the Taiwan reading per user", "skipping images for abstract nouns") so later sessions stay consistent instead of re-deciding.

When a user says "continue my deck", "next batch", or similar: find and read the state note first, then proceed with Phase B. Honor every decision already logged — consistency across sessions is what makes a 2,000-card deck feel hand-curated.

## Scale notes

- **Audio scales fine**: filenames are content-hashed, so re-runs only synthesize missing files. ~2,000 cards ≈ 4,000 clips; expect a long but unattended run. Use `--media-dir` pointed at one persistent directory for the whole project.
- **Images do not scale well**: keyword CC lookup is slow and noisy at volume. For large decks default images off, or enable them only for concrete, imageable nouns.
- **Validation is cheap** — run it every batch, not once at the end. A schema mistake caught at batch 2 costs 50 cards; at batch 40 it costs a rebuild.
- **Duplicate protection across sessions** comes from the wordlist, not memory: never generate a word that isn't in `wordlist.json`, and never regenerate one marked `"done"`.
