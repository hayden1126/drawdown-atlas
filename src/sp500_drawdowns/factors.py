"""Stage 5: defensive-factor aggregation over top-5 winners.

Computes pre-drawdown price-based factor proxies (beta, vol, 12-1 momentum) for
each top-5 winner and for the full point-in-time SPX universe baseline, joins
sector/industry from yfinance with parquet caching, and emits four artifacts
(per-winner table, winners-vs-universe summary, sector counts, narrative
report).

Honest scope: factor proxies are price-based only (no fundamentals); sector
classifications use current GICS, not point-in-time; n is small for inference.
This stage is a descriptive atlas, not a hypothesis test.
"""
from __future__ import annotations

import logging
from typing import Iterable

import numpy as np
import pandas as pd

from . import constituents as cons
from . import prices as px_mod
from .paths import (
    FACTORS_CSV,
    FACTORS_REPORT_MD,
    FACTORS_SECTOR_CSV,
    FACTORS_SUMMARY_CSV,
    SECTOR_MAP_CACHE,
    SPX_CACHE,
    TOP5_CSV,
)

log = logging.getLogger(__name__)

LOOKBACK_DAYS = 252
MOMENTUM_SKIP_DAYS = 21
TRADING_DAYS = 252

SECTOR_FALLBACK: dict[str, tuple[str, str]] = {
    "ED": ("Utilities", "Utilities—Regulated Electric"),
    "D": ("Utilities", "Utilities—Diversified"),
    "EIX": ("Utilities", "Utilities—Regulated Electric"),
    "XEL": ("Utilities", "Utilities—Regulated Electric"),
    "DTE": ("Utilities", "Utilities—Regulated Electric"),
    "OKE": ("Energy", "Oil & Gas Midstream"),
    "EOG": ("Energy", "Oil & Gas E&P"),
    "DOC": ("Real Estate", "REIT—Healthcare Facilities"),
    "NBR": ("Energy", "Oil & Gas Drilling"),
    "NEM": ("Basic Materials", "Gold"),
    "J": ("Industrials", "Engineering & Construction"),
    "XRAY": ("Healthcare", "Medical Instruments & Supplies"),
    "PFE": ("Healthcare", "Drug Manufacturers—General"),
    "ADBE": ("Technology", "Software—Infrastructure"),
}


def _log_returns(s: pd.Series) -> pd.Series:
    return np.log(s / s.shift(1)).dropna()


def pre_drawdown_factors(
    ticker_series: pd.Series,
    spx_series: pd.Series,
    peak_date: pd.Timestamp,
    lookback: int = LOOKBACK_DAYS,
) -> dict[str, float] | None:
    """Return {beta, vol, momentum} computed over [peak - lookback, peak].

    Beta is OLS slope of ticker daily log-returns on SPX daily log-returns over
    the lookback window. Vol is annualized stdev of ticker daily log-returns.
    Momentum is the 12-1 return: ticker price at (peak - 21d) / ticker price at
    (peak - lookback) - 1.

    Returns None if there isn't enough overlapping data in the window.
    """
    end = pd.Timestamp(peak_date)
    start = end - pd.Timedelta(days=int(lookback * 1.5))

    t = ticker_series[(ticker_series.index >= start) & (ticker_series.index <= end)]
    m = spx_series[(spx_series.index >= start) & (spx_series.index <= end)]
    if t.empty or m.empty:
        return None

    t_ret = _log_returns(t)
    m_ret = _log_returns(m)
    aligned = pd.concat([t_ret, m_ret], axis=1, keys=["t", "m"]).dropna()
    aligned = aligned.tail(lookback)
    if len(aligned) < 60:
        return None

    var_m = aligned["m"].var()
    if var_m <= 0:
        return None
    beta = aligned[["t", "m"]].cov().iloc[0, 1] / var_m
    vol = float(aligned["t"].std(ddof=1) * np.sqrt(TRADING_DAYS))

    if len(t) >= lookback:
        p_end = t.iloc[-MOMENTUM_SKIP_DAYS]
        p_start = t.iloc[-lookback]
        momentum = float(p_end / p_start - 1.0) if p_start > 0 else float("nan")
    else:
        momentum = float("nan")

    return {
        "pre_dd_beta": round(float(beta), 4),
        "pre_dd_vol": round(vol, 4),
        "pre_dd_momentum": round(momentum, 4) if momentum == momentum else float("nan"),
    }


def _load_sector_cache() -> dict[str, tuple[str, str]]:
    if not SECTOR_MAP_CACHE.exists():
        return {}
    df = pd.read_parquet(SECTOR_MAP_CACHE)
    return {row.ticker: (row.sector, row.industry) for row in df.itertuples()}


def _save_sector_cache(mapping: dict[str, tuple[str, str]]) -> None:
    rows = [
        {"ticker": t, "sector": s, "industry": i} for t, (s, i) in sorted(mapping.items())
    ]
    pd.DataFrame(rows).to_parquet(SECTOR_MAP_CACHE)


