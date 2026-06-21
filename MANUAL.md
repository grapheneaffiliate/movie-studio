# HOLLYWOOD STUDIO — Operator's Manual

A complete autonomous production suite. You give one prompt; the agent writes the
screenplay, designs the shots, generates every clip through your Higgsfield
account, *looks at its own footage*, regenerates what fails, scores it, mixes it,
and hands you a finished file. This manual covers everything in the box.

---

## 1. What This Is (Architecture)

Three layers, deliberately separated:

| Layer | Component | Role |
|---|---|---|
| **Brain** | Claude Code + `CLAUDE.md` + 7 skills | Writer, director, cinematographer, editor, QC reviewer. All creative judgment lives here. |
| **Render farm** | Higgsfield MCP (your Ultra account) | Every pixel and every audio sample: images, video clips, music, TTS dialogue, SFX, upscaling, reframing. |
| **Edit bay** | ffmpeg via `scripts/` | Deterministic local assembly: normalization, transitions, audio mixing/ducking, muxing, frame extraction. Free and repeatable — never spend credits on what ffmpeg can do. |

The connective tissue is **`project.json` + `shotlist.json` on disk**. Every
decision, job ID, grade, and credit spent is written to disk the moment it
happens, so any crashed, interrupted, or context-exhausted session resumes
losslessly. The agent's "eyes" are `review.py` contact sheets viewed through
Claude Code's Read tool — this is the loop that turns a generation slot machine
into a studio.

```
PROMPT ─► DEVELOPMENT ─► PRE-PRO ─► PRODUCTION ─► DAILIES ─► SOUND ─► POST ─► QC ─► FILE
          screenplay     shotlist    generate      see+grade   score    cut    final
          characters     elements    img→video     retake      voice    mix    review
                         budget      download      approve     sfx      mux    deliver
```

---

## 2. Installation

```bash
# Requirements: ffmpeg >= 4.3, python3 >= 3.9, Claude Code, Higgsfield account
unzip hollywood-studio.zip && cd hollywood-studio

# Connect your Higgsfield account (one time; browser auth uses your Ultra plan)
claude mcp add --transport http higgsfield https://mcp.higgsfield.ai/mcp

# Verify the environment
python3 scripts/preflight.py
```

`CLAUDE.md` and `.claude/skills/` auto-load whenever `claude` is launched from
this directory. No pip packages, no Node deps — stdlib + ffmpeg only.

### Running unattended
For true fire-and-forget runs, launch with auto-approved permissions scoped to
this directory, e.g. add to `.claude/settings.json`:
```json
{ "permissions": { "allow": ["Bash(python3 scripts/*)", "Bash(ffmpeg*)", "Bash(ffprobe*)", "Read", "Write", "mcp__higgsfield__*"] } }
```
or run `claude --dangerously-skip-permissions` *from inside this folder only*.
The Budget Gate (§6) is your spending guardrail either way.

---

## 3. Using It

Start Claude Code in the folder and speak plainly:

**Full productions** (full pipeline engages automatically):
> "Make a 2-minute noir short about a lighthouse keeper who receives radio
> signals from her own future. Rain everywhere. Melancholy score."

> "Music video: synthwave track about night driving, 9:16 vertical for Reels,
> neon Tokyo aesthetic."

> "30-second ad for a chimney sweep company — warm, family, autumn, trustworthy
> voiceover."

**Single assets** (pipeline collapses to generate → review → deliver):
> "Make me a 4K image of a golden-ratio spiral interferometer as museum-piece
> product photography."
> "Write and produce a 90-second ambient track for deep-work focus."

**Edits and continuations** (the manifest makes everything addressable):
> "Shot 7 of the lighthouse film looks wrong — her jacket changed color. Fix it."
> "Recut the trailer with a faster second act."
> "Resume the noir short." / "Status on all projects."
> "Make a vertical version of the final cut."

The agent decides everything unspecified using the Defaults Table in CLAUDE.md
(runtime, aspect, look, voice casting, music) and logs each decision — you audit
choices at the end instead of being interrupted during.

