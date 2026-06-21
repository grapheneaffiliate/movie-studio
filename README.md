# Hollywood Studio — One-Prompt AI Production Suite

An autonomous film/music/image studio. Claude Code is the agent (writer, director,
editor, colorist, sound mixer, finisher, marketer, QC); your Higgsfield account is
the render farm; ffmpeg is the edit bay. A frame-extraction review loop gives the
agent eyes on its own footage. One prompt in, a graded, mastered, QC'd, multi-
platform-ready film out.

## Setup (one time)

```bash
# 1. Drop this folder anywhere, e.g. ~/hollywood-studio
cd ~/hollywood-studio

# 2. Connect your Higgsfield account to Claude Code
claude mcp add --transport http higgsfield https://mcp.higgsfield.ai/mcp
# (authenticate in the browser when prompted — uses your Ultra plan)

# 3. Requirements: a full ffmpeg + ffprobe build (>=4.3, with libfreetype/libass
#    for titles & subtitles) on PATH, python3 (>=3.9), and a TTF font installed
#    (e.g. fonts-dejavu) for title cards/thumbnails. No pip packages needed.
ffmpeg -version && python3 --version
python3 scripts/preflight.py   # verifies binaries, filters, fonts, scripts, templates
```

The `.claude/skills/` directory and `CLAUDE.md` load automatically when you run
`claude` from this folder. `preflight.py` is the one-shot environment check — it
flags any missing ffmpeg filter or font before a run rather than mid-shoot.

## Usage

```bash
cd ~/hollywood-studio && claude
```

Then one prompt:

> "Make a 90-second cinematic trailer about a salvage pilot who finds a derelict
> cathedral-ship in the asteroid belt. Moody, Blade Runner palette."

The agent will: write the screenplay → design the shot list → cast characters as
Higgsfield Elements → estimate the budget and animatic the pacing (cheap) →
generate start frames → review them → animate approved frames into clips → build
contact sheets and score every take on 5 axes → regenerate failures → generate
music/dialogue/SFX → assemble, mix, add title cards & subtitles → apply one
cinematic color grade → master the loudness → run an automated QC gate → render
`projects/<slug>/final/<slug>_final.mp4` and platform deliverables — checking its
own work at every stage.

Also handles single assets and finishing tasks directly: "make me an image of…",
"write and produce a song about…", "recut the trailer with a faster act 2", "shot
7 looks wrong, fix it", "make a 9:16 vertical cut with burned-in captions", "build
a YouTube thumbnail", "master this track to −14 LUFS", "export an EDL for Resolve."

## Anatomy

```
CLAUDE.md                 The studio's operating system (pipeline, hard rules)
.claude/skills/           Twelve departments —
                          core:       creative-writing, screenwriting, shot-design,
                                      production, review-loop, sound-department, post-production
                          finishing:  previsualization, motion-graphics, color-grading,
                                      mastering-delivery, marketing-distribution
scripts/  (all stdlib + ffmpeg — free, re-runnable; credits are for the render farm only)
  new_project.py · preflight.py · status.py   scaffold, env check, crash recovery
  assemble.py · audio_mix.py · download.py     timeline, stem mix+ducking, persist results
  review.py                                    contact sheets, strips, last-frame continuity
  estimate.py · beatgrid.py · animatic.py      pre-viz: cost, beat-grid, see-before-you-shoot
  titles.py · subtitle.py · thumbnail.py       graphics: cards/lowers/credits, captions, key art
  grade.py                                     13 cinematic color looks (+ LUTs)
  master.py · qc.py · package.py · edl_export.py  loudness, QC gate, multi-platform, NLE handoff
templates/                shotlist.json + project.json schemas, models.md (render-farm ref)
projects/                 Every film lives here, fully resumable from project.json
```

## Cost control

The agent preflights credits (`get_cost`) before batches and gives an instant
local estimate (`scripts/estimate.py`), reports estimates over 500 credits before
proceeding, generates images before videos (fail cheap), caps retakes at 2 per
shot, and logs every spend in `project.json`. Everything in the edit bay —
assembly, titles, subtitles, color grade, loudness master, QC, multi-platform
export, EDL/FCPXML — is local ffmpeg and **free**; credits are spent only on the
render farm (generation, hero upscale/reframe, dubbing, virality).

## Tips

- Long runs: launch with `claude --dangerously-skip-permissions` inside this
  directory only if you're comfortable — otherwise approve tool batches as they come.
- A 2-minute film ≈ 18–25 shots. Expect a few retakes; the review loop is doing
  its job.
- For your music-video channel: say "music video, use track style X" — the agent
  generates the track first, beat-grids it, then cuts picture to its structure.
- Finishing is free and re-runnable: ask for a different color grade, a vertical
  cut, captions, a new thumbnail, or a loudness target any time without spending
  credits — only re-generation costs.
