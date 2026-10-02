# SOCH — Rishi Shah · music-video production kit

A beginner-friendly pipeline that takes **"SOCH"** (original Hindi/Hinglish Mumbai street rap,
~96 BPM, ~3:00) from lyrics → song → scene clips → finished videos:

| Output | Format |
|---|---|
| `output/SOCH_Official_Music_Video.mp4` | 1920×1080, 16:9, H.264/AAC, exactly the song's length |
| `output/SOCH_Reel_9x16.mp4` | 1080×1920 vertical, full song, re-framed from the original clips |
| `output/SOCH_Hook_Reel.mp4` | 1080×1920, 35 s promo around the final hook, title card + fades |

> **What's real and what isn't.** This repo contains code, lyrics, prompts and plans. It does
> **not** contain the song or any video footage — those must come from a generation service
> (paid, with your approval) or from you. The scripts never create fake media: the final
> files can only be built from a real song + real clips. A `--draft` mode exists for previews,
> and it writes only to `output/drafts/` with a visible "DRAFT" label.

---

## Quick start

```bash
cd SOCH_MUSIC_VIDEO
python -m pip install -r requirements.txt     # requests + python-dotenv
python scripts/check_environment.py           # FFmpeg, fonts, keys (presence only)
python soch.py                                # does the next FREE step and tells you what's next
```

`python soch.py` looks at what exists and does the next free step:

1. **No song?** → builds the music request (dry run) and shows your two options.
2. **Song but missing clips?** → updates subtitles to the real song length, shows the clip plan (dry run).
3. **Everything present?** → builds the master, the 9:16 reel and the hook reel, then validates them.

It **never** spends money. Every paid command needs `--confirm-paid`, and you run it yourself.

You need **Python 3.9+** and **FFmpeg** (with libx264 + libass). Node.js is not needed.

---

## Step 1 — the song

### Option A: ElevenLabs Music API (paid)
ElevenLabs has an official music API (`POST https://api.elevenlabs.io/v1/music`) that accepts a
**composition plan**: sections with durations, styles and lyric lines. `generate_music.py` builds
that plan from `lyrics/final_lyrics.txt` + the timeline in `config/project.json`
(intro 12 s, verse 33 s, hook 20 s, …, total 180 s).

```bash
cp .env.example .env              # then paste your key after ELEVENLABS_API_KEY=
python scripts/generate_music.py                 # dry run: writes prompts/generated/music_request_preview.json
python scripts/generate_music.py --confirm-paid  # PAID: generates and saves assets/audio/soch_song.mp3
```
- Needs a paid ElevenLabs plan that includes music. Cost comes from your plan's credits — check
  your plan's pricing page before confirming.
- The audio is only saved if real audio comes back and FFmpeg can decode it.
- It does **not** auto-retry after a timeout (the song may already have been billed); it tells you to
  check your ElevenLabs history first.
- `"Q ki"` is sent to the singer as **"kyunki"** so it isn't pronounced "queue". Subtitles keep "Q ki".

### Option B: any music tool you already use (manual, free here)
Open `prompts/music_prompt.txt`, which has the style box, exclusions, structure and the full lyrics.
Paste it into the tool, download the result, then:
```bash
python scripts/generate_music.py --import "C:/Users/you/Downloads/soch.mp3"
```
I couldn't verify an official public API for other popular song generators, so they're supported
through import only.

### After you have the song (important)
1. Listen to it and note where each section really starts.
2. In `config/project.json`, set `music.beat_offset_sec` (the time of the first downbeat) and, if
   sections moved, copy `planned_timeline` into `actual_timeline` with the real times.
3. `python scripts/create_subtitles.py --force` regenerates subtitles for the real timing.

---

## Step 2 — scene clips (32 scenes)

`prompts/scene_prompts.json` holds the full shot list, with timestamps, section, lyric excerpt,
location, action, camera, lighting, transition and a **ready-to-paste prompt** (under 1000 chars)
for each scene. The settings are gritty Mumbai-inspired streets, graffiti alleys, railway underpasses,
a rooftop skyline, an underground show, and school and college friends.

**Character:** a generic young adult Indian male rapper in a black oversized hoodie, dark cargo
trousers, sneakers and understated silver accessories. It will **not** look like Rishi unless you put
a real photo of him in `assets/character_reference/` (see the README there).

### Option A: Runway API (paid)
```bash
python scripts/generate_video_clips.py                                   # dry run + cost summary
python scripts/generate_video_clips.py --confirm-paid --scenes scene_01  # test ONE scene first
python scripts/generate_video_clips.py --confirm-paid --limit 5          # then in batches
```
- No reference image: each scene uses **text-to-video**.
- Reference image present: character scenes first make a **keyframe image** using the reference
  (`@rishi`), then animate it with **image-to-video**. Characters stay more consistent this way.
- **Resumable.** Task IDs are saved in `logs/video_generation_state.json`. If you re-run after a
  crash or timeout, the script polls the existing task instead of paying again. Failed tasks are
  cleared so they can be retried.
- Transient errors (429/5xx/network) are retried with backoff. Authentication and validation
  errors stop immediately.
- The dry run reports total seconds (currently **240 s** of video for 32 clips: 16×5 s and 16×10 s,
  plus 22 keyframe images if you add a reference). Check Runway's current API pricing before you
  confirm.

### Option B: any video tool (manual)
Generate clips anywhere using the prompts. Name each file with its scene number, e.g. `scene_07.mp4`
or `SOCH scene-7 take2.mp4`, then run:
```bash
python scripts/generate_video_clips.py --import-dir ~/Downloads/soch_clips
```
Files containing `vertical` or `9x16` in the name go to `assets/generated_clips/vertical/` and
are used for the 9:16 reel instead of cropping.

