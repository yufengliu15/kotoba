#!/usr/bin/env python3
"""AnkiGen deck builder.

Consumes a deck.json (see references/deck-json.md), generates TTS audio via
edge-tts, optionally fetches CC-licensed images from Openverse, and packages a
standalone .apkg via genanki. Also renders an HTML preview of the cards using
the exact production template, for the user-approval gate.

Usage:
  python build_deck.py deck.json --out "My Deck.apkg"            # full build
  python build_deck.py deck.json --preview preview.html          # preview only
  python build_deck.py deck.json --out d.apkg --no-audio --no-images

The template/CSS below is the single source of truth: the preview and the
packaged deck render from the same strings.
"""
import argparse
import asyncio
import hashlib
import html as html_mod
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import zlib

import validate as validator

TAG_RE = re.compile(r"<[^>]+>")

DEFAULT_VOICES = {
    "zh-CN": ("zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural"),
    "zh-TW": ("zh-TW-HsiaoChenNeural", "zh-TW-YunJheNeural"),
    "ja-JP": ("ja-JP-NanamiNeural", "ja-JP-KeitaNeural"),
    "ko-KR": ("ko-KR-SunHiNeural", "ko-KR-InJoonNeural"),
    "fr-FR": ("fr-FR-DeniseNeural", "fr-FR-HenriNeural"),
    "de-DE": ("de-DE-KatjaNeural", "de-DE-ConradNeural"),
    "es-ES": ("es-ES-ElviraNeural", "es-ES-AlvaroNeural"),
}

FIELDS = [
    "Word", "WordRuby", "Reading", "Definition", "POS",
    "Sentence", "SentenceRuby", "SentenceMeaning",
    "WordAudio", "SentenceAudio", "Image", "Notes",
]

FRONT_TMPL = """
<div class="front">
  <div class="word">{{Word}}</div>
  <div class="sentence">{{Sentence}}</div>
</div>
"""

BACK_TMPL = """
<div class="back">
  <div class="word">{{#WordRuby}}{{WordRuby}}{{/WordRuby}}{{^WordRuby}}{{Word}}{{/WordRuby}}</div>
  {{^WordRuby}}{{#Reading}}<div class="reading">{{Reading}}</div>{{/Reading}}{{/WordRuby}}
  <div class="definition">{{Definition}}{{#POS}} <span class="pos">[{{POS}}]</span>{{/POS}}</div>
  <div class="sentence">{{#SentenceRuby}}{{SentenceRuby}}{{/SentenceRuby}}{{^SentenceRuby}}{{Sentence}}{{/SentenceRuby}}</div>
  <div class="meaning">{{SentenceMeaning}}</div>
  <div class="audio">{{WordAudio}} {{SentenceAudio}}</div>
  {{#Image}}<div class="image">{{Image}}</div>{{/Image}}
  {{#Notes}}<div class="notes">{{Notes}}</div>{{/Notes}}
</div>
"""

CSS = """
.card {
  font-family: "Hiragino Sans", "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
  font-size: 24px;
  text-align: center;
  color: #eceff4;
  background-color: #2b2b2f;
  line-height: 1.6;
}
.word { font-size: 58px; margin: 18px 0 6px 0; }
.word ruby rt { font-size: 0.32em; color: #c8cdd6; }
.reading { font-size: 26px; color: #c8cdd6; margin-bottom: 4px; }
.definition { font-size: 28px; margin: 14px 0; }
.pos { font-size: 18px; color: #9aa3b2; }
.sentence { font-size: 28px; margin: 16px 0 6px 0; }
.sentence ruby rt { font-size: 0.38em; color: #c8cdd6; }
.meaning { font-size: 22px; color: #c8cdd6; margin-bottom: 10px; }
.t { color: #4a9eff; font-weight: bold; }
.t ruby rt { color: #4a9eff; }
.audio { margin: 12px 0; }
.image img { max-height: 260px; max-width: 90%; border-radius: 10px; margin-top: 10px; }
.notes { font-size: 18px; color: #9aa3b2; margin-top: 12px; }
.nightMode .card { background-color: #2b2b2f; }
"""


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "deck"