---

## 4. Utility Reference (scripts/)

All scripts are stdlib-only, take a project directory, and are safe to re-run.

### `preflight.py` — environment check
```bash
python3 scripts/preflight.py
```
Verifies ffmpeg/ffprobe presence and version (xfade needs ≥ 4.3), Python ≥ 3.9,
writable `projects/`, intact templates, all sibling scripts. Exit 0 = clear to
shoot. The agent runs this at the top of every production prompt and aborts with
a fix list rather than failing mid-shoot.

### `new_project.py` — scaffolder
```bash
python3 scripts/new_project.py "lighthouse-noir" "Make a 2-minute noir..." \
    [--deliverable trailer|short_film|music_video|ad|feature|image|track] \
    [--runtime 120] [--aspect 16:9|9:16|1:1]
```
Creates the full directory tree, a populated `project.json` (verbatim prompt
preserved — it's the contract), and an empty `shotlist.json`. Refuses to
overwrite existing projects. Deliverable defaults set runtime automatically
(trailer 75 s, short film 180 s, ad 30 s…).

### `status.py` — dashboard & crash recovery
```bash
python3 scripts/status.py                      # one line per project
python3 scripts/status.py projects/lighthouse-noir   # full dashboard
```
Full mode shows stage, per-shot status/takes/approvals, budget, finals on disk,
and — critically — **reconciliation** between the manifest and disk:
- `GHOST` — approved take referenced but file missing → re-download via job ID
- `STEM-MISSING` — audio cue in shotlist with no file → regenerate/download
- `ORPHAN` — clip on disk unreferenced (harmless, kept as alternate take)

Ends with the exact **resume point**. This is the first command of every resumed
session.

### `download.py` — persist Higgsfield results
```bash
python3 scripts/download.py "<result_url>" projects/<slug>/clips/s04_t01.mp4
python3 scripts/download.py --batch manifest.json   # [{"url":..,"dest":..},...]
```
Streams to disk, rejects suspiciously small files, and ffprobe-validates
video/audio. Naming convention is load-bearing: clips are `s<shot>_t<take>.mp4`;
audio stems must be `audio/<kind>/<id>.<ext>` matching shotlist IDs exactly.

### `review.py` — the agent's eyes
```bash
python3 scripts/review.py contact projects/<slug>            # sheet per clip
python3 scripts/review.py contact projects/<slug> s04_t02.mp4
python3 scripts/review.py strip projects/<slug>/clips/s04_t02.mp4 --n 8
python3 scripts/review.py lastframe projects/<slug>/clips/s03_t01.mp4
python3 scripts/review.py cutsheet projects/<slug>/final/cut.mp4
```
- **contact** — 9-frame grid PNG per clip → the standard dailies artifact the
  agent views and grades (5 axes: fidelity, continuity, technical,
  cinematography, cut compatibility).
- **strip** — N full-res frames for deep inspection; near-identical frames =
  frozen video, wild deltas = morphing.
- **lastframe** — extracts a clip's final frame; uploaded back to Higgsfield as
  the next shot's `start_image` → seamless scene continuity chaining. This is
  the single most important trick for "fuller length" coherence.
- **cutsheet** — 1 frame / 2 s grid of an assembled cut for whole-film QC
  (palette drift, pacing, global continuity).

All outputs land in `dailies/`.

### `assemble.py` — timeline renderer
```bash
python3 scripts/assemble.py projects/<slug> --draft   # fast 720p review cut
python3 scripts/assemble.py projects/<slug>           # 1080p CRF17 final
python3 scripts/assemble.py projects/<slug> --out final/custom.mp4
```
Reads `shotlist.json`, **hard-fails if any shot lacks `approved_take`** (by
design — no blind assembly, ever). Normalizes every clip (resolution/fps/pixfmt/
SAR), trims to shotlist durations, builds the transition graph (`cut`, `fade`,
`fadeblack`, `dissolve`, `wipeleft/right`, `slideup/down`, `circleopen/close`,
`pixelize`, …), and renders. If `audio/mixdown.wav` exists it auto-muxes a
`*_mix.mp4`. Pacing changes are free: edit `duration_s` or reorder `shots[]`
and re-run — never regenerate for an editorial problem.

### `audio_mix.py` — sound mixer
```bash
python3 scripts/audio_mix.py projects/<slug> [--runtime 92.5]
```
Reads the shotlist `audio` block, places every stem at its `start_at_s` with its
`gain_db`, **automatically ducks music −7 dB during dialogue windows** (±0.3 s),
trims to picture runtime, limits to −0.45 dBFS, writes `audio/mixdown.wav`.
Re-run `assemble.py` afterward to mux. Default gains: music −6, dialogue 0,
ambience −12, hard SFX −3.

---

## 5. Data Schemas (the contracts everything obeys)

### `shotlist.json` — the edit decision list
Per shot: `id`, `duration_s`, `shot_type`, `camera`, `action`,
`start_frame_prompt` (still-image prompt, style language + `<<<element_id>>>`
placeholders), `video_prompt` (motion/camera), `video_model`/`image_model`,
`chain_from_last_frame_of` (continuity chaining), `transition_in`, `status`
(`pending → generated → approved | blocked`), `takes[]`, `approved_take`,
`review_notes[]`. Plus top-level `characters[]` (with `element_id`) and the
`audio` block (`music`/`dialogue`/`sfx`, each cue with `id`, `start_at_s`,
`gain_db`). See `templates/shotlist.json` for the annotated original and
`projects/smoketest/` for a worked, runnable example.

### `project.json` — resumable state
`stage`, `user_prompt` (verbatim), `target_runtime_s`,
`budget.{estimate_credits, spent_credits, ledger[]}`,
`continuity_assets.{elements, souls}`, `higgsfield_jobs` (job IDs recorded
*before* waiting on them — crash insurance against paying twice), `notes[]`
(the autonomous decision log).

---

## 6. The Autonomy Protocol (what makes it hands-off)

Fully specified in `CLAUDE.md`; the contract in brief:

- **The prompt is the greenlight.** The agent never pauses to ask except at four
  gates: **Budget** (> 500 credits projected — states the number, waits for
  "go"), **Identity** (your own face/likeness → Soul training needs your photos),
  **Triple-fault** (a shot fails 3 full *redesigns*, not 3 prompts), and genuine
  prompt **Contradiction**.
- **Defaults Table** resolves everything unspecified — runtime by deliverable
  type, 16:9 unless social formats are implied, always scored, ≤ 3 recurring
  characters, kling3_0/soul_2 routing, voice casting by character profile. Every
  default taken is logged to `project.json notes[]` + a human-readable
  *Director's log* appended to `screenplay.md`.
- **Image-first law**: every video shot's start frame is generated and visually
  approved as a cheap image before any video credits are spent.
- **Error ladder** (descend, never skip to asking): apply tool `adjustments` →
  call `recovery_tool` → fix params from schema → revise the failing prompt
  element → switch model → redesign the shot (new angle/blocking/split) → mark
  `blocked` and cut around it. Transients get 3 backoff retries.
- **Checkpoint everything**: state is written after every tool result; a killed
  session resumes via `status.py` reconciliation with zero credit waste.
- **Definition of Done**: ffprobe-valid final with both streams, runtime within
  ±15% of target, final-cut QC logged, and a closing report — path, runtime,
  shots, retakes, credits vs estimate, and an honest list of the weakest shots.

### Tuning autonomy
Edit `CLAUDE.md` directly:
- Raise/lower the **Budget Gate** number (§1) to match your comfort.
- Change Defaults Table rows (e.g., default 9:16 if your channel is vertical-first).
- Tighten review: raise the approval bar in `review-loop/SKILL.md` ("no axis < 4")
  for higher quality at higher credit cost.
- Add a standing style: append a "House Style" section (palette, lens language,
  logo end-card for A&T ads, your channel's registers) — every project inherits it.

---

## 7. The Seven Departments (.claude/skills/)

| Skill | Stage | What it owns |
|---|---|---|
| `creative-writing` | Development | Concept novelty (first-idea rule, subversion levers, specificity-as-originality) + the *generative screenplay* format: a SPEC block per clip naming every on-screen detail — subjects/count, wardrobe (verbatim from bible), props, light source+direction, camera, what moves AND what stays static — so downstream prompts are built by transcription, not invention. The upstream fix for most generation errors. |
| `screenwriting` | Development | Logline → treatment → character bible (in prompt-ready language, one outfit per act) → formatted screenplay with *visual* action lines → style page. Enforces generatability (no crowds/mirrors/fine hand work — uses cinematic workarounds). |
| `shot-design` | Pre-pro | Script → shotlist.json. Shot rhythm (wide→medium→close, cutaways to hide AI seams), character casting → Higgsfield **Elements**, the two prompts per shot, continuity chain planning, per-shot model routing, **credit budgeting**, audio block authoring. |
| `production` | Production | The image-first law, `<<<element_id>>>` placement, start_image animation, chaining via lastframe, download + status discipline, single-asset fast path. |
| `review-loop` | Dailies + QC | Contact-sheet grading on 5 axes, approve/retake/redesign decisions, deep strip inspection, final-cut QC with one fix pass, surgical edit requests. |
| `sound-department` | Sound | Model routing (sonilo music / inworld TTS / mirelo SFX), per-act cues, voice casting, stem naming discipline, timing math (dialogue must fit its shot), ffprobe verification. |
| `post-production` | Post | Draft→final render discipline, transition vocabulary, trim-don't-regenerate pacing, reframe/upscale deliverables, closing report. |

---

## 8. Cost Model & Expectations

- Images are ~10× cheaper than video — the image-first law means most failures
  cost pennies.
- A 2-minute film ≈ 18–25 shots; expect 15–30% of shots to need one retake.
  Plan a few thousand credits for a polished short; a 75 s trailer is far less.
- Free operations (use liberally): trims, reorders, transitions, remixes,
  re-renders — all ffmpeg.
- Paid operations (gate behind review): any `generate_*`, upscale, reframe.
- The agent preflights with `get_cost: true`, writes the estimate to the budget,
  and reconciles actual spend in the closing report.

## 9. Troubleshooting

| Symptom | Fix |
|---|---|
| `REFUSING TO ASSEMBLE: shots without approved takes` | Working as intended — run the dailies loop; check `status.py` for which shots. |
| `GHOST` in status | Result never downloaded or disk cleaned — recover via the job ID in `higgsfield_jobs` (job_display / show_generations), re-download. |
| Character drifts between shots | Element placeholder missing from a `video_prompt`, or a chain broken — check `<<<UUID>>>` presence and `chain_from_last_frame_of` after any reorder. |
| Frozen-looking clip | Confirm with `strip`; retake with stronger motion verbs in `video_prompt` and an explicit camera move. |
| Audio mixdown shorter/longer than picture | mixdown trims to picture runtime automatically; if dialogue is clipped, the line overran its shot — shorten the line text and regenerate (never speed-warp). |
| MCP auth errors mid-run | Re-auth (`claude mcp list` / re-add); job IDs in the manifest mean nothing already paid for is lost. |
| Out of credits mid-run | Agent stops at the exact shot, records position, reports. Top up, say "resume". |

## 10. Extending the Studio

The architecture is deliberately open — each addition is just a skill + maybe a script:
- **Subtitles**: a `subtitles` skill writing SRT from the dialogue block timing
  (already exact), burned in via one ffmpeg `subtitles=` filter.
- **Channel templates**: per-register style pages for your music-video channel's
  contemplative / confrontational / manifesto identities as reusable style files
  in `templates/`.
- **A&T ad factory**: Higgsfield's Marketing Studio tools (`show_marketing_studio`)
  slot into the production skill for product-URL → ad pipelines.
- **Parallel takes**: generate `count: 2` takes per shot and let dailies pick the
  winner — higher cost, higher floor.
- **Virality pass**: run `virality_predictor` on final cuts as an eighth stage
  before delivery.
