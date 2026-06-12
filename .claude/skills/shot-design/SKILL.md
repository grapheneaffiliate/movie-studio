---
name: shot-design
description: PRE-PRODUCTION stage. Convert screenplay.md into shotlist.json — shot breakdown, character Elements, per-shot prompts, continuity chains, model routing, credit budget, audio block. Use after screenwriting completes, or when re-planning shots.
---

# Shot Design — the Pre-production department

You translate the screenplay into the machine-readable plan everything else
executes: `shotlist.json` (schema: `templates/shotlist.json`; worked example:
`projects/smoketest/`). Advance stage to `"production"` when done.

## 1. Shot breakdown

- Every shot 4-10 s. Average ~4-6 s. Target runtime ÷ avg length = shot count;
  reconcile with the screenplay's beats before writing entries.
- **Rhythm**: enter scenes wide → medium → close. Insert cutaways (hands-off
  inserts, environment details) every 3-4 character shots — they hide AI seams
  and give the editor escape routes.
- Vary `shot_type` and `camera` between adjacent shots; two identical setups
  back-to-back reads as a generation glitch even when it isn't.

## 2. Character casting → Elements

For each character in the bible, create a Higgsfield **Element** (instant) from
a generated reference portrait, or a **Soul** if the user provided photos
(Identity gate — ask first; that's one of the four legitimate gates).
Record under `project.json continuity_assets.elements` as `name → uuid`, and in
shotlist `characters[]`. In prompts, reference as `<<<uuid>>>` embedded in the
prompt TEXT — never in `medias[]`.

## 3. The two prompts per shot

- `start_frame_prompt` — a complete still-image prompt: style-page language
  (palette, lens, grade) + scene content + `<<<element_id>>>` for any character
  in frame. This is what gets generated and approved cheaply as an image.
- `video_prompt` — motion and camera ONLY ("slow dolly push-in, heat shimmer
  rising, she turns toward the window"). The look is already locked in the start
  frame; restating style here causes drift. Include one explicit camera move and
  strong motion verbs (frozen-clip insurance).

## 4. Continuity chains

When shot B continues shot A's space/time, set B's
`chain_from_last_frame_of: "sA"` — production will extract A's approved last
frame (`review.py lastframe`) and use it as B's `start_image`. Plan chains scene
by scene; a chain break after reorders is the #1 cause of drift. Chains cross
cuts within a scene, never across scene boundaries.

## 5. Model routing (per shot, from CLAUDE.md table)

- `video_model`: `kling3_0` default (start-image workflow), `seedance_2_0` fallback.
- `image_model`: `soul_2` for character/portrait frames, `nano_banana_2` for
  environments and anything with text.

## 6. Credit budget (before any generation)

Preflight representative jobs with `get_cost: true`: one image, one video at
your settings. Estimate = shots × (1 image + 1 video) × 1.3 retake factor +
audio cues. Write to `project.json budget.estimate_credits`. **If projected
spend > 500 credits, stop and report the number — wait for "go"** (Budget gate).

## 7. Audio block

Author `audio.music / dialogue / sfx` now, not after picture lock:
- music: one cue per act minimum, `prompt` in music-language (genre, tempo,
  instrumentation), `start_at_s` on the film timeline.
- dialogue: one cue per spoken line, `character`, exact `text`, `start_at_s`
  aligned to its shot's timeline position.
- sfx: ambience beds per location + hard effects for on-screen events.
- Gains: music −6, dialogue 0, ambience −12, hard SFX −3 (audio_mix.py defaults).
- IDs are filenames: `m01`, `d01`, `x01`… — `audio/<kind>/<id>.<ext>` must match.

## Done when

Every shot has all schema fields; `transition_in` chosen per cut; budget written;
audio block complete; `python3 scripts/status.py projects/<slug>` shows the full
shot table. Next: production.
