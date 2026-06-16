#!/usr/bin/env python3
"""Deterministic validation for AnkiGen deck.json files.

Catches structural errors before packaging: missing fields, duplicate words,
target word absent from its sentence, malformed ruby, invalid pinyin syllables
(Mandarin). It cannot judge whether a well-formed reading is the CORRECT
reading, or whether a sentence is natural -- that is the LLM self-check's job.

Usage: python validate.py deck.json
Exit code 0 = clean, 1 = errors found (printed to stdout).
"""
import json
import re
import sys
import unicodedata

RUBY_RE = re.compile(r"<ruby>(.*?)<rt>(.*?)</rt></ruby>", re.S)
TAG_RE = re.compile(r"<[^>]+>")

# Structural pinyin check: legal initial + legal final (+ optional erhua r).
# Approximate on purpose -- it catches English words, typos, and tone-number
# leakage, which is the actual failure class. It will not reject every
# impossible initial/final combo.
PINYIN_RE = re.compile(
    r"^(zh|ch|sh|[bpmfdtnlgkhjqxrzcsyw])?"
    r"(a|o|e|ai|ei|ao|ou|an|en|ang|eng|ong|er|i|ia|ie|iao|iu|ian|in|iang|ing|iong|"
    r"u|ua|uo|uai|ui|ue|uan|un|uang|ueng|v|ve|van|vn)r?$"
)
TONE_MAP = str.maketrans(
    "āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜü",
    "aaaaeeeeiiiioooouuuuvvvvv",
)


def strip_tags(s):
    return TAG_RE.sub("", s or "")


def normalize_syllable(syl):
    s = unicodedata.normalize("NFC", syl.strip().lower())
    return s.translate(TONE_MAP)


def is_valid_pinyin(syl):
    return bool(PINYIN_RE.match(normalize_syllable(syl)))


def validate(deck):
    errors = []
    warnings = []
    lang = deck.get("language", "")
    is_zh = lang.startswith("zh")

    for key in ("deck_name", "language", "cards"):
        if not deck.get(key):
            errors.append(f"deck: missing required top-level key '{key}'")
    cards = deck.get("cards", [])
    if not cards:
        errors.append("deck: no cards")

    seen = {}
    for i, c in enumerate(cards):
        tag = f"card {i} ({c.get('word', '?')})"

        for f in ("word", "definition", "sentence", "sentence_meaning"):
            if not (c.get(f) or "").strip():
                errors.append(f"{tag}: missing required field '{f}'")

        word = (c.get("word") or "").strip()
        if word:
            if word in seen:
                errors.append(f"{tag}: duplicate of card {seen[word]}")
            seen[word] = i

        # Target word must appear in the sentence (tags stripped).
        sent_plain = strip_tags(c.get("sentence", ""))
        if word and word not in sent_plain:
            errors.append(f"{tag}: sentence does not contain the word")
        # And should be highlighted.
        if word and 'class="t"' not in (c.get("sentence") or ""):
            warnings.append(f"{tag}: target not wrapped in <span class=\"t\"> in sentence")

        # Ruby checks.
        for field in ("word_ruby", "sentence_ruby"):
            ruby = c.get(field) or ""
            if not ruby:
                continue
            if ruby.count("<ruby>") != ruby.count("</ruby>") or ruby.count("<rt>") != ruby.count("</rt>"):
                errors.append(f"{tag}: malformed ruby markup in {field}")
                continue
            pairs = RUBY_RE.findall(ruby)
            if not pairs:
                errors.append(f"{tag}: {field} set but contains no <ruby>base<rt>reading</rt></ruby> pairs")
                continue
            if is_zh:
                for base, rt in pairs:
                    base_clean = strip_tags(base)
                    for syl in rt.strip().split():
                        if syl and not is_valid_pinyin(syl):
                            errors.append(
                                f"{tag}: invalid pinyin syllable '{syl}' over '{base_clean}' in {field}"
                            )

        # word_ruby text (rt readings removed) must reassemble to the word.
        # Plain text BETWEEN ruby elements is allowed -- Japanese okurigana
        # stay outside ruby (<ruby>食<rt>た</rt></ruby>べる).
        wr = c.get("word_ruby") or ""
        if wr and word:
            bases = strip_tags(re.sub(r"<rt>.*?</rt>", "", wr, flags=re.S))
            if bases != word:
                errors.append(f"{tag}: word_ruby base text '{bases}' != word '{word}'")

        # reading vs word_ruby consistency (Mandarin).
        if is_zh and wr and c.get("reading"):
            rt_join = "".join(rt.strip() for _, rt in RUBY_RE.findall(wr)).replace(" ", "")
            reading = (c.get("reading") or "").replace(" ", "")
            if normalize_syllable(rt_join) != normalize_syllable(reading):
                warnings.append(
                    f"{tag}: reading '{c['reading']}' != ruby readings '{rt_join}' -- verify"
                )

        # Tone numbers leaking into readings.
        if is_zh:
            for f in ("reading", "word_ruby", "sentence_ruby"):
                if re.search(r"[a-zü]\d", (c.get(f) or "").lower()):
                    errors.append(f"{tag}: tone numbers found in {f}; use tone marks")

    return errors, warnings


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as fh:
        deck = json.load(fh)
    errors, warnings = validate(deck)
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    n = len(deck.get("cards", []))
    print(f"\n{n} cards checked: {len(errors)} errors, {len(warnings)} warnings.")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
