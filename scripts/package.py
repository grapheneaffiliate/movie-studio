#!/usr/bin/env python3
"""
package.py — Delivery: export platform-spec masters from one final cut.

A real studio ships "versions": the same film conformed to each destination's
resolution, aspect, codec, and loudness. This does it locally (free) — including
smart pan-&-scan reframe when the destination aspect differs (e.g. 16:9 → 9:16
for Reels) so you don't spend Higgsfield `reframe` credits on routine social cuts.

Presets:
  youtube      1920x1080  16:9  H.264 high, faststart, -14 LUFS
  youtube4k    3840x2160  16:9  (upscales if source is smaller)
  reels        1080x1920  9:16  (TikTok / Shorts / Reels)
  feed         1080x1350  4:5   (Instagram feed)
  square       1080x1080  1:1
  twitter      1280x720   16:9
  web          1280x720   16:9  smaller bitrate, faststart
  cinema       1920x804   2.39:1 letterbox crop

Modes:
  list     Show presets.
  export   One preset → one file (with reframe + loudness).
  all      Standard social bundle (youtube + reels + square) into a dir.

Usage:
  python3 scripts/package.py export final/cut_master.mp4 --preset reels \
      --focus center --out deliverables/film_reels.mp4
  python3 scripts/package.py all final/cut_master.mp4 --outdir projects/x/deliverables
"""
import subprocess, sys, argparse
from pathlib import Path

# preset: (w, h, crf, loudness_LUFS, faststart)
PRESETS = {
    "youtube":   (1920, 1080, 18, -14, True),
    "youtube4k": (3840, 2160, 18, -14, True),
    "reels":     (1080, 1920, 20, -14, True),
    "feed":      (1080, 1350, 20, -14, True),
    "square":    (1080, 1080, 20, -14, True),
    "twitter":   (1280, 720, 20, -14, True),
    "web":       (1280, 720, 23, -14, True),
    "cinema":    (1920, 804, 17, -27, True),
}


def probe_dims(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    w, h = r.stdout.strip().split(",")
    return int(w), int(h)


def has_audio(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a",
                        "-show_entries", "stream=index", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    return bool(r.stdout.strip())


def reframe_vf(src_w, src_h, dst_w, dst_h, focus):
    """Scale-to-cover then crop to exact target with focus offset."""
    src_ar = src_w / src_h
    dst_ar = dst_w / dst_h
    if abs(src_ar - dst_ar) < 0.01:
        return f"scale={dst_w}:{dst_h}:flags=lanczos"
    # cover then crop
    base = f"scale={dst_w}:{dst_h}:force_original_aspect_ratio=increase:flags=lanczos"
    if dst_ar < src_ar:  # cropping horizontally (e.g. 16:9 -> 9:16)
        x = {"left": "0", "center": "(iw-ow)/2", "right": "iw-ow"}.get(focus, "(iw-ow)/2")
        crop = f"crop={dst_w}:{dst_h}:{x}:0"
    else:  # cropping vertically
        y = {"top": "0", "center": "(ih-oh)/2", "bottom": "ih-oh"}.get(focus, "(ih-oh)/2")
        crop = f"crop={dst_w}:{dst_h}:0:{y}"
    return f"{base},{crop}"


def export_one(src, preset, out, focus):
    w, h, crf, lufs, fast = PRESETS[preset]
    sw, sh = probe_dims(src)
    vf = reframe_vf(sw, sh, w, h, focus) + ",format=yuv420p,setsar=1"
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-i", str(src), "-vf", vf,
           "-c:v", "libx264", "-profile:v", "high", "-preset", "slow",
           "-crf", str(crf), "-pix_fmt", "yuv420p"]
    if fast:
        cmd += ["-movflags", "+faststart"]
    if has_audio(src):
        cmd += ["-af", f"loudnorm=I={lufs}:TP=-1.5:LRA=11",
                "-c:a", "aac", "-b:a", "320k", "-ar", "48000"]
    else:
        cmd += ["-an"]
    cmd.append(str(out))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-3000:]); sys.exit(f"export failed: {preset}")
    size = out.stat().st_size / 1e6
    print(f"  {preset:10s} {w}x{h}  -> {out}  ({size:.1f} MB)")


def cmd_list(_a):
    print("DELIVERY PRESETS (package.py export <in> --preset <name>):\n")
    for name, (w, h, crf, lufs, _f) in PRESETS.items():
        print(f"  {name:10s} {w}x{h:<5d} crf{crf}  {lufs} LUFS")
    print("\n  --focus left|center|right (for 16:9->9:16) or top|center|bottom")


def cmd_export(a):
    if a.preset not in PRESETS:
        sys.exit(f"Unknown preset '{a.preset}'. Run: package.py list")
    print(f"Exporting {a.preset}:")
    export_one(Path(a.src), a.preset, Path(a.out), a.focus)


def cmd_all(a):
    src = Path(a.src)
    outdir = Path(a.outdir)
    stem = src.stem.replace("_master", "").replace("_final", "") or "film"
    bundle = a.presets.split(",") if a.presets else ["youtube", "reels", "square"]
    print(f"Delivery bundle for {src.name} -> {outdir}/:")
    for p in bundle:
        if p not in PRESETS:
            print(f"  (skip unknown preset {p})"); continue
        export_one(src, p, outdir / f"{stem}_{p}.mp4", a.focus)
    print(f"\nDelivered {len(bundle)} versions to {outdir}/")


def main():
    ap = argparse.ArgumentParser(description="Multi-platform delivery export")
    sub = ap.add_subparsers(dest="mode", required=True)
    sub.add_parser("list").set_defaults(func=cmd_list)
    e = sub.add_parser("export")
    e.add_argument("src"); e.add_argument("--preset", required=True)
    e.add_argument("--focus", default="center")
    e.add_argument("--out", required=True)
    e.set_defaults(func=cmd_export)
    al = sub.add_parser("all")
    al.add_argument("src"); al.add_argument("--outdir", required=True)
    al.add_argument("--presets", default="")
    al.add_argument("--focus", default="center")
    al.set_defaults(func=cmd_all)
    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
