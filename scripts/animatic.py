#!/usr/bin/env python3
"""
animatic.py — Pre-visualization: a timed animatic from start-frame stills.

The fail-cheap law, extended to editing. Before spending a single video credit,
generate every shot's START FRAME as an image (you already do this), then string
those stills into a timed slideshow at the real shotlist durations — with the
scratch mixdown if it exists. Now you can SEE the pacing, the shot rhythm, and
the story flow for the price of images, and fix the edit before animating.

It reads shotlist.json, finds each shot's start frame in refs/ (named after the
shot id: refs/s01.png, refs/s01_start.jpg, …), and for any missing frame drops a
labeled slate so the timing still reads. Optional Ken Burns push-in sells motion.

Usage:
  python3 scripts/animatic.py build projects/<slug>            # -> final/<slug>_animatic.mp4
  python3 scripts/animatic.py build projects/<slug> --kenburns --audio
  python3 scripts/animatic.py build projects/<slug> --out previz.mp4
"""
import json, subprocess, sys, argparse, tempfile, shutil
from pathlib import Path

FONTS = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
         "/Library/Fonts/Arial.ttf", "C:/Windows/Fonts/arial.ttf"]
IMG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".bmp")


def font():
    for f in FONTS:
        if Path(f).exists():
            return f
    return None


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-2500:]); sys.exit(f"FAILED: {cmd[0]}")


def find_frame(proj: Path, shot_id: str):
    for d in (proj / "refs", proj / "dailies"):
        if not d.exists():
            continue
        for e in IMG_EXT:
            for cand in (d / f"{shot_id}{e}", d / f"{shot_id}_start{e}", d / f"{shot_id}_frame{e}"):
                if cand.exists():
                    return cand
        hits = sorted(d.glob(f"{shot_id}*"))
        hits = [h for h in hits if h.suffix.lower() in IMG_EXT]
        if hits:
            return hits[0]
    return None


def seg_from_image(img, dst, w, h, dur, fps, kenburns):
    frames = max(int(dur * fps), 1)
    if kenburns:
        vf = (f"scale={w*2}:{h*2}:force_original_aspect_ratio=increase,"
              f"crop={w*2}:{h*2},"
              f"zoompan=z='min(zoom+0.0010,1.12)':d={frames}:"
              f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps},"
              f"format=yuv420p,setsar=1")
        run(["ffmpeg", "-y", "-loop", "1", "-i", str(img), "-vf", vf,
             "-t", f"{dur}", "-r", str(fps), "-c:v", "libx264", "-crf", "20",
             "-pix_fmt", "yuv420p", str(dst)])
    else:
        vf = (f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
              f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p")
        run(["ffmpeg", "-y", "-loop", "1", "-i", str(img), "-vf", vf,
             "-t", f"{dur}", "-r", str(fps), "-c:v", "libx264", "-crf", "20",
             "-pix_fmt", "yuv420p", str(dst)])


def seg_slate(shot_id, label, dst, w, h, dur, fps):
    f = font()
    txt = f"{shot_id}\\n{label}"
    vf = []
    if f:
        vf.append(f"drawtext=fontfile='{f}':text='{shot_id}':fontcolor=white:"
                  f"fontsize={int(h*0.12)}:x=(w-text_w)/2:y=(h-text_h)/2-40")
        vf.append(f"drawtext=fontfile='{f}':text='{label}':fontcolor=gray:"
                  f"fontsize={int(h*0.045)}:x=(w-text_w)/2:y=(h+text_h)/2+30")
    vfs = ("," + ",".join(vf)) if vf else ""
    run(["ffmpeg", "-y", "-f", "lavfi",
         "-i", f"color=c=0x1a1a1a:s={w}x{h}:d={dur}:r={fps}",
         "-vf", f"format=yuv420p{vfs}", "-t", f"{dur}",
         "-c:v", "libx264", "-crf", "22", "-pix_fmt", "yuv420p", str(dst)])


def cmd_build(a):
    proj = Path(a.target)
    sl = json.loads((proj / "shotlist.json").read_text())
    fps = sl.get("fps", 24)
    ar = sl.get("aspect_ratio", "16:9")
    w, h = (1280, 720) if ar == "16:9" else (720, 1280) if ar == "9:16" else (960, 960)
    shots = sl.get("shots", [])
    if not shots:
        sys.exit("No shots in shotlist yet — write the shotlist first (shot-design).")

    tmp = Path(tempfile.mkdtemp(prefix="animatic_"))
    segs, total, found = [], 0.0, 0
    try:
        for s in shots:
            dur = float(s.get("duration_s", 4))
            total += dur
            dst = tmp / f"{s['id']}.mp4"
            img = find_frame(proj, s["id"])
            if img:
                found += 1
                seg_from_image(img, dst, w, h, dur, fps, a.kenburns)
            else:
                label = (s.get("shot_type") or s.get("action") or "no start frame")[:48]
                seg_slate(s["id"], label, dst, w, h, dur, fps)
            segs.append(dst)

        lst = tmp / "concat.txt"
        lst.write_text("".join(f"file '{p.resolve()}'\n" for p in segs))
        out = Path(a.out) if a.out else proj / "final" / f"{proj.name}_animatic.mp4"
        out.parent.mkdir(parents=True, exist_ok=True)
        silent = tmp / "silent.mp4"
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
             "-c", "copy", str(silent)])

        mix = proj / "audio" / "mixdown.wav"
        if a.audio and mix.exists():
            run(["ffmpeg", "-y", "-i", str(silent), "-i", str(mix),
                 "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
                 "-b:a", "192k", "-shortest", str(out)])
            audio_note = "with scratch mixdown"
        else:
            shutil.copy(silent, out)
            audio_note = "silent" + (" (no mixdown yet)" if a.audio else "")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\nANIMATIC: {out}")
    print(f"  {len(shots)} shots, {found} real frames + {len(shots)-found} slates, "
          f"{total:.1f}s, {audio_note}")
    print("  Review the pacing in this BEFORE animating — fix edit/durations now (free).")


def main():
    ap = argparse.ArgumentParser(description="Pre-viz animatic from start frames")
    sub = ap.add_subparsers(dest="mode", required=True)
    b = sub.add_parser("build")
    b.add_argument("target", help="project dir")
    b.add_argument("--out", default=None)
    b.add_argument("--kenburns", action="store_true", help="slow push-in on each still")
    b.add_argument("--audio", action="store_true", help="mux audio/mixdown.wav if present")
    b.set_defaults(func=cmd_build)
    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
