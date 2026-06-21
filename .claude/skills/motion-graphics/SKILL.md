---
name: motion-graphics
description: GRAPHICS stage (post). Title cards, lower-thirds, end-credit rolls, watermarks/brand bugs, burned-in subtitles, and key art. Use for trailer title cards, ad end-cards, accessibility captions, channel branding, and any on-screen text/graphics. All ffmpeg, free.
---

# Motion Graphics — the title & graphics department

On-screen text is the one thing the render farm must NOT make: the generatability
law forbids legible in-world text (it morphs). Everything textual is added here,
in post, with ffmpeg — sharp, correct, and free. Two tools: `titles.py` and
`subtitle.py`.

## Title cards & graphics (`titles.py`)

```bash
# Open/close cards (trailers get both per the Defaults Table)
python3 scripts/titles.py card "DERELICT" --sub "a salvage story" --dur 3 \
    --aspect 16:9 --out projects/<slug>/final/card_open.mp4
# Lower-third (name/role) over a clip
python3 scripts/titles.py lower projects/<slug>/final/cut.mp4 \
    --name "MARA VALE" --role "Salvage Pilot" --at 4 --dur 4 --out cut_lt.mp4
# Scrolling end credits
python3 scripts/titles.py credits --file credits.txt --dur 24 --out credits.mp4
# Channel/brand bug or ad end-card watermark
python3 scripts/titles.py watermark cut.mp4 --logo brand.png --pos br --out branded.mp4
```
- **Cards are clips.** A standalone card is a normal `.mp4` at project dims —
  add it to `shotlist.json` as a shot with its file as `approved_take` so
  `assemble.py` places it in the timeline with a transition (`fade`/`fadeblack`
  open and close). Match `--aspect`/`--fps` to the shotlist.
- **Lower-thirds & watermarks overlay** an existing cut (keep audio). Use a
  lower-third the first time each character or location appears; use a watermark
  for channel identity / the A&T end-card.
- Text fades in/out automatically; fonts auto-pick a cinematic serif (override
  with `--font`). Keep titles short — drawtext does not reflow long lines.

## Subtitles & captions (`subtitle.py`)

The dialogue block timing is already exact, so captions are deterministic:
```bash
python3 scripts/subtitle.py srt  projects/<slug>                 # frame-accurate SRT
python3 scripts/subtitle.py ass  projects/<slug> --style cinema  # styled
python3 scripts/subtitle.py burn projects/<slug>/final/cut.mp4 \
    --sub projects/<slug>/<slug>.srt --style caption --out cut_sub.mp4
```
- **Always ship an SRT** alongside video deliverables (accessibility + silent-feed
  autoplay reach on social). For social cutdowns, **burn** captions in (`caption`
  style — bold, high-contrast) since most viewers watch muted.
- Styles: `cinema` (subtle, film), `caption` (bold social), `karaoke` (lyric
  videos). For music videos use `subtitle.py lyrics <timed-file>` to build cues
  from `MM:SS  lyric` lines.

## Key art (`thumbnail.py`)

Posters/thumbnails live in marketing-distribution, but the tool is here:
`thumbnail.py make <frame-or-video> --title … --preset youtube|poster --scrim`.

## Where this fits

Run after a picture cut exists (post-production). Order: assemble → cards/titles
into the timeline or overlaid → subtitles burned/exported → grade → master. Log
the title/credit text and any brand assets in `project.json notes`.
