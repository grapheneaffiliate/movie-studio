# Higgsfield Render-Farm Reference (cheat sheet)

Fast lookup for the connected Higgsfield MCP tools. This is a *starting* routing
table — when a job is unusual or a model name may have changed, confirm with
`models_explore(action:'recommend')` before generating. Always preflight cost with
the `get_cost` flag and check `balance` before a batch (Budget Gate, CLAUDE.md §1).

> Tool namespace: the README adds the server as `higgsfield`, so tools appear as
> `mcp__higgsfield__<tool>`. In some hosted clients the same server appears as
> `mcp__claude_ai_Higgsfield__<tool>`. Same tools, same args — match whatever your
> session exposes.

## Generation (the paid core)

| Tool | Use | Notes |
|---|---|---|
| `generate_image` | start frames, key art, posters, style frames | image-first law: make + approve these before video |
| `generate_video` | animate an approved start frame into a clip | pass `start_image`; 4-10s shots |
| `generate_audio` | music, dialogue/TTS, SFX | route by cue type (below) |
| `generate_3d` | image → GLB mesh | props/assets for 3D handoff |

### Model routing (defaults — verify with `models_explore`)
| Need | Model |
|---|---|
| Cinematic video w/ character continuity | `kling3_0` (needs start_image) / `seedance_2_0` (fallback) |
| Multi-shot scene w/ native audio | `kling3_0` |
| Character/portrait start frames | `soul_2` |
| Environments, text, 4K key art | `nano_banana_2` |
| Character identity across whole film | Soul (trained, needs photos) or Element (instant) |
| Music / score | `sonilo_music` |
| Dialogue / narration | `inworld_text_to_speech` |
| SFX / ambience | `mirelo_text_to_audio` |

## Edit / enhance (prefer over re-generating)

| Tool | Use |
|---|---|
| `upscale_image` / `upscale_video` | raise resolution to 2K/4K — **final/hero only** |
| `outpaint_image` | expand/uncrop a frame |
| `reframe` | change a video's aspect — **hero only**; routine social crops are free via `scripts/package.py` |
| `remove_background` | cutout / transparent |
| `motion_control` | recast / puppeteer / motion transfer |
| `dubbing` / `voice_change` | localize audio / swap a voice without re-shooting |

## Analyze / distribute

| Tool | Use |
|---|---|
| `virality_predictor` | hook strength, retention, engagement — on finals + teasers |
| `video_analysis_create` / `_status` | deeper analysis of a clip |
| `show_marketing_studio` | product-URL → ad pipeline (A&T ad factory) |
| `models_explore` | list voices, recommend a model for a goal, read a tool's schema |

## Media I/O (getting assets in)

- Local file (photo/clip/audio) → `media_upload_widget` (UI clients) or
  `media_upload` → PUT bytes → `media_confirm`.
- Web URL → `media_import_url` first, then pass the returned `media_id`.
- **Never** put element IDs or raw URLs in `medias[]` — embed `<<<UUID>>>` in the
  prompt TEXT; pass uploaded media by `media_id`.

## Job hygiene (crash insurance)

Record every `job_id` in `project.json higgsfield_jobs` **before** waiting on it.
A dead session recovers results via `show_generations` / `job_display` /
`reveal_generation` instead of paying twice. Download to disk immediately
(`scripts/download.py`) — a job URL is not a durable copy.
