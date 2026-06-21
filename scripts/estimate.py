#!/usr/bin/env python3
"""
estimate.py — Local credit budget estimate from shotlist.json (no API calls).

Plan spend BEFORE committing. shot-design must preflight real costs with the
Higgsfield `get_cost` flag, but this gives an instant, dependency-free ballpark
from the plan itself — and flags the Budget Gate (CLAUDE.md §1: >500 credits
projected = stop and ask).

Costs are approximate and adjustable (Higgsfield pricing drifts; --img/--vid/etc.
override). The point is the SHAPE of the spend and an early gate trip, not cents.

Usage:
  python3 scripts/estimate.py projects/<slug>
  python3 scripts/estimate.py projects/<slug> --vid 60 --retake 1.4 --gate 500
"""
import json, argparse
from pathlib import Path

DEFAULTS = dict(img=5, vid=50, music=20, dialogue=3, sfx=5, retake=1.3, gate=500)


def main():
    ap = argparse.ArgumentParser(description="Local credit budget estimate")
    ap.add_argument("project_dir")
    ap.add_argument("--img", type=float, default=DEFAULTS["img"], help="credits / start-frame image")
    ap.add_argument("--vid", type=float, default=DEFAULTS["vid"], help="credits / video clip")
    ap.add_argument("--music", type=float, default=DEFAULTS["music"])
    ap.add_argument("--dialogue", type=float, default=DEFAULTS["dialogue"])
    ap.add_argument("--sfx", type=float, default=DEFAULTS["sfx"])
    ap.add_argument("--retake", type=float, default=DEFAULTS["retake"], help="retake multiplier on visuals")
    ap.add_argument("--gate", type=float, default=DEFAULTS["gate"], help="budget-gate threshold")
    a = ap.parse_args()

    proj = Path(a.project_dir)
    sl = json.loads((proj / "shotlist.json").read_text())
    shots = sl.get("shots", [])
    audio = sl.get("audio", {})
    n_shots = len(shots)
    n_music = len(audio.get("music", []))
    n_dlg = len(audio.get("dialogue", []))
    n_sfx = len(audio.get("sfx", []))

    img_cost = n_shots * a.img
    vid_cost = n_shots * a.vid
    visual_base = img_cost + vid_cost
    visual_with_retakes = visual_base * a.retake
    music_cost = n_music * a.music
    dlg_cost = n_dlg * a.dialogue
    sfx_cost = n_sfx * a.sfx
    audio_cost = music_cost + dlg_cost + sfx_cost
    total = visual_with_retakes + audio_cost

    print(f"== Credit estimate: {sl.get('project', proj.name)} ==")
    print(f"  shots: {n_shots}   music: {n_music}  dialogue: {n_dlg}  sfx: {n_sfx}\n")
    print(f"  start frames   {n_shots:3d} x {a.img:>5.0f} = {img_cost:>8.0f}")
    print(f"  video clips    {n_shots:3d} x {a.vid:>5.0f} = {vid_cost:>8.0f}")
    print(f"  retake factor  x{a.retake:<4.2f}        = {visual_with_retakes - visual_base:>+8.0f}")
    print(f"  music          {n_music:3d} x {a.music:>5.0f} = {music_cost:>8.0f}")
    print(f"  dialogue       {n_dlg:3d} x {a.dialogue:>5.0f} = {dlg_cost:>8.0f}")
    print(f"  sfx            {n_sfx:3d} x {a.sfx:>5.0f} = {sfx_cost:>8.0f}")
    print(f"  {'-'*34}")
    print(f"  TOTAL (est.)                = {total:>8.0f} credits")

    if total > a.gate:
        print(f"\n  ⚠ BUDGET GATE: estimate {total:.0f} > {a.gate:.0f} — "
              f"state this to the user and wait for 'go' before generating.")
    else:
        print(f"\n  ✓ under budget gate ({a.gate:.0f}) — clear to proceed (still preflight get_cost).")
    print("\n  NOTE: approximate. shot-design must confirm with Higgsfield get_cost before batches.")


if __name__ == "__main__":
    main()
