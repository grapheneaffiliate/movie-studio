---
name: color-grading
description: COLOR stage (post). Apply one committed cinematic grade across the whole cut to unify the look and hide AI palette drift; match stubborn shots to their scene; apply author LUTs. Use after picture lock, before mastering. Tool: grade.py.
---

# Color Grading — the colorist

A committed grade is the cheapest thing that makes generated footage look
*authored* — and it hides the small palette drift between AI shots that no amount
of prompting fully removes. The style page (screenwriting) named one look; here
you commit it to pixels. All ffmpeg, free, re-runnable.

## The one-look law

Pick ONE grade for the whole piece and apply it to the FINAL assembled cut:
```bash
python3 scripts/grade.py list
python3 scripts/grade.py apply projects/<slug>/final/<slug>_v1.mp4 \
    --look teal-orange --out projects/<slug>/final/<slug>_graded.mp4
```
Never mix looks across acts (same law as the style page). Choose by genre:

| Style page look | grade.py `--look` |
|---|---|
| Blockbuster / sci-fi / action | `teal-orange` |
| Crime / drama / timeless | `noir` or `noir-color` |
| War / gritty thriller | `bleach-bypass` |
| Night scenes shot bright | `day-for-night` |
| Nostalgia / period / memory | `vintage` or `sepia` |
| Neon city / synthwave | `cyberpunk` |
| Golden warmth / cool tech | `warm` / `cool` |
| Horror | `horror` |
| Social punch (Reels/TikTok) | `vibrant` |
| Prestige restraint | `moody` |

Add-ons: `--vignette` (focus the eye), `--grain 4-8` (filmic texture, kills the
"too clean" CGI tell), `--contrast 1.1`.

## Shot-matching (the surgical use)

When dailies approved a shot whose color drifted slightly from its scene, match
it *before* the global grade by grading that one clip toward its neighbors —
cheaper than a retake:
```bash
python3 scripts/grade.py apply projects/<slug>/clips/s07_t02.mp4 --look warm --out s07_matched.mp4
```
Then point the shotlist `approved_take` at the matched file (keep the original as
an alternate take — never delete).

## Author LUTs

If a look was designed in Resolve/Premiere and exported as a `.cube`:
```bash
python3 scripts/grade.py lut <in> --cube look.cube --out graded.mp4
```

## Where this fits

After post-production assembles the picture and QC passes the draft; before
mastering and delivery. Grade the cut, re-QC the cutsheet for palette consistency
(review-loop), then hand to mastering-delivery. Log the chosen look in
`project.json notes` so recuts stay consistent.