def fetch_sectors(tickers: Iterable[str]) -> dict[str, tuple[str, str]]:
    """Resolve sector/industry for each ticker via yfinance, with cache + fallback."""
    import yfinance as yf

    cache = _load_sector_cache()
    todo = [t for t in tickers if t not in cache]
    log.info("Sector lookup: %d cached, %d to fetch", len(cache), len(todo))
    for t in todo:
        sector, industry = "Unknown", "Unknown"
        try:
            info = yf.Ticker(t).info
            sector = info.get("sector") or "Unknown"
            industry = info.get("industry") or "Unknown"
        except Exception as exc:
            log.debug("yfinance sector lookup failed for %s: %s", t, exc)
        if sector == "Unknown" and t in SECTOR_FALLBACK:
            sector, industry = SECTOR_FALLBACK[t]
        cache[t] = (sector, industry)
    if todo:
        _save_sector_cache(cache)
    return cache


def _load_spx() -> pd.Series:
    df = pd.read_parquet(SPX_CACHE)
    col = "close" if "close" in df.columns else df.columns[0]
    s = df[col]
    s.index = pd.to_datetime(s.index)
    s.name = "SPX"
    return s.dropna()


def _baseline_for_drawdown(
    peak: pd.Timestamp,
    universe: set[str],
    price_data: dict[str, pd.Series],
    spx: pd.Series,
) -> dict[str, float]:
    betas, vols, moms = [], [], []
    for t in universe:
        s = price_data.get(t)
        if s is None or s.empty:
            continue
        f = pre_drawdown_factors(s, spx, peak)
        if f is None:
            continue
        betas.append(f["pre_dd_beta"])
        vols.append(f["pre_dd_vol"])
        if f["pre_dd_momentum"] == f["pre_dd_momentum"]:
            moms.append(f["pre_dd_momentum"])
    return {
        "universe_n": len(betas),
        "universe_median_beta": float(np.median(betas)) if betas else float("nan"),
        "universe_median_vol": float(np.median(vols)) if vols else float("nan"),
        "universe_median_momentum": float(np.median(moms)) if moms else float("nan"),
    }


def run() -> None:
    if not TOP5_CSV.exists():
        raise FileNotFoundError(
            f"{TOP5_CSV} not found — run stages 1-4 first (`cli rank`)."
        )
    top5 = pd.read_csv(TOP5_CSV, parse_dates=["peak_date", "trough_date"])
    log.info(
        "Loaded %d winner rows across %d drawdowns",
        len(top5),
        top5["peak_date"].nunique(),
    )

    spx = _load_spx()
    current, changes = cons.fetch_wikipedia_tables()

    membership_by_peak: dict[pd.Timestamp, set[str]] = {}
    union: set[str] = set(top5["ticker"].unique())
    for peak in top5["peak_date"].unique():
        peak_ts = pd.Timestamp(peak)
        mem = cons.membership_at(peak_ts, current, changes)
        membership_by_peak[peak_ts] = mem
        union |= mem

    log.info("Loading prices for %d tickers (winners + universe union)", len(union))
    price_data = px_mod.get_prices_for(sorted(union))

    winners = sorted(top5["ticker"].unique())
    sector_map = fetch_sectors(winners)

    per_winner_rows = []
    for row in top5.itertuples(index=False):
        s = price_data.get(row.ticker)
        if s is None or s.empty:
            continue
        f = pre_drawdown_factors(s, spx, pd.Timestamp(row.peak_date))
        sector, industry = sector_map.get(row.ticker, ("Unknown", "Unknown"))
        per_winner_rows.append(
            {
                "peak_date": pd.Timestamp(row.peak_date).date(),
                "trough_date": pd.Timestamp(row.trough_date).date(),
                "ticker": row.ticker,
                "sector": sector,
                "industry": industry,
                "pre_dd_beta": f["pre_dd_beta"] if f else float("nan"),
                "pre_dd_vol": f["pre_dd_vol"] if f else float("nan"),
                "pre_dd_momentum": f["pre_dd_momentum"] if f else float("nan"),
                "drawdown_return_pct": row.return_pct,
            }
        )
    per_winner = pd.DataFrame(per_winner_rows)
    per_winner.to_csv(FACTORS_CSV, index=False)
    log.info("Wrote %d rows to %s", len(per_winner), FACTORS_CSV)

    summary_rows = []
    for peak in sorted(top5["peak_date"].unique()):
        peak_ts = pd.Timestamp(peak)
        wsub = per_winner[per_winner["peak_date"] == peak_ts.date()]
        baseline = _baseline_for_drawdown(
            peak_ts, membership_by_peak[peak_ts], price_data, spx
        )
        summary_rows.append(
            {
                "peak_date": peak_ts.date(),
                "winners_n": len(wsub),
                "winners_median_beta": float(wsub["pre_dd_beta"].median())
                if not wsub.empty
                else float("nan"),
                "winners_median_vol": float(wsub["pre_dd_vol"].median())
                if not wsub.empty
                else float("nan"),
                "winners_median_momentum": float(wsub["pre_dd_momentum"].median())
                if not wsub.empty
                else float("nan"),
                **baseline,
            }
        )
    summary = pd.DataFrame(summary_rows)
    overall = {
        "peak_date": "OVERALL",
        "winners_n": len(per_winner),
        "winners_median_beta": float(per_winner["pre_dd_beta"].median()),
        "winners_median_vol": float(per_winner["pre_dd_vol"].median()),
        "winners_median_momentum": float(per_winner["pre_dd_momentum"].median()),
        "universe_n": int(summary["universe_n"].sum()),
        "universe_median_beta": float(summary["universe_median_beta"].median()),
        "universe_median_vol": float(summary["universe_median_vol"].median()),
        "universe_median_momentum": float(summary["universe_median_momentum"].median()),
    }
    summary = pd.concat([summary, pd.DataFrame([overall])], ignore_index=True)
    summary.to_csv(FACTORS_SUMMARY_CSV, index=False)
    log.info("Wrote summary to %s", FACTORS_SUMMARY_CSV)

    sector_counts = (
        per_winner.groupby("sector").size().sort_values(ascending=False).reset_index(name="count")
    )
    sector_counts["pct"] = (sector_counts["count"] / len(per_winner) * 100).round(1)
    sector_counts.to_csv(FACTORS_SECTOR_CSV, index=False)
    log.info("Wrote sector counts to %s", FACTORS_SECTOR_CSV)

    _write_report(per_winner, summary, sector_counts, overall)


