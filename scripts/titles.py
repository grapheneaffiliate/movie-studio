#!/usr/bin/env python3
"""
titles.py — Motion graphics: title cards, lower-thirds, credit rolls, watermarks.

The Art Department's edit-bay tool. All ffmpeg, all free — never spend render-farm
credits on text the way you'd spend them on footage. Produces either standalone
clips (drop them into shotlist.json as a shot with a ready clip) or overlays an
existing cut.

Modes:
  card       Full-screen title card (open/close cards, act breaks, chapter cards).
  lower      Lower-third name/role over an existing clip at a timestamp.
  credits    Scrolling end-credit roll (standalone clip).
  watermark  Persistent logo or text bug overlaid on a clip (channel branding).

Usage:
  python3 scripts/titles.py card "DERELICT" --sub "a salvage story" \
      --dur 3 --aspect 16:9 --out projects/x/final/card_open.mp4
  python3 scripts/titles.py lower projects/x/final/cut.mp4 \
      --name "MARA VALE" --role "Salvage Pilot" --at 4 --dur 4 --out cut_lt.mp4
  python3 scripts/titles.py credits --file credits.txt --dur 24 \
      --aspect 16:9 --out projects/x/final/credits.mp4
  python3 scripts/titles.py watermark projects/x/final/cut.mp4 \
      --logo brand.png --pos br --opacity 0.7 --out cut_branded.mp4
  python3 scripts/titles.py watermark in.mp4 --text "© 2026 A&T" --pos br --out out.mp4

Fonts: pass --font /path/to.ttf, or it auto-picks a cinematic serif/sans on PATH.
Colors accept #rrggbb or ffmpeg color names. Text fades in/out automatically.
"""
import subprocess, sys, argparse, tempfile, os
from pathlib import Path

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    "C:/Windows/Fonts/timesbd.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]

DIMS = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1440, 1440),
        "4:5": (1080, 1350), "2.39:1": (1920, 804)}


def find_font(override=None):
    if override:
        if Path(override).exists():
            return override
        sys.exit(f"--font not found: {override}")
    for f in FONT_CANDIDATES:
        if Path(f).exists():
            return f
    # last resort: ask fontconfig
    try:
        r = subprocess.run(["fc-match", "-f", "%{file}", "serif:bold"],
                           capture_output=True, text=True)
        if r.returncode == 0 and Path(r.stdout.strip()).exists():
            return r.stdout.strip()
    except FileNotFoundError:
        pass
    sys.exit("No usable font found — pass --font /path/to/font.ttf")


def run(cmd):
    print("+", " ".join(cmd[:6]), "...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-3000:])
        sys.exit(f"FAILED: {cmd[0]}")


def esc(text):
    """Escape text for inline drawtext."""
    return (text.replace("\\", "\\\\").replace(":", "\\:")
                .replace("'", "’").replace("%", "\\%"))


def dims(aspect):
    if aspect in DIMS:
        return DIMS[aspect]
    if "x" in aspect:
        w, h = aspect.split("x")
        return int(w), int(h)
    sys.exit(f"Unknown aspect {aspect}; use 16:9 9:16 1:1 4:5 2.39:1 or WxH")


def probe_dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip())


def cmd_card(a):
    font = find_font(a.font)
    w, h = dims(a.aspect)
    fs_title = a.size or int(h * 0.10)
    fs_sub = int(fs_title * 0.42)
    fin = min(a.fade, a.dur / 2)
    filters = [
        f"drawtext=fontfile='{font}':text='{esc(a.title)}':fontcolor={a.color}:"
        f"fontsize={fs_title}:x=(w-text_w)/2:y=(h-text_h)/2-{int(fs_sub*0.9) if a.sub else 0}:"
        f"alpha='if(lt(t,{fin}),t/{fin},if(lt(t,{a.dur-fin}),1,({a.dur}-t)/{fin}))'"
    ]
    if a.sub:
        filters.append(
            f"drawtext=fontfile='{font}':text='{esc(a.sub)}':fontcolor={a.color}:"
            f"fontsize={fs_sub}:x=(w-text_w)/2:y=(h+text_h)/2+{int(fs_title*0.3)}:"
            f"alpha='if(lt(t,{fin}),t/{fin},if(lt(t,{a.dur-fin}),1,({a.dur}-t)/{fin}))'")
    vf = ",".join(filters)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-f", "lavfi",
         "-i", f"color=c={a.bg}:s={w}x{h}:d={a.dur}:r={a.fps}",
         "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17",
         "-t", f"{a.dur}", str(a.out)])
    print(f"\nCARD: {a.out}  ({w}x{h}, {a.dur}s)")


