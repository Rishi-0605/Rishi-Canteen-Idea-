#!/usr/bin/env python3
"""SOCH test suite. Free, local, no paid calls.

  python tests/run_tests.py           # all tests incl. end-to-end render with synthetic fixtures (~3-6 min)
  python tests/run_tests.py --fast    # skip the end-to-end render

End-to-end tests use SYNTHETIC TEST FIXTURES (a click/bass test tone and colour-bar clips)
created in a temporary folder and deleted afterwards. They test the editing pipeline only;
they are never written to assets/ or output/ and are not the song or the music video.

Result types:  PASS | FAIL | BLOCKED (needs credentials or an external service — not a failure of this code)
"""
from __future__ import annotations

import argparse
import json
import os
import py_compile
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from soch_common import (find_song, get_secret, load_config, load_scenes, media_info, original_lines,  # noqa: E402
                         parse_lyrics, scene_slots)

RESULTS: list[tuple[str, str, str]] = []


def record(status: str, name: str, detail: str = "") -> None:
    RESULTS.append((status, name, detail))
    print(f"[{status:7}] {name}{'  — ' + detail if detail else ''}", flush=True)


def test(name):
    def deco(fn):
        def wrapper(*a, **kw):
            try:
                res = fn(*a, **kw)
                if isinstance(res, tuple):
                    record(*res[:1], name, res[1])
                else:
                    record("PASS", name, res or "")
            except AssertionError as exc:
                record("FAIL", name, str(exc))
            except Exception as exc:  # noqa: BLE001
                record("FAIL", name, f"{type(exc).__name__}: {str(exc)[:300]}")
        return wrapper
    return deco


# --------------------------------------------------------------------------- static tests

@test("python syntax (all scripts)")
def t_syntax():
    files = list((ROOT / "scripts").glob("*.py")) + [ROOT / "soch.py", Path(__file__)]
    for f in files:
        py_compile.compile(str(f), doraise=True)
    return f"{len(files)} files compile"


@test("config: structure and timeline")
def t_config():
    cfg = load_config()
    for key in ("project", "music", "planned_timeline", "music_generation", "video_generation", "edit", "subtitles"):
        assert key in cfg, f"missing config key {key}"
    tl = cfg["planned_timeline"]
    assert tl[0]["start"] == 0, "timeline must start at 0"
    for a, b in zip(tl, tl[1:]):
        assert a["end"] == b["start"], f"gap/overlap between {a['id']} and {b['id']}"
    assert tl[-1]["end"] == cfg["project"]["target_duration_sec"], "timeline must end at target duration"
    expected = [("intro", 0, 12), ("verse1", 12, 45), ("hook", 45, 65), ("verse2", 65, 98), ("bridge", 98, 108),
                ("verse3", 108, 140), ("final_hook", 140, 165), ("outro", 165, 180)]
    assert [(s["id"], s["start"], s["end"]) for s in tl] == expected, "timeline differs from the brief"
    hr = cfg["edit"]["hook_reel"]
    assert 30 <= hr["end"] - hr["start"] <= 60, "hook reel must be 30-60 s"
    assert cfg["music"]["bpm"] == 96
    return "8 sections, 0:00-3:00, contiguous"


@test("lyrics: approved lines preserved word-for-word and in order")
def t_lyrics():
    cfg = load_config()
    secs = parse_lyrics()
    assert [s.id for s in secs] == [s["id"] for s in cfg["planned_timeline"]], "lyric sections != timeline"
    all_lines = [l for s in secs for l in s.lines]
    idx = []
    for line in original_lines():
        assert line in all_lines, f"approved line missing/altered: {line!r}"
        idx.append(all_lines.index(line))
    assert idx == sorted(idx), "approved lines are out of order"
    return f"{len(original_lines())} approved lines, {len(all_lines)} total lyric lines"


