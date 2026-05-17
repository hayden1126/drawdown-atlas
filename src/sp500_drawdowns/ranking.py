"""Stage 4: per-drawdown peak->trough returns, top-5 selection."""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from . import constituents as cons
from . import prices as px_mod
from .paths import DRAWDOWNS_CSV, OUTPUT, TOP5_CSV

log = logging.getLogger(__name__)

TOLERANCE_DAYS = 5  # how far we'll look for a non-NaN price near peak/trough


def _price_near(series: pd.Series, target: pd.Timestamp, direction: str) -> tuple[pd.Timestamp, float] | None:
    """Find a non-null close near ``target``.

    direction='backward': use the most recent close on or before ``target`` (for peak).
    direction='forward': use the earliest close on or after ``target`` (for trough).
    Returns None if no observation within TOLERANCE_DAYS.
    """
    if series.empty:
        return None
    idx = series.index
    if direction == "backward":
        mask = idx <= target
        candidates = series[mask]
        if candidates.empty:
            return None
        ts = candidates.index[-1]
        if (target - ts).days > TOLERANCE_DAYS:
            return None
        return ts, float(candidates.iloc[-1])
    else:
        mask = idx >= target
        candidates = series[mask]
        if candidates.empty:
            return None
        ts = candidates.index[0]
        if (ts - target).days > TOLERANCE_DAYS:
            return None
        return ts, float(candidates.iloc[0])


def rank_drawdown(
    peak_date: pd.Timestamp,
    trough_date: pd.Timestamp,
    universe: set[str],
    price_data: dict[str, pd.Series],
    top_n: int = 5,
) -> pd.DataFrame:
    rows = []
    for ticker in sorted(universe):
        s = price_data.get(ticker)
        if s is None or s.empty:
            continue
        p = _price_near(s, peak_date, "backward")
        t = _price_near(s, trough_date, "forward")
        if p is None or t is None:
            continue
        p_ts, p_px = p
        t_ts, t_px = t
        if p_px <= 0 or t_ts <= p_ts:
            continue
        ret = t_px / p_px - 1.0
        rows.append(
            {
                "ticker": ticker,
                "return_pct": round(ret * 100, 3),
                "peak_px": p_px,
                "trough_px": t_px,
                "peak_obs_date": p_ts.date(),
                "trough_obs_date": t_ts.date(),
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.sort_values("return_pct", ascending=False).head(top_n).reset_index(drop=True)
    df.insert(0, "rank", df.index + 1)
    return df


def rank_for_drawdowns(
    drawdowns: pd.DataFrame, top_n: int = 5
) -> pd.DataFrame:
    """Rank top-N constituent performers for each row of ``drawdowns``.

    ``drawdowns`` must have columns ``peak_date``, ``trough_date``, ``max_dd_pct``
    (as produced by ``drawdowns.episodes_to_dataframe``).
    """
    current, changes = cons.fetch_wikipedia_tables()

    membership_by_peak: dict[pd.Timestamp, set[str]] = {}
    universe_union: set[str] = set()
    for _, row in drawdowns.iterrows():
        peak = pd.Timestamp(row["peak_date"])
        mem = cons.membership_at(peak, current, changes)
        membership_by_peak[peak] = mem
        universe_union |= mem

    log.info("Universe size across these drawdowns: %d tickers", len(universe_union))
    price_data = px_mod.get_prices_for(sorted(universe_union))
    log.info("Loaded price data for %d / %d tickers", len(price_data), len(universe_union))

    all_rows = []
    for _, row in drawdowns.iterrows():
        peak = pd.Timestamp(row["peak_date"])
        trough = pd.Timestamp(row["trough_date"])
        confidence = cons.membership_confidence(peak, changes)
        mem = membership_by_peak[peak]
        top = rank_drawdown(peak, trough, mem, price_data, top_n=top_n)
        if top.empty:
            log.warning("No ranked tickers for drawdown peak=%s", peak.date())
            continue
        top.insert(0, "peak_date", peak.date())
        top.insert(1, "trough_date", trough.date())
        top["sp500_drawdown_pct"] = row["max_dd_pct"]
        top["membership_confidence"] = confidence
        all_rows.append(top)

    if not all_rows:
        return pd.DataFrame()
    return pd.concat(all_rows, ignore_index=True)


def run() -> pd.DataFrame:
    drawdowns = pd.read_csv(DRAWDOWNS_CSV, parse_dates=["peak_date", "trough_date"])
    current, changes = cons.fetch_wikipedia_tables()

    # First pass: figure out the union of all tickers we'll ever need
    membership_by_peak: dict[pd.Timestamp, set[str]] = {}
    universe_union: set[str] = set()
    for _, row in drawdowns.iterrows():
        peak = row["peak_date"]
        mem = cons.membership_at(peak, current, changes)
        membership_by_peak[peak] = mem
        universe_union |= mem

    log.info("Total unique tickers across all drawdowns: %d", len(universe_union))
    price_data = px_mod.get_prices_for(sorted(universe_union))
    log.info("Loaded price data for %d / %d tickers", len(price_data), len(universe_union))

    all_rows = []
    for _, row in drawdowns.iterrows():
        peak = row["peak_date"]
        trough = row["trough_date"]
        confidence = cons.membership_confidence(peak, changes)
        mem = membership_by_peak[peak]
        top = rank_drawdown(peak, trough, mem, price_data)
        if top.empty:
            log.warning("No ranked tickers for drawdown peak=%s", peak.date())
            continue
        top.insert(0, "peak_date", peak.date())
        top.insert(1, "trough_date", trough.date())
        top["sp500_drawdown_pct"] = row["max_dd_pct"]
        top["membership_confidence"] = confidence
        all_rows.append(top)

    if not all_rows:
        log.warning("No rankings produced")
        out = pd.DataFrame()
    else:
        out = pd.concat(all_rows, ignore_index=True)
    out.to_csv(TOP5_CSV, index=False)
    log.info("Wrote top-5 rankings to %s", TOP5_CSV)
    return out


def run_year(year: int, top_n: int = 5) -> pd.DataFrame:
    """Rank top-N performers for within-year drawdowns produced by drawdowns.run_year."""
    in_csv = OUTPUT / f"drawdowns_{year}.csv"
    drawdowns = pd.read_csv(in_csv, parse_dates=["peak_date", "trough_date"])
    out = rank_for_drawdowns(drawdowns, top_n=top_n)
    out_csv = OUTPUT / f"top5_per_drawdown_{year}.csv"
    out.to_csv(out_csv, index=False)
    log.info("Wrote %d ranking rows to %s", len(out), out_csv)
    return out
