#!/usr/bin/env python3
"""
master.py — Audio mastering: loudness normalization to delivery spec (EBU R128).

audio_mix.py mixes and limits; master.py is the final loudness pass that makes a
deliverable conform to the platform's spec so it isn't turned down (or rejected)
on ingest. Two-pass loudnorm = accurate, deterministic, broadcast-grade.

Targets (Integrated LUFS / True Peak dBTP):
  youtube/streaming -14 / -1.0      podcast      -16 / -1.5
  tiktok/reels      -14 / -1.0      broadcast    -23 / -1.0   (EBU R128)
  instagram         -14 / -1.0      atsc (US TV) -24 / -2.0
  film/cinema       -27 / -2.0      music        -14 / -1.0

Modes:
  list      Show targets.
  measure   Report a file's current Integrated LUFS, True Peak, LRA.
  apply     Two-pass normalize to a target; remux video (copy) or write audio.

Usage:
  python3 scripts/master.py measure projects/x/final/cut_mix.mp4
  python3 scripts/master.py apply projects/x/final/cut_mix.mp4 --target youtube \
      --out projects/x/final/cut_master.mp4
  python3 scripts/master.py apply projects/x/audio/mixdown.wav --target broadcast \
      --out projects/x/audio/mixdown_master.wav
"""
import subprocess, sys, argparse, json, re
from pathlib import Path

TARGETS = {
    "youtube": (-14.0, -1.0), "streaming": (-14.0, -1.0), "music": (-14.0, -1.0),
    "tiktok": (-14.0, -1.0), "reels": (-14.0, -1.0), "instagram": (-14.0, -1.0),
    "podcast": (-16.0, -1.5), "broadcast": (-23.0, -1.0), "atsc": (-24.0, -2.0),
    "film": (-27.0, -2.0), "cinema": (-27.0, -2.0),
}
LRA = 11.0
AUDIO_EXT = (".wav", ".mp3", ".m4a", ".flac", ".aac", ".ogg")


def has_audio(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a",
                        "-show_entries", "stream=index", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    return bool(r.stdout.strip())


def measure(path, I, TP):
    """Run loudnorm analysis pass, return the parsed JSON dict."""
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path),
         "-af", f"loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json",
         "-f", "null", "-"],
        capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.DOTALL)
    if not m:
        sys.stderr.write(r.stderr[-2000:])
        sys.exit("Could not parse loudnorm measurement — does the file have audio?")
    return json.loads(m.group(0))


def cmd_list(_a):
    print("LOUDNESS TARGETS (master.py apply <in> --target <name>):\n")
    for name, (I, TP) in TARGETS.items():
        print(f"  {name:11s} {I:>6.1f} LUFS   TP {TP:>4.1f} dBTP")


def cmd_measure(a):
    if not has_audio(a.src):
        sys.exit(f"No audio stream in {a.src}")
    d = measure(a.src, -14.0, -1.0)
    print(f"MEASURED: {a.src}")
    print(f"  Integrated : {float(d['input_i']):>7.2f} LUFS")
    print(f"  True Peak  : {float(d['input_tp']):>7.2f} dBTP")
    print(f"  LRA        : {float(d['input_lra']):>7.2f} LU")
    print(f"  Threshold  : {float(d['input_thresh']):>7.2f} LUFS")


def cmd_apply(a):
    src = Path(a.src)
    if a.target not in TARGETS:
        sys.exit(f"Unknown target '{a.target}'. Run: master.py list")
    if not has_audio(src):
        sys.exit(f"No audio stream to master in {src}")
    I, TP = TARGETS[a.target]
    print(f"Pass 1/2 — measuring {src.name} ...")
    d = measure(src, I, TP)
    af = (f"loudnorm=I={I}:TP={TP}:LRA={LRA}:"
          f"measured_I={d['input_i']}:measured_TP={d['input_tp']}:"
          f"measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}:"
          f"offset={d['target_offset']}:linear=true:print_format=summary")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    is_audio = src.suffix.lower() in AUDIO_EXT
    print(f"Pass 2/2 — applying ({a.target}: {I} LUFS / TP {TP}) ...")
    if is_audio:
        cmd = ["ffmpeg", "-y", "-i", str(src), "-af", af, "-ar", "48000", str(out)]
    else:
        cmd = ["ffmpeg", "-y", "-i", str(src), "-map", "0:v?", "-map", "0:a",
               "-c:v", "copy", "-af", af, "-c:a", "aac", "-b:a", "256k",
               "-ar", "48000", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-3000:]); sys.exit("master failed")
    # report achieved
    chk = measure(out, I, TP)
    print(f"\nMASTERED: {out}")
    print(f"  {float(d['input_i']):.1f} -> {float(chk['input_i']):.1f} LUFS "
          f"(target {I})   TP {float(chk['input_tp']):.1f} dBTP")


def main():
    ap = argparse.ArgumentParser(description="Loudness mastering (EBU R128)")
    sub = ap.add_subparsers(dest="mode", required=True)
    sub.add_parser("list").set_defaults(func=cmd_list)
    m = sub.add_parser("measure"); m.add_argument("src"); m.set_defaults(func=cmd_measure)
    ap_a = sub.add_parser("apply")
    ap_a.add_argument("src")
    ap_a.add_argument("--target", default="youtube")
    ap_a.add_argument("--out", required=True)
    ap_a.set_defaults(func=cmd_apply)
    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