@test("scene plan: contiguous coverage, fields, prompt length")
def t_scenes():
    doc = load_scenes()
    scenes = doc["scenes"]
    ids = [s["id"] for s in scenes]
    assert len(ids) == len(set(ids)), "duplicate scene ids"
    assert scenes[0]["start"] == 0 and scenes[-1]["end"] == 180, "scenes must cover 0-180"
    for a, b in zip(scenes, scenes[1:]):
        assert a["end"] == b["start"], f"gap between {a['id']} and {b['id']}"
    req = ("prompt", "camera", "lighting", "location", "action", "transition_in", "lyrics_excerpt", "section")
    for s in scenes:
        for k in req:
            assert k in s, f"{s['id']} missing {k}"
        assert len(s["prompt"]) <= 1000, f"{s['id']} prompt > 1000 chars"
        assert s["end"] - s["start"] <= 10, f"{s['id']} longer than 10 s"
    lipsync = sum(1 for s in scenes if s["needs_lipsync"])
    return f"{len(scenes)} scenes, {lipsync} flagged for lip-sync"


@test("subtitles: SRT valid, exact approved wording, one cue per lyric line")
def t_subs():
    from create_subtitles import parse_srt, validate_srt
    cfg = load_config()
    srt = ROOT / cfg["subtitles"]["srt_file"]
    problems = validate_srt(srt, cfg, 180.0)
    assert not problems, "; ".join(problems[:5])
    cues = parse_srt(srt)
    lyric_lines = [l for s in parse_lyrics() for l in s.lines]
    joined = [" ".join(c.text.split("\n")) for c in cues]
    assert joined == lyric_lines, "cue texts differ from final_lyrics.txt"
    return f"{len(cues)} cues; timings are APPROXIMATE (flagged for review)"


@test("music adapter: dry-run request (no network)")
def t_music_request():
    import logging
    from generate_music import ElevenLabsMusic
    cfg = load_config()
    req = ElevenLabsMusic(cfg, logging.getLogger("t")).build_request()
    plan = req["json"]["composition_plan"]
    assert abs(req["_total_sec"] - 180) < 0.01, "section durations must total 180 s"
    text = json.dumps(req, ensure_ascii=False)
    assert "kyunki" in text and " Q ki " not in text, "pronunciation override not applied"
    assert "meethi" in text and "itthi" not in text, "mitthi -> meethi override not applied"
    key = get_secret(cfg["music_generation"]["elevenlabs"]["api_key_env"])
    assert not key or key not in text, "secret leaked into request preview"
    return f"{len(plan['sections'])} sections, 'Q ki' -> 'kyunki', 'mitthi' -> 'meethi' for the singer"


@test("video adapter: dry-run plans (no network)")
def t_video_plan():
    from generate_video_clips import plan_scene
    cfg = load_config()
    scenes = load_scenes()["scenes"]
    plans_noref = [plan_scene(s, cfg, None) for s in scenes]
    assert all(p["mode"] == "text_to_video" for p in plans_noref)
    assert all("@rishi" not in p["steps"][0]["body"]["promptText"] for p in plans_noref)
    plans_ref = [plan_scene(s, cfg, Path("ref.png")) for s in scenes]
    kf = sum(1 for p in plans_ref if p["mode"].startswith("keyframe"))
    assert kf == sum(1 for s in scenes if s["has_character"])
    assert all(p["duration"] in cfg["video_generation"]["runway"]["allowed_durations"] for p in plans_ref)
    return f"{len(scenes)} scenes; with reference image: {kf} keyframe+i2v, {len(scenes) - kf} t2v; " \
           f"{sum(p['duration'] for p in plans_noref)} s total"


@test("timing: scene slots gap-free and frame-exact for several song lengths")
def t_slots():
    cfg = load_config()
    scenes = load_scenes()["scenes"]
    fps = cfg["edit"]["fps"]
    for dur in (172.3, 180.0, 183.47, 195.0):
        slots = scene_slots(cfg, scenes, dur)
        assert slots[0]["start"] == 0 and abs(slots[-1]["end"] - dur) < 1e-6
        assert all(s["frames"] > 0 for s in slots), "empty slot"
        assert sum(s["frames"] for s in slots) == round(dur * fps), "frame total != song length"
        for a, b in zip(slots, slots[1:]):
            assert a["end"] == b["start"], "gap between slots"
    return "172.3 / 180 / 183.47 / 195 s all OK"


