#!/usr/bin/env python3
"""Create / validate lyric subtitles for SOCH.

  python scripts/create_subtitles.py            # write lyrics/subtitles.srt (approximate timings)
  python scripts/create_subtitles.py --check    # validate the existing SRT only
  python scripts/create_subtitles.py --force    # overwrite even if you hand-edited the SRT

Timings are ESTIMATES: each section's lyric lines are spread across that section's
window (config: actual_timeline, else planned_timeline), weighted by syllables and
snapped to the beat grid. They are NOT derived from the vocal audio. Review them in a
subtitle editor (e.g. Subtitle Edit / Aegisub) against the real song.

If you edit the SRT by hand, this script will refuse to overwrite it unless --force.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from soch_common import (SUBTITLE_STATE, PROJECT_ROOT, PipelineError, actual_timeline, beat_len, find_song,  # noqa: E402
                         load_config, media_info, original_lines, parse_lyrics, setup_logging, snap_to_beat)

STATE_FILE = SUBTITLE_STATE
HOOK_SECTIONS = {"hook", "final_hook"}


@dataclass
class Cue:
    start: float
    end: float
    text: str
    section: str = ""


# --------------------------------------------------------------------------- timing

def syllables(line: str) -> int:
    return max(2, len(re.findall(r"[aeiouy]+", line.lower())))


def wrap(text: str, max_chars: int) -> str:
    """Break a long line into two rows at the space nearest the middle."""
    if len(text) <= max_chars or " " not in text:
        return text
    mid = len(text) // 2
    spaces = [i for i, c in enumerate(text) if c == " "]
    cut = min(spaces, key=lambda i: abs(i - mid))
    return text[:cut].rstrip() + "\n" + text[cut + 1:].lstrip()


def build_cues(cfg: dict, song_duration: float | None = None) -> list[Cue]:
    sub = cfg["subtitles"]
    windows = {s["id"]: s for s in actual_timeline(cfg, song_duration)}
    beat = beat_len(cfg)
    cues: list[Cue] = []
    for section in parse_lyrics():
        if section.id not in windows:
            raise PipelineError(f"Lyrics section [{section.id}] is not in the config timeline.")
        if not section.lines:
            continue
        w = windows[section.id]
        s, e = float(w["start"]), float(w["end"])
        avail = e - s
        n = len(section.lines)
        sparse = avail / n > 4.0  # intro / bridge / outro: few spoken lines in a long window
        cap = sub["sparse_section_max_cue_sec"] if sparse else sub["max_cue_sec"]
        if sparse:
            raw_starts = [s + i * avail / n for i in range(n)]
        else:
            # +4 per line: breath + reading time, so short shouts ("Chal!") stay readable
            weights = [syllables(l) + 4 for l in section.lines]
            total = sum(weights)
            raw_starts, acc = [], s
            for wt in weights:
                raw_starts.append(acc)
                acc += avail * wt / total
        starts: list[float] = []
        for t in raw_starts:
            t = snap_to_beat(t, cfg)
            t = min(max(t, s), e - sub["min_cue_sec"])
            if starts and t <= starts[-1]:
                t = starts[-1] + beat / 2
            starts.append(round(t, 3))
        for i, (line, st) in enumerate(zip(section.lines, starts)):
            nxt = starts[i + 1] if i + 1 < n else e
            end = min(nxt - sub["gap_sec"], st + cap)
            if end - st < sub["min_cue_sec"]:
                end = min(nxt - 0.02, st + sub["min_cue_sec"])
            cues.append(Cue(st, round(end, 3), line, section.id))
    return cues


# --------------------------------------------------------------------------- SRT io

def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def parse_srt_time(value: str) -> float:
    h, m, rest = value.strip().replace(".", ",").split(":")
    s, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def render_srt(cues: list[Cue], max_chars: int) -> str:
    blocks = []
    for i, c in enumerate(cues, 1):
        blocks.append(f"{i}\n{srt_time(c.start)} --> {srt_time(c.end)}\n{wrap(c.text, max_chars)}\n")
    return "\n".join(blocks)


def parse_srt(path: Path) -> list[Cue]:
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").strip()
    cues = []
    for block in re.split(r"\n\s*\n", text):
        rows = block.strip().split("\n")
        if len(rows) < 3 or "-->" not in rows[1]:
            raise PipelineError(f"Malformed SRT block in {path.name}:\n{block[:200]}")
        a, b = rows[1].split("-->")
        cues.append(Cue(parse_srt_time(a), parse_srt_time(b), "\n".join(rows[2:])))
    return cues


def validate_srt(path: Path, cfg: dict, duration: float | None = None) -> list[str]:
    """Returns a list of problems (empty = valid)."""
    problems = []
    try:
        cues = parse_srt(path)
    except (PipelineError, ValueError) as exc:
        return [f"cannot parse: {exc}"]
    if not cues:
        return ["no cues"]
    prev_end = 0.0
    for i, c in enumerate(cues, 1):
        if c.end <= c.start:
            problems.append(f"cue {i}: end <= start")
        if c.start < prev_end - 1e-3:
            problems.append(f"cue {i}: overlaps previous cue")
        if c.end - c.start < 0.5:
            problems.append(f"cue {i}: shorter than 0.5 s (unreadable)")
        for row in c.text.split("\n"):
            if len(row) > cfg["subtitles"]["max_chars_per_row"] + 8:
                problems.append(f"cue {i}: row longer than {cfg['subtitles']['max_chars_per_row']} chars")
        prev_end = c.end
    if duration and cues[-1].end > duration + 0.05:
        problems.append(f"last cue ends at {cues[-1].end:.2f}s, after the song ends ({duration:.2f}s)")
    joined = [" ".join(c.text.split("\n")) for c in cues]
    for line in original_lines():
        if line not in joined:
            problems.append(f"approved line missing or altered: {line!r}")
    return problems


# --------------------------------------------------------------------------- ASS (styled burn-in)

def ass_time(t: float) -> str:
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360_000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def write_ass(srt_path: Path, out_path: Path, cfg: dict, width: int, height: int, style_key: str,
              song_duration: float | None = None, time_offset: float = 0.0) -> Path:
    """Convert the (possibly hand-edited) SRT into an ASS file sized for the target
    frame, so font sizes/margins are in real pixels for 16:9 and 9:16 alike."""
    sub = cfg["subtitles"]
    st = sub[style_key]
    hook_windows = [(s["start"], s["end"]) for s in actual_timeline(cfg, song_duration) if s["id"] in HOOK_SECTIONS]
    font = sub["font"]

    def style(name: str, colour: str) -> str:
        return (f"Style: {name},{font},{st['font_size']},{colour},&H000000FF,&H00000000,&H80000000,"
                f"-1,0,0,0,100,100,0,0,1,{st['outline']},{st['shadow']},2,"
                f"{st['margin_lr']},{st['margin_lr']},{st['margin_v']},1")

    lines = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {width}", f"PlayResY: {height}",
        "WrapStyle: 0", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
        style("Lyric", "&H00FFFFFF"), style("Hook", sub["hook_highlight_colour"]), "",
        "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for c in parse_srt(srt_path):
        start, end = c.start - time_offset, c.end - time_offset
        if end <= 0:
            continue
        mid = (c.start + c.end) / 2
        name = "Hook" if any(a <= mid < b for a, b in hook_windows) else "Lyric"
        text = c.text.replace("{", "(").replace("}", ")").replace("\n", "\\N")
        lines.append(f"Dialogue: 0,{ass_time(max(0, start))},{ass_time(end)},{name},,0,0,0,,{text}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


# --------------------------------------------------------------------------- CLI

def sha(path: Path) -> str:
    # normalise line endings so a Windows git checkout doesn't look like a hand edit
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="only validate the existing SRT")
    ap.add_argument("--force", action="store_true", help="overwrite a hand-edited SRT")
    ap.add_argument("--song-duration", type=float, help="override song duration (seconds)")
    ap.add_argument("--out", type=Path, help="write somewhere else (default from config)")
    args = ap.parse_args()

    log = setup_logging("subtitles")
    cfg = load_config()
    out = args.out or (PROJECT_ROOT / cfg["subtitles"]["srt_file"])

    duration = args.song_duration
    song = find_song(cfg)
    if duration is None and song:
        duration = media_info(song)["duration"]
        log.info("Using real song duration %.2fs from %s", duration, song.name)
    elif duration is None:
        log.info("No song yet: timings follow the PLANNED timeline (0:00-3:00).")

    if args.check:
        if not out.exists():
            log.error("No SRT at %s", out)
            return 1
        problems = validate_srt(out, cfg, duration)
        for p in problems:
            log.error("SRT: %s", p)
        log.info("SRT check: %s", "PASS" if not problems else f"FAIL ({len(problems)} problems)")
        return 0 if not problems else 1

    state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
    if out.exists() and not args.force and args.out is None:
        if state.get("sha256") != sha(out):
            log.warning("%s looks hand-edited (or was not made by this script). Not overwriting. "
                        "Use --force to regenerate.", out.name)
            return 0

    cues = build_cues(cfg, duration)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_srt(cues, cfg["subtitles"]["max_chars_per_row"]), encoding="utf-8")
    if args.out is None:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps({"sha256": sha(out), "song_duration": duration}, indent=2))

    problems = validate_srt(out, cfg, duration)
    for p in problems:
        log.error("SRT: %s", p)
    log.info("Wrote %d cues -> %s", len(cues), out)
    log.warning("TIMINGS ARE APPROXIMATE (estimated from section windows, not from the vocals). "
                "Review every cue against the real song before publishing.")
    return 0 if not problems else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except PipelineError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
