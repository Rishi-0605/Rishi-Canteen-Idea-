#!/usr/bin/env python3
"""Build the vertical (9:16) versions — separate from the 16:9 master.

  python scripts/create_vertical_version.py              # full reel + hook reel
  python scripts/create_vertical_version.py --hook-only  # re-cut the hook reel from an existing full reel
  python scripts/create_vertical_version.py --draft      # allow placeholder cards (DRAFT outputs)

Framing: rendered from the ORIGINAL clips (not by cropping the finished master), so
subtitles are laid out for 1080x1920 and nothing is cut off. Each 16:9 clip is scaled to
cover the frame and cropped around scenes[].vertical_focus_x (0 = left, 0.5 = centre,
1 = right) in prompts/scene_prompts.json. If you have a native vertical clip for a scene,
put it in assets/generated_clips/vertical/<scene_id>.mp4 and it will be used instead.

Hook reel: edit.hook_reel.start/end (snapped to the beat), 30-60 s, title card, audio fades.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assemble_video import build_video  # noqa: E402
from soch_common import (OUTPUT_DIR, PROJECT_ROOT, PipelineError, filter_path, load_config, media_info,  # noqa: E402
                         require_ffmpeg, run, setup_logging, snap_to_beat)


def build_hook_reel(cfg: dict, log, reel: Path, out_file: Path | None = None, draft: bool = False) -> Path:
    require_ffmpeg()
    hc = cfg["edit"]["hook_reel"]
    if not reel.exists():
        raise PipelineError(f"Full vertical reel not found ({reel}). Run without --hook-only first.")
    reel_dur = media_info(reel)["duration"]
    start = snap_to_beat(float(hc["start"]), cfg)
    end = min(snap_to_beat(float(hc["end"]), cfg), reel_dur)
    length = end - start
    if not 30 <= length <= 60:
        raise PipelineError(f"Hook reel would be {length:.1f}s; set edit.hook_reel start/end for 30-60 s.")
    if out_file is None:
        out_file = OUTPUT_DIR / "drafts" / "SOCH_DRAFT_hook_reel.mp4" if draft else PROJECT_ROOT / hc["file"]
    out_file.parent.mkdir(parents=True, exist_ok=True)

    title = reel.parent / "hook_title.txt"
    title.write_text(hc.get("title_text", "SOCH"), encoding="utf-8")
    w = cfg["edit"]["vertical"]["width"]
    fin, fout = float(hc["audio_fade_in"]), float(hc["audio_fade_out"])
    vf = [
        f"fade=t=in:st=0:d={fin}",
        f"fade=t=out:st={length - fout:.3f}:d={fout}",
        (f"drawtext=textfile={filter_path(title)}:font={cfg['subtitles']['font']}:fontsize={w // 11}:"
         "fontcolor=white:borderw=5:bordercolor=black:x=(w-text_w)/2:y=h*0.12:"
         "alpha='if(lt(t,0.3),0,if(lt(t,0.8),(t-0.3)/0.5,if(lt(t,3),1,if(lt(t,3.5),(3.5-t)/0.5,0))))'"),
    ]
    af = f"afade=t=in:st=0:d={fin},afade=t=out:st={length - fout:.3f}:d={fout}"
    ec = cfg["edit"]
    tmp = out_file.with_name(out_file.stem + ".part.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.3f}", "-i", reel, "-t", f"{length:.3f}",
         "-vf", ",".join(vf), "-af", af,
         "-c:v", "libx264", "-preset", ec["x264_preset"], "-crf", str(ec["crf"]), "-pix_fmt", "yuv420p",
         "-profile:v", "high", "-c:a", "aac", "-b:a", ec["audio_bitrate"], "-ar", "48000",
         "-movflags", "+faststart", tmp], log)
    tmp.replace(out_file)
    info = media_info(out_file)
    log.info("[hook reel] %.2f-%.2fs -> %s  %sx%s  %.2fs", start, end, out_file.name,
             info["width"], info["height"], info["duration"])
    return out_file


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hook-only", action="store_true")
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--no-subs", action="store_true")
    ap.add_argument("--audio", type=Path)
    ap.add_argument("--clips-dir", type=Path)
    ap.add_argument("--out-dir", type=Path, help="write both files here (testing)")
    ap.add_argument("--work-dir", type=Path)
    args = ap.parse_args()
    log = setup_logging("vertical")
    cfg = load_config()

    reel_out = hook_out = None
    if args.out_dir:
        reel_out = args.out_dir / Path(cfg["edit"]["vertical"]["file"]).name
        hook_out = args.out_dir / Path(cfg["edit"]["hook_reel"]["file"]).name
    if args.hook_only:
        reel = reel_out or (OUTPUT_DIR / "drafts" / "SOCH_DRAFT_vertical.mp4" if args.draft
                            else PROJECT_ROOT / cfg["edit"]["vertical"]["file"])
    else:
        reel = build_video("vertical", cfg, log, audio=args.audio, clips_dir=args.clips_dir, out_file=reel_out,
                           draft=args.draft, subs=not args.no_subs, work_dir=args.work_dir)
    build_hook_reel(cfg, log, reel, hook_out, draft=args.draft)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except PipelineError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
