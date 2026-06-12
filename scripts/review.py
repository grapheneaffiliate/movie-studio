#!/usr/bin/env python3
"""
review.py — The agent's eyes.

Modes:
  contact   Build a contact-sheet PNG (grid of frames) for one clip or all clips
            so Claude can visually inspect motion, continuity, artifacts.
  lastframe Extract the final frame of a clip as PNG — feed it to the next shot's
            start_image for seamless continuity chaining.
  strip     Extract N evenly-spaced frames as individual PNGs (deeper inspection).
  cutsheet  Contact sheet of the FINAL assembled cut (1 frame / 2 s) for final QC.

Usage:
  python3 scripts/review.py contact projects/<slug> [clip.mp4]
  python3 scripts/review.py lastframe projects/<slug>/clips/s01_t01.mp4
  python3 scripts/review.py strip projects/<slug>/clips/s01_t01.mp4 --n 8
  python3 scripts/review.py cutsheet projects/<slug>/final/<file>.mp4

All outputs land in <project>/dailies/. After running, VIEW the PNGs with the
Read tool and write verdicts into shotlist.json review_notes.
"""
import subprocess, sys, argparse, math
from pathlib import Path

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(r.stderr[-2000:])

def dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip())

def dailies_dir(p: Path) -> Path:
    for parent in [p] + list(p.parents):
        if (parent / "project.json").exists() or parent.name in ("clips", "final"):
            base = parent if (parent / "project.json").exists() else parent.parent
            d = base / "dailies"; d.mkdir(exist_ok=True); return d
    d = p.parent / "dailies"; d.mkdir(exist_ok=True); return d

def contact(clip: Path, frames=9, tile=None):
    d = dur(clip)
    tile = tile or f"{math.ceil(math.sqrt(frames))}x{math.ceil(frames/math.ceil(math.sqrt(frames)))}"
    out = dailies_dir(clip) / f"{clip.stem}_contact.png"
    fps = frames / max(d, 0.1)
    run(["ffmpeg", "-y", "-i", str(clip),
         "-vf", f"fps={fps:.4f},scale=480:-1,tile={tile}", "-frames:v", "1", str(out)])
    print(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["contact", "lastframe", "strip", "cutsheet"])
    ap.add_argument("target")
    ap.add_argument("clip", nargs="?")
    ap.add_argument("--n", type=int, default=8)
    a = ap.parse_args()
    t = Path(a.target)

    if a.mode == "contact":
        clips = [t / "clips" / a.clip] if a.clip else sorted((t / "clips").glob("*.mp4")) if t.is_dir() else [t]
        for c in clips:
            contact(c)
    elif a.mode == "lastframe":
        out = dailies_dir(t) / f"{t.stem}_last.png"
        run(["ffmpeg", "-y", "-sseof", "-0.1", "-i", str(t), "-update", "1",
             "-frames:v", "1", "-q:v", "1", str(out)])
        print(out)
    elif a.mode == "strip":
        d = dur(t); dd = dailies_dir(t)
        for i in range(a.n):
            ts = d * (i + 0.5) / a.n
            out = dd / f"{t.stem}_f{i:02d}.png"
            run(["ffmpeg", "-y", "-ss", f"{ts:.3f}", "-i", str(t),
                 "-frames:v", "1", "-q:v", "2", str(out)])
            print(out)
    elif a.mode == "cutsheet":
        d = dur(t)
        n = max(int(d / 2), 6)
        contact(t, frames=min(n, 36))

if __name__ == "__main__":
    main()