def cmd_lower(a):
    font = find_font(a.font)
    src = Path(a.src)
    h_guess = 1080
    fs_name = a.size or int(h_guess * 0.045)
    fs_role = int(fs_name * 0.6)
    st, en = a.at, a.at + a.dur
    fin = 0.4
    margin_x = "60"
    base_y = "h-h/4"
    alpha = (f"if(lt(t,{st}),0,if(lt(t,{st+fin}),(t-{st})/{fin},"
             f"if(lt(t,{en-fin}),1,if(lt(t,{en}),({en}-t)/{fin},0))))")
    bar = (f"drawbox=x={margin_x}-20:y={base_y}-10:w=8:h={fs_name+fs_role+30}:"
           f"color={a.accent}@1:t=fill:enable='between(t,{st},{en})'")
    name = (f"drawtext=fontfile='{font}':text='{esc(a.name)}':fontcolor=white:"
            f"fontsize={fs_name}:x={margin_x}:y={base_y}:alpha='{alpha}':"
            f"box=1:boxcolor=black@0.35:boxborderw=12")
    parts = [bar, name]
    if a.role:
        parts.append(
            f"drawtext=fontfile='{font}':text='{esc(a.role)}':fontcolor=white@0.85:"
            f"fontsize={fs_role}:x={margin_x}:y={base_y}+{fs_name+8}:alpha='{alpha}':"
            f"box=1:boxcolor=black@0.35:boxborderw=10")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-i", str(src), "-vf", ",".join(parts),
         "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "copy", str(a.out)])
    print(f"\nLOWER-THIRD: {a.out}  ({a.name} @ {a.at}s for {a.dur}s)")


def cmd_credits(a):
    font = find_font(a.font)
    w, h = dims(a.aspect)
    if a.file:
        text = Path(a.file).read_text()
    elif a.text:
        text = a.text.replace("\\n", "\n")
    else:
        sys.exit("credits needs --file or --text")
    tf = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
    tf.write(text)
    tf.close()
    fs = a.size or int(h * 0.045)
    # scroll from below the frame to above it over the full duration
    y_expr = f"h-(t/{a.dur})*(h+text_h)"
    vf = (f"drawtext=fontfile='{font}':textfile='{tf.name}':fontcolor={a.color}:"
          f"fontsize={fs}:x=(w-text_w)/2:y={y_expr}:line_spacing={int(fs*0.4)}")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    try:
        run(["ffmpeg", "-y", "-f", "lavfi",
             "-i", f"color=c={a.bg}:s={w}x{h}:d={a.dur}:r={a.fps}",
             "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17",
             "-t", f"{a.dur}", str(a.out)])
    finally:
        os.unlink(tf.name)
    print(f"\nCREDITS: {a.out}  ({w}x{h}, {a.dur}s scroll)")


