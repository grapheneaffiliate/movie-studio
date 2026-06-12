#!/usr/bin/env python3
"""
status.py — Project dashboard and disk⇄manifest reconciliation.

Usage:
  python3 scripts/status.py                  # list all projects, one line each
  python3 scripts/status.py projects/<slug>  # full dashboard + reconciliation

Reconciliation flags:
  ORPHAN  clip on disk not referenced by any shot's takes[]   (harmless)
  GHOST   approved_take referenced but missing on disk        (must re-download)
  STEM-MISSING  audio id in shotlist with no file on disk     (regenerate/download)

The agent runs this on every resume and fixes GHOST/STEM-MISSING before continuing.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def one_line(pdir: Path):
    try:
        m = json.loads((pdir / "project.json").read_text())
    except Exception:
        return f"{pdir.name:30s} <corrupt or missing project.json>"
    sl_path = pdir / "shotlist.json"
    shots = approved = 0
    if sl_path.exists():
        sl = json.loads(sl_path.read_text())
        shots = len(sl.get("shots", []))
        approved = sum(1 for s in sl.get("shots", []) if s.get("approved_take"))
    return (f"{m.get('slug', pdir.name):30s} stage={m.get('stage','?'):14s} "
            f"shots={approved}/{shots} spent={m.get('budget',{}).get('spent_credits',0)}cr")

def dashboard(pdir: Path):
    m = json.loads((pdir / "project.json").read_text())
    sl = json.loads((pdir / "shotlist.json").read_text())
    print(f"== {m['slug']} — {m.get('title','')} ==")
    print(f"stage: {m['stage']}   deliverable: {m.get('deliverable')}   "
          f"target: {m.get('target_runtime_s')}s   "
          f"credits: {m['budget'].get('spent_credits',0)} spent / "
          f"{m['budget'].get('estimate_credits',0)} est")
    print(f"prompt: {m.get('user_prompt','')[:100]}")

    print("\nSHOTS")
    referenced = set()
    issues = []
    for s in sl.get("shots", []):
        ap = s.get("approved_take")
        for t in s.get("takes", []): referenced.add(t)
        mark = "✓" if ap else ("✗" if s.get("status") == "blocked" else "·")
        print(f"  {mark} {s['id']:5s} {s.get('status','pending'):10s} "
              f"takes={len(s.get('takes',[]))} dur={s.get('duration_s','?')}s"
              + (f"  -> {ap}" if ap else ""))
        if ap and not (pdir / "clips" / ap).exists():
            issues.append(f"GHOST: {s['id']} approved_take {ap} missing on disk")

    on_disk = {p.name for p in (pdir / "clips").glob("*.mp4")}
    for orphan in sorted(on_disk - referenced):
        issues.append(f"ORPHAN: clips/{orphan} not in any takes[] (harmless)")

    exts = (".wav", ".mp3", ".m4a", ".flac", ".aac", ".ogg")
    for kind in ("music", "dialogue", "sfx"):
        for item in sl.get("audio", {}).get(kind, []):
            if not any((pdir / "audio" / kind / f"{item['id']}{e}").exists() for e in exts):
                issues.append(f"STEM-MISSING: audio/{kind}/{item['id']}")

    finals = sorted((pdir / "final").glob("*.mp4"))
    print(f"\nFINAL: {', '.join(f.name for f in finals) or '(none)'}")

    print("\nRECONCILIATION")
    if issues:
        for i in issues: print("  !", i)
    else:
        print("  clean — disk matches manifest")

    nxt = next((s["id"] for s in sl.get("shots", []) if not s.get("approved_take")
                and s.get("status") != "blocked"), None)
    print(f"\nRESUME POINT: stage={m['stage']}"
          + (f", first unapproved shot={nxt}" if nxt else ", all shots approved"))

def main():
    if len(sys.argv) == 1:
        pp = ROOT / "projects"
        projs = sorted(d for d in pp.iterdir() if d.is_dir()) if pp.exists() else []
        if not projs: print("No projects yet — scripts/new_project.py"); return
        for d in projs: print(one_line(d))
    else:
        dashboard(Path(sys.argv[1]))

if __name__ == "__main__":
    main()
