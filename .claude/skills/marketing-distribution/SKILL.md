---
name: marketing-distribution
description: MARKETING stage (after delivery). Make thumbnails/posters/key art, predict virality and tune the hook, cut social teasers, and localize via dubbing/subtitles. Use when the user wants reach — a thumbnail, a trailer cutdown, a vertical teaser, multi-language versions, or a virality check. Tools: thumbnail.py, package.py, subtitle.py + Higgsfield virality_predictor/dubbing/voice_change.
---

# Marketing & Distribution — getting the film seen

A finished film nobody clicks is a failed deliverable. This department turns the
master into reach: the click (thumbnail), the hook (first 3 seconds), the cutdowns
(teasers), and the spread (localization). Picture/sound must already be delivered
(mastering-delivery). Local tools are free; Higgsfield tools cost credits — gate
them behind the Budget rules.

## 1. The click — key art & thumbnails (`thumbnail.py`)

```bash
python3 scripts/thumbnail.py make projects/<slug>/final/<slug>_final.mp4 --at 12 \
    --title "DERELICT" --sub "no one is coming" --preset youtube --scrim --out thumb.png
python3 scripts/thumbnail.py make refs/key_art.png --title "DERELICT" \
    --preset poster --pos bottom --scrim --out poster.png
```
Grab the strongest frame (or a purpose-generated key-art image — `soul_2`/
`nano_banana_2` make better posters than a random grab). `--scrim` keeps text
legible; keep titles 1-3 words. Presets: `youtube` (1280x720), `poster` (2:3),
`vertical`, `square`, `wide`. Make 2-3 variants and pick the boldest.

## 2. The hook — virality prediction (Higgsfield)

```
virality_predictor  → on the FINAL cut (and on vertical teasers)
```
Run it on the deliverable to score hook strength, retention risk, and audience
response. If the hook scores weak, the cheapest fix is **editorial**: move the
strongest 1-2 seconds to the front (reorder `shots[]` / add a cold-open teaser
shot), tighten the first 3 seconds, harden the opening transition to a cut, then
re-render and re-check. Only regenerate a hook shot if no existing frame lands.
Log scores + the change you made in `project.json notes`.

## 3. The cutdowns — social teasers (`package.py` + motion-graphics)

From one master, ship the formats audiences actually scroll:
```bash
python3 scripts/package.py all projects/<slug>/final/<slug>_final.mp4 --outdir deliverables
python3 scripts/subtitle.py burn deliverables/<slug>_reels.mp4 --sub <slug>.srt --style caption --out reels_cap.mp4
```
- A **vertical teaser** (9:16, 15-30s) is the highest-reach asset — cut to the
  hook, burn captions (most social is watched muted), add a brand bug
  (`titles.py watermark`).
- For a trailer, a 6-10s "teaser for the trailer" vertical drives the long-form.

## 4. The spread — localization (Higgsfield)

```
dubbing      → translate + lip-natural dub the final into target languages
voice_change → swap a voice without re-generating the shot
subtitle.py  → ship an SRT per language alongside (always cheaper than dubbing)
```
Default to **subtitled** versions for reach (free SRT, fast); reserve **dubbing**
for the user's priority markets or when the piece is dialogue-driven. One dub +
several subtitle tracks is the cost-smart spread. Log target languages chosen.

## Where this fits

Optional eighth stage, after `delivered`. Engage when the user asks for reach,
a channel upload, a campaign, or multi-language. Keep the master untouched —
everything here is a derivative in `deliverables/`. Report assets made, virality
score + the hook change, and the platform/language matrix shipped.