@test("secrets: .env ignored by git, no keys in tracked files")
def t_secrets():
    gi = (ROOT / ".gitignore").read_text()
    assert ".env" in gi.split(), ".env not in .gitignore"
    ex = (ROOT / ".env.example").read_text()
    for line in ex.splitlines():
        if "=" in line and not line.startswith("#"):
            assert line.split("=", 1)[1].strip() in ("", "your_key_here"), f"real-looking value in .env.example: {line}"
    return ".env ignored; .env.example has placeholders only"


# --------------------------------------------------------------------------- end-to-end (synthetic fixtures)

def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *map(str, args)], check=True)


def make_fixtures(tmp: Path, song_dur: float) -> tuple[Path, Path]:
    """TEST TONE + colour-bar clips. Clearly synthetic; never used as real media."""
    audio = tmp / "TEST_TONE_not_the_song.wav"
    # 96 BPM click (every 0.625 s) over a 55 Hz bass tone
    ff("-f", "lavfi", "-i", f"sine=f=55:d={song_dur}", "-f", "lavfi",
       "-i", f"aevalsrc='0.6*sin(2*PI*1000*t)*lt(mod(t,0.625),0.03)':d={song_dur}",
       "-filter_complex", "amix=inputs=2", "-ar", "48000", "-ac", "2", audio)
    clips = tmp / "clips"
    (clips / "vertical").mkdir(parents=True)
    scenes = load_scenes()["scenes"]
    for i, s in enumerate(scenes):
        # vary length and shape on purpose: 5 s, 10 s, a too-short 2 s clip (loop), a 4:3 clip (crop)
        dur = 2 if i == 5 else (10 if s["generate_duration_sec"] == 10 else 5)
        size = "960x720" if i == 7 else "1280x720"
        ff("-f", "lavfi", "-i", f"testsrc2=s={size}:r=24:d={dur}", "-vf",
           f"drawtext=text='TEST {s['id']}':fontsize=48:fontcolor=white:x=40:y=40:font=Arial",
           "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", clips / f"{s['id']}.mp4")
    ff("-f", "lavfi", "-i", "testsrc2=s=720x1280:r=24:d=5", "-c:v", "libx264", "-preset", "ultrafast",
       "-pix_fmt", "yuv420p", clips / "vertical" / "scene_03.mp4")
    return audio, clips


def py(*args, env=None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *map(str, args)], cwd=ROOT, capture_output=True, text=True, env=env)


@test("end-to-end: master + 9:16 reel + hook reel from synthetic fixtures, validated")
def t_e2e(tmp: Path, env: dict):
    song_dur = 183.47  # deliberately not exactly 180 s
    t0 = time.time()
    audio, clips = make_fixtures(tmp, song_dur)
    out = tmp / "out"
    work = tmp / "work"
    r = py("scripts/assemble_video.py", "--audio", audio, "--clips-dir", clips,
           "--out", out / "SOCH_Official_Music_Video.mp4", "--work-dir", work, env=env)
    assert r.returncode == 0, f"assemble failed: {(r.stdout + r.stderr)[-800:]}"
    r = py("scripts/create_vertical_version.py", "--audio", audio, "--clips-dir", clips,
           "--out-dir", out, "--work-dir", work, env=env)
    assert r.returncode == 0, f"vertical failed: {(r.stdout + r.stderr)[-800:]}"
    r = py("scripts/validate_outputs.py", "--dir", out, "--audio", audio, env=env)
    print("          " + r.stdout.strip().replace("\n", "\n          "))
    assert r.returncode == 0, "validation failed"
    m = media_info(out / "SOCH_Official_Music_Video.mp4")
    return f"song {song_dur}s -> master {m['duration']:.2f}s; all 3 outputs valid ({time.time() - t0:.0f}s)"


@test("end-to-end: --draft with missing clips writes only to drafts, never final names")
def t_draft(tmp: Path, env: dict):
    audio = tmp / "TEST_TONE_not_the_song.wav"
    sparse = tmp / "sparse_clips"
    sparse.mkdir()
    for f in sorted((tmp / "clips").glob("scene_0[1-3].mp4")):
        os.link(f, sparse / f.name)
    r = py("scripts/assemble_video.py", "--audio", audio, "--clips-dir", sparse, "--work-dir", tmp / "work_draft", env=env)
    assert r.returncode != 0 and "missing" in r.stdout, "final build must refuse when clips are missing"
    draft_out = tmp / "draft" / "SOCH_DRAFT_master.mp4"
    r = py("scripts/assemble_video.py", "--draft", "--audio", audio, "--clips-dir", sparse,
           "--out", draft_out, "--work-dir", tmp / "work_draft", env=env)
    assert r.returncode == 0, (r.stdout + r.stderr)[-600:]
    info = media_info(draft_out)
    assert (info["width"], info["height"]) == (1920, 1080) and info["has_audio"]
    return "final build refused (missing clips); draft built with labelled placeholders"


