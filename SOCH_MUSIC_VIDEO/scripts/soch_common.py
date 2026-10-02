"""Shared helpers for the SOCH pipeline: paths, config, logging, secrets,
ffmpeg/ffprobe wrappers, beat-grid timing and lyrics parsing.

Only the Python standard library is required here (python-dotenv is optional).
"""
from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "project.json"
LYRICS_PATH = PROJECT_ROOT / "lyrics" / "final_lyrics.txt"
ORIGINAL_LINES_PATH = PROJECT_ROOT / "lyrics" / "original_lines.txt"
SCENES_PATH = PROJECT_ROOT / "prompts" / "scene_prompts.json"
AUDIO_DIR = PROJECT_ROOT / "assets" / "audio"
CLIPS_DIR = PROJECT_ROOT / "assets" / "generated_clips"
VERTICAL_CLIPS_DIR = CLIPS_DIR / "vertical"
REFERENCE_DIR = PROJECT_ROOT / "assets" / "character_reference"
OUTPUT_DIR = PROJECT_ROOT / "output"
WORK_DIR = OUTPUT_DIR / "work"
LOGS_DIR = PROJECT_ROOT / "logs"
SUBTITLE_STATE = PROJECT_ROOT / "lyrics" / ".subtitles_state.json"

VIDEO_EXTS = (".mp4", ".mov", ".webm", ".mkv")
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")


class PipelineError(Exception):
    """A failure the user can act on; the message says what to do."""


# --------------------------------------------------------------------------- config / logging

def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_config(path: Path | None = None) -> dict:
    """SOCH_CONFIG env var can point at an alternative config (used by the tests)."""
    return load_json(path or Path(os.environ.get("SOCH_CONFIG") or CONFIG_PATH))


def load_scenes(path: Path | None = None) -> dict:
    return load_json(path or SCENES_PATH)


def rel(path: Path | str) -> str:
    """Project-relative POSIX path (used for ffmpeg filter args, which hate drive letters)."""
    p = Path(path).resolve()
    try:
        return p.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return p.as_posix()


def setup_logging(name: str, verbose: bool = False) -> logging.Logger:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log = logging.getLogger(name)
    if log.handlers:
        return log
    log.setLevel(logging.DEBUG)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG if verbose else logging.INFO)
    console.setFormatter(logging.Formatter("%(levelname)-7s %(message)s"))
    logfile = logging.FileHandler(LOGS_DIR / f"{name}.log", encoding="utf-8")
    logfile.setLevel(logging.DEBUG)
    logfile.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(message)s"))
    log.addHandler(console)
    log.addHandler(logfile)
    return log


# --------------------------------------------------------------------------- secrets

def load_env() -> None:
    """Load .env into os.environ (python-dotenv if installed, else a tiny parser).
    Existing environment variables win. Values are never printed."""
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file, override=False)
        return
    except ImportError:
        pass
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_secret(name: str) -> str | None:
    load_env()
    value = os.environ.get(name, "").strip()
    if not value or value.startswith("your_") or value.lower() in {"changeme", "xxx"}:
        return None
    return value


def mask(value: str | None) -> str:
    if not value:
        return "<not set>"
    return f"<set, {len(value)} chars>"


# --------------------------------------------------------------------------- ffmpeg / ffprobe

def which(tool: str) -> str | None:
    return shutil.which(tool)


def require_ffmpeg() -> None:
    missing = [t for t in ("ffmpeg", "ffprobe") if not which(t)]
    if missing:
        raise PipelineError(
            f"Missing {', '.join(missing)}. Install FFmpeg (https://ffmpeg.org/download.html) "
            "and make sure it is on your PATH, then run scripts/check_environment.py."
        )


