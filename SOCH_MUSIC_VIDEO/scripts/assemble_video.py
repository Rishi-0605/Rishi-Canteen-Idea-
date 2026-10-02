#!/usr/bin/env python3
"""Assemble the 16:9 master: real song + scene clips + burned-in lyric subtitles.

  python scripts/assemble_video.py            # -> output/SOCH_Official_Music_Video.mp4
  python scripts/assemble_video.py --draft    # missing clips become labelled placeholder cards
                                              #    -> output/drafts/SOCH_DRAFT_master.mp4 (never the final name)
  python scripts/assemble_video.py --no-subs  # without burned-in subtitles

How the edit works
  * Each scene's planned window is remapped to the real song's sections, snapped to the
    beat grid and converted to whole frames, so slots are contiguous: no black gaps, and
    the video is exactly as long as the song (intro and outro preserved).
  * Clips are scaled to COVER the frame and centre-cropped (never squashed). A clip shorter
    than its slot is slowed by at most edit.max_slowdown, otherwise looped (logged).
  * Rendered segments are cached in output/work/, so re-runs only redo changed scenes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from create_subtitles import build_cues, render_srt, validate_srt, write_ass  # noqa: E402
from soch_common import (CLIPS_DIR, OUTPUT_DIR, PROJECT_ROOT, VERTICAL_CLIPS_DIR, PipelineError,  # noqa: E402
                         filter_path, find_clip, find_song, fmt_clock, load_config, load_scenes, media_info,
                         require_ffmpeg, run, scene_slots, setup_logging)

FADE_IN_SEC, FLASH_SEC, FADE_OUT_SEC = 0.8, 0.25, 1.5


def transition_filter(kind: str, dur: float) -> str | None:
    if kind == "fade_in":
        return f"fade=t=in:st=0:d={FADE_IN_SEC}"
    if kind == "flash":
        return f"fade=t=in:st=0:d={FLASH_SEC}:color=white"
    if kind == "fade_out":
        return f"fade=t=out:st={max(0.0, dur - FADE_OUT_SEC):.3f}:d={FADE_OUT_SEC}"
    return None


def segment_signature(**kw) -> str:
    return hashlib.sha1(json.dumps(kw, sort_keys=True, default=str).encode()).hexdigest()[:16]


def render_segment(slot: dict, clip: Path | None, dest: Path, cfg: dict, w: int, h: int, log,
                   focus_x: float = 0.5, draft: bool = False) -> None:
    ec = cfg["edit"]
    fps = ec["fps"]
    frames = slot["frames"]
    dur = frames / fps
    sc = slot["scene"]
    trans = sc.get("transition_in", "cut")
    if slot["is_last"] and trans != "fade_out":
        trans_extra = transition_filter("fade_out", dur)
    else:
        trans_extra = None
    enc = ["-an", "-c:v", "libx264", "-preset", ec["x264_preset"], "-crf", str(max(0, ec["crf"] - 2)),
           "-pix_fmt", "yuv420p", "-r", str(fps), "-frames:v", str(frames)]

    if clip is None:
        card = dest.with_suffix(".txt")
        card.write_text(f"DRAFT PLACEHOLDER - CLIP MISSING\n{sc['id']}  {fmt_clock(slot['start'])}-{fmt_clock(slot['end'])}\n"
                        f"{sc['location'][:60]}\n{sc['type']}", encoding="utf-8")
        size = max(24, h // 30)
        vf = (f"drawtext=textfile={filter_path(card)}:fontcolor=white:fontsize={size}:line_spacing={size // 2}:"
              f"x=(w-text_w)/2:y=(h-text_h)/2:font={cfg['subtitles']['font']}")
        run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c=0x1a1a22:s={w}x{h}:r={fps}",
             "-vf", vf, *enc, dest], log)
        return

    info = media_info(clip)
    cdur = info["duration"] or 0
    inputs = ["-i", clip]
    pre = ["setpts=PTS-STARTPTS"]
    max_slow = cfg["video_generation"]["max_slowdown"]
    if cdur >= dur:
        pass
    elif cdur * max_slow >= dur:
        factor = dur / cdur
        pre.append(f"setpts={factor:.5f}*PTS")
        log.info("    %s: clip %.2fs < slot %.2fs -> slowed %.0f%%", sc["id"], cdur, dur, (factor - 1) * 100)
    else:
        inputs = ["-stream_loop", "-1", "-i", clip]
        log.warning("    %s: clip %.2fs is much shorter than slot %.2fs -> LOOPED. Consider a longer clip.",
                    sc["id"], cdur, dur)
    chain = pre + [
        f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos",
        f"crop={w}:{h}:x=(in_w-{w})*{focus_x:.3f}:y=(in_h-{h})/2",
        "setsar=1", f"fps={fps}", "format=yuv420p",
    ]
    for f in (transition_filter(trans, dur), trans_extra):
        if f:
            chain.append(f)
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-vf", ",".join(chain), *enc, dest], log)


def build_video(kind: str, cfg: dict, log, audio: Path | None = None, clips_dir: Path | None = None,
                out_file: Path | None = None, draft: bool = False, subs: bool = True,
                work_dir: Path | None = None) -> Path:
    """kind: 'master' (16:9) or 'vertical' (9:16). Returns the output path."""
    require_ffmpeg()
    spec = cfg["edit"][kind]
    w, h = spec["width"], spec["height"]
    song = audio or find_song(cfg)
    if not song:
        raise PipelineError("No song found in assets/audio/. Run: python scripts/generate_music.py")
    song_info = media_info(song)
    if not song_info["has_audio"]:
        raise PipelineError(f"{song} has no audio stream.")
    sdur = song_info["duration"]
    clips_dir = clips_dir or CLIPS_DIR
    work = (work_dir or OUTPUT_DIR / "work") / kind
    work.mkdir(parents=True, exist_ok=True)
    if out_file is None:
        out_file = OUTPUT_DIR / "drafts" / f"SOCH_DRAFT_{kind}.mp4" if draft else PROJECT_ROOT / spec["file"]
    out_file.parent.mkdir(parents=True, exist_ok=True)

    scenes = load_scenes()["scenes"]
    slots = scene_slots(cfg, scenes, sdur)
    log.info("[%s %dx%d] song %s (%.2fs), %d scene slots", kind, w, h, Path(song).name, sdur, len(slots))
    if len(slots) < len(scenes):
        log.warning("Song is shorter than the plan: %d scene(s) at the end were dropped.", len(scenes) - len(slots))

    # resolve clips
    resolved, missing = [], []
    for slot in slots:
        sid = slot["scene"]["id"]
        clip = None
        if kind == "vertical":
            clip = find_clip(sid, clips_dir / VERTICAL_CLIPS_DIR.name)
        clip = clip or find_clip(sid, clips_dir)
        if clip is None:
            missing.append(sid)
        resolved.append(clip)
    if missing and not draft:
        raise PipelineError(f"{len(missing)}/{len(slots)} scene clips missing ({', '.join(missing[:8])}"
                            f"{'...' if len(missing) > 8 else ''}). Generate/import them "
                            "(python scripts/generate_video_clips.py) or preview with --draft.")
    if missing:
        log.warning("DRAFT: %d missing clip(s) will show labelled placeholder cards.", len(missing))

    # render segments (cached)
    seg_list = work / "segments.txt"
    lines = []
    for i, (slot, clip) in enumerate(zip(slots, resolved), 1):
        sc = slot["scene"]
        focus = float(sc.get("vertical_focus_x", 0.5)) if kind == "vertical" else 0.5
        sig = segment_signature(clip=str(clip), mtime=clip.stat().st_mtime if clip else None,
                                size=clip.stat().st_size if clip else None, frames=slot["frames"], w=w, h=h,
                                focus=focus, trans=sc.get("transition_in"), last=slot["is_last"],
                                edit={k: cfg["edit"][k] for k in ("fps", "crf", "x264_preset")},
                                slow=cfg["video_generation"]["max_slowdown"])
        seg = work / f"{sc['id']}_{sig}.mp4"
        if not seg.exists():
            for old in work.glob(f"{sc['id']}_*.mp4"):
                old.unlink()
            log.info("  [%2d/%d] %s %s-%s %s", i, len(slots), sc["id"], fmt_clock(slot["start"]),
                     fmt_clock(slot["end"]), "(placeholder)" if clip is None else Path(clip).name)
            render_segment(slot, clip, seg, cfg, w, h, log, focus_x=focus, draft=draft)
        lines.append(f"file '{seg.resolve().as_posix()}'")
    seg_list.write_text("\n".join(lines) + "\n", encoding="utf-8")

    clean = work / "clean_video.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", seg_list, "-c", "copy", clean], log)

    # subtitles
    vf = []
    if subs:
        srt = PROJECT_ROOT / cfg["subtitles"]["srt_file"]
        if not srt.exists():
            log.warning("No SRT found; generating approximate one in %s", srt)
            srt.write_text(render_srt(build_cues(cfg, sdur), cfg["subtitles"]["max_chars_per_row"]), encoding="utf-8")
        problems = validate_srt(srt, cfg, sdur)
        for p in problems:
            log.warning("  subtitle issue: %s", p)
        ass = write_ass(srt, work / "subs.ass", cfg, w, h, "master_style" if kind == "master" else "vertical_style", sdur)
        flt = f"ass={filter_path(ass)}"
        fonts_dir = PROJECT_ROOT / cfg["subtitles"]["fonts_dir"]
        if fonts_dir.is_dir() and any(fonts_dir.iterdir()):
            flt += f":fontsdir={filter_path(fonts_dir)}"
        vf.append(flt)
    if draft:
        vf.append(f"drawtext=text='DRAFT':fontcolor=white@0.6:fontsize={h // 22}:x=w-text_w-30:y=30:"
                  f"font={cfg['subtitles']['font']}")

    ec = cfg["edit"]
    tmp = out_file.with_name(out_file.stem + ".part.mp4")
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", clean, "-i", song, "-map", "0:v:0", "-map", "1:a:0"]
    if vf:
        cmd += ["-vf", ",".join(vf)]
    cmd += ["-c:v", "libx264", "-preset", ec["x264_preset"], "-crf", str(ec["crf"]), "-pix_fmt", "yuv420p",
            "-profile:v", "high", "-r", str(ec["fps"]),
            "-c:a", "aac", "-b:a", ec["audio_bitrate"], "-ar", "48000",
            "-t", f"{sdur:.3f}", "-movflags", "+faststart", tmp]
    log.info("  encoding final %s ...", out_file.name)
    run(cmd, log)
    tmp.replace(out_file)
    info = media_info(out_file)
    log.info("  -> %s  %sx%s  %.2fs  %s/%s", out_file.relative_to(PROJECT_ROOT) if out_file.is_relative_to(PROJECT_ROOT)
             else out_file, info["width"], info["height"], info["duration"], info["vcodec"], info["acodec"])
    return out_file


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--draft", action="store_true", help="allow missing clips (placeholder cards, DRAFT output)")
    ap.add_argument("--no-subs", action="store_true")
    ap.add_argument("--audio", type=Path, help="use this audio file instead of assets/audio/soch_song.*")
    ap.add_argument("--clips-dir", type=Path, help="use clips from this folder")
    ap.add_argument("--out", type=Path, help="output file path")
    ap.add_argument("--work-dir", type=Path, help="cache folder for rendered segments")
    args = ap.parse_args()
    log = setup_logging("assemble")
    cfg = load_config()
    build_video("master", cfg, log, audio=args.audio, clips_dir=args.clips_dir, out_file=args.out,
                draft=args.draft, subs=not args.no_subs, work_dir=args.work_dir)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except PipelineError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
