#!/usr/bin/env python3
"""
thumbnail.py — Key art, posters, and thumbnails. The marketing image.

A media maker lives or dies on the thumbnail/poster. This frames a still (from a
generated key-art image or grabbed from the final cut), reframes it to the target
shape, lays a readability scrim, and sets a title + tagline — all locally.

Presets:
  youtube  1280x720   (16:9 video thumbnail)
  poster   1080x1620  (2:3 theatrical one-sheet)
  vertical 1080x1920  (Shorts/Reels/Stories cover)
  square   1080x1080
  wide     1920x1080

Usage:
  python3 scripts/thumbnail.py make refs/key_art.png --title "DERELICT" \
      --sub "in the belt, no one is coming" --preset youtube --scrim --out thumb.png
  python3 scripts/thumbnail.py make projects/x/final/cut.mp4 --at 12 \
      --title "DERELICT" --preset poster --pos bottom --accent "#c8a04a" --out poster.png

Keep titles short — drawtext is wrapped softly but big posters read best at 1-3
words. Source can be an image or a video (use --at to pick the grab time).
"""
import subprocess, sys, argparse, tempfile, os, textwrap
from pathlib import Path

FONTS = ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "/Library/Fonts/Arial.ttf", "C:/Windows/Fonts/arialbd.ttf"]
PRESETS = {"youtube": (1280, 720), "poster": (1080, 1620),
           "vertical": (1080, 1920), "square": (1080, 1080), "wide": (1920, 1080)}
VID_EXT = (".mp4", ".mov", ".webm", ".mkv")


def font():
    for f in FONTS:
        if Path(f).exists():
            return f
    sys.exit("No font found — install dejavu fonts or edit FONTS in thumbnail.py")


def esc(t):
    return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-3000:]); sys.exit("thumbnail failed")


def main():
    ap = argparse.ArgumentParser(description="Key art / poster / thumbnail generator")
    sub = ap.add_subparsers(dest="mode", required=True)
    m = sub.add_parser("make")
    m.add_argument("src")
    m.add_argument("--title", default="")
    m.add_argument("--sub", default="")
    m.add_argument("--preset", default="youtube", choices=list(PRESETS))
    m.add_argument("--at", type=float, default=None, help="grab time if src is video")
    m.add_argument("--pos", default="bottom", choices=["bottom", "center", "top"])
    m.add_argument("--scrim", action="store_true", help="gradient darkening for legibility")
    m.add_argument("--accent", default="#c8a04a")
    m.add_argument("--out", required=True)
    a = ap.parse_args()

    w, h = PRESETS[a.preset]
    src = Path(a.src)
    tmp = None
    if src.suffix.lower() in VID_EXT:
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False); tmp.close()
        run(["ffmpeg", "-y", "-ss", str(a.at or 1.0), "-i", str(src),
             "-frames:v", "1", tmp.name])
        base = Path(tmp.name)
    else:
        base = src

    f = font()
    chain = [f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos",
             f"crop={w}:{h}"]
    if a.scrim:
        # a black layer whose alpha ramps up toward the text side (legibility scrim)
        if a.pos == "bottom":
            ramp = "clip(255*(Y/H-0.35)/0.65,0,210)"
        elif a.pos == "top":
            ramp = "clip(255*(0.5-Y/H)/0.5,0,210)"
        else:
            ramp = "110"
    fs_title = int(h * 0.11)
    fs_sub = int(fs_title * 0.34)
    wrapped = "\n".join(textwrap.wrap(a.title, width=max(int(w / (fs_title*0.62)), 8))) if a.title else ""

    # title temp file (handles wrapping/newlines cleanly)
    title_tf = None
    draws = []
    y_title = {"bottom": f"h-h*0.20", "center": "(h-text_h)/2", "top": "h*0.10"}[a.pos]
    if wrapped:
        title_tf = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
        title_tf.write(wrapped); title_tf.close()
        draws.append(
            f"drawtext=fontfile='{f}':textfile='{title_tf.name}':fontcolor=white:"
            f"fontsize={fs_title}:x=(w-text_w)/2:y={y_title}:line_spacing={int(fs_title*0.15)}:"
            f"shadowcolor=black@0.8:shadowx=4:shadowy=4")
    if a.sub:
        y_sub = {"bottom": "h-h*0.075", "center": "(h+text_h)/2+30", "top": "h*0.10+text_h+40"}[a.pos]
        draws.append(
            f"drawtext=fontfile='{f}':text='{esc(a.sub.upper())}':fontcolor={a.accent}:"
            f"fontsize={fs_sub}:x=(w-text_w)/2:y={y_sub}:"
            f"shadowcolor=black@0.8:shadowx=2:shadowy=2")

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    try:
        if a.scrim:
            # base + a black layer whose alpha follows the ramp, overlaid
            fc = (f"[0:v]{','.join(chain)}[bg];"
                  f"color=c=black:s={w}x{h},format=rgba,"
                  f"geq=r=0:g=0:b=0:a='{ramp}'[scr];"
                  f"[bg][scr]overlay[v]")
            vf_post = (";[v]" + ",".join(draws) + "[out]") if draws else ";[v]null[out]"
            run(["ffmpeg", "-y", "-i", str(base),
                 "-filter_complex", fc + vf_post, "-map", "[out]",
                 "-frames:v", "1", str(a.out)])
        else:
            vf = ",".join(chain + draws)
            run(["ffmpeg", "-y", "-i", str(base), "-vf", vf, "-frames:v", "1", str(a.out)])
    finally:
        if tmp:
            os.unlink(tmp.name)
        if title_tf:
            os.unlink(title_tf.name)
    print(f"THUMBNAIL [{a.preset} {w}x{h}]: {a.out}")


if __name__ == "__main__":
    main()
