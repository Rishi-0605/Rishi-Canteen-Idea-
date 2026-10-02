#!/usr/bin/env python3
"""Check that this computer can run the SOCH pipeline. Free; makes no paid calls.

  python scripts/check_environment.py            # tools, libraries, fonts, credentials (presence only)
  python scripts/check_environment.py --network  # also test that the API hosts are reachable (no auth, no cost)
"""
from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from soch_common import PROJECT_ROOT, find_reference_image, find_song, get_secret, load_config, mask, which  # noqa: E402

OK, WARN, FAIL = "PASS", "WARN", "FAIL"


def ffmpeg_features() -> dict:
    out = {}
    try:
        enc = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
        flt = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
        ver = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout.splitlines()[0]
    except (OSError, IndexError):
        return out
    out["version"] = ver
    out["libx264"] = " libx264 " in enc
    out["aac"] = " aac " in enc
    for f in ("ass", "drawtext", "fade", "scale", "crop", "concat", "blackdetect"):
        out[f] = f" {f} " in flt
    return out


def font_available(name: str) -> bool | None:
    if not which("fc-match"):
        return None
    res = subprocess.run(["fc-match", name], capture_output=True, text=True).stdout
    return bool(res.strip())


def reachable(url: str) -> str:
    import requests
    try:
        r = requests.head(url, timeout=10, allow_redirects=True)
        return f"reachable (HTTP {r.status_code})"
    except requests.RequestException as exc:
        return f"NOT reachable ({type(exc).__name__})"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--network", action="store_true")
    args = ap.parse_args()
    cfg = load_config()
    rows: list[tuple[str, str, str]] = []

    py_ok = sys.version_info >= (3, 9)
    rows.append((OK if py_ok else FAIL, "Python >= 3.9", sys.version.split()[0]))
    for tool in ("ffmpeg", "ffprobe"):
        rows.append((OK if which(tool) else FAIL, tool, which(tool) or "not found - install FFmpeg"))
    feats = ffmpeg_features()
    if feats:
        rows.append((OK, "ffmpeg version", feats["version"][:60]))
        for k in ("libx264", "aac", "ass", "drawtext", "blackdetect"):
            rows.append((OK if feats.get(k) else FAIL, f"ffmpeg: {k}", "yes" if feats.get(k) else
                         "missing - use a full FFmpeg build (with libx264, libass, freetype)"))
    for mod, why in (("requests", "needed for API calls"), ("dotenv", "optional: .env loading (fallback built in)")):
        have = importlib.util.find_spec(mod) is not None
        rows.append((OK if have else (WARN if mod == "dotenv" else FAIL), f"python: {mod}", "installed" if have else why))
    font = cfg["subtitles"]["font"]
    fa = font_available(font)
    rows.append((OK if fa else WARN, f"subtitle font '{font}'",
                 "found" if fa else "unknown/maybe missing - put a .ttf in assets/fonts/ and set subtitles.font"))

    # project state
    song = find_song(cfg)
    rows.append((OK if song else WARN, "song", song.name if song else "missing (next: python scripts/generate_music.py)"))
    ref = find_reference_image()
    rows.append((OK if ref else WARN, "character reference image", ref.name if ref else
                 "none (optional; improves consistency)"))

    # credentials: presence only, never values
    env_file = PROJECT_ROOT / ".env"
    rows.append((OK if env_file.exists() else WARN, ".env file", "found" if env_file.exists() else
                 "not found (copy .env.example to .env)"))
    for label, env in (("music API key", cfg["music_generation"]["elevenlabs"]["api_key_env"]),
                       ("video API key", cfg["video_generation"]["runway"]["api_key_env"])):
        v = get_secret(env)
        rows.append((OK if v else WARN, f"{label} {env}", mask(v)))

    if args.network:
        for label, url in (("ElevenLabs API host", "https://api.elevenlabs.io"),
                           ("Runway API host", cfg["video_generation"]["runway"]["base_url"])):
            res = reachable(url)
            rows.append((OK if res.startswith("reachable") else WARN, label, res))

    width = max(len(r[1]) for r in rows)
    for status, name, detail in rows:
        print(f"[{status}] {name.ljust(width)}  {detail}")
    fails = sum(1 for r in rows if r[0] == FAIL)
    print(f"\n{'Environment OK for local editing.' if not fails else f'{fails} blocking problem(s) - fix the FAIL rows.'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
