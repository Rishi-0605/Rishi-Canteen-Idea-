"""Build a working copy of the SYNTHETIC sample data at stage 1 or stage 2.

Stage 2 appends the rows under sample_data/updates/stage2/ to the matching
CSV files (new results, shareholding, announcements, prices), which is how
new disclosures arrive in real use.
"""

from __future__ import annotations

import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE_DATES = {1: "2026-10-20", 2: "2026-10-29"}


def build(dest: Path, stage: int = 1) -> Path:
    dest = Path(dest)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(HERE, dest, ignore=shutil.ignore_patterns("updates", "__pycache__", "*.py", "*.toml"))
    if stage >= 2:
        apply(dest, HERE / "updates" / "stage2")
    return dest


def apply(dest: Path, overlay: Path) -> None:
    for f in overlay.rglob("*.csv"):
        target = dest / f.relative_to(overlay)
        lines = f.read_text(encoding="utf-8").splitlines()[1:]
        with open(target, "a", encoding="utf-8") as fh:
            for line in lines:
                fh.write(line + "\n")