def strip_tags(s):
    return TAG_RE.sub("", s or "")


def stable_id(name, salt):
    return zlib.crc32((salt + name).encode("utf-8")) & 0x7FFFFFFF


def media_name(prefix, text, voice):
    h = hashlib.md5(f"{voice}|{text}".encode("utf-8")).hexdigest()[:12]
    return f"ankigen-{prefix}-{h}.mp3"


# ---------------------------------------------------------------- audio
async def synth_all(jobs, media_dir, concurrency=6):
    import edge_tts
    sem = asyncio.Semaphore(concurrency)
    failed = []

    async def one(text, voice, fname):
        path = os.path.join(media_dir, fname)
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return
        async with sem:
            for attempt in range(3):
                try:
                    await edge_tts.Communicate(text, voice).save(path)
                    return
                except Exception:
                    await asyncio.sleep(1.5 * (attempt + 1))
            failed.append(fname)

    await asyncio.gather(*(one(t, v, f) for t, v, f in jobs))
    return failed


def generate_audio(deck, media_dir):
    lang = deck["language"]
    vw, vs = DEFAULT_VOICES.get(lang, (None, None))
    voice_word = deck.get("voice_word") or vw
    voice_sent = deck.get("voice_sentence") or vs or voice_word
    if not voice_word:
        print(f"  no default voice for '{lang}' and none specified -- skipping audio")
        return {}
    jobs, mapping = [], {}
    for c in deck["cards"]:
        w = c["word"]
        s = strip_tags(c["sentence"])
        fw = media_name("w", w, voice_word)
        fs = media_name("s", s, voice_sent)
        jobs.append((w, voice_word, fw))
        jobs.append((s, voice_sent, fs))
        mapping[w] = (fw, fs)
    failed = asyncio.run(synth_all(jobs, media_dir))
    if failed:
        print(f"  WARNING: {len(failed)} audio files failed after retries; those fields left empty")
    for w, (fw, fs) in list(mapping.items()):
        mapping[w] = (
            fw if fw not in failed and os.path.exists(os.path.join(media_dir, fw)) else None,
            fs if fs not in failed and os.path.exists(os.path.join(media_dir, fs)) else None,
        )
    return mapping


