#!/usr/bin/env python3
"""Build preview/SOCH_Preview.html — a FREE in-browser preview of SOCH.

  python preview/build_preview.py

What the page is: an original demo beat synthesized live in the browser (Web Audio),
an animated storyboard of the 32 planned scenes, and the lyrics timed to the beat so
you can rap along. It is NOT the final song or the final music video.

The preview quantizes section boundaries to whole bars (96 BPM = 2.5 s per bar) so the
synthesized drops, subtitles and scene cuts line up. Data comes straight from
config/project.json, lyrics/final_lyrics.txt and prompts/scene_prompts.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
from create_subtitles import build_cues  # noqa: E402
from soch_common import apply_pronunciation, load_config, load_scenes, parse_lyrics, scene_slots  # noqa: E402

# Which drawn "set" each scene uses in the animated storyboard.
ARCHETYPE = {
    "scene_01": "skyline", "scene_02": "underpass", "scene_03": "alley", "scene_04": "market",
    "scene_05": "gully", "scene_06": "bridge", "scene_07": "phones", "scene_08": "alley_close",
    "scene_09": "venue", "scene_10": "alley_crew", "scene_11": "venue_crowd", "scene_12": "corner",
    "scene_13": "queue", "scene_14": "desk", "scene_15": "corridor", "scene_16": "venue",
    "scene_17": "car", "scene_18": "venue_close", "scene_19": "platform", "scene_20": "platform_train",
    "scene_21": "schoolgate", "scene_22": "canteen", "scene_23": "alley_crew", "scene_24": "rooftop_friends",
    "scene_25": "rooftop", "scene_26": "venue_crowd", "scene_27": "venue_friends", "scene_28": "alley_crew",
    "scene_29": "venue_close", "scene_30": "venue_tickets", "scene_31": "rooftop_dawn", "scene_32": "underpass_end",
}
BAR = 2.5
DURATION = 180.0


def main() -> int:
    cfg = load_config()
    # bar-quantized section windows for the preview (e.g. intro 0-12.5, verse 1 12.5-45 ...)
    cfg["actual_timeline"] = [dict(s, start=round(s["start"] / BAR) * BAR, end=round(s["end"] / BAR) * BAR)
                              for s in cfg["planned_timeline"]]
    sections = cfg["actual_timeline"]
    cues = build_cues(cfg, DURATION)
    scenes = load_scenes()["scenes"]
    slots = scene_slots(cfg, scenes, DURATION)
    lyrics = {s.id: s.lines for s in parse_lyrics()}

    data = {
        "title": cfg["project"]["title"], "artist": cfg["project"]["artist"],
        "bpm": cfg["music"]["bpm"], "duration": DURATION,
        "sections": [{"id": s["id"], "label": s["label"], "start": s["start"], "end": s["end"],
                      "lines": len(lyrics.get(s["id"], []))} for s in sections],
        "cues": [{"s": round(c.start, 3), "e": round(c.end, 3), "t": c.text, "sec": c.section,
                  "say": apply_pronunciation(c.text, cfg)} for c in cues],
        "scenes": [{"id": sl["scene"]["id"], "s": round(sl["start"], 3), "e": round(sl["end"], 3),
                    "sec": sl["scene"]["section"], "arch": ARCHETYPE[sl["scene"]["id"]],
                    "type": sl["scene"]["type"], "loc": sl["scene"]["location"],
                    "action": sl["scene"]["action"], "cam": sl["scene"]["camera"],
                    "light": sl["scene"]["lighting"], "tr": sl["scene"]["transition_in"],
                    "fx": sl["scene"]["vertical_focus_x"]} for sl in slots],
    }
    missing = [s["id"] for s in scenes if s["id"] not in ARCHETYPE]
    if missing:
        print("No storyboard set for:", ", ".join(missing))
        return 1
    template = (HERE / "template.html").read_text(encoding="utf-8")
    out = HERE / "SOCH_Preview.html"
    out.write_text(template.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False)), encoding="utf-8")
    print(f"Wrote {out} ({out.stat().st_size // 1024} KB): {len(data['cues'])} lyric cues, {len(data['scenes'])} scenes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
