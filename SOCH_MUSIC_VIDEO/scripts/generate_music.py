#!/usr/bin/env python3
"""Get the SOCH song into assets/audio/ — via an API or by importing a file you made yourself.

  python scripts/generate_music.py                     # DRY RUN: build + save the request, no network, no cost
  python scripts/generate_music.py --confirm-paid      # call the provider (PAID — uses your plan's credits)
  python scripts/generate_music.py --import song.mp3   # manual import (free): copy, probe, register

Provider: ElevenLabs Music (official API, POST https://api.elevenlabs.io/v1/music) with a
composition plan built from lyrics/final_lyrics.txt and the config timeline. Needs
ELEVENLABS_API_KEY in .env and a plan that includes music generation.

No song file is ever created unless real audio bytes came back from the provider (and
ffprobe confirms they decode) or you imported a real file.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from soch_common import (AUDIO_DIR, LOGS_DIR, PROJECT_ROOT, PipelineError, apply_pronunciation,  # noqa: E402
                         find_song, get_secret, load_config, mask, media_info, parse_lyrics,
                         planned_timeline, probe_ok, require_ffmpeg, setup_logging)

REQUEST_PREVIEW = PROJECT_ROOT / "prompts" / "generated" / "music_request_preview.json"
SONG_INFO = AUDIO_DIR / "song_info.json"
LINE_LIMIT = 200          # ElevenLabs: max characters per lyric line in a composition plan
SECTION_MS = (3000, 120000)  # ElevenLabs: allowed section duration range


class MusicProvider:
    """Adapter interface. Add another provider by subclassing and registering in PROVIDERS."""
    name = "base"
    paid = True

    def __init__(self, cfg: dict, log):
        self.cfg, self.log = cfg, log

    def build_request(self) -> dict:
        raise NotImplementedError

    def credentials_ok(self) -> bool:
        raise NotImplementedError

    def generate(self, request: dict, out_base: Path) -> Path:
        raise NotImplementedError


class ElevenLabsMusic(MusicProvider):
    name = "elevenlabs"

    def __init__(self, cfg, log):
        super().__init__(cfg, log)
        self.pc = cfg["music_generation"]["elevenlabs"]

    def credentials_ok(self) -> bool:
        key = get_secret(self.pc["api_key_env"])
        self.log.info("%s: %s", self.pc["api_key_env"], mask(key))
        return key is not None

    def build_request(self) -> dict:
        mg = self.cfg["music_generation"]
        timeline = {s["id"]: s for s in planned_timeline(self.cfg)}
        sections = []
        for sec in parse_lyrics():
            win = timeline[sec.id]
            dur_ms = int(round((win["end"] - win["start"]) * 1000))
            if not SECTION_MS[0] <= dur_ms <= SECTION_MS[1]:
                raise PipelineError(f"Section {sec.id} is {dur_ms} ms; provider allows {SECTION_MS}.")
            lines = [apply_pronunciation(l, self.cfg) for l in sec.lines]
            too_long = [l for l in lines if len(l) > LINE_LIMIT]
            if too_long:
                raise PipelineError(f"Lyric line over {LINE_LIMIT} chars in {sec.id}: {too_long[0]!r}")
            sections.append({
                "section_name": win["label"],
                "positive_local_styles": mg["section_styles"].get(sec.id, []) + sec.directions,
                "negative_local_styles": [],
                "duration_ms": dur_ms,
                "lines": lines,
            })
        body = {
            "composition_plan": {
                "positive_global_styles": mg["global_positive_styles"],
                "negative_global_styles": mg["global_negative_styles"],
                "sections": sections,
            },
            "model_id": self.pc["model_id"],
        }
        if self.pc.get("respect_sections_durations") is not None:
            body["respect_sections_durations"] = self.pc["respect_sections_durations"]
        total = sum(s["duration_ms"] for s in sections) / 1000
        return {"method": "POST", "url": self.pc["endpoint"],
                "params": {"output_format": self.pc["output_format"]},
                "headers": {"xi-api-key": "<from .env: " + self.pc["api_key_env"] + ">",
                            "Content-Type": "application/json"},
                "json": body, "_total_sec": total}

    def generate(self, request: dict, out_base: Path) -> Path:
        import requests  # imported here so dry runs work without it

        key = get_secret(self.pc["api_key_env"])
        headers = dict(request["headers"], **{"xi-api-key": key})
        last_err = None
        for attempt in range(1, self.pc["max_retries"] + 1):
            self.log.info("Calling ElevenLabs Music (attempt %d/%d) — this can take a few minutes...",
                          attempt, self.pc["max_retries"])
            try:
                r = requests.post(request["url"], params=request["params"], headers=headers,
                                  json=request["json"], timeout=self.pc["request_timeout_sec"])
            except requests.ConnectionError as exc:
                last_err = f"connection error before a response: {exc}"
            except requests.Timeout:
                # The request reached the server, so it may have been billed: never auto-retry.
                raise PipelineError("Timed out waiting for the song. It MAY have been generated and charged — "
                                    "check your ElevenLabs history/usage page before running again.")
            else:
                ctype = r.headers.get("Content-Type", "")
                if r.status_code == 200 and ctype.startswith("audio/") and len(r.content) > 10_000:
                    ext = ".wav" if "wav" in ctype else ".mp3"
                    out = out_base.with_suffix(ext)
                    tmp = out.with_suffix(ext + ".part")
                    tmp.write_bytes(r.content)
                    ok, why = probe_ok(tmp, need_audio=True, min_duration=10)
                    if not ok:
                        tmp.unlink(missing_ok=True)
                        raise PipelineError(f"Provider returned audio that does not decode ({why}). Nothing saved.")
                    tmp.replace(out)
                    return out
                detail = r.text[:500] if not ctype.startswith("audio/") else f"{len(r.content)} bytes"
                last_err = f"HTTP {r.status_code} ({ctype}): {detail}"
                if r.status_code not in (429, 500, 502, 503, 504):
                    raise PipelineError(f"ElevenLabs request not successful — not retrying. {last_err}")
            wait = 2 ** attempt * 5
            self.log.warning("Transient failure: %s — retrying in %ds", last_err, wait)
            time.sleep(wait)
        raise PipelineError(f"Music generation failed after retries: {last_err}")


PROVIDERS = {"elevenlabs": ElevenLabsMusic}


def register_song(path: Path, cfg: dict, source: str, log) -> dict:
    info = media_info(path)
    record = {"file": path.name, "source": source, "duration_sec": info["duration"],
              "codec": info["acodec"], "sample_rate": info["sample_rate"], "channels": info["channels"],
              "registered_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    SONG_INFO.write_text(json.dumps(record, indent=2))
    lo, hi = cfg["music"]["min_ok_duration_sec"], cfg["music"]["max_ok_duration_sec"]
    log.info("Song registered: %s (%.2f s, %s, %s Hz)", path.name, info["duration"], info["acodec"], info["sample_rate"])
    if not lo <= info["duration"] <= hi:
        log.warning("Song is %.1f s — outside the expected %d-%d s. The edit will follow the real length, "
                    "but check config planned/actual timelines.", info["duration"], lo, hi)
    log.info("NEXT: listen to it, set music.beat_offset_sec and (if sections moved) actual_timeline in "
             "config/project.json, then run: python scripts/create_subtitles.py --force")
    return record


def import_song(src: Path, cfg: dict, log, overwrite: bool) -> int:
    require_ffmpeg()
    if not src.exists():
        raise PipelineError(f"File not found: {src}")
    ok, why = probe_ok(src, need_audio=True, min_duration=10)
    if not ok:
        raise PipelineError(f"{src.name} is not usable audio: {why}")
    ext = src.suffix.lower()
    if ext not in cfg["music"]["accepted_extensions"]:
        raise PipelineError(f"Unsupported extension {ext}; use one of {cfg['music']['accepted_extensions']}")
    existing = find_song(cfg)
    if existing and not overwrite:
        raise PipelineError(f"A song already exists ({existing.name}). Use --overwrite to replace it.")
    if existing:
        existing.unlink()
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    dest = AUDIO_DIR / f"{cfg['music']['song_basename']}{ext}"
    shutil.copy2(src, dest)
    register_song(dest, cfg, f"manual import of {src.name}", log)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--import", dest="import_path", type=Path, help="import an existing song file (free)")
    ap.add_argument("--confirm-paid", action="store_true", help="actually call the PAID provider API")
    ap.add_argument("--overwrite", action="store_true", help="replace an existing song")
    ap.add_argument("--provider", help="override config music_generation.provider")
    args = ap.parse_args()

    log = setup_logging("music")
    cfg = load_config()

    if args.import_path:
        return import_song(args.import_path, cfg, log, args.overwrite)

    existing = find_song(cfg)
    if existing and not args.overwrite:
        log.info("Song already present: %s — nothing to do (use --overwrite to regenerate).", existing.name)
        return 0

    name = args.provider or cfg["music_generation"]["provider"]
    if name not in PROVIDERS:
        raise PipelineError(f"Unknown provider {name!r}. Available: {', '.join(PROVIDERS)} (or use --import).")
    provider = PROVIDERS[name](cfg, log)
    request = provider.build_request()
    REQUEST_PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    REQUEST_PREVIEW.write_text(json.dumps(request, indent=2, ensure_ascii=False))
    log.info("Request built for %s: %d sections, %.0f s total. Preview (no secrets): %s",
             name, len(request["json"]["composition_plan"]["sections"]), request["_total_sec"],
             REQUEST_PREVIEW.relative_to(PROJECT_ROOT))

    has_key = provider.credentials_ok()
    if not args.confirm_paid:
        log.info("DRY RUN — no API call made, no cost incurred.")
        if not has_key:
            log.info("To use the API: add %s to .env (see .env.example).",
                     cfg["music_generation"][name]["api_key_env"])
        log.info("To generate (PAID, uses your %s credits): python scripts/generate_music.py --confirm-paid", name)
        log.info("Or make the song yourself with prompts/music_prompt.txt and run: "
                 "python scripts/generate_music.py --import <file>")
        return 0
    if not has_key:
        raise PipelineError(f"{cfg['music_generation'][name]['api_key_env']} is not set in .env.")

    require_ffmpeg()
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    if existing:
        existing.unlink()
    out = provider.generate(request, AUDIO_DIR / cfg["music"]["song_basename"])
    register_song(out, cfg, f"generated via {name} API", log)
    with open(LOGS_DIR / "music_generation_history.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"utc": datetime.now(timezone.utc).isoformat(), "provider": name, "file": out.name}) + "\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except PipelineError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
