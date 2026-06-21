#!/usr/bin/env python3
"""
edl_export.py — Hand the cut to a human finisher (DaVinci Resolve / Premiere / FCP).

The studio assembles autonomously, but a real production often wants a colorist or
editor to take the timeline into a pro NLE. This exports shotlist.json as:
  • a CMX3600 .edl  — universal, cuts-only, with clip names + transition notes
  • an .fcpxml      — rich timeline (durations, spine, asset links) Resolve/FCP import

Both reference the local approved clips by path, so an editor opens the project
with every shot already laid out in order at the right durations.

Usage:
  python3 scripts/edl_export.py projects/<slug>                 # both, into final/
  python3 scripts/edl_export.py projects/<slug> --format fcpxml
"""
import json, subprocess, sys, argparse
from pathlib import Path
from xml.sax.saxutils import escape


def probe_dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def tc(frames, fps):
    fps_i = int(round(fps))
    f = int(round(frames))
    h = f // (fps_i * 3600)
    m = (f // (fps_i * 60)) % 60
    s = (f // fps_i) % 60
    ff = f % fps_i
    return f"{h:02d}:{m:02d}:{s:02d}:{ff:02d}"


def collect(proj: Path):
    sl = json.loads((proj / "shotlist.json").read_text())
    fps = sl.get("fps", 24)
    shots = []
    for s in sl.get("shots", []):
        ap = s.get("approved_take")
        if not ap:
            continue
        clip = proj / "clips" / ap
        real = probe_dur(clip) if clip.exists() else None
        dur = float(s.get("duration_s", 4))
        if real:
            dur = min(dur, real)
        shots.append({
            "id": s["id"], "file": ap, "path": clip.resolve(),
            "dur": dur, "real": real or dur,
            "transition": (s.get("transition_in") or {"type": "cut"}),
        })
    return sl, fps, shots


def write_edl(proj, sl, fps, shots, out):
    lines = [f"TITLE: {sl.get('project', proj.name).upper()}", "FCM: NON-DROP FRAME", ""]
    rec = 0.0
    for i, sh in enumerate(shots, 1):
        df = sh["dur"] * fps
        src_in, src_out = 0, df
        rec_in, rec_out = rec * fps, (rec + sh["dur"]) * fps
        lines.append(
            f"{i:03d}  AX       V     C        "
            f"{tc(src_in, fps)} {tc(src_out, fps)} {tc(rec_in, fps)} {tc(rec_out, fps)}")
        lines.append(f"* FROM CLIP NAME: {sh['file']}")
        tt = sh["transition"]["type"]
        if tt != "cut":
            lines.append(f"* TRANSITION INTENT: {tt} "
                         f"{sh['transition'].get('duration_s', 0.5)}s (add in NLE)")
        lines.append("")
        rec += sh["dur"]
    out.write_text("\n".join(lines))
    print(f"EDL: {out}  ({len(shots)} events, {rec:.1f}s)  [cuts-only, transitions noted]")


def write_fcpxml(proj, sl, fps, shots, out):
    fps_i = int(round(fps))
    ar = sl.get("aspect_ratio", "16:9")
    w, h = (1920, 1080) if ar == "16:9" else (1080, 1920) if ar == "9:16" else (1440, 1440)
    fd = f"1/{fps_i}s"

    def frdur(seconds):
        return f"{int(round(seconds * fps_i))}/{fps_i}s"

    resources = [f'    <format id="r1" name="FFVideoFormat{h}p{fps_i}" '
                 f'frameDuration="{fd}" width="{w}" height="{h}"/>']
    clips_xml = []
    offset = 0.0
    for idx, sh in enumerate(shots, 1):
        aid = f"a{idx}"
        uri = sh["path"].as_uri()
        resources.append(
            f'    <asset id="{aid}" name="{escape(sh["id"])}" src="{escape(uri)}" '
            f'start="0s" duration="{frdur(sh["real"])}" hasVideo="1" hasAudio="1" '
            f'format="r1"/>')
        clips_xml.append(
            f'          <asset-clip ref="{aid}" name="{escape(sh["id"])}" '
            f'offset="{frdur(offset)}" duration="{frdur(sh["dur"])}" start="0s"/>')
        offset += sh["dur"]

    total = frdur(offset)
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.9">
  <resources>
{chr(10).join(resources)}
  </resources>
  <library>
    <event name="{escape(sl.get('project', proj.name))}">
      <project name="{escape(sl.get('project', proj.name))}">
        <sequence format="r1" duration="{total}" tcStart="0s" tcFormat="NDF">
          <spine>
{chr(10).join(clips_xml)}
          </spine>
        </sequence>
      </project>
    </event>
  </library>
</fcpxml>
"""
    out.write_text(xml)
    print(f"FCPXML: {out}  ({len(shots)} clips, {offset:.1f}s)  [import into Resolve/Premiere/FCP]")


def main():
    ap = argparse.ArgumentParser(description="Export EDL / FCPXML for NLE handoff")
    ap.add_argument("project_dir")
    ap.add_argument("--format", default="both", choices=["both", "edl", "fcpxml"])
    ap.add_argument("--out-dir", default=None)
    a = ap.parse_args()

    proj = Path(a.project_dir)
    sl, fps, shots = collect(proj)
    if not shots:
        sys.exit("No approved shots to export. Run the dailies loop / approve takes first.")
    outdir = Path(a.out_dir) if a.out_dir else proj / "final"
    outdir.mkdir(parents=True, exist_ok=True)
    name = sl.get("project", proj.name)

    total_planned = len(sl.get("shots", []))
    if len(shots) < total_planned:
        print(f"NOTE: exporting {len(shots)}/{total_planned} approved shots "
              f"({total_planned - len(shots)} not yet approved, omitted).")
    if a.format in ("both", "edl"):
        write_edl(proj, sl, fps, shots, outdir / f"{name}.edl")
    if a.format in ("both", "fcpxml"):
        write_fcpxml(proj, sl, fps, shots, outdir / f"{name}.fcpxml")


if __name__ == "__main__":
    main()
