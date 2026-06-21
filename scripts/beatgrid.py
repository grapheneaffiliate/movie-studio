#!/usr/bin/env python3
"""
beatgrid.py — Detect beats/onsets in a track and propose music-video cut points.

For music videos the edit is cut to the track. This decodes the audio (via
ffmpeg) to mono PCM, builds an energy-flux onset envelope, picks onsets, estimates
tempo, and emits a beat grid + a suggested shot breakdown (cut on beats, merged so
no shot is shorter than --min-shot). Feed the cut list back to shot-design as
shotlist durations so picture lands on the music.

Pure stdlib (wave/array) + ffmpeg for decode — no numpy.

Usage:
  python3 scripts/beatgrid.py track.mp3
  python3 scripts/beatgrid.py projects/x/audio/music/m01.m4a --every 2 --min-shot 1.5
  python3 scripts/beatgrid.py track.wav --json cuts.json
"""
import subprocess, sys, argparse, wave, array, tempfile, os, json, math
from pathlib import Path

SR = 22050


def decode_mono(path):
    tf = tempfile.NamedTemporaryFile(suffix=".wav", delete=False); tf.close()
    r = subprocess.run(["ffmpeg", "-y", "-i", str(path), "-ac", "1", "-ar", str(SR),
                        "-f", "wav", tf.name], capture_output=True, text=True)
    if r.returncode != 0:
        os.unlink(tf.name); sys.stderr.write(r.stderr[-2000:]); sys.exit("decode failed")
    w = wave.open(tf.name, "rb")
    n = w.getnframes()
    raw = w.readframes(n)
    w.close(); os.unlink(tf.name)
    sw = 2
    samples = array.array("h")
    samples.frombytes(raw[: (len(raw) // sw) * sw])
    return samples


def onset_envelope(samples, hop=512, win=1024):
    """Half-wave-rectified energy flux per hop -> onset strength."""
    n = len(samples)
    env, prev = [], 0.0
    for i in range(0, n - win, hop):
        s = 0
        for j in range(i, i + win, 4):  # decimate inner loop for speed
            v = samples[j]
            s += v * v
        e = math.sqrt(s / (win / 4)) if win else 0.0
        flux = e - prev
        env.append(flux if flux > 0 else 0.0)
        prev = e
    return env, hop / SR


def pick_onsets(env, dt, min_gap=0.12):
    if not env:
        return []
    # adaptive threshold: local mean + k*local std over a moving window
    W = max(int(0.5 / dt), 8)
    peaks = []
    last_t = -1e9
    k = 1.4
    for i in range(1, len(env) - 1):
        lo, hi = max(0, i - W), min(len(env), i + W)
        window = env[lo:hi]
        mean = sum(window) / len(window)
        var = sum((x - mean) ** 2 for x in window) / len(window)
        thr = mean + k * math.sqrt(var)
        if env[i] > thr and env[i] >= env[i - 1] and env[i] >= env[i + 1]:
            t = i * dt
            if t - last_t >= min_gap:
                peaks.append(t); last_t = t
    return peaks


def estimate_bpm(onsets):
    if len(onsets) < 4:
        return None
    iois = [onsets[i + 1] - onsets[i] for i in range(len(onsets) - 1)]
    iois = [x for x in iois if 0.2 < x < 2.0]  # 30-300 bpm window
    if not iois:
        return None
    iois.sort()
    med = iois[len(iois) // 2]
    bpm = 60.0 / med
    while bpm < 70:
        bpm *= 2
    while bpm > 180:
        bpm /= 2
    return round(bpm, 1)


def main():
    ap = argparse.ArgumentParser(description="Beat detection -> music-video cut points")
    ap.add_argument("track")
    ap.add_argument("--every", type=int, default=1, help="cut every N detected beats")
    ap.add_argument("--min-shot", type=float, default=1.0, help="merge beats so shots >= this")
    ap.add_argument("--json", default=None, help="write cut list to JSON")
    a = ap.parse_args()

    samples = decode_mono(a.track)
    dur = len(samples) / SR
    env, dt = onset_envelope(samples)
    onsets = pick_onsets(env, dt)
    bpm = estimate_bpm(onsets)

    # candidate cut points: every Nth onset
    cuts = onsets[:: max(a.every, 1)]
    # merge so each segment >= min-shot
    merged = [0.0]
    for c in cuts:
        if c - merged[-1] >= a.min_shot:
            merged.append(round(c, 2))
    if dur - merged[-1] < a.min_shot and len(merged) > 1:
        merged.pop()
    merged.append(round(dur, 2))
    segs = [round(merged[i + 1] - merged[i], 2) for i in range(len(merged) - 1)]

    print(f"== Beat grid: {Path(a.track).name} ==")
    print(f"  duration {dur:.1f}s   onsets detected {len(onsets)}   "
          f"est. tempo {bpm if bpm else '?'} BPM")
    if bpm:
        beat = 60.0 / bpm
        print(f"  beat ≈ {beat:.3f}s   bar(4/4) ≈ {beat*4:.2f}s")
    print(f"\n  Suggested {len(segs)} shots (cut every {a.every} beat(s), min {a.min_shot}s):")
    for i, (start, length) in enumerate(zip(merged[:-1], segs), 1):
        print(f"    s{i:02d}  start {start:6.2f}s  duration {length:5.2f}s")

    if a.json:
        Path(a.json).write_text(json.dumps({
            "track": str(a.track), "duration_s": round(dur, 2), "bpm": bpm,
            "onsets": [round(o, 3) for o in onsets],
            "cuts": merged, "shot_durations": segs}, indent=2))
        print(f"\n  cut list -> {a.json}")
    print("\n  Feed shot_durations into shot-design so picture lands on the beat.")


if __name__ == "__main__":
    main()