@test("manual import: song + clips validated, bad files rejected (temp folders)")
def t_imports(tmp: Path):
    import logging
    import generate_music as gm
    import generate_video_clips as gv
    import soch_common as sc
    log = logging.getLogger("t")
    cfg = load_config()
    saved = (sc.AUDIO_DIR, gm.AUDIO_DIR, gm.SONG_INFO, gv.CLIPS_DIR)
    try:
        audio_dir = tmp / "imp_audio"
        sc.AUDIO_DIR = gm.AUDIO_DIR = audio_dir
        gm.SONG_INFO = audio_dir / "song_info.json"
        bad = tmp / "not_audio.mp3"
        bad.write_text("this is not audio")
        try:
            gm.import_song(bad, cfg, log, overwrite=False)
            raise AssertionError("a non-audio file was accepted")
        except sc.PipelineError:
            pass
        gm.import_song(tmp / "TEST_TONE_not_the_song.wav", cfg, log, overwrite=False)
        assert (audio_dir / "soch_song.wav").exists() and gm.SONG_INFO.exists()
        clips_dir = tmp / "imp_clips"
        gv.CLIPS_DIR = clips_dir
        src = tmp / "incoming"
        src.mkdir()
        import shutil
        shutil.copy(tmp / "clips" / "scene_01.mp4", src / "SOCH scene-1 take2.mp4")
        shutil.copy(tmp / "clips" / "vertical" / "scene_03.mp4", src / "scene_03_vertical.mp4")
        (src / "scene_02.mp4").write_text("broken")
        gv.import_dir(src, load_scenes()["scenes"], log, overwrite=False)
        assert (clips_dir / "scene_01.mp4").exists(), "scene-1 not imported"
        assert (clips_dir / "vertical" / "scene_03.mp4").exists(), "vertical clip not routed"
        assert not (clips_dir / "scene_02.mp4").exists(), "broken clip was imported"
    finally:
        sc.AUDIO_DIR, gm.AUDIO_DIR, gm.SONG_INFO, gv.CLIPS_DIR = saved
    return "song import OK, non-audio rejected; clip names matched, vertical routed, broken clip rejected"


def blocked_external() -> None:
    cfg = load_config()
    for label, env in (("music generation API (ElevenLabs)", cfg["music_generation"]["elevenlabs"]["api_key_env"]),
                       ("video generation API (Runway)", cfg["video_generation"]["runway"]["api_key_env"])):
        if get_secret(env):
            record("BLOCKED", label, f"{env} is set, but paid calls are never made by tests — run with --confirm-paid yourself")
        else:
            record("BLOCKED", label, f"{env} not configured")
    if not find_song(cfg):
        record("BLOCKED", "real song / final exports", "no song in assets/audio yet")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fast", action="store_true")
    args = ap.parse_args()
    for t in (t_syntax, t_config, t_lyrics, t_scenes, t_subs, t_music_request, t_video_plan, t_slots, t_secrets):
        t()
    if not args.fast:
        with tempfile.TemporaryDirectory(prefix="soch_test_") as d:
            tmp = Path(d)
            cfg = load_config()
            cfg["edit"]["x264_preset"] = "ultrafast"
            test_cfg = tmp / "test_config.json"
            test_cfg.write_text(json.dumps(cfg))
            env = dict(os.environ, SOCH_CONFIG=str(test_cfg))
            t_e2e(tmp, env)
            t_draft(tmp, env)
            t_imports(tmp)
    blocked_external()
    counts = {k: sum(1 for r in RESULTS if r[0] == k) for k in ("PASS", "FAIL", "BLOCKED")}
    print(f"\nSUMMARY: {counts['PASS']} passed, {counts['FAIL']} failed, {counts['BLOCKED']} blocked (external)")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
