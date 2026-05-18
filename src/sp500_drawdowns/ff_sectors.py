"""Stage 7: Fama-French sector-portfolio gap-close for pre-1985 drawdowns.

yfinance constituent prices effectively start in 1985, so 12 of the 26 detected
drawdowns (1928, 1929, 1955, 1956, 1959, 1961, 1966, 1967, 1968, 1973, 1980,
1983) have no top-5 constituent data and therefore no Stage 5/6 factor or
sector breakdown. This is a real coverage gap.

Closing the gap with constituent prices would require paid CRSP data. As an
open-source alternative, this module uses Ken French's 12-industry value-
weighted daily portfolios (1926-07-01 onward, free from Dartmouth) to compute
which *industries* led during each drawdown. We can't tell you which stocks
won in 1973, but we can tell you Energy and Utilities led the cap-weighted
CRSP universe peak-to-trough.

Honest disclosure: FF industry portfolios cover the full CRSP universe, not
just SPX constituents, so this is a proxy, not a perfect substitute.
"""
from __future__ import annotations

import io
import logging
import zipfile

import pandas as pd
import requests

from .paths import (
    DRAWDOWNS_CSV,
    FF_INDUSTRY_CACHE,
    FF_SECTOR_LEADERS_CSV,
    FF_SECTOR_RETURNS_CSV,
)

log = logging.getLogger(__name__)

FF_ZIP_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "12_Industry_Portfolios_daily_CSV.zip"
)
USER_AGENT = (
    "drawdown-atlas/0.2 (research; +https://github.com/hayden1126/drawdown-atlas)"
)

FF_TO_GICS: dict[str, str] = {
    "NoDur": "Consumer Defensive",
    "Durbl": "Consumer Cyclical",
    "Manuf": "Industrials",
    "Enrgy": "Energy",
    "Chems": "Basic Materials",
    "BusEq": "Technology",
    "Telcm": "Communication Services",
    "Utils": "Utilities",
    "Shops": "Consumer Cyclical",
    "Hlth": "Healthcare",
    "Money": "Financial Services",
    "Other": "Other",
}

FF_INDUSTRIES = list(FF_TO_GICS.keys())


def _parse_ff_daily_csv(text: str) -> pd.DataFrame:
    """Parse the Fama-French 12-industry daily CSV.

    The file has multiple sections (Average VW Returns, Average EW Returns,
    Number of Firms, ...) separated by blank lines and headers. We want the
    first section: average value-weighted returns.
    """
    lines = text.splitlines()
    data_start = None
    for i, line in enumerate(lines):
        first = line.strip().split(",")[0].strip()
        if first.isdigit() and len(first) == 8:
            data_start = i
            break
    if data_start is None:
        raise ValueError("Could not find data rows in FF CSV.")

    header_idx = None
    for j in range(data_start - 1, -1, -1):
        candidate = [c.strip() for c in lines[j].split(",")]
        if len(candidate) >= 13 and candidate[1] in FF_INDUSTRIES:
            header_idx = j
            break
    if header_idx is None:
        raise ValueError("Could not find header row in FF CSV.")

    data_end = data_start
    while data_end < len(lines):
        first = lines[data_end].strip().split(",")[0].strip()
        if first.isdigit() and len(first) == 8:
            data_end += 1
        else:
            break

    csv_block = "\n".join([lines[header_idx], *lines[data_start:data_end]])
    df = pd.read_csv(io.StringIO(csv_block))
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={df.columns[0]: "date"})
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    df = df.set_index("date").sort_index()
    return df / 100.0  # FF publishes in percent; convert to decimal


def fetch_ff_industries(force: bool = False) -> pd.DataFrame:
    """Return the 12-industry value-weighted daily returns frame. Cached."""
    if FF_INDUSTRY_CACHE.exists() and not force:
        return pd.read_parquet(FF_INDUSTRY_CACHE)

    log.info("Fetching Fama-French 12-industry daily portfolios ...")
    r = requests.get(FF_ZIP_URL, headers={"User-Agent": USER_AGENT}, timeout=60)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        name = zf.namelist()[0]
        with zf.open(name) as f:
            text = f.read().decode("utf-8", errors="replace")

    df = _parse_ff_daily_csv(text)
    df.to_parquet(FF_INDUSTRY_CACHE)
    log.info(
        "Cached %d rows of FF 12-industry daily returns (%s to %s)",
        len(df),
        df.index.min().date(),
        df.index.max().date(),
    )
    return df


def sector_returns_in_window(
    df: pd.DataFrame, peak: pd.Timestamp, trough: pd.Timestamp
) -> pd.Series:
    """Cumulative compound return per industry over [peak, trough]."""
    window = df[(df.index >= peak) & (df.index <= trough)]
    if window.empty:
        return pd.Series(dtype=float)
    return (1.0 + window).prod() - 1.0


def top_sectors(
    df: pd.DataFrame, peak: pd.Timestamp, trough: pd.Timestamp, n: int = 3
) -> pd.DataFrame:
    """Return the top-n FF industries by peak-to-trough cumulative return."""
    s = sector_returns_in_window(df, peak, trough)
    if s.empty:
        return pd.DataFrame()
    out = s.sort_values(ascending=False).head(n).reset_index()
    out.columns = ["ff_industry", "cum_return_pct"]
    out["cum_return_pct"] = (out["cum_return_pct"] * 100).round(3)
    out["gics_sector"] = out["ff_industry"].map(FF_TO_GICS)
    out.insert(0, "rank", range(1, len(out) + 1))
    return out


def run(top_n: int = 3) -> None:
    if not DRAWDOWNS_CSV.exists():
        raise FileNotFoundError(
            f"{DRAWDOWNS_CSV} not found - run `cli drawdowns` first."
        )
    drawdowns = pd.read_csv(DRAWDOWNS_CSV, parse_dates=["peak_date", "trough_date"])
    ff = fetch_ff_industries()

    full_rows = []
    leader_rows = []
    for row in drawdowns.itertuples(index=False):
        peak = pd.Timestamp(row.peak_date)
        trough = pd.Timestamp(row.trough_date)
        full = sector_returns_in_window(ff, peak, trough)
        if full.empty:
            log.warning("No FF data in window for drawdown peak=%s", peak.date())
            continue
        for ind, ret in full.items():
            full_rows.append(
                {
                    "peak_date": peak.date(),
                    "trough_date": trough.date(),
                    "ff_industry": ind,
                    "gics_sector": FF_TO_GICS.get(ind, "Other"),
                    "cum_return_pct": round(float(ret) * 100, 3),
                }
            )
        top = top_sectors(ff, peak, trough, n=top_n)
        for trow in top.itertuples(index=False):
            leader_rows.append(
                {
                    "peak_date": peak.date(),
                    "trough_date": trough.date(),
                    "rank": int(trow.rank),
                    "ff_industry": trow.ff_industry,
                    "gics_sector": trow.gics_sector,
                    "cum_return_pct": trow.cum_return_pct,
                }
            )

    pd.DataFrame(full_rows).to_csv(FF_SECTOR_RETURNS_CSV, index=False)
    log.info(
        "Wrote %d FF sector-return rows to %s", len(full_rows), FF_SECTOR_RETURNS_CSV
    )

    leaders = pd.DataFrame(leader_rows)
    leaders.to_csv(FF_SECTOR_LEADERS_CSV, index=False)
    log.info(
        "Wrote %d FF sector-leader rows (%d drawdowns) to %s",
        len(leaders),
        leaders["peak_date"].nunique() if not leaders.empty else 0,
        FF_SECTOR_LEADERS_CSV,
    )
