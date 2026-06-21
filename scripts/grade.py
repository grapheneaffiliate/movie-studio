#!/usr/bin/env python3
"""
grade.py — The colorist. Apply a cinematic color grade to a cut, clip, or still.

Color is the cheapest way to make AI footage look intentional and consistent.
A committed grade (one look across the whole piece — the style page's law) hides
the small palette drift that plagues generated shots. All ffmpeg, all free,
re-runnable: never bake a grade you can't revise.

Modes:
  list    Show the look book.
  apply   Apply a named look (+ optional vignette / film grain / contrast).
  lut     Apply a 3D LUT (.cube) — for grades authored in Resolve/Premiere.

Usage:
  python3 scripts/grade.py list
  python3 scripts/grade.py apply in.mp4 --look teal-orange --out graded.mp4
  python3 scripts/grade.py apply in.mp4 --look noir --vignette --grain 6 --out g.mp4
  python3 scripts/grade.py apply key_art.png --look vintage --out key_art_graded.png
  python3 scripts/grade.py lut in.mp4 --cube look.cube --out graded.mp4

Works on video (keeps audio) and stills (png/jpg). Apply on the FINAL cut for a
unified look, or per-clip during dailies to match a stubborn shot to its scene.
"""
import subprocess, sys, argparse
from pathlib import Path

LOOKS = {
    "teal-orange": (
        "Blockbuster: teal shadows, warm skin/highlights. The default 'cinematic'.",
        "colorbalance=rs=-0.15:gs=0.00:bs=0.12:rh=0.12:gh=0.04:bh=-0.12,"
        "eq=contrast=1.06:saturation=1.12"),
    "noir": (
        "High-contrast black & white. Crime, drama, timeless.",
        "hue=s=0,eq=contrast=1.28:brightness=-0.02,curves=preset=strong_contrast"),
    "bleach-bypass": (
        "Silver-retention look: desaturated, hard contrast, gritty (war/thriller).",
        "eq=saturation=0.42:contrast=1.30:brightness=0.015"),
    "day-for-night": (
        "Shoot bright, sell as night: cool, dim, low-sat blue cast.",
        "colorbalance=bs=0.16:bm=0.10:bh=0.05,"
        "eq=brightness=-0.13:contrast=1.06:saturation=0.78"),
    "vintage": (
        "Faded film: lifted milky blacks, warm, gentle desaturation.",
        "curves=r='0/0.06 1/0.95':g='0/0.05 1/0.94':b='0/0.07 1/0.90',"
        "eq=saturation=0.86:contrast=0.96"),
    "cyberpunk": (
        "Neon night city: magenta/cyan push, electric saturation.",
        "colorbalance=rs=0.10:bs=0.16:gh=-0.05:bh=0.12,"
        "eq=saturation=1.40:contrast=1.10,hue=h=-8"),
    "warm": (
        "Golden hour / nostalgia: warm white balance, soft punch.",
        "colorbalance=rm=0.07:rh=0.07:bm=-0.06:bh=-0.07,eq=saturation=1.06:contrast=1.03"),
    "cool": (
        "Clinical / tech / winter: cool white balance.",
        "colorbalance=bm=0.07:bh=0.07:rm=-0.05:rh=-0.06,eq=saturation=1.0:contrast=1.04"),
    "sepia": (
        "Antique sepia tone (period/flashback).",
        "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131:0"),
    "horror": (
        "Sickly green-cyan pallor, crushed and desaturated.",
        "colorbalance=gs=0.08:gm=0.06:gh=0.04:rs=-0.05,"
        "eq=saturation=0.84:contrast=1.16:brightness=-0.05"),
    "vibrant": (
        "Social-punch: high saturation/contrast + light sharpen (Reels/TikTok).",
        "eq=saturation=1.32:contrast=1.12:brightness=0.01,unsharp=5:5:0.8"),
    "moody": (
        "Underexposed, desaturated, cool — prestige-drama restraint.",
        "eq=saturation=0.82:contrast=1.13:brightness=-0.03,colorbalance=bs=0.06:bh=-0.03"),
    "noir-color": (
        "Color noir: deep contrast, amber practicals against blue night.",
        "colorbalance=bs=0.10:rm=0.04:rh=0.06:bh=-0.04,"
        "eq=contrast=1.18:saturation=0.92:brightness=-0.04"),
}

