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

SECTOR_MAP_CACHE = CACHE / "sector_map.parquet"
FACTORS_CSV = OUTPUT / "defensive_factors_per_winner.csv"
FACTORS_SUMMARY_CSV = OUTPUT / "defensive_factors_summary.csv"
FACTORS_SECTOR_CSV = OUTPUT / "defensive_factors_sector_counts.csv"
FACTORS_REPORT_MD = OUTPUT / "defensive_factors_report.md"

REGIME_LABELS_CSV = OUTPUT / "regime_labels.csv"
REGIME_SECTOR_CSV = OUTPUT / "regime_sector_counts.csv"
REGIME_FACTOR_CSV = OUTPUT / "regime_factor_summary.csv"
REGIME_REPORT_MD = OUTPUT / "regime_report.md"

FF_INDUSTRY_CACHE = CACHE / "ff_12_industry_daily.parquet"
FF_SECTOR_RETURNS_CSV = OUTPUT / "ff_sector_returns_per_drawdown.csv"
FF_SECTOR_LEADERS_CSV = OUTPUT / "ff_sector_leaders.csv"
REGIME_EXTENDED_REPORT_MD = OUTPUT / "regime_extended_report.md"
