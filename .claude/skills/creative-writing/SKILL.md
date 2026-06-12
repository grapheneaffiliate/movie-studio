---
name: creative-writing
description: Concept and script-craft layer inside DEVELOPMENT. Pushes premises past first-idea cliché, then writes the script as a "generative screenplay" — every clip-level detail (subject, wardrobe, props, light, camera, motion) specified once in SPEC blocks so downstream Higgsfield prompts are lossless and generations fail less. Use with the screenwriting skill on every original production, and whenever shots keep failing for reasons traceable to an underspecified script.
---

# Creative Writing — concept lab & generative script craft

Screenwriting owns structure and format (logline → treatment → bible →
screenplay → style page). This skill owns two things layered on top:
**originality** of the concept and **detail-completeness** of the page. The
output is the same `screenplay.md` — but written so that shot-design can build
every prompt by *transcription*, never by invention. If shot-design ever has to
make up a detail, the script failed; come back here.

## 1. The novelty engine (run before the treatment is locked)

- **First-idea rule**: generate three distinct premises for the prompt and
  discard the first — it is everyone's first (the model's most probable
  completion is by definition the most generic film). Pick or fuse from the
  survivors. Log all three in the Director's log so the user can see the road
  not taken.
- **Subversion levers** (apply at least one, deliberately): invert the POV
  (the lighthouse's story, not the keeper's) · displace era or setting ·
  shift scale (cosmic stakes in one room; intimate stakes across a galaxy) ·
  impose a formal constraint (real-time, single location, palindrome
  structure, loop) · make the genre's signature image do the opposite job.
- **Specificity is originality**: generic nouns are where clichés live. "A
  radio" is stock; "a brass marine receiver with one red dial light" is a
  film. Upgrade every load-bearing noun to a researched, concrete one — this
  doubles as prompt material later.
- Novelty serves a feeling. Every device above must aim at the one emotion the
  piece is about, named in the logline. Clever-but-cold gets cut.
- Stay inside the generatability law (screenwriting skill): a brilliant
  premise the render farm can't shoot is a failed premise. Invent within the
  medium's strengths: atmosphere, faces, weather, light, scale, slow motion.

## 2. The Generative Screenplay format (SPEC blocks)

Every action paragraph must map 1:1 to one 4-10 s clip, and each carries a
fenced SPEC block — the single source of truth that shot-design transcribes
into `start_frame_prompt` / `video_prompt`:

```
[SPEC s07]
subjects: MARA only — no other people in frame
wardrobe: act-1 oilskin coat (verbatim from bible), wet hair strands on cheek
props:    brass marine receiver, one red dial light, enamel mug (chipped, left of radio)
space:    lighthouse lamp room, rain sheeting on glass behind her
light:    single tungsten practical low-left, teal moonlight rim from window
camera:   50mm, waist-up, slow push-in from doorway height
motion:   only her hand moves — turns the dial one slow click; rain streaks; beam sweeps once
static:   her face, the mug, the horizon line
sound-hook: her own voice crackles through static (cue d03)
```

Rules that make SPEC blocks error-proof:

- **One subject action per clip.** Two actions = the model blends them into
  mush. Split the beat into two shots instead.
- **Name every noun that will be on screen.** Anything visible but unnamed is
  a detail the model will invent — and invented details are where retakes come
  from. Empty space must be claimed too ("bare stone wall behind her").
- **Count people explicitly.** "One woman, no other people" prevents the
  extra-figure hallucination, the most common continuity killer.
- **Say what does NOT move** (`static:`). Unconstrained frames drift; this
  line is the cheapest frozen-clip and morph insurance there is.
- **Continuity nouns are verbatim quotes from the bible.** The coat is
  "weathered oilskin coat" in every single SPEC, never "her raincoat" in s07
  and "the slicker" in s12 — paraphrase is how wardrobe drifts. Repetition is
  a feature of this format, not bad writing.
- Light gets a source and a direction, not a mood ("single tungsten practical
  low-left", not "moody lighting").

## 3. Detail → error map (what each missing detail costs)

| Underspecified in script | Generation failure it causes |
|---|---|
| wardrobe per beat | costume drift between shots |
| light source + direction | relit scenes, flicker between takes |
| unnamed props / claimed empty space | hallucinated clutter, changing set dressing |
| motion verbs + `static:` line | frozen clips, or everything-moves chaos |
| explicit camera move | random AI camera drift |
| people count | extra background figures |
| material words (brass, enamel, oilskin) | plastic-looking texture mush |
| time of day + weather per scene | continuity-breaking sky/light jumps |

When dailies show a recurring failure class, fix the SPEC vocabulary here —
upstream — not just the one prompt.

## 4. Prompt-language craft (how SPEC lines are worded)

These rules make SPEC lines paste-ready for Higgsfield:

- Concrete and sensory over abstract: nouns you can photograph, verbs you can
  watch. Metaphors live in the treatment, never in a SPEC.
- One sentence, one fact. Front-load the subject. No pronouns — repeat the
  noun ("MARA turns the dial", not "she turns it").
- Numbers wherever possible: one woman, two windows, 35mm, golden hour.
- Phrase absences as positives: "empty street, bare walls" — never "no cars,
  no people". Models render every noun they read, including negated ones.
- Style tokens (palette, stock, lens language) are defined ONCE on the style
  page and reused verbatim in every start-frame prompt; SPEC blocks never
  restate or vary them.

## 5. Handoff contract

shot-design builds prompts mechanically: `start_frame_prompt` = style-page
tokens + SPEC subjects/wardrobe/props/space/light + `<<<element_id>>>`;
`video_prompt` = SPEC camera + motion + static lines. Sound-department reads
the `sound-hook:` lines as the first draft of the SFX/dialogue cue list. A
script is done when a stranger could generate the film from SPEC blocks alone
without asking a single question.