def run(cmd: list[str], log: logging.Logger | None = None, cwd: Path = PROJECT_ROOT) -> subprocess.CompletedProcess:
    if log:
        log.debug("$ %s", " ".join(str(c) for c in cmd))
    proc = subprocess.run([str(c) for c in cmd], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        tail = "\n".join(proc.stderr.strip().splitlines()[-25:])
        raise PipelineError(f"Command failed ({cmd[0]}, exit {proc.returncode}):\n{tail}")
    return proc


def ffprobe_json(path: Path) -> dict:
    proc = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path])
    return json.loads(proc.stdout or "{}")


def media_info(path: Path) -> dict:
    """Summarise a media file. Raises PipelineError if ffprobe cannot read it."""
    data = ffprobe_json(Path(path))
    info = {"path": str(path), "duration": None, "has_video": False, "has_audio": False,
            "width": None, "height": None, "vcodec": None, "acodec": None, "fps": None,
            "sample_rate": None, "channels": None}
    fmt_dur = data.get("format", {}).get("duration")
    if fmt_dur not in (None, "N/A"):
        info["duration"] = float(fmt_dur)
    for s in data.get("streams", []):
        if s.get("codec_type") == "video" and not info["has_video"]:
            if s.get("disposition", {}).get("attached_pic"):
                continue  # cover art inside an mp3 is not video
            info.update(has_video=True, width=s.get("width"), height=s.get("height"), vcodec=s.get("codec_name"))
            num, _, den = (s.get("avg_frame_rate") or "0/1").partition("/")
            try:
                info["fps"] = round(float(num) / float(den or 1), 3) if float(den or 1) else None
            except ValueError:
                pass
            if info["duration"] is None and s.get("duration"):
                info["duration"] = float(s["duration"])
        elif s.get("codec_type") == "audio" and not info["has_audio"]:
            info.update(has_audio=True, acodec=s.get("codec_name"),
                        sample_rate=int(s.get("sample_rate") or 0) or None, channels=s.get("channels"))
    return info


def probe_ok(path: Path, need_video: bool = False, need_audio: bool = False, min_duration: float = 0.3) -> tuple[bool, str]:
    try:
        info = media_info(path)
    except (PipelineError, json.JSONDecodeError) as exc:
        return False, f"unreadable ({str(exc).splitlines()[0][:120]})"
    if need_video and not info["has_video"]:
        return False, "no video stream"
    if need_audio and not info["has_audio"]:
        return False, "no audio stream"
    if not info["duration"] or info["duration"] < min_duration:
        return False, f"duration too short ({info['duration']})"
    return True, "ok"


# --------------------------------------------------------------------------- assets

def find_song(cfg: dict) -> Path | None:
    base = cfg["music"]["song_basename"]
    for ext in cfg["music"]["accepted_extensions"]:
        p = AUDIO_DIR / f"{base}{ext}"
        if p.exists() and p.stat().st_size > 0:
            return p
    return None


def find_clip(scene_id: str, folder: Path = CLIPS_DIR) -> Path | None:
    for ext in VIDEO_EXTS:
        p = folder / f"{scene_id}{ext}"
        if p.exists() and p.stat().st_size > 0:
            return p
    return None


