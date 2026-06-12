---
name: sound-department
description: SOUND stage. Generate score, dialogue TTS, and SFX from the shotlist audio block; cast voices; verify stems; mix with audio_mix.py. Use after picture approval, or for single-track requests and audio fixes.
---

# Sound Department — score, voice, effects

You realize the shotlist `audio` block as files on disk and a mixdown. Stage
advances to `"post"` when `audio/mixdown.wav` exists and verifies.

## Model routing

| Cue type | Model |
|---|---|
| Music / score | `sonilo_music` |
| Dialogue / narration | `inworld_text_to_speech` |
| SFX / ambience | `mirelo_text_to_audio` |

## Stem discipline (naming is load-bearing)

Every cue id in the shotlist maps to exactly one file:
`audio/<music|dialogue|sfx>/<id>.<wav|mp3|m4a|flac|aac|ogg>` — id match is
exact; `status.py` flags any gap as STEM-MISSING and `audio_mix.py` skips it
with a warning. Download every generation immediately (`download.py`).

## Music

- One cue per act minimum (per shotlist plan). Generate to the cue's
  `duration_s`; if the model returns long, it's fine — the mix trims.
- Music-language prompts: genre, tempo/bpm, instrumentation, dynamic arc
  ("slow build", "drops to solo piano"). Reuse motif language across cues so
  acts feel scored, not playlisted.
- Music-video flow is inverted: generate the full track FIRST, listen-map its
  structure (intro/verse/chorus timestamps via ffprobe duration + the brief),
  then hand timestamps back to shot-design to cut picture to it.

## Dialogue

- **Voice casting**: list voices via `models_explore`, pick per character by
  age/energy/register from the bible's voice profile. Log the casting + why in
  project.json notes. One voice per character, never re-cast mid-film.
- **Timing math (hard rule)**: a line must fit inside its shot. After
  generating, `ffprobe` the stem duration; if it exceeds the shot's
  `duration_s` minus 0.5 s handles, SHORTEN THE LINE TEXT and regenerate —
  never speed-warp audio. Update `start_at_s` to the line's real timeline
  position (shot start + beat offset).

## SFX

- Ambience bed per location (looping texture: "rain on glass, distant foghorn"),
  hard effects for on-screen events synced to `start_at_s`.
- Gains if unset: music −6, dialogue 0, ambience −12, hard SFX −3.

## Verify, then mix

Every stem: ffprobe-readable, has an audio stream, duration sane vs cue. Then:
```bash
python3 scripts/audio_mix.py projects/<slug>          # reads runtime from final/
```
The mixer places stems at `start_at_s`, applies `gain_db`, ducks music −7 dB
under dialogue (±0.3 s), trims to picture, limits, writes `audio/mixdown.wav`.
Re-run `assemble.py` afterward to mux the `*_mix.mp4`. If dialogue sounds
clipped at the end, the line overran its window — fix the text, not the clock.
