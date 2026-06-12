---
name: screenwriting
description: DEVELOPMENT stage. Turn the user's prompt into screenplay.md — logline, treatment, character bible, formatted screenplay, style page. Use when starting any film/trailer/music-video/ad project, or when a story revision is requested.
---

# Screenwriting — the Development department

You own everything that happens before a single frame is designed. Output is one
file: `projects/<slug>/screenplay.md`. Advance `project.json` stage to
`"pre-production"` when done and log every creative default you took in `notes[]`.

Run the **creative-writing** skill alongside this one: it pressure-tests the
concept for novelty before the treatment locks, and adds a `[SPEC sNN]` block
under each action paragraph so every clip-level detail is captured on the page.

## Output structure (screenplay.md, in this order)

1. **Logline** — one sentence: protagonist + want + obstacle + tone.
2. **Treatment** — one paragraph per act. For a trailer: hook / escalation / button.
   For a music video: structure mapped to the track (verse/chorus/bridge).
3. **Character bible** — for each character (hard cap 3), written in
   *prompt-ready language* (the exact words shot-design will paste into image
   prompts):
   - physical description: age, build, face, hair — concrete and visual
   - **one outfit per act**, described in fabric/color terms ("weathered olive
     flight jacket, brass goggles"). Wardrobe never changes mid-act — this is a
     continuity law, not a style choice.
   - voice profile (age/energy/register) for sound-department casting
4. **Screenplay** — standard format: scene headings (INT./EXT., location, time),
   action lines, dialogue. Action lines must be *visual* — describe what the
   camera sees, never internal states ("she remembers" is unfilmable; "her hand
   stops on the dial" is a shot).
5. **Style page** — one committed look for the whole piece: palette (3-5 named
   colors), lens language (focal lengths, depth), lighting philosophy, film-stock
   or grade reference. Never mix looks across acts.
6. **`### Director's log`** — append-only; one line per significant decision.
   Started here, extended by every later department.

## Generatability law (write only what the render farm can shoot)

AI video fails predictably. Do not write these; use the workaround:

| Never write | Write instead |
|---|---|
| Crowds, background extras | empty spaces, implied presence (shadows, PA audio, distant silhouettes) |
| Mirrors, reflections of characters | reaction shots, over-shoulder framing |
| Fine hand work (typing, knots, instruments) | close-up on face + sound design, or cutaway to result |
| Legible on-screen text in-world | title cards added in post, or keep signage out of focus |
| Two characters touching/fighting closely | shot/reverse-shot, impact implied by sound + reaction |
| Continuous long takes (>10 s) | sequences of 4-10 s shots |

## Scope discipline

- Runtime targets from the Defaults Table (CLAUDE.md §2). A 2-minute film is
  18-25 shots — write a story that fits, not one that needs trimming later.
- Dialogue only if the prompt implies speech; every line must be speakable
  inside one 4-10 s shot (~20 words max).
- The user's verbatim prompt is the contract: every concrete noun in it
  ("rain everywhere", "neon Tokyo") must be traceable to a scene.

## Handoff

Done when screenplay.md has all six sections and `project.json` notes record:
genre/tone choice, runtime, character count, look commitment. Next: shot-design.
