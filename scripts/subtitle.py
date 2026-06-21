#!/usr/bin/env python3
"""
subtitle.py — Captions & subtitles from the shotlist dialogue block.

The dialogue timing is already exact (sound-department set start_at_s and the
stems exist on disk), so subtitles are deterministic: read the audio block, read
each dialogue stem's real duration, emit a frame-accurate SRT / styled ASS, and
optionally burn it into a cut. Accessibility + reach in one free step.

Modes:
  srt     Write an .srt from the shotlist dialogue cues.
  ass     Write a styled .ass (cinema | caption | karaoke looks).
  burn    Burn an existing .srt/.ass into a video (libass).
  lyrics  Build subtitles from a timed lyric file (music videos): lines of
          "MM:SS  text" → SRT, each line ending when the next begins.

Usage:
  python3 scripts/subtitle.py srt  projects/<slug>            # -> <slug>.srt
  python3 scripts/subtitle.py ass  projects/<slug> --style cinema
  python3 scripts/subtitle.py burn projects/<slug>/final/cut.mp4 \
      --sub projects/<slug>/<slug>.srt --style cinema --out cut_sub.mp4
  python3 scripts/subtitle.py lyrics lyrics.txt --out song.srt
"""
import json, subprocess, sys, argparse, re
from pathlib import Path

EXTS = (".wav", ".mp3", ".m4a", ".flac", ".aac", ".ogg")

STYLES = {
    # name: (Fontname, Fontsize, PrimaryColour, OutlineColour, Outline, Shadow, Bold, marginV)
    "cinema":  ("DejaVu Serif", 22, "&H00FFFFFF", "&H64000000", 1, 1, 0, 60),
    "caption": ("DejaVu Sans", 26, "&H00FFFFFF", "&H00000000", 3, 0, 1, 50),
    "karaoke": ("DejaVu Sans", 30, "&H0000E0FF", "&H00202020", 3, 1, 1, 70),
}


def probe_dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def find_stem(proj: Path, sid: str):
    d = proj / "audio" / "dialogue"
    for e in EXTS:
        p = d / f"{sid}{e}"
        if p.exists():
            return p
    return None


def ts(seconds, sep=","):
    if seconds < 0:
        seconds = 0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms == 1000:
        s += 1; ms = 0
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def cues_from_shotlist(proj: Path):
    sl = json.loads((proj / "shotlist.json").read_text())
    out = []
    for item in sl.get("audio", {}).get("dialogue", []):
        start = float(item.get("start_at_s", 0))
        stem = find_stem(proj, item["id"])
        dur = probe_dur(stem) if stem else None
        if dur is None:
            # estimate: ~2.6 words/sec, floor 1.2s
            words = max(len(item.get("text", "").split()), 1)
            dur = max(words / 2.6, 1.2)
        text = item.get("text", "").strip()
        out.append((start, start + dur, text))
    out.sort(key=lambda c: c[0])
    # prevent overlaps
    for i in range(len(out) - 1):
        if out[i][1] > out[i + 1][0]:
            out[i] = (out[i][0], out[i + 1][0] - 0.05, out[i][2])
    return out


def write_srt(cues, dest: Path):
    lines = []
    for i, (s, e, t) in enumerate(cues, 1):
        lines.append(f"{i}\n{ts(s)} --> {ts(e)}\n{t}\n")
    dest.write_text("\n".join(lines))
    print(f"SRT: {dest}  ({len(cues)} cues)")


