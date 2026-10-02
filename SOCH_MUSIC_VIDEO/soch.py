#!/usr/bin/env python3
"""SOCH — one command that checks where the project is and does the next FREE step.

  python soch.py            # check status, run the next free step, tell you what's next
  python soch.py --status   # only report, change nothing
  python soch.py --draft    # preview edit now, with labelled placeholders for missing clips

This script NEVER makes paid API calls. Paid steps are printed as commands for you to
run yourself (they need --confirm-paid).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
from soch_common import (SUBTITLE_STATE, PipelineError, find_clip, find_song, load_config, load_scenes,  # noqa: E402
                         media_info, which)

PY = sys.executable


def step(cmd: list[str]) -> int:
    print(f"\n$ {' '.join(cmd)}")
    return subprocess.call([PY, *cmd], cwd=ROOT)


def banner(text: str) -> None:
    print(f"\n{'=' * 70}\n {text}\n{'=' * 70}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--status", action="store_true", help="report only")
    ap.add_argument("--draft", action="store_true", help="build DRAFT previews with placeholders for missing clips")
    args = ap.parse_args()

    cfg = load_config()
    scenes = load_scenes()["scenes"]
    banner(f"{cfg['project']['title']} — {cfg['project']['artist']} — project status")

    ffmpeg_ok = bool(which("ffmpeg") and which("ffprobe"))
    song = find_song(cfg)
    song_dur = media_info(song)["duration"] if (song and ffmpeg_ok) else None
    have = [s["id"] for s in scenes if find_clip(s["id"])]
    missing = [s["id"] for s in scenes if s["id"] not in have]
    srt = ROOT / cfg["subtitles"]["srt_file"]
    outputs = {k: ROOT / cfg["edit"][k]["file"] for k in ("master", "vertical", "hook_reel")}

    print(f" FFmpeg          : {'OK' if ffmpeg_ok else 'MISSING'}")
    print(f" Song            : {f'{song.name} ({song_dur:.1f}s)' if song and song_dur else (song.name if song else 'missing')}")
    print(f" Subtitles       : {'present' if srt.exists() else 'missing'} (timings approximate until reviewed)")
    print(f" Scene clips     : {len(have)}/{len(scenes)}")
    for k, p in outputs.items():
        print(f" {('Output ' + k).ljust(16)}: {'exists' if p.exists() else '-'}")

    if not ffmpeg_ok:
        banner("NEXT: install FFmpeg")
        print(" Install FFmpeg, then run: python scripts/check_environment.py")
        return 1
    if args.status:
        return 0

    if not song:
        banner("NEXT STEP: get the song (step 1 of 3)")
        step(["scripts/generate_music.py"])  # dry run: builds request preview, free
        print("\n Choose ONE:\n"
              "  A) API (PAID):  add ELEVENLABS_API_KEY to .env, then\n"
              "                  python scripts/generate_music.py --confirm-paid\n"
              "  B) Manual:      use prompts/music_prompt.txt in a music tool you have access to, download\n"
              "                  the song, then: python scripts/generate_music.py --import <file>\n"
              " Then run python soch.py again.")
        return 0

    # keep approximate subtitles in step with the real song length (never overwrites hand edits)
    state_file = SUBTITLE_STATE
    state = json.loads(state_file.read_text()) if state_file.exists() else {}
    if not srt.exists() or abs((state.get("song_duration") or 0) - song_dur) > 0.05:
        banner("Updating approximate subtitles to the real song length")
        step(["scripts/create_subtitles.py"])

    if missing and not args.draft:
        banner(f"NEXT STEP: scene clips (step 2 of 3) — {len(missing)} missing")
        step(["scripts/generate_video_clips.py"])  # dry run, free
        print("\n Choose:\n"
              "  A) API (PAID):   add RUNWAYML_API_SECRET to .env, test ONE scene first:\n"
              f"                  python scripts/generate_video_clips.py --confirm-paid --scenes {missing[0]}\n"
              "  B) Manual:       make clips with any tool using prompts/scene_prompts.json, name them\n"
              "                  scene_01.mp4 ... and run: python scripts/generate_video_clips.py --import-dir <folder>\n"
              "  Preview now:     python soch.py --draft   (placeholders for missing clips, DRAFT files only)")
        return 0

    banner("Assembling (step 3 of 3)" + (" — DRAFT preview" if args.draft else ""))
    extra = ["--draft"] if args.draft else []
    if step(["scripts/assemble_video.py", *extra]) != 0:
        return 1
    if step(["scripts/create_vertical_version.py", *extra]) != 0:
        return 1
    if args.draft:
        banner("Draft previews are in output/drafts/. Final files need all clips.")
        return 0
    rc = step(["scripts/validate_outputs.py"])
    banner("DONE — review subtitle timing and lip-sync scenes before publishing" if rc == 0
           else "Exports finished but validation reported problems (see above)")
    return rc


if __name__ == "__main__":
    try:
        sys.exit(main())
    except PipelineError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
