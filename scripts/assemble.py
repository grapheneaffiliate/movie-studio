#!/usr/bin/env python3
"""
assemble.py — Build the picture cut from shotlist.json.

Takes every approved clip, normalizes (fps/resolution/pixfmt), trims to the
shotlist duration, applies transitions (cut | fade | xfade styles), and renders
a single video. Audio mixing is handled separately by audio_mix.py, then muxed.

Usage:
  python3 scripts/assemble.py projects/<slug> [--out final/<slug>_v1.mp4] [--draft]

--draft renders 720p fast preset for quick review cycles.
"""
import json, subprocess, sys, argparse, shlex
from pathlib import Path

XFADE_TYPES = {"fade", "dissolve", "wipeleft", "wiperight", "slideup", "slidedown",
               "circleopen", "circleclose", "fadeblack", "fadewhite", "radial",
               "smoothleft", "smoothright", "distance", "pixelize"}

def run(cmd):
    print("+", " ".join(shlex.quote(c) for c in cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-4000:])
        sys.exit(f"FAILED: {cmd[0]}")
    return r

def probe_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--out", default=None)
    ap.add_argument("--draft", action="store_true")
    args = ap.parse_args()

    proj = Path(args.project_dir)
    sl = json.loads((proj / "shotlist.json").read_text())
    fps = sl.get("fps", 24)
    ar = sl.get("aspect_ratio", "16:9")
    w, h = (1920, 1080) if ar == "16:9" else (1080, 1920) if ar == "9:16" else (1440, 1440)
    if args.draft:
        w, h = (w * 2 // 3, h * 2 // 3)

    shots = [s for s in sl["shots"] if s.get("approved_take")]
    missing = [s["id"] for s in sl["shots"] if not s.get("approved_take")]
    if missing:
        sys.exit(f"REFUSING TO ASSEMBLE: shots without approved takes: {missing}\n"
                 f"Run the dailies review loop first.")

    # 1. Normalize every approved clip into a uniform intermediate
    tmp = proj / "final" / ".norm"
    tmp.mkdir(parents=True, exist_ok=True)
    norm_paths, durs = [], []
    for s in shots:
        src = proj / "clips" / s["approved_take"]
        if not src.exists():
            sys.exit(f"Missing clip on disk: {src}")
        dst = tmp / f"{s['id']}.mp4"
        d = min(s["duration_s"], probe_duration(src))
        vf = (f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
              f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,fps={fps},format=yuv420p,setsar=1")
        run(["ffmpeg", "-y", "-i", str(src), "-t", f"{d:.3f}", "-vf", vf,
             "-an", "-c:v", "libx264", "-preset", "veryfast" if args.draft else "slow",
             "-crf", "20" if args.draft else "17", str(dst)])
        norm_paths.append(dst); durs.append(d)

    out = Path(args.out) if args.out else proj / "final" / f"{sl['project']}_{'draft' if args.draft else 'v1'}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)

    # 2. Build filtergraph: chain xfade where transitions requested, else concat
    transitions = [s.get("transition_in") or {"type": "cut"} for s in shots]
    needs_xfade = any(t["type"] in XFADE_TYPES for t in transitions[1:])

    if not needs_xfade:
        lst = tmp / "concat.txt"
        lst.write_text("".join(f"file '{p.resolve()}'\n" for p in norm_paths))
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
             "-c", "copy", str(out)])
    else:
        inputs = []
        for p in norm_paths:
            inputs += ["-i", str(p)]
        fg, cur, offset = [], "[0:v]", durs[0]
        for i in range(1, len(norm_paths)):
            t = transitions[i]
            ttype = t["type"] if t["type"] in XFADE_TYPES else "fade"
            tdur = min(float(t.get("duration_s", 0.5)), durs[i - 1] / 2, durs[i] / 2)
            if t["type"] == "cut":
                # exactly one frame: sub-frame xfade durations silently truncate the chain
                ttype, tdur = "fade", 1.0 / fps
            label = f"[v{i}]"
            fg.append(f"{cur}[{i}:v]xfade=transition={ttype}:duration={tdur:.4f}:"
                      f"offset={offset - tdur:.4f}{label}")
            cur = label
            offset += durs[i] - tdur
        run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fg),
             "-map", cur, "-c:v", "libx264",
             "-preset", "veryfast" if args.draft else "slow",
             "-crf", "20" if args.draft else "17", "-pix_fmt", "yuv420p", str(out)])

    # 3. Mux audio if the mixdown exists
    mix = proj / "audio" / "mixdown.wav"
    if mix.exists():
        muxed = out.with_name(out.stem + "_mix.mp4")
        run(["ffmpeg", "-y", "-i", str(out), "-i", str(mix),
             "-map", "0:v", "-map", "1:a", "-c:v", "copy",
             "-c:a", "aac", "-b:a", "256k", "-shortest", str(muxed)])
        print(f"\nDELIVERED (with audio): {muxed}")
    else:
        print(f"\nDELIVERED (picture only — run audio_mix.py then re-run): {out}")
    print(f"Total runtime ≈ {sum(durs):.1f}s across {len(shots)} shots")

if __name__ == "__main__":
    main()