# ---------------------------------------------------------------- images
def fetch_image(query, media_dir, idx):
    url = ("https://api.openverse.org/v1/images/?q=" + urllib.parse.quote(query)
           + "&page_size=3&mature=false&license_type=commercial,modification")
    req = urllib.request.Request(url, headers={"User-Agent": "ankigen-skill/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        results = json.load(r).get("results", [])
    for res in results:
        thumb = res.get("thumbnail") or res.get("url")
        if not thumb:
            continue
        try:
            req2 = urllib.request.Request(thumb, headers={"User-Agent": "ankigen-skill/1.0"})
            with urllib.request.urlopen(req2, timeout=15) as r2:
                data = r2.read()
            if len(data) < 2000:
                continue
            ext = ".jpg"
            ct = r2.headers.get("Content-Type", "")
            if "png" in ct:
                ext = ".png"
            elif "gif" in ct:
                ext = ".gif"
            fname = f"ankigen-img-{idx}-{hashlib.md5(query.encode()).hexdigest()[:8]}{ext}"
            with open(os.path.join(media_dir, fname), "wb") as fh:
                fh.write(data)
            credit = (f"{fname}: \"{res.get('title', 'untitled')}\" by {res.get('creator', 'unknown')}, "
                      f"{res.get('license', '?').upper()} {res.get('license_version', '')} -- {res.get('foreign_landing_url', '')}")
            return fname, credit
        except Exception:
            continue
    return None, None


def generate_images(deck, media_dir):
    mapping, credits = {}, []
    todo = [(i, c) for i, c in enumerate(deck["cards"]) if c.get("image_query")]
    for n, (i, c) in enumerate(todo):
        try:
            fname, credit = fetch_image(c["image_query"], media_dir, i)
        except Exception as e:
            print(f"  image lookup failed for '{c['image_query']}': {type(e).__name__}")
            fname, credit = None, None
        if fname:
            mapping[c["word"]] = fname
            credits.append(credit)
        if n and n % 10 == 0:
            print(f"  images: {n}/{len(todo)}")
    return mapping, credits


# ---------------------------------------------------------------- fields
def card_fields(c, audio_map, image_map):
    fw, fs = audio_map.get(c["word"], (None, None)) if audio_map else (None, None)
    img = image_map.get(c["word"]) if image_map else None
    return [
        c.get("word", ""),
        c.get("word_ruby", ""),
        c.get("reading", ""),
        c.get("definition", ""),
        c.get("pos", ""),
        c.get("sentence", ""),
        c.get("sentence_ruby", ""),
        c.get("sentence_meaning", ""),
        f"[sound:{fw}]" if fw else "",
        f"[sound:{fs}]" if fs else "",
        f'<img src="{img}">' if img else "",
        c.get("notes", ""),
    ]


# ---------------------------------------------------------------- preview
def mustache(tmpl, values):
    """Tiny renderer for the subset of Anki template syntax we use."""
    out = tmpl
    for _ in range(4):  # nested sections
        out = re.sub(
            r"{{#(\w+)}}(.*?){{/\1}}",
            lambda m: m.group(2) if values.get(m.group(1)) else "",
            out, flags=re.S)
        out = re.sub(
            r"{{\^(\w+)}}(.*?){{/\1}}",
            lambda m: "" if values.get(m.group(1)) else m.group(2),
            out, flags=re.S)
    return re.sub(r"{{(\w+)}}", lambda m: values.get(m.group(1), ""), out)


def write_preview(deck, audio_map, image_map, media_dir, out_path, limit=None):
    import base64
    cards = deck["cards"][:limit] if limit else deck["cards"]
    blocks = []
    for c in cards:
        vals = dict(zip(FIELDS, card_fields(c, audio_map, image_map)))
        # Real, clickable audio: embed the mp3 as a base64 data URI so the
        # approval gate covers audio quality, not just layout.
        for k in ("WordAudio", "SentenceAudio"):
            if not vals[k]:
                continue
            btn = '<span class="playbtn">&#9654;</span>'
            m = re.search(r"\[sound:([^\]]+)\]", vals[k])
            if m and media_dir:
                p = os.path.join(media_dir, m.group(1))
                if os.path.exists(p):
                    b64 = base64.b64encode(open(p, "rb").read()).decode()
                    btn = ('<span class="playbtn" onclick="new Audio'
                           f"('data:audio/mpeg;base64,{b64}').play()\">&#9654;</span>")
            vals[k] = btn
        if vals["Image"] and media_dir:
            m = re.search(r'src="([^"]+)"', vals["Image"])
            if m:
                p = os.path.join(media_dir, m.group(1))
                if os.path.exists(p):
                    b64 = base64.b64encode(open(p, "rb").read()).decode()
                    ext = os.path.splitext(p)[1].lstrip(".")
                    vals["Image"] = f'<img src="data:image/{ext};base64,{b64}">'
        front = mustache(FRONT_TMPL, vals)
        back = mustache(BACK_TMPL, vals)
        blocks.append(
            f'<div class="pair"><div class="card">{front}</div>'
            f'<div class="card">{back}</div></div>')
    page = f"""<!doctype html><meta charset="utf-8">
<title>{html_mod.escape(deck['deck_name'])} — preview</title>
<style>
body {{ background:#1a1a1d; margin:0; padding:30px; font-family:sans-serif; }}
h1 {{ color:#eceff4; font-size:20px; font-weight:600; }}
.pair {{ display:flex; gap:20px; margin-bottom:26px; flex-wrap:wrap; }}
.pair .card {{ flex:1; min-width:320px; border-radius:14px; padding:24px 16px;
  border:1px solid #3a3a40; }}
.playbtn {{ display:inline-block; background:#555; color:#fff; border-radius:50%;
  width:42px; height:42px; line-height:42px; margin:0 6px; font-size:18px;
  cursor:pointer; user-select:none; }}
{CSS}
</style>
<h1>{html_mod.escape(deck['deck_name'])} — {len(cards)} sample card(s), front | back</h1>
{''.join(blocks)}"""
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(page)
    print(f"Preview written to {out_path}")


# ---------------------------------------------------------------- package
def build_apkg(deck, audio_map, image_map, media_dir, out_path):
    import genanki
    model = genanki.Model(
        stable_id(deck["deck_name"], "ankigen-model-"),
        "AnkiGen Language Vocab",
        fields=[{"name": f} for f in FIELDS],
        templates=[{"name": "Recognition", "qfmt": FRONT_TMPL, "afmt": "{{FrontSide}}<hr id=answer>" + BACK_TMPL}],
        css=CSS,
    )
    gdeck = genanki.Deck(stable_id(deck["deck_name"], "ankigen-deck-"), deck["deck_name"])
    base_tags = [t.replace(" ", "_") for t in deck.get("tags", [])]
    media = []
    for i, c in enumerate(deck["cards"]):
        flds = card_fields(c, audio_map, image_map)
        tags = base_tags + [t.replace(" ", "_") for t in c.get("tags", [])]
        note = genanki.Note(model=model, fields=flds, tags=sorted(set(tags)), due=i)
        gdeck.add_note(note)
        for f in flds:
            for m in re.findall(r"\[sound:([^\]]+)\]", f) + re.findall(r'src="([^"]+)"', f):
                p = os.path.join(media_dir, m)
                if os.path.exists(p):
                    media.append(p)
    pkg = genanki.Package(gdeck)
    pkg.media_files = sorted(set(media))
    pkg.write_to_file(out_path)
    print(f"Packaged {len(deck['cards'])} cards -> {out_path}")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("deck_json")
    ap.add_argument("--out", help="output .apkg path")
    ap.add_argument("--preview", help="write an HTML preview to this path")
    ap.add_argument("--preview-limit", type=int, default=None)
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--no-images", action="store_true")
    ap.add_argument("--media-dir", default=None)
    args = ap.parse_args()

    with open(args.deck_json, encoding="utf-8") as fh:
        deck = json.load(fh)

    errors, warnings = validator.validate(deck)
    for w in warnings:
        print(f"WARN  {w}")
    if errors:
        for e in errors:
            print(f"ERROR {e}")
        print(f"\n{len(errors)} validation errors -- fix deck.json first.")
        sys.exit(1)

    media_dir = args.media_dir or os.path.join(
        os.path.dirname(os.path.abspath(args.deck_json)), f"media-{slug(deck['deck_name'])}")
    os.makedirs(media_dir, exist_ok=True)

    audio_map = {}
    if not args.no_audio:
        print("Generating audio (edge-tts)...")
        try:
            audio_map = generate_audio(deck, media_dir)
        except Exception as e:
            print(f"  audio generation unavailable ({type(e).__name__}: {e}); continuing without audio")

    image_map, credits = {}, []
    if not args.no_images:
        print("Fetching images (Openverse)...")
        image_map, credits = generate_images(deck, media_dir)
        print(f"  {len(image_map)} images attached")

    if args.preview:
        write_preview(deck, audio_map, image_map, media_dir, args.preview, args.preview_limit)
    if args.out:
        build_apkg(deck, audio_map, image_map, media_dir, args.out)
        if credits:
            cpath = re.sub(r"\.apkg$", "", args.out) + "-image-credits.txt"
            with open(cpath, "w", encoding="utf-8") as fh:
                fh.write("\n".join(credits) + "\n")
            print(f"Image attributions -> {cpath}")
    if not args.preview and not args.out:
        print("Nothing to do: pass --out and/or --preview")


if __name__ == "__main__":
    main()
