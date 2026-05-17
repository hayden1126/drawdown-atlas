"""Common filesystem paths."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
CACHE = DATA / "cache"
OUTPUT = DATA / "output"
PRICES_CACHE = CACHE / "prices"

for _p in (CACHE, OUTPUT, PRICES_CACHE):
    _p.mkdir(parents=True, exist_ok=True)

SPX_CACHE = CACHE / "spx.parquet"
DRAWDOWNS_CSV = OUTPUT / "drawdowns.csv"
CURRENT_MEMBERS_CACHE = CACHE / "sp500_current.parquet"
CHANGES_CACHE = CACHE / "sp500_changes.parquet"
MEMBERSHIP_CACHE = CACHE / "sp500_membership_at_peaks.parquet"
TOP5_CSV = OUTPUT / "top5_per_drawdown.csv"
REPORT_MD = OUTPUT / "report.md"
