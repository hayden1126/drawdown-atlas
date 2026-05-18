"""Stage 6: regime taxonomy — Goldman-style classification of each drawdown.

Labels each detected SPX drawdown as one of:
  - structural: regime change / system-level break (banking collapse, stagflation,
    valuation reset, monetary regime shift). Typically deepest and longest.
  - cyclical: business-cycle-driven correction. Late-cycle rate hikes, recessions
    without systemic break.
  - event-driven: exogenous shock (geopolitical, natural, single-policy, market
    microstructure). Typically sharp and short.

Labels are hand-curated from public sources (Goldman "Bear Necessities,"
Invesco bear-market taxonomy, NDR cyclical/secular framework). Rationales
quoted verbatim in the output for auditability.

Joins regimes onto the existing top-5 winners and factors output, producing
regime-conditional sector counts, factor exposures, and a narrative report.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .paths import (
    DRAWDOWNS_CSV,
    FACTORS_CSV,
    REGIME_FACTOR_CSV,
    REGIME_LABELS_CSV,
    REGIME_REPORT_MD,
    REGIME_SECTOR_CSV,
)

log = logging.getLogger(__name__)


REGIME_LABELS: dict[str, tuple[str, str]] = {
    "1928-05-14": ("cyclical", "Mild late-bull correction; pre-Crash noise."),
    "1929-09-16": ("structural", "Great Depression — banking collapse, deflationary spiral."),
    "1955-09-23": ("event-driven", "Eisenhower heart-attack shock; brief and sharp."),
    "1956-08-03": ("cyclical", "1957 recession; tight monetary policy."),
    "1959-08-03": ("cyclical", "1960 recession; Eisenhower-era credit tightening."),
    "1961-12-12": ("event-driven", "Kennedy 'steel crisis' policy shock; 1962 flash bear."),
    "1966-02-09": ("cyclical", "1966 credit crunch; late-cycle rate squeeze."),
    "1967-09-25": ("cyclical", "Brief inflation/rate-anxiety dip."),
    "1968-11-29": ("cyclical", "1969-70 recession."),
    "1973-01-11": ("structural", "Oil shock + stagflation + Nixon shock; macro regime change."),
    "1980-11-28": ("structural", "Volcker disinflation; monetary-policy regime shift."),
    "1983-10-10": ("cyclical", "Post-disinflation rate scare; mild cyclical."),
    "1987-08-25": ("event-driven", "Black Monday; portfolio-insurance microstructure shock."),
    "1989-10-09": ("cyclical", "Late-cycle S&L unease; minor."),
    "1990-07-16": ("event-driven", "Iraq invasion of Kuwait; oil shock + 1990 recession trigger."),
    "1997-10-07": ("event-driven", "Asian Financial Crisis; EM-FX contagion."),
    "1998-07-17": ("event-driven", "Russia default / LTCM blow-up."),
    "1999-07-16": ("cyclical", "Y2K + Fed-tightening cycle pre-2000 bust."),
    "2000-03-24": ("structural", "Dot-com bust; valuation reset and earnings collapse."),
    "2007-10-09": ("structural", "Global Financial Crisis; systemic credit failure."),
    "2015-05-21": ("event-driven", "China devaluation + oil collapse; commodity shock."),
    "2018-01-26": ("event-driven", "Vol-spike / XIV blow-up; microstructure event."),
    "2018-09-20": ("cyclical", "Fed-tightening scare into year-end 2018."),
    "2020-02-19": ("event-driven", "COVID-19 pandemic shock; fastest 30%+ in history."),
    "2022-01-03": ("structural", "Inflation/rate regime reset; end of zero-rate era."),
    "2025-02-19": ("event-driven", "2025 tariff/policy shock."),
}

REGIME_ORDER = ["structural", "cyclical", "event-driven"]


def load_labels() -> pd.DataFrame:
    rows = [
        {"peak_date": k, "regime": v[0], "rationale": v[1]}
        for k, v in REGIME_LABELS.items()
    ]
    df = pd.DataFrame(rows)
    df["peak_date"] = pd.to_datetime(df["peak_date"])
    return df.sort_values("peak_date").reset_index(drop=True)


def _bootstrap_median_ci(
    values: np.ndarray, n_boot: int = 2000, seed: int = 0
) -> tuple[float, float]:
    """Return a 95% bootstrap confidence interval for the median of `values`."""
    if len(values) == 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    samples = rng.choice(values, size=(n_boot, len(values)), replace=True)
    meds = np.median(samples, axis=1)
    return float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))


def run() -> None:
    labels = load_labels()
    labels_out = labels.copy()
    labels_out["peak_date"] = labels_out["peak_date"].dt.date
    labels_out.to_csv(REGIME_LABELS_CSV, index=False)
    log.info("Wrote %d regime labels to %s", len(labels_out), REGIME_LABELS_CSV)

    if DRAWDOWNS_CSV.exists():
        dd = pd.read_csv(DRAWDOWNS_CSV, parse_dates=["peak_date"])
        actual = set(dd["peak_date"].dt.strftime("%Y-%m-%d"))
        labeled = set(REGIME_LABELS.keys())
        unlabeled = actual - labeled
        unknown = labeled - actual
        if unlabeled:
            log.warning("Drawdowns with no regime label: %s", sorted(unlabeled))
        if unknown:
            log.warning("Regime labels with no matching drawdown: %s", sorted(unknown))

    if not FACTORS_CSV.exists():
        log.warning(
            "%s not found — sector and factor breakdowns will be skipped. "
            "Run `cli factors` first.",
            FACTORS_CSV,
        )
        _write_report(labels, sector_counts=None, factor_summary=None)
        return

    per_winner = pd.read_csv(FACTORS_CSV, parse_dates=["peak_date"])
    merged = per_winner.merge(labels[["peak_date", "regime"]], on="peak_date", how="left")
    merged["regime"] = merged["regime"].fillna("unlabeled")

    sector_counts = (
        merged.groupby(["regime", "sector"]).size().reset_index(name="count")
    )
    totals = sector_counts.groupby("regime")["count"].transform("sum")
    sector_counts["pct"] = (sector_counts["count"] / totals * 100).round(1)
    sector_counts = sector_counts.sort_values(["regime", "count"], ascending=[True, False])
    sector_counts.to_csv(REGIME_SECTOR_CSV, index=False)
    log.info("Wrote regime sector counts to %s", REGIME_SECTOR_CSV)

    rows = []
    for regime in REGIME_ORDER + ["unlabeled"]:
        sub = merged[merged["regime"] == regime]
        if sub.empty:
            continue
        beta_lo, beta_hi = _bootstrap_median_ci(sub["pre_dd_beta"].dropna().to_numpy())
        vol_lo, vol_hi = _bootstrap_median_ci(sub["pre_dd_vol"].dropna().to_numpy())
        rows.append(
            {
                "regime": regime,
                "n_drawdowns": int(sub["peak_date"].nunique()),
                "n_winner_episodes": len(sub),
                "winners_median_beta": round(float(sub["pre_dd_beta"].median()), 3),
                "beta_ci95_lo": round(beta_lo, 3),
                "beta_ci95_hi": round(beta_hi, 3),
                "winners_median_vol": round(float(sub["pre_dd_vol"].median()), 3),
                "vol_ci95_lo": round(vol_lo, 3),
                "vol_ci95_hi": round(vol_hi, 3),
                "winners_median_momentum": round(float(sub["pre_dd_momentum"].median()), 3),
                "winners_median_dd_return_pct": round(
                    float(sub["drawdown_return_pct"].median()), 3
                ),
            }
        )
    factor_summary = pd.DataFrame(rows)
    factor_summary.to_csv(REGIME_FACTOR_CSV, index=False)
    log.info("Wrote regime factor summary to %s", REGIME_FACTOR_CSV)

    _write_report(labels, sector_counts=sector_counts, factor_summary=factor_summary)


def _df_to_md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    header = "| " + " | ".join(str(c) for c in cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    rows = [
        "| " + " | ".join(str(v) for v in row) + " |"
        for row in df.itertuples(index=False, name=None)
    ]
    return "\n".join([header, sep, *rows])


def _write_report(
    labels: pd.DataFrame,
    sector_counts: pd.DataFrame | None,
    factor_summary: pd.DataFrame | None,
) -> None:
    lines: list[str] = []
    lines.append("# S&P 500 Drawdown Regime Taxonomy\n")
    lines.append(
        f"Classifies the {len(labels)} detected SPX drawdowns since 1928 into three "
        "categories following Goldman Sachs' bear-market taxonomy:\n"
    )
    lines.append(
        "- **structural** — regime-level break (banking collapse, stagflation, "
        "valuation reset, monetary regime shift). Typically deepest and longest.\n"
        "- **cyclical** — business-cycle correction. Late-cycle rate hikes, "
        "recessions without systemic break.\n"
        "- **event-driven** — exogenous shock (geopolitical, pandemic, "
        "single-policy, microstructure). Typically sharp and short.\n"
    )

    lines.append("## Episode labels\n")
    label_table = labels.copy()
    label_table["peak_date"] = label_table["peak_date"].dt.date
    lines.append(_df_to_md(label_table))
    lines.append("")

    counts = labels["regime"].value_counts().reindex(REGIME_ORDER).fillna(0).astype(int)
    lines.append("## Regime frequency\n")
    freq = pd.DataFrame({"regime": counts.index, "n_drawdowns": counts.values})
    lines.append(_df_to_md(freq))
    lines.append("")

    if factor_summary is not None and not factor_summary.empty:
        lines.append("## Factor exposures by regime\n")
        lines.append(
            "Median pre-drawdown beta / vol / momentum of the top-5 winners, "
            "grouped by regime. 95% confidence intervals via 2,000-sample "
            "bootstrap of the median.\n"
        )
        slim = factor_summary[
            [
                "regime",
                "n_drawdowns",
                "n_winner_episodes",
                "winners_median_beta",
                "beta_ci95_lo",
                "beta_ci95_hi",
                "winners_median_vol",
                "vol_ci95_lo",
                "vol_ci95_hi",
                "winners_median_momentum",
                "winners_median_dd_return_pct",
            ]
        ]
        lines.append(_df_to_md(slim))
        lines.append("")

    if sector_counts is not None and not sector_counts.empty:
        lines.append("## Sector leadership by regime\n")
        lines.append(
            "Top-5 winner sector frequency, broken out by regime. "
            "Comparing across columns shows whether winners look the same in "
            "every kind of selloff, or whether leadership rotates with regime.\n"
        )
        pivot = (
            sector_counts.pivot(index="sector", columns="regime", values="count")
            .fillna(0)
            .astype(int)
        )
        pivot = pivot.reindex(columns=[c for c in REGIME_ORDER if c in pivot.columns])
        pivot["total"] = pivot.sum(axis=1)
        pivot = pivot.sort_values("total", ascending=False)
        pivot = pivot.reset_index()
        lines.append(_df_to_md(pivot))
        lines.append("")

    lines.append("## Limitations\n")
    lines.append(
        "- **Regime labels are hand-curated, not algorithmic.** They follow "
        "published taxonomies (Goldman, Invesco, NDR) but every episode close to "
        "a category boundary involves judgment. Rationales are quoted in "
        "`regime_labels.csv` for auditability.\n"
        f"- **Small n.** {len(labels)} episodes across three regimes means "
        "~7-10 per cell. Bootstrap CIs treat winner-episodes as the unit, which "
        "inflates effective sample size but does not fix the underlying scarcity "
        "of independent drawdowns.\n"
        "- **GICS classification of constituents is current, not point-in-time.** "
        "Sector tilts pre-1999 are approximations.\n"
        "- **No macro-covariate validation.** A richer version would correlate "
        "regimes with inflation, credit spreads, and the yield curve at each "
        "peak - out of scope here.\n"
    )

    REGIME_REPORT_MD.write_text("\n".join(lines))
    log.info("Wrote regime report to %s", REGIME_REPORT_MD)
