"""Shared test helpers. Tests are offline and write only to temp directories."""

import datetime as dt
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fortune_research.config import Settings  # noqa: E402
from fortune_research.models import Fact, Source  # noqa: E402
from sample_data import stages  # noqa: E402


def src(name="test", official=True, published=None):
    return Source(url="https://example.invalid/%s" % name, title=name, publisher="Test", official=official, provider="test",
                  retrieved_at="2026-10-01T10:00:00+05:30", published=published)


def fact(name, value, pe, ptype="FY", unit=None, basis="consolidated", s=None):
    unit = unit or ("INR per share" if name == "eps_diluted" else "shares" if name == "shares_outstanding" else "INR crore")
    return Fact(name, value, unit, dt.date.fromisoformat(pe) if isinstance(pe, str) else pe, ptype, basis, s or src(name + str(pe)))


class Workspace:
    """A temp copy of the synthetic sample data at a stage, with settings pointing at it."""

    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="fortune-test-")
        self.root = Path(self._tmp.name)

    def settings(self, stage=1, extra=None):
        data = stages.build(self.root / ("data%d" % stage), stage)
        db = self.root / "db"
        ov = {"general": {"database": str(db / "research.db"), "reports_dir": str(db / "reports"), "data_dir": str(db)},
              "providers": {"local": {"roots": [str(data)]}},
              "portfolio": {"holdings_files": [str(data / "portfolio/holdings.csv"), str(data / "portfolio/holdings_broker2.xlsx")],
                            "transaction_files": [str(data / "portfolio/transactions.csv")],
                            "research_note_files": [str(data / "portfolio/research_notes.csv")]}}
        if extra:
            for k, v in extra.items():
                ov.setdefault(k, {}).update(v)
        return Settings.load(sample=True, overrides=ov)

    @staticmethod
    def as_of(stage):
        return dt.date.fromisoformat(stages.STAGE_DATES[stage])

    def cleanup(self):
        self._tmp.cleanup()


os.environ.setdefault("TZ", "Asia/Kolkata")
