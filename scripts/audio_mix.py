#!/usr/bin/env python3
"""
audio_mix.py — Mix music / dialogue / SFX stems onto the film timeline.

Reads the `audio` block of shotlist.json. Each entry has start_at_s and gain_db.
Stems are expected on disk (downloaded from Higgsfield generations):
  audio/music/<id>.*   audio/dialogue/<id>.*   audio/sfx/<id>.*
(any of wav/mp3/m4a/flac — first match wins)

Produces audio/mixdown.wav sized to the picture-cut runtime, with music ducked
-7 dB under dialogue automatically (sidechain-style via volume automation).

Usage: python3 scripts/audio_mix.py projects/<slug> [--runtime 92.5]
       (omit --runtime to read it from the latest file in final/)
"""
import json, subprocess, sys, argparse
from pathlib import Path

EXTS = (".wav", ".mp3", ".m4a", ".flac", ".aac", ".ogg")

def find_stem(proj: Path, kind: str, sid: str):
    d = proj / "audio" / kind
    for e in EXTS:
        p = d / f"{sid}{e}"
        if p.exists(): return p
    return None

def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir"); ap.add_argument("--runtime", type=float, default=None)
    a = ap.parse_args()
    proj = Path(a.project_dir)
    sl = json.loads((proj / "shotlist.json").read_text())
    audio = sl.get("audio", {})

    runtime = a.runtime
    if runtime is None:
        vids = sorted((proj / "final").glob("*.mp4"), key=lambda p: p.stat().st_mtime)
        if not vids: sys.exit("No picture cut in final/ and no --runtime given.")
        runtime = probe(vids[-1])

    inputs, filters, labels = [], [], []
    idx = 0
    dialogue_windows = []
    for kind in ("music", "dialogue", "sfx"):
        for item in audio.get(kind, []):
            stem = find_stem(proj, kind, item["id"])
            if not stem:
                print(f"WARN: missing stem {kind}/{item['id']} — skipping"); continue
            delay_ms = int(item.get("start_at_s", 0) * 1000)
            gain = item.get("gain_db", 0)
            f = (f"[{idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
                 f"volume={gain}dB,adelay={delay_ms}|{delay_ms}")
            if kind == "dialogue":
                dialogue_windows.append((item.get("start_at_s", 0),
                                         item.get("start_at_s", 0) + probe(stem)))
            lab = f"[a{idx}]"
            filters.append(f + lab); labels.append(lab)
            inputs += ["-i", str(stem)]; idx += 1

    if not labels: sys.exit("No stems found — generate audio first (sound-department skill).")

    # Duck music under dialogue via volume automation on the music labels
    # (simple, deterministic ducking: -7dB during any dialogue window +/- 0.3s)
    duck_expr = "+".join(f"between(t,{s-0.3:.2f},{e+0.3:.2f})" for s, e in dialogue_windows) or "0"
    mixed_filters = []
    li = 0
    for kind in ("music", "dialogue", "sfx"):
        for item in audio.get(kind, []):
            if find_stem(proj, kind, item["id"]) is None: continue
            if kind == "music" and dialogue_windows:
                old = labels[li]
                new = f"[ad{li}]"
                mixed_filters.append(f"{old}volume=volume='if(gt({duck_expr},0),0.45,1)':eval=frame{new}")
                labels[li] = new
            li += 1
    filters += mixed_filters

    fg = ";".join(filters) + ";" + "".join(labels) + \
         f"amix=inputs={len(labels)}:duration=longest:normalize=0,atrim=0:{runtime:.3f}," \
         f"alimiter=limit=0.95[out]"
    out = proj / "audio" / "mixdown.wav"
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", fg, "-map", "[out]",
           "-ar", "48000", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0: sys.exit(r.stderr[-3000:])
    print(f"Mixdown: {out}  ({runtime:.1f}s, {len(labels)} stems, "
          f"{len(dialogue_windows)} dialogue ducking windows)")

if __name__ == "__main__":
    main()
