#!/usr/bin/env python3
"""Get one video clip per scene into assets/generated_clips/<scene_id>.mp4.

  python scripts/generate_video_clips.py                      # DRY RUN: status + request preview, no cost
  python scripts/generate_video_clips.py --confirm-paid --scenes scene_01,scene_02   # PAID, chosen scenes
  python scripts/generate_video_clips.py --confirm-paid --limit 3                    # PAID, next 3 missing
  python scripts/generate_video_clips.py --import-dir ~/Downloads/soch_clips         # manual import (free)
  python scripts/generate_video_clips.py --export-lipsync-audio                      # song snippets for lip-sync tools

Provider: Runway API (https://api.dev.runwayml.com/v1, header X-Runway-Version).
 * Scene WITHOUT the character, or no reference image  -> text_to_video
 * Scene WITH the character AND a reference image in assets/character_reference/
     -> 1) text_to_image keyframe using the reference (tag @rishi) for consistency
        2) image_to_video from that keyframe
Each paid step is logged and tracked in logs/video_generation_state.json, so an
interrupted run resumes by polling the existing task instead of paying again.

Text-to-video does not produce accurate Hindi rap lip-sync. Scenes marked
needs_lipsync are best treated as performance B-roll, or run through a dedicated
lip-sync tool with the audio from --export-lipsync-audio.
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from soch_common import (CLIPS_DIR, LOGS_DIR, PROJECT_ROOT, VIDEO_EXTS, PipelineError, find_clip,  # noqa: E402
                         find_reference_image, find_song, get_secret, load_config, load_scenes, mask,
                         media_info, probe_ok, require_ffmpeg, run, scene_slots, setup_logging)

STATE_FILE = LOGS_DIR / "video_generation_state.json"
PREVIEW = PROJECT_ROOT / "prompts" / "generated" / "video_requests_preview.json"
KEYFRAME_DIR = CLIPS_DIR / "keyframes"
LIPSYNC_DIR = PROJECT_ROOT / "assets" / "lipsync_audio"
PROMPT_LIMIT = 1000
DATA_URI_LIMIT = 5 * 1024 * 1024
TRANSIENT = {408, 409, 425, 429, 500, 502, 503, 504}


class TaskFailed(PipelineError):
    """The provider finished the task as FAILED/CANCELLED (the task id must not be resumed)."""


# --------------------------------------------------------------------------- state (resumability)

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(STATE_FILE)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --------------------------------------------------------------------------- helpers

def data_uri(path: Path) -> str:
    raw = path.read_bytes()
    uri = f"data:{mimetypes.guess_type(path.name)[0] or 'image/png'};base64,{base64.b64encode(raw).decode()}"
    if len(uri) > DATA_URI_LIMIT:
        raise PipelineError(f"{path.name} is too large to upload inline ({len(raw)//1024} KB). "
                            "Resize it to ~1500 px on the long side and try again.")
    return uri


def plain_prompt(prompt: str) -> str:
    """Prompt without the reference tag (for steps that don't take reference images)."""
    return prompt.replace("@rishi, ", "").replace("@rishi", "the rapper")


def clamp_prompt(prompt: str) -> str:
    if len(prompt) <= PROMPT_LIMIT:
        return prompt
    cut = prompt[:PROMPT_LIMIT].rsplit(". ", 1)[0] + "."
    return cut


def pick_duration(want: int, allowed: list[int]) -> int:
    bigger = [d for d in sorted(allowed) if d >= want]
    return bigger[0] if bigger else max(allowed)


def plan_scene(scene: dict, cfg: dict, ref: Path | None) -> dict:
    rc = cfg["video_generation"]["runway"]
    duration = pick_duration(int(scene["generate_duration_sec"]), rc["allowed_durations"])
    if scene["has_character"] and ref:
        return {"mode": "keyframe+image_to_video", "duration": duration, "steps": [
            {"endpoint": "text_to_image", "body": {"model": rc["keyframe_model"], "ratio": rc["keyframe_ratio"],
                                                   "promptText": clamp_prompt(scene["prompt"]),
                                                   "referenceImages": [{"uri": f"<{ref.name}>", "tag": rc["reference_tag"]}]}},
            {"endpoint": "image_to_video", "body": {"model": rc["image_to_video_model"], "ratio": rc["video_ratio"],
                                                    "duration": duration, "promptImage": "<keyframe from step 1>",
                                                    "promptText": clamp_prompt(plain_prompt(scene["prompt"]))}}]}
    return {"mode": "text_to_video", "duration": duration, "steps": [
        {"endpoint": "text_to_video", "body": {"model": rc["text_to_video_model"], "ratio": rc["video_ratio"],
                                               "duration": duration,
                                               "promptText": clamp_prompt(plain_prompt(scene["prompt"]))}}]}


# --------------------------------------------------------------------------- Runway client

class Runway:
    def __init__(self, cfg: dict, log):
        import requests
        self.requests = requests
        self.rc = cfg["video_generation"]["runway"]
        self.log = log
        key = get_secret(self.rc["api_key_env"])
        if not key:
            raise PipelineError(f"{self.rc['api_key_env']} is not set in .env.")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {key}", "X-Runway-Version": self.rc["api_version"],
                                     "Content-Type": "application/json"})

    def _call(self, method: str, path: str, body: dict | None = None) -> dict:
        url = f"{self.rc['base_url']}/{path.lstrip('/')}"
        last = None
        for attempt in range(1, self.rc["max_retries"] + 1):
            try:
                r = self.session.request(method, url, json=body, timeout=60)
            except self.requests.RequestException as exc:
                last = f"network error: {exc}"
            else:
                if r.ok:
                    return r.json()
                last = f"HTTP {r.status_code}: {r.text[:400]}"
                if r.status_code not in TRANSIENT:
                    raise PipelineError(f"Runway rejected {method} /{path} — not retrying. {last}")
            wait = min(120, 2 ** attempt * 3)
            self.log.warning("  transient error (%s); retry %d/%d in %ds", last, attempt, self.rc["max_retries"], wait)
            time.sleep(wait)
        raise PipelineError(f"Runway {method} /{path} failed after retries: {last}")

    def start(self, endpoint: str, body: dict) -> str:
        task = self._call("POST", endpoint, body)
        if "id" not in task:
            raise PipelineError(f"Unexpected Runway response (no task id): {str(task)[:300]}")
        return task["id"]

    def wait(self, task_id: str) -> str:
        deadline = time.time() + self.rc["task_timeout_sec"]
        last_status = None
        while time.time() < deadline:
            task = self._call("GET", f"tasks/{task_id}")
            status = task.get("status")
            if status != last_status:
                self.log.info("  task %s: %s%s", task_id[:8], status,
                              f" ({int(task['progress'] * 100)}%)" if task.get("progress") else "")
                last_status = status
            if status == "SUCCEEDED":
                outputs = task.get("output") or []
                if not outputs:
                    raise PipelineError(f"Task {task_id} succeeded but returned no output URL.")
                return outputs[0]
            if status in ("FAILED", "CANCELLED"):
                raise TaskFailed(f"Task {task_id} {status}: {task.get('failure') or task.get('failureCode')}")
            time.sleep(self.rc["poll_interval_sec"])
        raise PipelineError(f"Task {task_id} still running after {self.rc['task_timeout_sec']}s. "
                            "Re-run later — the script will resume polling it (no new charge).")

    def download(self, url: str, dest: Path) -> Path:
        tmp = dest.with_name(dest.name + ".part")
        with self.requests.get(url, stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
        tmp.replace(dest)
        return dest


def generate_scene(rw: Runway, scene: dict, plan: dict, ref: Path | None, state: dict, log) -> Path:
    sid = scene["id"]
    st = state.setdefault(sid, {})
    rc = rw.rc
    dest = CLIPS_DIR / f"{sid}.mp4"

    if plan["mode"] == "keyframe+image_to_video":
        KEYFRAME_DIR.mkdir(parents=True, exist_ok=True)
        keyframe = KEYFRAME_DIR / f"{sid}.png"
        if not keyframe.exists():
            if not st.get("keyframe_task"):
                body = dict(plan["steps"][0]["body"], referenceImages=[{"uri": data_uri(ref), "tag": rc["reference_tag"]}])
                st.update(keyframe_task=rw.start("text_to_image", body), keyframe_started=now(), status="keyframe_running")
                save_state(state)
                log.info("  keyframe task started (%s)", st["keyframe_task"][:8])
            else:
                log.info("  resuming keyframe task %s (no new charge)", st["keyframe_task"][:8])
            try:
                url = rw.wait(st["keyframe_task"])
            except TaskFailed:
                st.pop("keyframe_task", None)
                st.update(status="keyframe_failed")
                save_state(state)
                raise
            rw.download(url, keyframe)
            st.update(status="keyframe_done")
            save_state(state)
        if not st.get("video_task"):
            body = dict(plan["steps"][1]["body"], promptImage=data_uri(keyframe))
            st.update(video_task=rw.start("image_to_video", body), video_started=now(), status="video_running")
            save_state(state)
            log.info("  video task started (%s)", st["video_task"][:8])
    elif not st.get("video_task"):
        st.update(video_task=rw.start("text_to_video", plan["steps"][0]["body"]), video_started=now(), status="video_running")
        save_state(state)
        log.info("  video task started (%s)", st["video_task"][:8])
    else:
        log.info("  resuming video task %s (no new charge)", st["video_task"][:8])

    try:
        url = rw.wait(st["video_task"])
    except TaskFailed:
        st.pop("video_task", None)
        st.update(status="video_failed")
        save_state(state)
        raise
    rw.download(url, dest)
    ok, why = probe_ok(dest, need_video=True)
    if not ok:
        bad = dest.with_suffix(".invalid.mp4")
        dest.replace(bad)
        st.update(status="download_invalid")
        save_state(state)
        raise PipelineError(f"Downloaded clip for {sid} is not valid video ({why}); kept as {bad.name}.")
    st.update(status="done", finished=now(), seconds=plan["duration"], mode=plan["mode"])
    save_state(state)
    return dest


# --------------------------------------------------------------------------- manual import / lip-sync audio

def import_dir(folder: Path, scenes: list[dict], log, overwrite: bool) -> int:
    ids = {s["id"] for s in scenes}
    imported = 0
    for f in sorted(folder.iterdir()):
        if f.suffix.lower() not in VIDEO_EXTS:
            continue
        m = re.search(r"scene[_\- ]?(\d{1,2})", f.stem, re.I)
        if not m or f"scene_{int(m.group(1)):02d}" not in ids:
            log.warning("skip %s (name must contain scene_01 .. scene_%02d)", f.name, len(ids))
            continue
        sid = f"scene_{int(m.group(1)):02d}"
        vertical = "vertical" in f.stem.lower() or "9x16" in f.stem.lower()
        target_dir = CLIPS_DIR / "vertical" if vertical else CLIPS_DIR
        if find_clip(sid, target_dir) and not overwrite:
            log.info("skip %s (%s already has a clip; use --overwrite)", f.name, sid)
            continue
        ok, why = probe_ok(f, need_video=True)
        if not ok:
            log.error("skip %s: %s", f.name, why)
            continue
        target_dir.mkdir(parents=True, exist_ok=True)
        for old in target_dir.glob(f"{sid}.*"):
            old.unlink()
        shutil.copy2(f, target_dir / f"{sid}{f.suffix.lower()}")
        info = media_info(f)
        log.info("imported %s -> %s/%s%s (%.1fs, %sx%s)", f.name, target_dir.name, sid, f.suffix.lower(),
                 info["duration"], info["width"], info["height"])
        imported += 1
    log.info("Imported %d clip(s).", imported)
    return 0


def export_lipsync_audio(cfg: dict, scenes: list[dict], log) -> int:
    require_ffmpeg()
    song = find_song(cfg)
    if not song:
        raise PipelineError("No song in assets/audio yet — generate or import it first.")
    dur = media_info(song)["duration"]
    LIPSYNC_DIR.mkdir(parents=True, exist_ok=True)
    n = 0
    for slot in scene_slots(cfg, scenes, dur):
        sc = slot["scene"]
        if not sc.get("needs_lipsync"):
            continue
        out = LIPSYNC_DIR / f"{sc['id']}.wav"
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{slot['start']:.3f}", "-t", f"{slot['end'] - slot['start']:.3f}",
             "-i", song, "-ac", "2", "-ar", "48000", out], log)
        log.info("%s  %.2f-%.2fs -> %s", sc["id"], slot["start"], slot["end"], out.relative_to(PROJECT_ROOT))
        n += 1
    log.info("Exported %d lip-sync audio snippets (full mix; use a vocal-only stem if your tool needs one).", n)
    return 0


