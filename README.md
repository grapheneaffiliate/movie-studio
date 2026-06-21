# Hollywood Studio — One-Prompt AI Production Suite

An autonomous film/music/image studio. Claude Code is the agent (writer, director,
editor, QC); your Higgsfield account is the render farm; ffmpeg is the edit bay.
A frame-extraction review loop gives the agent eyes on its own footage.

## Setup (one time)

```bash
# 1. Drop this folder anywhere, e.g. ~/hollywood-studio
cd ~/hollywood-studio

# 2. Connect your Higgsfield account to Claude Code
claude mcp add --transport http higgsfield https://mcp.higgsfield.ai/mcp
# (authenticate in the browser when prompted — uses your Ultra plan)

# 3. Requirements: ffmpeg + ffprobe on PATH, python3. No pip packages needed.
ffmpeg -version && python3 --version
```

The `.claude/skills/` directory and `CLAUDE.md` load automatically when you run
`claude` from this folder.

## Usage

```bash
cd ~/hollywood-studio && claude
```

Then one prompt:

> "Make a 90-second cinematic trailer about a salvage pilot who finds a derelict
> cathedral-ship in the asteroid belt. Moody, Blade Runner palette."

The agent will: write the screenplay → design the shot list → cast characters as
Higgsfield Elements → generate start frames (cheap) → review them → animate
approved frames into clips → build contact sheets and grade every take →
regenerate failures → generate score/dialogue/SFX → assemble, mix, and render
`projects/<slug>/final/<slug>_final.mp4` — checking its own work at every stage.

Also handles single assets directly: "make me an image of…", "write and produce
a song about…", "recut the trailer with a faster act 2", "shot 7 looks wrong, fix it."

## Anatomy

```
CLAUDE.md                 The studio's operating system (pipeline, hard rules)
.claude/skills/           Seven departments: creative-writing, screenwriting, shot-design,
                          production, review-loop, sound-department, post-production
scripts/assemble.py       Shotlist-driven ffmpeg timeline (xfade transitions, draft/final)
scripts/review.py         Contact sheets, frame strips, last-frame extraction (continuity)
scripts/audio_mix.py      Stem mixer with automatic dialogue ducking
scripts/download.py       Persist Higgsfield results to disk, verified
templates/                shotlist.json + project.json schemas
projects/                 Every film lives here, fully resumable from project.json
```

## Cost control

The agent preflights credits (`get_cost`) before batches, reports estimates over
500 credits before proceeding, generates images before videos (fail cheap), caps
retakes at 2 per shot, and logs every spend in `project.json`.

## Tips

- Long runs: launch with `claude --dangerously-skip-permissions` inside this
  directory only if you're comfortable — otherwise approve tool batches as they come.
- A 2-minute film ≈ 18–25 shots. Expect a few retakes; the review loop is doing
  its job.
- For your music-video channel: say "music video, use track style X" — the agent
  generates the track first, then cuts picture to its structure.
