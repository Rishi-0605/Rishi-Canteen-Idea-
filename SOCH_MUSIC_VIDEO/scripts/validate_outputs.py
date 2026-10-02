#!/usr/bin/env python3
"""Validate the exported videos: streams, codecs, dimensions, duration vs the song,
and black gaps. Free and local.

  python scripts/validate_outputs.py
  python scripts/validate_outputs.py --skip-black          # faster
  python scripts/validate_outputs.py --dir /some/folder --audio song.wav   # (used by tests)
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from soch_common import PROJECT_ROOT, find_song, load_config, media_info, require_ffmpeg  # noqa: E402


def black_segments(path: Path, min_len: float = 0.5) -> list[tuple[float, float]]:
    proc = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vf",
                           f"blackdetect=d={min_len}:pix_th=0.08", "-an", "-f", "null", "-"],
                          capture_output=True, text=True)
    return [(float(a), float(b)) for a, b in
            re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", proc.stderr)]


def check(path: Path, w: int, h: int, song_dur: float | None, dur_range: tuple[float, float] | None,
          skip_black: bool) -> list[str]:
    if not path.exists():
        return ["file missing"]
    info = media_info(path)
    problems = []
    if not info["has_video"]:
        problems.append("no video stream")
    if not info["has_audio"]:
        problems.append("no audio stream")
    if info["vcodec"] != "h264":
        problems.append(f"video codec {info['vcodec']} (expected h264)")
    if info["acodec"] != "aac":
        problems.append(f"audio codec {info['acodec']} (expected aac)")
    if (info["width"], info["height"]) != (w, h):
        problems.append(f"size {info['width']}x{info['height']} (expected {w}x{h})")
    if song_dur and abs(info["duration"] - song_dur) > 0.25:
        problems.append(f"duration {info['duration']:.2f}s differs from song {song_dur:.2f}s")
    if dur_range and not dur_range[0] <= info["duration"] <= dur_range[1] + 0.1:
        problems.append(f"duration {info['duration']:.2f}s outside {dur_range}")
    if not skip_black and info["has_video"]:
        end = info["duration"]
        # fades at the very start/end are intentional
        gaps = [(a, b) for a, b in black_segments(path) if a > 1.0 and b < end - 2.0]
        for a, b in gaps:
            problems.append(f"black gap {a:.2f}-{b:.2f}s")
    status = "PASS" if not problems else "FAIL"
    print(f"[{status}] {path.name}: {info['width']}x{info['height']} {info['vcodec']}/{info['acodec']} "
          f"{info['duration']:.2f}s")
    for p in problems:
        print(f"         - {p}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", type=Path, help="folder holding the three outputs (default: paths from config)")
    ap.add_argument("--audio", type=Path)
    ap.add_argument("--skip-black", action="store_true")
    args = ap.parse_args()
    require_ffmpeg()
    cfg = load_config()
    song = args.audio or find_song(cfg)
    song_dur = media_info(song)["duration"] if song else None
    if not song:
        print("[WARN] no song found - duration vs song not checked")
    ed = cfg["edit"]

    def path(key: str) -> Path:
        f = Path(ed[key]["file"])
        return args.dir / f.name if args.dir else PROJECT_ROOT / f

    total = 0
    total += len(check(path("master"), ed["master"]["width"], ed["master"]["height"], song_dur, None, args.skip_black))
    total += len(check(path("vertical"), ed["vertical"]["width"], ed["vertical"]["height"], song_dur, None, args.skip_black))
    total += len(check(path("hook_reel"), ed["vertical"]["width"], ed["vertical"]["height"], None, (30, 60), args.skip_black))
    print("ALL OUTPUTS VALID" if not total else f"{total} problem(s) found")
    return 0 if not total else 1


if __name__ == "__main__":
    sys.exit(main())
