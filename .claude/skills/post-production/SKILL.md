---
name: post-production
description: POST stage. Assemble the timeline, transitions, mux, render draft→final, alternate deliverables (vertical/upscale), closing report. Use for assembly, recuts, pacing changes, and delivery.
---

# Post-Production — the edit bay

You turn approved clips + mixdown into the delivered file. Everything here is
ffmpeg — free and repeatable. Never spend credits on an editorial problem.

## Render discipline: draft → QC → final

```bash
python3 scripts/assemble.py projects/<slug> --draft   # fast 720p review cut
# → review-loop cutsheet QC on the draft, fix pass if needed →
python3 scripts/assemble.py projects/<slug>           # 1080p CRF17
```
`assemble.py` refuses to run while any shot lacks `approved_take` — that is the
design, not an error. It normalizes (resolution/fps/pixfmt/SAR), trims each clip
to `duration_s`, builds the transition graph, renders, and auto-muxes
`*_mix.mp4` when `audio/mixdown.wav` exists. Final delivery file is
`final/<slug>_final.mp4` — copy/rename the muxed render to that name.

## Transition vocabulary (`transition_in`, dict form `{type, duration_s}`)

- `cut` — default; almost always right. Real films are ~90% cuts.
- `fade` / `dissolve` — time passing, softness; 0.5-1.0 s.
- `fadeblack` — act break, scene change with finality; 0.6-1.0 s.
- `fadewhite` — flashback/memory/impact.
- `wipeleft/right`, `slideup/down` — energetic, music-video language.
- `circleopen/close`, `pixelize`, `radial`, `distance`, `smoothleft/right` —
  stylized; use only when the style page justifies it.
Transitions eat duration from both neighbors — keep them ≤ ¼ of the shorter
neighbor (assemble clamps, but plan for it).

## Trim, don't regenerate

Pacing problems are shotlist edits + re-render, all free:
- Shot overstays → lower its `duration_s` (assemble trims from the head... the
  clip's first `duration_s` seconds are used; to use a later region, retime in
  the shotlist by splitting the shot).
- Limp act → reorder `shots[]`, tighten durations, harden transitions to cuts.
- Dead shot that won't regenerate → cut around it: reorder, extend neighbors,
  cover with an insert/cutaway that exists.
After ANY reorder, re-check `chain_from_last_frame_of` references still make
sense — a chain pointing at a shot that no longer precedes it is a continuity
bug (review-loop will catch it, but fix it here first).

## Alternate deliverables

- Vertical/horizontal versions: Higgsfield `reframe` on the FINAL cut (one paid
  op) — not per-clip.
- Hero upscale: `upscale_video` on the final only if the user asked or the
  deliverable demands 4K.

## Definition of Done + closing report (CLAUDE.md §6)

Verify: `final/<slug>_final.mp4` ffprobe-valid, BOTH streams, runtime within
±15% of target; cutsheet QC logged; stage = `"delivered"`; ledger totals match.
Then report: file path, runtime, shot count, retakes, credits spent vs
estimate, decision-log highlights, and an honest list of the weakest shots.
