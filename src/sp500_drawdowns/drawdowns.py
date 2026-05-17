"""Stage 1: detect SPX peak-to-trough drawdowns >= 10%.

Two modes:
- ``find_drawdowns``: classic, all-time-high based. An episode opens after a
  new ATH is broken to the downside and closes only when the ATH is reclaimed.
  Produces a small number of "mega" episodes (e.g. 2000-2002, 2007-2009).
- ``find_drawdowns_in_window``: window-scoped with reset-on-recovery. The
  running peak is initialized at the start of the slice (plus optional
  lookback) rather than to the all-time high, so each local peak→trough→
  recovery leg becomes its own episode. Used for calendar-year analysis.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable

import pandas as pd
import yfinance as yf

from .paths import DRAWDOWNS_CSV, OUTPUT, SPX_CACHE

log = logging.getLogger(__name__)

DRAWDOWN_THRESHOLD = -0.10  # 10% decline


@dataclass(frozen=True)
class DrawdownEpisode:
    peak_date: pd.Timestamp
    trough_date: pd.Timestamp
    recovery_date: pd.Timestamp | None
    peak_close: float
    trough_close: float
    max_dd: float


def load_spx(force: bool = False) -> pd.Series:
    """Adjusted close for ^GSPC, full available history. Cached."""
    if SPX_CACHE.exists() and not force:
        s = pd.read_parquet(SPX_CACHE)["close"]
        s.index = pd.to_datetime(s.index)
        return s
    log.info("Downloading ^GSPC full history from yfinance...")
    df = yf.download("^GSPC", period="max", auto_adjust=True, progress=False)
    if df.empty:
        raise RuntimeError("yfinance returned no data for ^GSPC")
    close = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close.name = "close"
    close.index = pd.to_datetime(close.index)
    close.to_frame().to_parquet(SPX_CACHE)
    return close


def _walk_legs(
    values, dates, threshold: float, initial_peak_idx: int = 0
) -> list[DrawdownEpisode]:
    """Walk a price series and emit peak→trough→recovery episodes.

    A "peak" is the running max from ``initial_peak_idx`` onward. When price
    recovers to that running max, the leg closes and the running max resets to
    the recovery price (i.e. each episode is local to its starting peak).
    Episodes still in progress at series end are emitted with recovery=None.
    """
    if len(values) <= initial_peak_idx + 1:
        return []
    episodes: list[DrawdownEpisode] = []
    peak_idx = initial_peak_idx
    peak_val = float(values[peak_idx])
    in_drawdown = False
    trough_idx = peak_idx
    trough_val = peak_val

    for i in range(peak_idx + 1, len(values)):
        v = float(values[i])
        if not in_drawdown:
            if v >= peak_val:
                peak_idx = i
                peak_val = v
            else:
                in_drawdown = True
                trough_idx = i
                trough_val = v
        else:
            if v < trough_val:
                trough_idx = i
                trough_val = v
            if v >= peak_val:
                max_dd = trough_val / peak_val - 1.0
                if max_dd <= threshold:
                    episodes.append(
                        DrawdownEpisode(
                            peak_date=dates[peak_idx],
                            trough_date=dates[trough_idx],
                            recovery_date=dates[i],
                            peak_close=peak_val,
                            trough_close=trough_val,
                            max_dd=max_dd,
                        )
                    )
                in_drawdown = False
                peak_idx = i
                peak_val = v

    if in_drawdown:
        max_dd = trough_val / peak_val - 1.0
        if max_dd <= threshold:
            episodes.append(
                DrawdownEpisode(
                    peak_date=dates[peak_idx],
                    trough_date=dates[trough_idx],
                    recovery_date=None,
                    peak_close=peak_val,
                    trough_close=trough_val,
                    max_dd=max_dd,
                )
            )
    return episodes


def find_drawdowns(
    close: pd.Series, threshold: float = DRAWDOWN_THRESHOLD
) -> list[DrawdownEpisode]:
    """Classic peak-to-trough drawdowns over the full series.

    Each episode is opened against the all-time high (i.e. running max from
    the start of the series). This is the original mode used by the main
    pipeline.
    """
    if close.empty:
        return []
    close = close.sort_index().dropna()
    return _walk_legs(close.to_numpy(dtype=float), close.index, threshold, 0)


def find_drawdowns_in_window(
    close: pd.Series,
    start: str | pd.Timestamp,
    end: str | pd.Timestamp,
    threshold: float = DRAWDOWN_THRESHOLD,
    lookback: str | pd.Timedelta = "365D",
) -> list[DrawdownEpisode]:
    """Local peak-to-trough legs whose trough falls within [start, end].

    The running peak resets after every recovery, so each leg is local to
    its own peak (rather than the all-time high). A ``lookback`` is prepended
    to the slice so a leg peaking shortly before ``start`` can still be
    detected.
    """
    if close.empty:
        return []
    close = close.sort_index().dropna()
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    lookback_td = pd.Timedelta(lookback) if not isinstance(lookback, pd.Timedelta) else lookback

    slice_start = start_ts - lookback_td
    slice_end = end_ts
    sliced = close.loc[slice_start:slice_end]
    if sliced.empty:
        return []

    episodes = _walk_legs(sliced.to_numpy(dtype=float), sliced.index, threshold, 0)
    # Keep episodes whose trough falls within the window
    return [e for e in episodes if start_ts <= e.trough_date <= end_ts]


def episodes_to_dataframe(episodes: Iterable[DrawdownEpisode]) -> pd.DataFrame:
    rows = [
        {
            "peak_date": e.peak_date.date(),
            "trough_date": e.trough_date.date(),
            "recovery_date": e.recovery_date.date() if e.recovery_date is not None else None,
            "peak_close": e.peak_close,
            "trough_close": e.trough_close,
            "max_dd_pct": round(e.max_dd * 100, 3),
        }
        for e in episodes
    ]
    return pd.DataFrame(rows)


def run(force_download: bool = False) -> pd.DataFrame:
    close = load_spx(force=force_download)
    episodes = find_drawdowns(close)
    df = episodes_to_dataframe(episodes)
    df.to_csv(DRAWDOWNS_CSV, index=False)
    log.info("Wrote %d drawdowns >=10%% to %s", len(df), DRAWDOWNS_CSV)
    return df


def run_year(
    year: int, threshold: float = DRAWDOWN_THRESHOLD, force_download: bool = False
) -> pd.DataFrame:
    """Detect within-year drawdown legs and write data/output/drawdowns_<year>.csv."""
    close = load_spx(force=force_download)
    episodes = find_drawdowns_in_window(
        close, f"{year}-01-01", f"{year}-12-31", threshold=threshold
    )
    df = episodes_to_dataframe(episodes)
    out_path = OUTPUT / f"drawdowns_{year}.csv"
    df.to_csv(out_path, index=False)
    log.info("Wrote %d within-%d drawdowns to %s", len(df), year, out_path)
    return df
