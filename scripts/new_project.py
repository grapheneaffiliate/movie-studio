#!/usr/bin/env python3
"""
new_project.py — Scaffold a project from a slug and the verbatim user prompt.

Usage: python3 scripts/new_project.py "salt-flat-trailer" "Make a 90 second..."
       [--deliverable trailer|short_film|music_video|ad|feature|image|track]
       [--runtime 90] [--aspect 16:9]

Creates the directory tree, a populated project.json, and an empty shotlist
seeded from templates. Idempotent: refuses to overwrite an existing project.
"""
import json, sys, argparse, datetime, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug"); ap.add_argument("prompt")
    ap.add_argument("--deliverable", default="short_film")
    ap.add_argument("--runtime", type=int, default=None)
    ap.add_argument("--aspect", default="16:9")
    a = ap.parse_args()

    slug = re.sub(r"[^a-z0-9-]+", "-", a.slug.lower()).strip("-")
    pdir = ROOT / "projects" / slug
    if pdir.exists():
        sys.exit(f"Project exists: {pdir} — resume it (scripts/status.py) or pick a new slug.")

    for d in ("clips", "refs", "dailies", "final",
              "audio/music", "audio/dialogue", "audio/sfx"):
        (pdir / d).mkdir(parents=True)

    defaults = {"trailer": 75, "short_film": 180, "music_video": 150,
                "ad": 30, "feature": 240, "image": 0, "track": 0}
    manifest = json.loads((ROOT / "templates" / "project.json").read_text())
    manifest.update({
        "slug": slug,
        "title": slug.replace("-", " ").title(),
        "created": datetime.date.today().isoformat(),
        "user_prompt": a.prompt,
        "deliverable": a.deliverable,
        "stage": "development",
        "target_runtime_s": a.runtime if a.runtime is not None
                            else defaults.get(a.deliverable, 120),
    })
    (pdir / "project.json").write_text(json.dumps(manifest, indent=2))

    sl = json.loads((ROOT / "templates" / "shotlist.json").read_text())
    sl.update({"project": slug, "aspect_ratio": a.aspect,
               "target_runtime_s": manifest["target_runtime_s"],
               "characters": [], "shots": [],
               "audio": {"music": [], "dialogue": [], "sfx": []}})
    sl.pop("$comment", None)
    (pdir / "shotlist.json").write_text(json.dumps(sl, indent=2))

    print(f"Scaffolded {pdir}")
    print(f"  deliverable={a.deliverable} runtime={manifest['target_runtime_s']}s "
          f"aspect={a.aspect}")
    print("  Next: screenwriting skill → screenplay.md")

if __name__ == "__main__":
    main()
