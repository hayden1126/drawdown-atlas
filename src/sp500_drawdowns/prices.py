"""Stage 3: cached bulk yfinance loader for constituent adjusted-close prices."""
from __future__ import annotations

import logging
import time
from pathlib import Path

import pandas as pd
import yfinance as yf

from .paths import PRICES_CACHE

log = logging.getLogger(__name__)

BATCH_SIZE = 40
MIN_DATE = "1985-01-01"  # earliest reasonable yfinance coverage for most US stocks
RETRIES = 2


def _path_for(ticker: str) -> Path:
    safe = ticker.replace("/", "_")
    return PRICES_CACHE / f"{safe}.parquet"


def have_cached(ticker: str) -> bool:
    return _path_for(ticker).exists()


def load_cached(ticker: str) -> pd.Series | None:
    p = _path_for(ticker)
    if not p.exists():
        return None
    s = pd.read_parquet(p)["close"]
    s.index = pd.to_datetime(s.index)
    s.name = ticker
    return s


def _save(ticker: str, series: pd.Series) -> None:
    if series.empty:
        # write empty marker so we don't keep retrying delisted/no-data tickers
        pd.DataFrame({"close": []}, index=pd.DatetimeIndex([], name="Date")).to_parquet(
            _path_for(ticker)
        )
        return
    series = series.dropna()
    series.name = "close"
    series.to_frame().to_parquet(_path_for(ticker))


def download_missing(tickers: list[str], start: str = MIN_DATE) -> dict[str, pd.Series]:
    """Download tickers not yet cached. Returns dict of ticker -> series."""
    missing = [t for t in tickers if not have_cached(t)]
    log.info("Need to download %d / %d tickers", len(missing), len(tickers))

    out: dict[str, pd.Series] = {}
    for i in range(0, len(missing), BATCH_SIZE):
        batch = missing[i : i + BATCH_SIZE]
        log.info("Downloading batch %d-%d: %s", i, i + len(batch) - 1, batch[:5])
        df = None
        for attempt in range(RETRIES + 1):
            try:
                df = yf.download(
                    batch,
                    start=start,
                    auto_adjust=True,
                    progress=False,
                    group_by="ticker",
                    threads=True,
                )
                break
            except Exception as exc:
                log.warning("Batch download failed (attempt %d): %s", attempt + 1, exc)
                time.sleep(1 + attempt)

        if df is None or df.empty:
            for t in batch:
                _save(t, pd.Series(dtype=float))
            continue

        for t in batch:
            try:
                if len(batch) == 1:
                    sub = df["Close"] if "Close" in df.columns else df.get(("Close",))
                else:
                    sub = df[t]["Close"] if (t, "Close") in df.columns or t in df.columns.levels[0] else None
                if sub is None or sub.empty or sub.dropna().empty:
                    _save(t, pd.Series(dtype=float))
                else:
                    _save(t, sub.dropna())
                    out[t] = sub.dropna()
            except Exception as exc:
                log.warning("Failed to extract %s: %s", t, exc)
                _save(t, pd.Series(dtype=float))

    return out


def get_prices_for(tickers: list[str]) -> dict[str, pd.Series]:
    """Return all available cached series for the given tickers (download if needed)."""
    download_missing(tickers)
    out: dict[str, pd.Series] = {}
    for t in tickers:
        s = load_cached(t)
        if s is not None and not s.empty:
            out[t] = s
    return out