### Lip-sync (read this)
Text-to-video does **not** produce accurate Hindi rap lip-sync. Nine scenes are flagged
`needs_lipsync`. You can:
1. Keep them as moody performance B-roll (no visible mouth sync: wide shots, back-light, motion), or
2. Run them through a dedicated lip-sync tool. Export the matching song snippet for each one:
   ```bash
   python scripts/generate_video_clips.py --export-lipsync-audio   # -> assets/lipsync_audio/scene_XX.wav
   ```
   Then import the lip-synced results with `--import-dir`. A vocal-only stem works better if your
   music tool provides one.

---

## Step 3 — edit and export (free, local FFmpeg)

```bash
python scripts/assemble_video.py            # 16:9 master
python scripts/create_vertical_version.py   # 9:16 full reel + hook reel
python scripts/validate_outputs.py          # dimensions, codecs, duration vs song, black gaps
# or just: python soch.py
```
How the edit works:
- **Timing.** Scene cuts are remapped onto the real song's sections, snapped to the 96 BPM beat grid
  and converted to whole frames. Slots are contiguous, so there are no black gaps, and the video is
  exactly as long as the song (intro and outro included).
- **No distortion.** Clips are scaled to *cover* the frame and cropped, never squashed. A short clip
  is slowed by at most 25%; beyond that it loops and a warning is logged.
- **Transitions.** Hard cuts on the beat, white flashes on the beat drops (0:12, 0:45, 1:38, 1:48, 2:20),
  a fade in from black and a fade out at the end.
- **Subtitles.** Burned in from `lyrics/subtitles.srt` with sizes tuned for 16:9 and for 9:16 (raised
  above the Reels/Shorts UI). Hook lines are highlighted in amber.
- **Caching.** Rendered segments are cached in `output/work/`, so changing one clip re-renders only
  that scene.
- **Preview anytime:** `python soch.py --draft` fills missing scenes with labelled placeholder cards
  and writes to `output/drafts/`.

The hook reel window is set in `config/project.json → edit.hook_reel` (default 2:17.5–2:52.5).

---

## Subtitles
- `lyrics/subtitles.srt` uses the **exact approved wording**, one cue per lyric line, with long lines
  split over two rows.
- **Timings are approximate.** They're estimated from the section windows (weighted by syllables,
  snapped to beats), not detected from the vocals. Review them in a subtitle editor such as
  Subtitle Edit or Aegisub, playing the real song.
- If you edit the SRT by hand, the scripts won't overwrite it unless you pass `--force`.
- `python scripts/create_subtitles.py --check` validates the format, overlaps, row lengths and the
  approved lines.
- Font: `subtitles.font` in the config (default Arial / Liberation Sans). You can put your own
  `.ttf` in `assets/fonts/`.

## Lyrics
- `lyrics/final_lyrics.txt` has the full song: intro, 3 verses, hook, beat-switch bridge, final hook
  and outro.
- `lyrics/original_lines.txt` has Rishi's 12 approved lines, kept word-for-word. Tests enforce this.
- **`lyrics/LYRICS_NOTES.md` lists 7 flagged wordings that need your decision** (e.g. *mitthi*
  meaning *meethi*? and a clean-version line).

---

## Testing
```bash
python tests/run_tests.py          # everything incl. a full render with SYNTHETIC test fixtures (~4-5 min)
python tests/run_tests.py --fast   # static checks only
```
Results are **PASS**, **FAIL** or **BLOCKED**. BLOCKED means a test needs credentials or an external
service; it is not a code failure. The end-to-end test renders all three outputs from a
**test tone and colour-bar clips** in a temporary folder, validates them, and deletes them. Those
fixtures are never written to `assets/` or `output/`.

## Project map
```
soch.py                          start here
config/project.json              timeline, BPM, providers, export + subtitle settings
lyrics/final_lyrics.txt          full song (parsed by the scripts)
lyrics/original_lines.txt        approved lines (word-for-word)
lyrics/LYRICS_NOTES.md           flagged wording, please review
lyrics/subtitles.srt             editable subtitles (approximate timings)
prompts/music_prompt.txt         copy-paste prompt for manual music tools
prompts/scene_prompts.json       32-scene shot list + prompts
scripts/check_environment.py     tools / fonts / keys check
scripts/generate_music.py        ElevenLabs adapter + manual import
scripts/generate_video_clips.py  Runway adapter + manual import + lip-sync audio export
scripts/create_subtitles.py      SRT generation/validation, ASS styling
scripts/assemble_video.py        16:9 master
scripts/create_vertical_version.py  9:16 reel + hook reel
scripts/validate_outputs.py      output checks
tests/run_tests.py               test suite
assets/audio/ generated_clips/ character_reference/ lipsync_audio/ fonts/
output/  logs/
```

## Troubleshooting
| Problem | Fix |
|---|---|
| `ffmpeg not found` | Install FFmpeg and add it to PATH (Windows: e.g. `winget install ffmpeg`). |
| `ass`/`libx264` missing | Use a full FFmpeg build. |
| Subtitles in the wrong font | Put a `.ttf` in `assets/fonts/` and set `subtitles.font` to its family name. |
| Cuts feel off-beat | Set `music.beat_offset_sec` to the first downbeat of the real song. |
| A scene looks looped | That clip is too short for its slot. Generate a 10 s version or a different take. |
| 401/403 from an API | Check the key in `.env` (no quotes or spaces) and that your plan includes API access. |

## Originality & safety
The music, vocals and lyrics are meant to be original. Don't name or imitate any artist in prompts.
The track is marked **explicit** (one line). Only use reference photos you have rights to. Keys live
only in `.env`, which is git-ignored, and the scripts print only whether a key is set.