def cmd_watermark(a):
    src = Path(a.src)
    pos = {"br": ("W-w-#m", "H-h-#m"), "bl": ("#m", "H-h-#m"),
           "tr": ("W-w-#m", "#m"), "tl": ("#m", "#m"),
           "bc": ("(W-w)/2", "H-h-#m"), "tc": ("(W-w)/2", "#m")}[a.pos]
    m = str(a.margin)
    x, y = pos[0].replace("#m", m), pos[1].replace("#m", m)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    if a.logo:
        run(["ffmpeg", "-y", "-i", str(src), "-i", str(a.logo),
             "-filter_complex",
             f"[1:v]format=rgba,colorchannelmixer=aa={a.opacity}[wm];"
             f"[0:v][wm]overlay={x}:{y}[v]",
             "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-crf", "18",
             "-pix_fmt", "yuv420p", "-c:a", "copy", str(a.out)])
    else:
        if not a.text:
            sys.exit("watermark needs --logo or --text")
        font = find_font(a.font)
        # convert overlay-style x/y to drawtext coords
        dx = x.replace("W", "w").replace("w-w", "w-text_w")
        dy = y.replace("H", "h").replace("h-h", "h-text_h")
        # safer: recompute for drawtext
        dxy = {"br": ("w-text_w-%s", "h-text_h-%s"), "bl": ("%s", "h-text_h-%s"),
               "tr": ("w-text_w-%s", "%s"), "tl": ("%s", "%s"),
               "bc": ("(w-text_w)/2", "h-text_h-%s"), "tc": ("(w-text_w)/2", "%s")}[a.pos]
        dx = dxy[0] % m if "%s" in dxy[0] else dxy[0]
        dy = dxy[1] % m if "%s" in dxy[1] else dxy[1]
        run(["ffmpeg", "-y", "-i", str(src),
             "-vf", f"drawtext=fontfile='{font}':text='{esc(a.text)}':"
                    f"fontcolor=white@{a.opacity}:fontsize=36:x={dx}:y={dy}:"
                    f"box=1:boxcolor=black@{a.opacity*0.4}:boxborderw=10",
             "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
             "-c:a", "copy", str(a.out)])
    print(f"\nWATERMARK: {a.out}  (pos={a.pos})")


def main():
    ap = argparse.ArgumentParser(description="Motion graphics: cards, lower-thirds, credits, watermarks")
    sub = ap.add_subparsers(dest="mode", required=True)

    c = sub.add_parser("card")
    c.add_argument("title")
    c.add_argument("--sub", default="")
    c.add_argument("--dur", type=float, default=3.0)
    c.add_argument("--aspect", default="16:9")
    c.add_argument("--bg", default="black")
    c.add_argument("--color", default="white")
    c.add_argument("--size", type=int, default=None)
    c.add_argument("--fade", type=float, default=0.6)
    c.add_argument("--fps", type=int, default=24)
    c.add_argument("--font", default=None)
    c.add_argument("--out", required=True)
    c.set_defaults(func=cmd_card)

    l = sub.add_parser("lower")
    l.add_argument("src")
    l.add_argument("--name", required=True)
    l.add_argument("--role", default="")
    l.add_argument("--at", type=float, default=2.0)
    l.add_argument("--dur", type=float, default=4.0)
    l.add_argument("--accent", default="#c8a04a")
    l.add_argument("--size", type=int, default=None)
    l.add_argument("--font", default=None)
    l.add_argument("--out", required=True)
    l.set_defaults(func=cmd_lower)

    cr = sub.add_parser("credits")
    cr.add_argument("--file", default=None)
    cr.add_argument("--text", default=None)
    cr.add_argument("--dur", type=float, default=20.0)
    cr.add_argument("--aspect", default="16:9")
    cr.add_argument("--bg", default="black")
    cr.add_argument("--color", default="white")
    cr.add_argument("--size", type=int, default=None)
    cr.add_argument("--fps", type=int, default=24)
    cr.add_argument("--font", default=None)
    cr.add_argument("--out", required=True)
    cr.set_defaults(func=cmd_credits)

    w = sub.add_parser("watermark")
    w.add_argument("src")
    w.add_argument("--logo", default=None)
    w.add_argument("--text", default=None)
    w.add_argument("--pos", default="br", choices=["br", "bl", "tr", "tl", "bc", "tc"])
    w.add_argument("--opacity", type=float, default=0.75)
    w.add_argument("--margin", type=int, default=48)
    w.add_argument("--font", default=None)
    w.add_argument("--out", required=True)
    w.set_defaults(func=cmd_watermark)

    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
