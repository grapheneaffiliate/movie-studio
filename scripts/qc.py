#!/usr/bin/env python3
"""
qc.py — Automated technical QC. The deliverable's pre-flight inspection.

Definition of Done (CLAUDE.md §6) demands an ffprobe-valid final with both
streams and runtime within ±15% of target. This automates that check and adds
the defect scans that AI footage specifically needs: black frames, frozen video
(a dead/limp generated clip that slipped past dailies), audio clipping, missing
loudness conformance, and dead silence.

Exit code 0 = PASS (no FAILs). Non-zero = at least one FAIL — do not deliver.

Usage:
  python3 scripts/qc.py projects/<slug>                 # QC newest file in final/
  python3 scripts/qc.py projects/<slug>/final/cut.mp4 [--target 90] [--aspect 16:9]
"""
import json, subprocess, sys, argparse, re
from pathlib import Path

PASS, WARN, FAIL = "PASS", "WARN", "FAIL"


def ff(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe_json(path):
    r = ff(["ffprobe", "-v", "error", "-show_format", "-show_streams",
            "-of", "json", str(path)])
    if r.returncode != 0:
        return None
    return json.loads(r.stdout)


def loudness(path):
    r = ff(["ffmpeg", "-hide_banner", "-i", str(path),
            "-af", "loudnorm=I=-14:TP=-1:LRA=11:print_format=json", "-f", "null", "-"])
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.DOTALL)
    return json.loads(m.group(0)) if m else None


def defect_scan(path):
    r = ff(["ffmpeg", "-hide_banner", "-i", str(path),
            "-vf", "blackdetect=d=0.4:pix_th=0.10,freezedetect=n=-55dB:d=0.7",
            "-af", "silencedetect=n=-50dB:d=1.5", "-f", "null", "-"])
    s = r.stderr
    blacks = [(float(a), float(b)) for a, b in
              re.findall(r"black_start:([\d.]+).*?black_end:([\d.]+)", s)]
    freezes = re.findall(r"freeze_start: ([\d.]+)", s)
    silences = [(float(a), float(b)) for a, b in
                re.findall(r"silence_start: ([\d.-]+).*?silence_end: ([\d.]+)", s, re.DOTALL)]
    return blacks, [float(f) for f in freezes], silences


def main():
    ap = argparse.ArgumentParser(description="Automated technical QC")
    ap.add_argument("target", help="project dir or video file")
    ap.add_argument("--target", dest="runtime", type=float, default=None,
                    help="expected runtime seconds (else read project.json)")
    ap.add_argument("--aspect", default=None)
    a = ap.parse_args()

    t = Path(a.target)
    target_runtime, aspect = a.runtime, a.aspect
    if t.is_dir():
        try:
            m = json.loads((t / "project.json").read_text())
            target_runtime = target_runtime or m.get("target_runtime_s")
        except Exception:
            pass
        finals = sorted((t / "final").glob("*.mp4"), key=lambda p: p.stat().st_mtime)
        finals = [f for f in finals if not f.stem.endswith("draft")]
        if not finals:
            sys.exit("No final/*.mp4 to QC.")
        vid = finals[-1]
    else:
        vid = t

    print(f"== QC: {vid} ==")
    results = []  # (level, check, detail)

    info = probe_json(vid)
    if not info:
        print(f"  {FAIL}  container — ffprobe cannot read the file")
        sys.exit(1)

    vstreams = [s for s in info["streams"] if s["codec_type"] == "video"]
    astreams = [s for s in info["streams"] if s["codec_type"] == "audio"]
    results.append((PASS if vstreams else FAIL, "video stream",
                    f"{len(vstreams)} present"))
    results.append((PASS if astreams else FAIL, "audio stream",
                    f"{len(astreams)} present" if astreams else "MISSING — final needs sound"))

    dur = float(info["format"].get("duration", 0))
    if vstreams:
        w, h = vstreams[0]["width"], vstreams[0]["height"]
        fr = vstreams[0].get("avg_frame_rate", "0/1")
        try:
            num, den = fr.split("/"); fps = float(num) / float(den) if float(den) else 0
        except Exception:
            fps = 0
        results.append((PASS, "resolution", f"{w}x{h} @ {fps:.2f}fps  dur {dur:.1f}s"))
        if aspect:
            exp = {"16:9": 16/9, "9:16": 9/16, "1:1": 1.0, "4:5": 0.8, "2.39:1": 2.39}.get(aspect)
            if exp and abs((w/h) - exp) > 0.05:
                results.append((WARN, "aspect", f"{w}x{h} != {aspect}"))

    if target_runtime:
        lo, hi = target_runtime * 0.85, target_runtime * 1.15
        lvl = PASS if lo <= dur <= hi else FAIL
        results.append((lvl, "runtime ±15%",
                        f"{dur:.1f}s vs target {target_runtime:.0f}s [{lo:.0f}-{hi:.0f}]"))

    # defect scans
    blacks, freezes, silences = defect_scan(vid)
    interior_black = [(s, e) for s, e in blacks if s > 0.6 and (dur - e) > 0.6 and (e - s) > 0.8]
    if interior_black:
        results.append((WARN, "black frames",
                        f"{len(interior_black)} interior black gap(s): "
                        + ", ".join(f"{s:.1f}-{e:.1f}s" for s, e in interior_black[:4])))
    else:
        results.append((PASS, "black frames", "none interior (head/tail fades ok)"))

    if freezes:
        results.append((WARN, "frozen video",
                        f"{len(freezes)} freeze(s) >=0.7s at "
                        + ", ".join(f"{x:.1f}s" for x in freezes[:5])
                        + " — likely a dead generated clip"))
    else:
        results.append((PASS, "frozen video", "no freezes"))

    if astreams:
        total_sil = sum(min(e, dur) - s for s, e in silences if s >= 0)
        if dur and total_sil > 0.6 * dur:
            results.append((WARN, "silence", f"{total_sil:.1f}s silent of {dur:.1f}s — check the mix"))
        else:
            results.append((PASS, "silence", f"{total_sil:.1f}s silent (ok)"))
        ld = loudness(vid)
        if ld:
            I, tp = float(ld["input_i"]), float(ld["input_tp"])
            if tp > 0.0:
                results.append((FAIL, "true peak", f"{tp:.1f} dBTP — CLIPPING"))
            elif tp > -0.5:
                results.append((WARN, "true peak", f"{tp:.1f} dBTP — clipping risk"))
            else:
                results.append((PASS, "true peak", f"{tp:.1f} dBTP"))
            if I < -23 or I > -9:
                results.append((WARN, "loudness", f"{I:.1f} LUFS — run master.py to conform"))
            else:
                results.append((PASS, "loudness", f"{I:.1f} LUFS"))

    print()
    icon = {PASS: "✓", WARN: "!", FAIL: "✗"}
    for lvl, check, detail in results:
        print(f"  {icon[lvl]} {lvl:4s} {check:16s} {detail}")

    fails = sum(1 for r in results if r[0] == FAIL)
    warns = sum(1 for r in results if r[0] == WARN)
    print(f"\n  VERDICT: {'FAIL' if fails else 'PASS'}  ({fails} fail, {warns} warn)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