def write_ass(cues, dest: Path, style="cinema", play_w=1920, play_h=1080):
    fn, fs, pc, oc, outl, shad, bold, mv = STYLES.get(style, STYLES["cinema"])
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {play_w}
PlayResY: {play_h}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV
Style: Default,{fn},{fs},{pc},{oc},&H64000000,{bold},0,1,{outl},{shad},2,80,80,{mv}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, Effect, Text
"""
    rows = []
    for s, e, t in cues:
        t = t.replace("\n", "\\N")
        rows.append(f"Dialogue: 0,{ts(s, '.')[:-1]},{ts(e, '.')[:-1]},Default,,0,0,0,,{t}")
    dest.write_text(header + "\n".join(rows) + "\n")
    print(f"ASS: {dest}  ({len(cues)} cues, style={style})")


def sub_path_escape(p: str):
    # escape for the subtitles= filter argument
    return p.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def cmd_srt(a):
    proj = Path(a.target)
    cues = cues_from_shotlist(proj)
    if not cues:
        sys.exit("No dialogue cues in shotlist.json audio block.")
    out = Path(a.out) if a.out else proj / f"{proj.name}.srt"
    write_srt(cues, out)


def cmd_ass(a):
    proj = Path(a.target)
    cues = cues_from_shotlist(proj)
    if not cues:
        sys.exit("No dialogue cues in shotlist.json audio block.")
    sl = json.loads((proj / "shotlist.json").read_text())
    ar = sl.get("aspect_ratio", "16:9")
    pw, ph = (1920, 1080) if ar == "16:9" else (1080, 1920) if ar == "9:16" else (1440, 1440)
    out = Path(a.out) if a.out else proj / f"{proj.name}.ass"
    write_ass(cues, out, a.style, pw, ph)


def cmd_burn(a):
    src = Path(a.target)
    sub = Path(a.sub)
    if not sub.exists():
        sys.exit(f"Subtitle file not found: {sub}")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    filt = f"subtitles=filename='{sub_path_escape(str(sub))}'"
    if sub.suffix.lower() == ".srt" and a.style in STYLES:
        fn, fs, pc, oc, outl, shad, bold, mv = STYLES[a.style]
        force = (f"FontName={fn},FontSize={fs},PrimaryColour={pc},"
                 f"OutlineColour={oc},Outline={outl},Shadow={shad},Bold={bold},"
                 f"MarginV={mv},Alignment=2")
        filt += f":force_style='{force}'"
    r = subprocess.run(["ffmpeg", "-y", "-i", str(src), "-vf", filt,
                        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
                        "-c:a", "copy", str(out)], capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-3000:])
        sys.exit("burn failed")
    print(f"BURNED: {out}")


def cmd_lyrics(a):
    src = Path(a.target)
    raw = src.read_text().splitlines()
    parsed = []
    pat = re.compile(r"^\s*(?:\[?(\d+):(\d{1,2})(?:\.(\d+))?\]?)\s+(.*)$")
    for ln in raw:
        if not ln.strip():
            continue
        m = pat.match(ln)
        if not m:
            continue
        mm, ss, frac, text = m.groups()
        t = int(mm) * 60 + int(ss) + (float("0." + frac) if frac else 0)
        parsed.append((t, text.strip()))
    if not parsed:
        sys.exit("No timed lines found. Format each line as 'MM:SS  lyric text'.")
    cues = []
    for i, (t, text) in enumerate(parsed):
        end = parsed[i + 1][0] - 0.05 if i + 1 < len(parsed) else t + 4
        cues.append((t, end, text))
    out = Path(a.out) if a.out else src.with_suffix(".srt")
    write_srt(cues, out)


def main():
    ap = argparse.ArgumentParser(description="Subtitles & captions from the dialogue block")
    sub = ap.add_subparsers(dest="mode", required=True)
    for name in ("srt", "ass"):
        p = sub.add_parser(name)
        p.add_argument("target", help="project dir")
        p.add_argument("--out", default=None)
        if name == "ass":
            p.add_argument("--style", default="cinema", choices=list(STYLES))
        p.set_defaults(func=cmd_srt if name == "srt" else cmd_ass)
    b = sub.add_parser("burn")
    b.add_argument("target", help="video file")
    b.add_argument("--sub", required=True)
    b.add_argument("--style", default="cinema", choices=list(STYLES) + ["none"])
    b.add_argument("--out", required=True)
    b.set_defaults(func=cmd_burn)
    ly = sub.add_parser("lyrics")
    ly.add_argument("target", help="timed lyric text file")
    ly.add_argument("--out", default=None)
    ly.set_defaults(func=cmd_lyrics)
    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