def find_reference_image() -> Path | None:
    if not REFERENCE_DIR.exists():
        return None
    images = sorted(p for p in REFERENCE_DIR.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    return images[0] if images else None


# --------------------------------------------------------------------------- timing

def parse_ts(value) -> float:
    """Accepts seconds (number) or 'm:ss(.ms)'."""
    if isinstance(value, (int, float)):
        return float(value)
    m, _, s = str(value).rpartition(":")
    return float(m or 0) * 60 + float(s)


def fmt_clock(sec: float) -> str:
    sec = max(0.0, sec)
    return f"{int(sec // 60)}:{sec % 60:05.2f}"


def beat_len(cfg: dict) -> float:
    return 60.0 / float(cfg["music"]["bpm"])


def snap_to_beat(t: float, cfg: dict) -> float:
    if not cfg["edit"].get("snap_cuts_to_beat", True):
        return t
    b = beat_len(cfg)
    off = float(cfg["music"].get("beat_offset_sec", 0.0))
    return max(0.0, off + round((t - off) / b) * b)


def planned_timeline(cfg: dict) -> list[dict]:
    return [dict(s) for s in cfg["planned_timeline"]]


def actual_timeline(cfg: dict, song_duration: float | None = None) -> list[dict]:
    """The real section windows. Falls back to the plan; the last section always
    ends at the real song end so the outro is never cut and never padded with black."""
    sections = [dict(s) for s in (cfg.get("actual_timeline") or cfg["planned_timeline"])]
    if song_duration:
        sections = [s for s in sections if s["start"] < song_duration - 0.5]
        sections[-1]["end"] = song_duration
    return sections


def remap_time(t: float, planned: list[dict], actual: list[dict]) -> float:
    """Map a time on the planned timeline onto the actual timeline, section by section."""
    act = {s["id"]: s for s in actual}
    for p in planned:
        if p["start"] <= t <= p["end"] and p["id"] in act:
            a = act[p["id"]]
            frac = (t - p["start"]) / max(1e-6, p["end"] - p["start"])
            return a["start"] + frac * (a["end"] - a["start"])
    if t >= planned[-1]["end"]:
        return actual[-1]["end"]
    return t


# --------------------------------------------------------------------------- lyrics

@dataclass
class LyricSection:
    id: str
    lines: list[str] = field(default_factory=list)
    directions: list[str] = field(default_factory=list)


def parse_lyrics(path: Path | None = None) -> list[LyricSection]:
    sections: list[LyricSection] = []
    for raw in (path or LYRICS_PATH).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        header = re.fullmatch(r"\[([a-z0-9_]+)\]", line)
        if header:
            sections.append(LyricSection(header.group(1)))
            continue
        if not sections:
            raise PipelineError(f"Lyric line before any [section] header: {line!r}")
        if line.startswith("{") and line.endswith("}"):
            sections[-1].directions.append(line[1:-1].strip())
        else:
            sections[-1].lines.append(line)
    return sections


def original_lines() -> list[str]:
    return [l.strip() for l in ORIGINAL_LINES_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]


def apply_pronunciation(text: str, cfg: dict) -> str:
    for src, dst in cfg.get("pronunciation_overrides", {}).items():
        text = re.sub(rf"\b{re.escape(src)}\b", dst, text)
    return text


def scene_slots(cfg: dict, scenes: list[dict], song_duration: float) -> list[dict]:
    """Turn the planned scene list into contiguous, gap-free slots on the REAL song:
    remap each cut to the actual section windows, snap it to the beat grid, then
    convert to whole frames so the cumulative length equals the song exactly."""
    planned = planned_timeline(cfg)
    actual = actual_timeline(cfg, song_duration)
    fps = cfg["edit"]["fps"]
    min_len = beat_len(cfg)
    cuts = [0.0]
    for sc in scenes[1:]:
        t = snap_to_beat(remap_time(float(sc["start"]), planned, actual), cfg)
        if t >= song_duration - min_len:
            break  # song shorter than the plan: later scenes are dropped, never squeezed to nothing
        if t < cuts[-1] + min_len:
            t = cuts[-1] + min_len
        cuts.append(t)
    cuts.append(song_duration)
    frames = [round(c * fps) for c in cuts]
    slots = []
    for i in range(len(cuts) - 1):
        slots.append({"scene": scenes[i], "start": cuts[i], "end": cuts[i + 1],
                      "frames": frames[i + 1] - frames[i], "is_last": i == len(cuts) - 2})
    return slots


def filter_path(path: Path | str) -> str:
    """Path for use inside an ffmpeg filter argument (ass=, textfile=). Prefers a
    project-relative path (cwd is the project root); otherwise escapes ':'."""
    p = rel(path)
    if ":" in p or "'" in p:
        p = "'" + p.replace("\\", "/").replace("'", r"'\''").replace(":", r"\:") + "'"
    return p
