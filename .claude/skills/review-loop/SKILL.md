---
name: review-loop
description: DAILIES + FINAL QC stage. Grade every take from contact sheets on 5 axes, decide approve/retake/redesign, deep-inspect with frame strips, QC the final cut. Use after any generation, before any assembly, and for "shot X looks wrong" requests.
---

# Review Loop — the dailies & QC department

You are the studio's eyes. Nothing enters the cut unseen. The write to
shotlist.json IS the decision — un-logged approvals don't count.

## Grading a take

```bash
python3 scripts/review.py contact projects/<slug> s04_t02.mp4
```
VIEW the contact sheet with the Read tool, grade 1-5 on five axes, write to the
shot's `review_notes[]`:

| Axis | Question |
|---|---|
| **fidelity** | Does it show what `action`/`video_prompt` asked for? |
| **continuity** | Character/wardrobe/location/lighting match the bible and adjacent shots? |
| **technical** | Artifacts: morphing, extra limbs, warped faces/text, flicker, frozen frames? |
| **cinematography** | Composition, motion quality, does the camera move read as intended? |
| **cut compatibility** | Will its first/last frames cut cleanly against neighbors? |

Verdict:
- **approve** — no axis < 3 and no continuity failure → set `approved_take`,
  `status: "approved"`.
- **retake** (≤ 2 per shot) — right design, bad execution → revise the failing
  prompt element only, regenerate, next take number.
- **redesign** (≤ 2 per shot) — the design itself can't generate → new angle,
  new blocking, or split the shot. Counts reset for the new design.
- 3 failed *redesigns* = Triple-fault → only then ask the user (CLAUDE.md gate),
  or mark `blocked` and cut around it if the shot isn't structurally essential.

Record verdict format: `{"take": "s04_t02.mp4", "grades": {fidelity: 4, ...},
"verdict": "approve", "why": "..."}`.

## Deep inspection (when the contact sheet is ambiguous)

```bash
python3 scripts/review.py strip projects/<slug>/clips/s04_t02.mp4 --n 8
```
- Near-identical frames → frozen video → retake with stronger motion verbs +
  explicit camera move.
- Wild deltas between adjacent frames → morphing → retake; if twice, redesign
  with simpler motion.

## Final-cut QC (after assembly)

```bash
python3 scripts/review.py cutsheet projects/<slug>/final/<file>.mp4
```
VIEW the whole film as a grid. Check: palette drift across acts, pacing (any
shot visibly overstaying), global continuity (wardrobe/location jumps), title
cards if required. **One fix pass allowed**: editorial fixes are free (trim,
reorder, transition — edit shotlist, re-run assemble); regeneration fixes only
for true failures. Log QC results in project.json notes, then deliver.

## Surgical edits ("shot 7 looks wrong — fix it")

Locate the shot in the manifest → contact-sheet its approved take → diagnose
against the 5 axes → fix at the cheapest effective level: editorial (free) →
retake → redesign. Re-run assemble; re-QC only the affected region.
