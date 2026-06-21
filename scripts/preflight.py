#!/usr/bin/env python3
"""
preflight.py — Verify the studio environment before a production run.

Checks: ffmpeg/ffprobe present and modern enough (xfade needs >=4.3), python
version, writable projects/, templates intact, and prints a reminder list for
things only the agent can verify live (Higgsfield MCP connectivity, credits).

Exit code 0 = clear to shoot. Non-zero = print fix list and abort the run.
"""
import shutil, subprocess, sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
fails, warns = [], []

def check_bin(name):
    p = shutil.which(name)
    if not p:
        fails.append(f"{name} not on PATH — install ffmpeg (apt/brew install ffmpeg)")
        return None
    return p

ff = check_bin("ffmpeg"); check_bin("ffprobe")
if ff:
    v = subprocess.run([ff, "-version"], capture_output=True, text=True).stdout.split()[2]
    try:
        major, minor = (int(x) for x in v.split(".")[:2])
        if (major, minor) < (4, 3):
            fails.append(f"ffmpeg {v} too old — xfade transitions need >= 4.3")
    except ValueError:
        warns.append(f"could not parse ffmpeg version '{v}' — proceeding")
    # filters the finishing departments rely on (titles/subtitles/grade/master/qc)
    filt = subprocess.run([ff, "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    need = {"drawtext": "title cards / lower-thirds / thumbnails (motion-graphics)",
            "subtitles": "burned-in captions (motion-graphics)",
            "loudnorm": "loudness mastering + QC (mastering-delivery)",
            "blackdetect": "QC defect scan", "freezedetect": "QC frozen-clip scan",
            "zoompan": "animatic Ken Burns (previsualization)"}
    for fname, why in need.items():
        if fname not in filt:
            warns.append(f"ffmpeg lacks '{fname}' filter — {why} unavailable "
                         f"(install a full ffmpeg build with libfreetype/libass)")

if sys.version_info < (3, 9):
    fails.append(f"python {sys.version.split()[0]} too old — need >= 3.9")

proj = ROOT / "projects"
proj.mkdir(exist_ok=True)
t = proj / ".write_test"
try:
    t.write_text("ok"); t.unlink()
except OSError:
    fails.append(f"projects/ not writable: {proj}")

for tpl in ("shotlist.json", "project.json"):
    p = ROOT / "templates" / tpl
    if not p.exists():
        fails.append(f"missing template: {p}")
    else:
        try: json.loads(p.read_text())
        except json.JSONDecodeError as e: fails.append(f"corrupt template {tpl}: {e}")

for s in ("assemble.py", "review.py", "audio_mix.py", "download.py",
          "new_project.py", "status.py",
          # finishing & distribution departments
          "titles.py", "subtitle.py", "grade.py", "master.py", "package.py",
          "animatic.py", "qc.py", "thumbnail.py", "edl_export.py",
          "estimate.py", "beatgrid.py"):
    if not (ROOT / "scripts" / s).exists():
        fails.append(f"missing script: scripts/{s}")

# a usable font for drawtext-based tools (titles/thumbnail/animatic slates)
import glob
font_globs = ["/usr/share/fonts/**/*.ttf", "/Library/Fonts/*.ttf",
              "/System/Library/Fonts/**/*.ttf", "C:/Windows/Fonts/*.ttf"]
if not any(glob.glob(g, recursive=True) for g in font_globs):
    warns.append("no .ttf font found — titles/thumbnails need one "
                 "(install fonts-dejavu) or pass --font")

print("PREFLIGHT —", ROOT)
for w in warns: print("  WARN:", w)
if fails:
    print("  ✗ NOT CLEAR TO SHOOT:")
    for f in fails: print("    -", f)
    sys.exit(1)
print("  ✓ binaries, templates, scripts, write access OK")
print("  AGENT MUST ALSO VERIFY LIVE: (1) Higgsfield MCP responds (call `balance`),"
      " (2) sufficient credits for the budget estimate.")
sys.exit(0)