# --------------------------------------------------------------------------- CLI

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--confirm-paid", action="store_true", help="actually call the PAID provider API")
    ap.add_argument("--scenes", help="comma-separated scene ids (default: all missing)")
    ap.add_argument("--limit", type=int, help="generate at most N scenes this run")
    ap.add_argument("--import-dir", type=Path, help="import clips named like scene_07*.mp4 from a folder")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--export-lipsync-audio", action="store_true")
    args = ap.parse_args()

    log = setup_logging("video")
    cfg = load_config()
    scenes = load_scenes()["scenes"]

    if args.import_dir:
        require_ffmpeg()
        return import_dir(args.import_dir, scenes, log, args.overwrite)
    if args.export_lipsync_audio:
        return export_lipsync_audio(cfg, scenes, log)

    wanted = set(args.scenes.split(",")) if args.scenes else None
    if wanted and (unknown := wanted - {s["id"] for s in scenes}):
        raise PipelineError(f"Unknown scene ids: {', '.join(sorted(unknown))}")
    ref = find_reference_image()
    log.info("Character reference image: %s", ref.name if ref else
             "none (character scenes will use text-to-video; consistency will be weaker)")

    todo, previews, have = [], [], 0
    for sc in scenes:
        clip = find_clip(sc["id"])
        if clip and not args.overwrite:
            have += 1
            continue
        if wanted and sc["id"] not in wanted:
            continue
        plan = plan_scene(sc, cfg, ref)
        todo.append((sc, plan))
        previews.append({"scene": sc["id"], **plan})
    if args.limit:
        todo = todo[: args.limit]

    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW.write_text(json.dumps(previews, indent=2, ensure_ascii=False))
    gen_seconds = sum(p["duration"] for _, p in todo)
    keyframes = sum(1 for _, p in todo if p["mode"].startswith("keyframe"))
    log.info("Clips present: %d/%d. To generate this run: %d scenes = %d s of video%s.",
             have, len(scenes), len(todo), gen_seconds, f" + {keyframes} keyframe images" if keyframes else "")
    for sc, plan in todo:
        log.info("  %s  %-24s %2ds  %s", sc["id"], plan["mode"], plan["duration"], sc["location"][:60])
    if not todo:
        log.info("Nothing to generate.")
        return 0

    rc = cfg["video_generation"]["runway"]
    has_key = get_secret(rc["api_key_env"]) is not None
    log.info("%s: %s", rc["api_key_env"], mask(get_secret(rc["api_key_env"])))
    if not args.confirm_paid:
        log.info("DRY RUN — no API call made, no cost incurred. Request preview: %s", PREVIEW.relative_to(PROJECT_ROOT))
        log.info("Cost: check Runway's current API pricing for %d s of %s/%s video%s before confirming.",
                 gen_seconds, rc["text_to_video_model"], rc["image_to_video_model"],
                 f" and {keyframes} {rc['keyframe_model']} images" if keyframes else "")
        log.info("Tip: test with ONE scene first:  python scripts/generate_video_clips.py --confirm-paid --scenes %s",
                 todo[0][0]["id"])
        log.info("Or generate clips anywhere and import:  python scripts/generate_video_clips.py --import-dir <folder>")
        if not has_key:
            log.info("To use the API: add %s to .env (see .env.example).", rc["api_key_env"])
        return 0

    require_ffmpeg()
    rw = Runway(cfg, log)
    state = load_state()
    if args.overwrite:
        for sc, _ in todo:
            state.pop(sc["id"], None)
            (KEYFRAME_DIR / f"{sc['id']}.png").unlink(missing_ok=True)
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    failed = []
    for i, (sc, plan) in enumerate(todo, 1):
        log.info("[%d/%d] %s (%s, %ds)", i, len(todo), sc["id"], plan["mode"], plan["duration"])
        try:
            out = generate_scene(rw, sc, plan, ref, state, log)
            log.info("  saved %s", out.relative_to(PROJECT_ROOT))
        except PipelineError as exc:
            log.error("  %s failed: %s", sc["id"], exc)
            failed.append(sc["id"])
            if "rejected" in str(exc) and ("401" in str(exc) or "403" in str(exc)):
                log.error("Authentication problem — stopping.")
                break
    log.info("Done. %d succeeded, %d failed%s.", len(todo) - len(failed), len(failed),
             f" ({', '.join(failed)}) — re-run to retry/resume" if failed else "")
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except PipelineError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
