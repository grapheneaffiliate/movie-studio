---
name: production
description: PRODUCTION stage. Execute shotlist.json — generate start frames, animate into clips via Higgsfield, chain continuity, download everything, checkpoint state. Use when shooting shots, and for single-asset requests (one image / one track).
---

# Production — the shooting department

You execute the shotlist, one shot at a time, top to bottom. Stage advances to
`"dailies"` (in practice you interleave with review-loop per shot).

## The Image-First Law (never break this)

For every video shot:
1. Generate the start frame as an IMAGE (`start_frame_prompt`, `image_model`).
2. VIEW it (download → Read tool). Wrong composition/character/look? Revise the
   prompt and regenerate — up to 2 revisions. Images are ~10× cheaper than video;
   this is where failure is supposed to happen.
3. Only an approved image becomes `start_image` for video generation.

Exception: shots with `chain_from_last_frame_of` take their start image from
the previous shot's approved take instead:
```bash
python3 scripts/review.py lastframe projects/<slug>/clips/s03_t01.mp4
# upload the PNG via media_upload / media_import_url → use as start_image
```

## Per-shot procedure

```
start frame (image-first) → animate (video_model, start_image, video_prompt,
duration_s) → record job_id in project.json higgsfield_jobs BEFORE waiting →
download immediately → update shotlist (takes[], status="generated") →
hand to review-loop → next shot
```

- `<<<element_id>>>` placeholders go in PROMPT TEXT for every shot where that
  character appears — including video prompts. Never in `medias[]`.
- Download with `python3 scripts/download.py "<url>" projects/<slug>/clips/s04_t01.mp4`
  the moment a job finishes. Job URLs are not a durable copy.
- Naming is load-bearing: `s<shot>_t<take>.mp4`, takes numbered from `t01`.
  Never overwrite an existing take; a retake is the next take number.
- Checkpoint `project.json` after every tool result: job ids on submit, paths on
  download, credits on spend (budget.ledger gets one row per generation).

## Order of shooting

Shoot in shotlist order so continuity chains resolve naturally (a chained shot
needs its parent's APPROVED take first). If a shot is waiting on a retake
upstream of a chain, shoot unchained shots meanwhile — never idle on one shot.

## Error handling

Follow the CLAUDE.md ladder: adjustments → recovery_tool → schema fix → prompt
revision → model switch (kling3_0 ⇄ seedance_2_0) → redesign → `blocked` + cut
around. Transient/network: 3 retries with backoff. Out of credits: stop at the
exact shot, record position in project.json, report.

## Single-asset fast path

"Make me an image / a track" collapses the pipeline: brief (one paragraph,
logged) → generate → download → VIEW/listen-check (ffprobe for audio) → up to 2
revisions → deliver file path. Still scaffold a project (manifest discipline
applies), still log spend.
