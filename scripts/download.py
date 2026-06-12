#!/usr/bin/env python3
"""
download.py — Pull Higgsfield generation results to local disk.

The agent gets result URLs from Higgsfield MCP tool responses (generate_*,
show_generations, job_display). Immediately persist them — job URLs are not a
durable copy and the cut must build from local files.

Usage:
  python3 scripts/download.py <url> <dest_path>
  python3 scripts/download.py --batch manifest.json
      manifest.json: [{"url": "...", "dest": "projects/x/clips/s01_t01.mp4"}, ...]

Verifies the file is non-trivial and (for video/audio) ffprobe-readable.
"""
import sys, json, subprocess, urllib.request, argparse
from pathlib import Path

def fetch(url: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "hollywood-studio/1.0"})
    with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    size = dest.stat().st_size
    if size < 10_000:
        sys.exit(f"Suspiciously small download ({size} B): {dest} — check the URL/job status.")
    if dest.suffix.lower() in (".mp4", ".mov", ".webm", ".wav", ".mp3", ".m4a", ".glb"):
        if dest.suffix.lower() != ".glb":
            p = subprocess.run(["ffprobe", "-v", "error", str(dest)], capture_output=True)
            if p.returncode != 0:
                sys.exit(f"Downloaded but unreadable by ffprobe: {dest}")
    print(f"OK {dest} ({size/1e6:.2f} MB)")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url_or_flag"); ap.add_argument("dest", nargs="?")
    a = ap.parse_args()
    if a.url_or_flag == "--batch":
        for item in json.loads(Path(a.dest).read_text()):
            fetch(item["url"], Path(item["dest"]))
    else:
        if not a.dest: sys.exit("usage: download.py <url> <dest>")
        fetch(a.url_or_flag, Path(a.dest))

if __name__ == "__main__":
    main()
