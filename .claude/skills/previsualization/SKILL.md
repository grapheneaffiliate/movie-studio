---
name: previsualization
description: PRE-VIZ stage (between pre-pro and production). Estimate the budget, build a timed animatic from start frames before spending video credits, and beat-grid a track for music-video cutting. Use after shot-design, before any video generation, and whenever pacing or spend is in question.
---

# Pre-visualization — see and cost the film before you shoot it

Pre-viz extends the studio's two cheapest-failure laws — *image-first* and
*trim-don't-regenerate* — back to before production. You confirm the edit works
and the budget is sane while everything is still free or pennies.

Run this stage after `shot-design` writes the shotlist and before `production`
spends a single video credit.

## 1. Cost the plan (instant, no API)

```bash
python3 scripts/estimate.py projects/<slug>
```
Ballpark credits from the shotlist shape (shots × image+video × retake factor +
audio cues) and an automatic **Budget Gate** trip (>500 → state the number, wait
for "go", per CLAUDE.md §1). This is the cheap early warning; shot-design still
confirms real costs with Higgsfield `get_cost` before batches. Override the cost
assumptions if pricing has drifted (`--vid 60 --img 6 --retake 1.4`).

## 2. Animatic — the edit, for the price of images

After production generates and approves each shot's **start frame** (you do this
anyway under the image-first law), string those stills into a timed animatic at
real shotlist durations:
```bash
python3 scripts/animatic.py build projects/<slug> --kenburns --audio
```
- Reads `shotlist.json` durations; finds each shot's frame in `refs/` (name them
  after the shot: `refs/s01.png`); drops a labeled **slate** for any frame not
  yet made, so timing still reads.
- `--kenburns` adds a slow push-in (sells motion); `--audio` muxes
  `audio/mixdown.wav` if the scratch track exists.
- **VIEW the animatic** (review-loop's eyes) and judge PACING and STORY FLOW
  before animating: a shot that drags, a beat that's missing, an act that sags.
  Fix it now by editing `duration_s` / reordering `shots[]` — all free. Every
  problem caught here is a video credit not wasted.

A music video should animatic against the **real track** (generate music first),
not scratch — pacing to the song is the whole point.

## 3. Beat grid (music videos)

When the deliverable is a music video, cut to the track:
```bash
python3 scripts/beatgrid.py projects/<slug>/audio/music/m01.m4a --every 2 --min-shot 1.5 --json cuts.json
```
Detects onsets, estimates tempo, and proposes a shot breakdown where every cut
lands on a beat (merged so no shot is shorter than `--min-shot`). Feed the
`shot_durations` back to shot-design as the shotlist durations so picture hits
the music. `--every 1` = cut every beat (frenetic), `--every 4` = once per bar
(calm). This is why the music-video flow is inverted: **track → beat grid →
shotlist → picture.**

## Handoff

Animatic reviewed and pacing locked; budget under the gate (or user said "go").
Now production can spend video credits with confidence. Next: production.