IMG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")


def cmd_list(_a):
    print("LOOK BOOK (grade.py apply <in> --look <name>):\n")
    for name, (desc, _) in LOOKS.items():
        print(f"  {name:14s} {desc}")
    print("\n  add-ons: --vignette  --grain <0-20>  --contrast <mult, e.g. 1.1>")
    print("  custom LUT: grade.py lut <in> --cube look.cube --out <out>")


def build_chain(look, vignette, grain, contrast):
    chain = [LOOKS[look][1]]
    if contrast and abs(contrast - 1.0) > 1e-6:
        chain.append(f"eq=contrast={contrast}")
    if vignette:
        chain.append("vignette=PI/4.5")
    if grain and grain > 0:
        chain.append(f"noise=alls={int(grain)}:allf=t+u")
    chain.append("format=yuv420p")
    return ",".join(chain)


def cmd_apply(a):
    if a.look not in LOOKS:
        sys.exit(f"Unknown look '{a.look}'. Run: grade.py list")
    src = Path(a.src)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    vf = build_chain(a.look, a.vignette, a.grain, a.contrast)
    is_img = src.suffix.lower() in IMG_EXT
    if is_img:
        vf = vf.replace(",format=yuv420p", "")  # keep full color for stills
        cmd = ["ffmpeg", "-y", "-i", str(src), "-vf", vf, "-frames:v", "1", str(out)]
    else:
        cmd = ["ffmpeg", "-y", "-i", str(src), "-vf", vf,
               "-c:v", "libx264", "-crf", "17", "-preset", "slow",
               "-c:a", "copy", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-3000:]); sys.exit("grade failed")
    extras = [x for x in (("vignette" if a.vignette else ""),
                          (f"grain{a.grain}" if a.grain else ""),
                          (f"contrast{a.contrast}" if a.contrast != 1.0 else "")) if x]
    print(f"GRADED [{a.look}{(' +' + '+'.join(extras)) if extras else ''}]: {out}")


def cmd_lut(a):
    src = Path(a.src); cube = Path(a.cube); out = Path(a.out)
    if not cube.exists():
        sys.exit(f"LUT not found: {cube}")
    out.parent.mkdir(parents=True, exist_ok=True)
    esc = str(cube).replace("\\", "/").replace(":", "\\:")
    vf = f"lut3d='{esc}',format=yuv420p"
    is_img = src.suffix.lower() in IMG_EXT
    if is_img:
        cmd = ["ffmpeg", "-y", "-i", str(src), "-vf", f"lut3d='{esc}'",
               "-frames:v", "1", str(out)]
    else:
        cmd = ["ffmpeg", "-y", "-i", str(src), "-vf", vf,
               "-c:v", "libx264", "-crf", "17", "-preset", "slow",
               "-c:a", "copy", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-3000:]); sys.exit("LUT apply failed")
    print(f"GRADED [LUT {cube.name}]: {out}")


def main():
    ap = argparse.ArgumentParser(description="Cinematic color grading")
    sub = ap.add_subparsers(dest="mode", required=True)
    sub.add_parser("list").set_defaults(func=cmd_list)
    ap_a = sub.add_parser("apply")
    ap_a.add_argument("src")
    ap_a.add_argument("--look", required=True)
    ap_a.add_argument("--vignette", action="store_true")
    ap_a.add_argument("--grain", type=int, default=0)
    ap_a.add_argument("--contrast", type=float, default=1.0)
    ap_a.add_argument("--out", required=True)
    ap_a.set_defaults(func=cmd_apply)
    ap_l = sub.add_parser("lut")
    ap_l.add_argument("src")
    ap_l.add_argument("--cube", required=True)
    ap_l.add_argument("--out", required=True)
    ap_l.set_defaults(func=cmd_lut)
    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
