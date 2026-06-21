---
name: mastering-delivery
description: DELIVERY stage (final). Loudness-master to spec, run automated technical QC, export multi-platform versions, and hand off to pro NLEs via EDL/FCPXML. Use as the last stage before the closing report, and whenever exporting platform versions. Tools: master.py, qc.py, package.py, edl_export.py.
---

# Mastering & Delivery — the finishing department

The last mile a real studio never skips: conform the deliverable to spec, prove
it technically, and ship the right file to each destination. All local, free.

## 1. Master the loudness (`master.py`)

`audio_mix.py` limits; mastering makes loudness *conform* so platforms don't turn
the film down or reject it on ingest. Two-pass EBU R128:
```bash
python3 scripts/master.py measure projects/<slug>/final/<slug>_v1_mix.mp4
python3 scripts/master.py apply  projects/<slug>/final/<slug>_v1_mix.mp4 \
    --target youtube --out projects/<slug>/final/<slug>_master.mp4
```
Targets: `youtube/streaming/music/tiktok/reels/instagram` −14, `podcast` −16,
`broadcast` −23, `atsc` −24, `film/cinema` −27 LUFS. Pick by the primary
destination. Master AFTER grade (color doesn't touch audio, but master last so
the file you QC is the file you ship).

## 2. Technical QC (`qc.py`) — gate before delivery

```bash
python3 scripts/qc.py projects/<slug>          # QCs newest final, reads target runtime
```
Automates the Definition of Done checks + AI-specific defect scans: container
validity, both streams present, resolution/fps, **runtime within ±15%**, interior
black frames, **frozen video** (a dead generated clip that slipped past dailies),
audio clipping (true peak), loudness conformance, dead silence. **Exit code 0 =
PASS; non-zero = at least one FAIL — do not deliver.** Fix FAILs (a freeze →
retake/redesign that shot via review-loop; runtime → trim/extend in post; loudness
→ re-run master) and re-QC. Log the QC verdict in `project.json notes`.

## 3. Multi-platform export (`package.py`)

Ship versions, not one file:
```bash
python3 scripts/package.py all projects/<slug>/final/<slug>_master.mp4 \
    --outdir projects/<slug>/deliverables
python3 scripts/package.py export <master> --preset reels --focus center --out reels.mp4
```
Presets conform resolution, codec, faststart, and loudness; **smart pan-&-scan
reframe** handles 16:9→9:16/1:1 locally so you don't spend Higgsfield `reframe`
credits on routine social cuts (reserve `reframe`/`upscale_video` for hero 4K or
when a true AI re-frame beats a center crop). Default bundle = youtube + reels +
square; `--focus left|center|right` controls the crop for vertical.

## 4. Pro-tool handoff (`edl_export.py`)

When a human colorist/editor will finish the cut:
```bash
python3 scripts/edl_export.py projects/<slug>           # writes .edl + .fcpxml to final/
```
FCPXML imports into DaVinci Resolve / Premiere / Final Cut with every approved
shot laid out in order at the right durations; the EDL is the universal cuts-only
fallback (transition intentions noted as comments). Offer this when the user asks
to "finish it in Resolve" or wants a human pass.

## Definition of Done (CLAUDE.md §6)

`final/<slug>_final.mp4` = the mastered, QC-passed file (copy/rename the master to
this name). Then deliver the platform bundle and the closing report. Do not set
stage `delivered` until `qc.py` exits 0.