def _df_to_md(df: pd.DataFrame) -> str:
    """Minimal markdown-table renderer (avoids the tabulate optional dependency)."""
    cols = list(df.columns)
    header = "| " + " | ".join(str(c) for c in cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    rows = ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False, name=None)]
    return "\n".join([header, sep, *rows])


def _write_report(
    per_winner: pd.DataFrame,
    summary: pd.DataFrame,
    sector_counts: pd.DataFrame,
    overall: dict,
) -> None:
    lines = []
    lines.append("# Defensive-Factor Aggregation of S&P 500 Drawdown Winners\n")
    lines.append(
        f"Aggregates the top-5 best-performing point-in-time S&P 500 constituents "
        f"across {per_winner['peak_date'].nunique()} drawdowns since 1928 "
        f"(n={len(per_winner)} winner-episodes).\n"
    )

    lines.append("## Sector frequency among winners\n")
    lines.append(_df_to_md(sector_counts))
    lines.append("")

    lines.append("## Factor exposures: winners vs full point-in-time SPX universe\n")
    lines.append(
        "Pre-drawdown factor proxies computed over the 252 trading days ending on "
        "the SPX peak date. Beta vs SPX daily log-returns; vol annualized; "
        "momentum = 12-1 (skip last ~1 month).\n"
    )
    overall_table = pd.DataFrame(
        [
            {
                "metric": "Median beta",
                "winners": round(overall["winners_median_beta"], 3),
                "universe": round(overall["universe_median_beta"], 3),
            },
            {
                "metric": "Median annualized vol",
                "winners": round(overall["winners_median_vol"], 3),
                "universe": round(overall["universe_median_vol"], 3),
            },
            {
                "metric": "Median 12-1 momentum",
                "winners": round(overall["winners_median_momentum"], 3),
                "universe": round(overall["universe_median_momentum"], 3),
            },
        ]
    )
    lines.append(_df_to_md(overall_table))
    lines.append("")

    lines.append("## Per-drawdown winners vs universe\n")
    sm = summary[summary["peak_date"] != "OVERALL"].copy()
    sm = sm[
        [
            "peak_date",
            "winners_median_beta",
            "universe_median_beta",
            "winners_median_vol",
            "universe_median_vol",
        ]
    ].round(3)
    lines.append(_df_to_md(sm))
    lines.append("")

    lines.append("## Limitations\n")
    lines.append(
        "- **Factor proxies are price-based, not fundamentals.** No profitability, "
        "leverage, or accruals — those require Compustat (paid). Treat beta/vol as "
        "noisy proxies for the canonical defensive-equity factors.\n"
        "- **Sector classification uses _current_ GICS, not point-in-time.** A "
        "ticker classified today as Utilities may have been classified differently "
        "decades ago; we don't attempt historical GICS reconstruction.\n"
        f"- **Small sample.** n={len(per_winner)} winner-episodes across "
        f"{per_winner['peak_date'].nunique()} drawdowns is too small for formal "
        "hypothesis testing. This is a descriptive atlas, not an inferential study.\n"
        "- **No look-ahead correction within the drawdown.** Factor proxies are "
        "computed strictly _before_ the peak — but the _identity_ of the top-5 is "
        "still observed ex-post.\n"
    )

    FACTORS_REPORT_MD.write_text("\n".join(lines))
    log.info("Wrote report to %s", FACTORS_REPORT_MD)
