"""Stage 5: render top-5 results as a Markdown report."""
from __future__ import annotations

import logging

import pandas as pd

from . import constituents as cons
from .paths import DRAWDOWNS_CSV, OUTPUT, REPORT_MD, TOP5_CSV

log = logging.getLogger(__name__)

CONFIDENCE_NOTE = {
    "high": "",
    "medium": " _(membership reconstruction has medium confidence; Wikipedia's change log gets patchy pre-2000.)_",
    "low": " _(membership reconstruction has **low** confidence — the change log doesn't reach this date; results may include current-set bias.)_",
}


def _security_lookup(current: pd.DataFrame, changes: pd.DataFrame) -> dict[str, str]:
    names = dict(zip(current["ticker"], current["security"]))
    # Fill in names for tickers no longer in the current list using the changes log
    for col_t, col_s in (("added_ticker", "added_security"), ("removed_ticker", "removed_security")):
        if col_t in changes.columns and col_s in changes.columns:
            for t, s in zip(changes[col_t], changes[col_s]):
                if isinstance(t, str) and t and t not in names and isinstance(s, str) and s:
                    names[t] = s
    return names


def run() -> str:
    drawdowns = pd.read_csv(DRAWDOWNS_CSV, parse_dates=["peak_date", "trough_date"])
    top5 = pd.read_csv(TOP5_CSV, parse_dates=["peak_date", "trough_date"])
    current, changes = cons.fetch_wikipedia_tables()
    names = _security_lookup(current, changes)

    lines: list[str] = []
    lines.append("# S&P 500 Drawdowns & Best Constituent Performers")
    lines.append("")
    lines.append(
        "Each section below is a peak-to-trough drawdown of the S&P 500 of "
        "at least 10%, with the five constituents that delivered the best "
        "total return (yfinance adjusted close) over the same peak→trough window. "
        "Universe is the point-in-time S&P 500 membership as of the peak date, "
        "reconstructed from Wikipedia's change log."
    )
    lines.append("")
    lines.append(
        "**Caveats:** Membership reconstruction degrades pre-2000 (Wikipedia's "
        "\"Selected changes\" table doesn't fully cover earlier decades). Tickers "
        "with no yfinance history over the relevant window are silently skipped."
    )
    lines.append("")

    grouped = top5.groupby(["peak_date", "trough_date"])

    for _, dd in drawdowns.iterrows():
        peak, trough = dd["peak_date"], dd["trough_date"]
        try:
            grp = grouped.get_group((peak, trough))
        except KeyError:
            grp = pd.DataFrame()
        conf = grp["membership_confidence"].iloc[0] if not grp.empty else "low"
        note = CONFIDENCE_NOTE.get(conf, "")

        lines.append(
            f"## {peak.date()} → {trough.date()}  (SPX {dd['max_dd_pct']}%){note}"
        )
        lines.append("")
        if grp.empty:
            lines.append("_No constituents with sufficient price data._")
            lines.append("")
            continue
        lines.append("| Rank | Ticker | Company | Return |")
        lines.append("|---:|:--|:--|---:|")
        for _, r in grp.iterrows():
            t = r["ticker"]
            name = names.get(t, "—")
            lines.append(
                f"| {int(r['rank'])} | {t} | {name} | {r['return_pct']:+.2f}% |"
            )
        lines.append("")

    text = "\n".join(lines)
    REPORT_MD.write_text(text)
    log.info("Wrote report to %s", REPORT_MD)
    return text


def run_year(year: int) -> str:
    """Render a year-scoped within-window drawdown report."""
    in_dd = OUTPUT / f"drawdowns_{year}.csv"
    in_top = OUTPUT / f"top5_per_drawdown_{year}.csv"
    drawdowns = pd.read_csv(in_dd, parse_dates=["peak_date", "trough_date"])
    top5 = (
        pd.read_csv(in_top, parse_dates=["peak_date", "trough_date"])
        if in_top.exists()
        else pd.DataFrame()
    )
    current, changes = cons.fetch_wikipedia_tables()
    names = _security_lookup(current, changes)

    lines: list[str] = []
    lines.append(f"# S&P 500 Drawdowns Within {year} — Best Constituent Performers")
    lines.append("")
    lines.append(
        f"Each section is a peak-to-trough leg of the S&P 500 of at least 10% "
        f"whose trough falls within {year}. Unlike the main report, the running "
        "peak resets after each recovery, so a year can contain multiple distinct "
        "legs. Recovery to the prior all-time high is **not** required."
    )
    lines.append("")
    if drawdowns.empty:
        lines.append(f"_No S&P 500 drawdowns of ≥10% recorded within {year}._")
        text = "\n".join(lines) + "\n"
        out = OUTPUT / f"report_{year}.md"
        out.write_text(text)
        log.info("Wrote report to %s", out)
        return text

    grouped = (
        top5.groupby(["peak_date", "trough_date"]) if not top5.empty else None
    )
    for _, dd in drawdowns.iterrows():
        peak, trough = dd["peak_date"], dd["trough_date"]
        if grouped is not None:
            try:
                grp = grouped.get_group((peak, trough))
            except KeyError:
                grp = pd.DataFrame()
        else:
            grp = pd.DataFrame()
        conf = grp["membership_confidence"].iloc[0] if not grp.empty else "low"
        note = CONFIDENCE_NOTE.get(conf, "")

        lines.append(
            f"## {peak.date()} → {trough.date()}  (SPX {dd['max_dd_pct']}%){note}"
        )
        lines.append("")
        if grp.empty:
            lines.append("_No constituents with sufficient price data._")
            lines.append("")
            continue
        lines.append("| Rank | Ticker | Company | Return |")
        lines.append("|---:|:--|:--|---:|")
        for _, r in grp.iterrows():
            t = r["ticker"]
            name = names.get(t, "—")
            lines.append(
                f"| {int(r['rank'])} | {t} | {name} | {r['return_pct']:+.2f}% |"
            )
        lines.append("")

    text = "\n".join(lines)
    out = OUTPUT / f"report_{year}.md"
    out.write_text(text)
    log.info("Wrote report to %s", out)
    return text
