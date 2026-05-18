# S&P 500 Drawdowns — Output Format Reference

This bundle contains the outputs of the seven-stage `drawdown-atlas` pipeline:
human-readable Markdown reports and machine-readable CSVs. Everything is
reproducible from the source pipeline at
<https://github.com/hayden1126/drawdown-atlas>.

## What "drawdown" means here

A **drawdown** is a peak-to-trough decline in the S&P 500 (`^GSPC`,
adjusted close from yfinance). We report drawdowns with magnitude **≥ 10%**.

Two definitions are used across the files:

| Mode | Used in | Rule |
|---|---|---|
| **All-time-high (ATH)** | `drawdowns.csv`, `top5_per_drawdown.csv`, `report.md`, all Stage 5/6 outputs | A drawdown opens after each new ATH and closes only when the index reclaims that ATH. Produces a small number of large "mega" episodes (e.g., one row spanning 2000–2002). |
| **Within-window (reset-on-recovery)** | `drawdowns_<YYYY>.csv`, `top5_per_drawdown_<YYYY>.csv`, `report_<YYYY>.md` | The running peak resets after each *local* recovery, so each local peak→trough→recovery leg whose trough falls inside the year is its own episode. Recovery to the prior ATH is **not** required. |

For each drawdown we also report the **5 S&P 500 constituents with the highest
total return over the same peak→trough window** (yfinance adjusted close, so
dividends and splits are baked in). Universe = the actual point-in-time S&P 500
membership as of the **peak date**, reconstructed from Wikipedia's "Selected
changes to the list of S&P 500 components" by walking changes backward from
today's list.

### Caveats (read before drawing conclusions)

- **Pre-2000 membership reconstruction is incomplete.** Wikipedia's changes
  table only goes back to 1976-07-01 and is patchy until ~2000. Each ranking
  row carries a `membership_confidence` column: `high` (≥2000), `medium`
  (1976–1999), `low` (pre-1976). Rows with `low`/`medium` confidence may
  include current-set bias and should be treated with caution.
- **Pre-1985 price coverage is missing.** yfinance constituent history starts
  ~1985, so 12 of the 26 detected drawdowns have no top-5 ranking and no
  Stage 5/6 factor data. They are still labeled in `regime_labels.csv`.
- **Delisted/acquired tickers** (Lehman, Wachovia, ABK, etc.) often have no
  yfinance history and are silently skipped during ranking. About 20% of the
  historical universe falls into this bucket.
- **Adjusted close** is used throughout. Returns are implicitly total returns
  (price + dividends, split-adjusted).
- **Peak → trough only.** Recovery-leg performance is out of scope.
- **GICS sector tags are current, not point-in-time.** Sector assignments in
  Stages 5 and 6 use today's GICS classification, not the classification that
  applied at each drawdown's peak.

---

## Pipeline stages and outputs

### Stage 1 — Drawdown detection
- `drawdowns.csv` — 26 rows; ATH-mode peak-to-trough episodes ≥10%.

### Stage 2 — Constituent reconstruction
- Cached only (`data/cache/sp500_*.parquet`); no public output file.

### Stage 3 — Price loading
- Cached only (`data/cache/prices/*.parquet`); no public output file.

### Stage 4 — Top-5 ranking
- `top5_per_drawdown.csv` — 5 rows per covered drawdown (70 total).
- `report.md` — human-readable, all-of-history version.

### Stage 5 — Defensive-factor aggregation
- `defensive_factors_per_winner.csv` — per-winner factor exposures.
- `defensive_factors_summary.csv` — winners-vs-universe summary, per drawdown and overall.
- `defensive_factors_sector_counts.csv` — sector frequency among winners.
- `defensive_factors_report.md` — narrative report.

### Stage 6 — Regime taxonomy
- `regime_labels.csv` — hand-curated regime classification for every drawdown.
- `regime_sector_counts.csv` — sector frequency by regime.
- `regime_factor_summary.csv` — factor exposures by regime (with bootstrap CIs).
- `regime_report.md` — narrative report.

### Stage 7 — Fama-French sector gap-close (covers pre-1985 drawdowns)
- `ff_sector_returns_per_drawdown.csv` — peak-to-trough cumulative return per industry, every drawdown.
- `ff_sector_leaders.csv` — top-3 industries per drawdown, with GICS sector mapping.

### Within-year variant
- `drawdowns_<YYYY>.csv`, `top5_per_drawdown_<YYYY>.csv`, `report_<YYYY>.md`.

---

## File-by-file schemas

### `report.md` — human-readable, all of history

Markdown report. One section per ATH-mode drawdown ≥10% from 1928 onward.
Each section contains:

- Header: `## <peak_date> → <trough_date>  (SPX <max_dd_pct>%)` plus a
  confidence note if applicable.
- Body: a 5-row table of `(rank, ticker, company, return)`.

Reads top-down chronologically.

### `drawdowns.csv` — machine-readable, all of history

One row per ATH-mode drawdown ≥10%. Columns:

| Column | Type | Meaning |
|---|---|---|
| `peak_date` | `YYYY-MM-DD` | Trading day on which the all-time high (that this drawdown will fall from) was set. |
| `trough_date` | `YYYY-MM-DD` | Trading day on which the lowest close of the drawdown occurred. |
| `recovery_date` | `YYYY-MM-DD` or blank | Trading day on which the index reclaimed `peak_close`. Blank if it never recovered. |
| `peak_close` | float | SPX adjusted close on `peak_date`. |
| `trough_close` | float | SPX adjusted close on `trough_date`. |
| `max_dd_pct` | float | `(trough_close / peak_close - 1) * 100`. Negative, e.g. `-49.147`. |

26 rows in the current build (1928 → 2025).

### `top5_per_drawdown.csv` — machine-readable rankings, all of history

One row per (drawdown, ranked constituent). Five rows per drawdown. Columns:

| Column | Type | Meaning |
|---|---|---|
| `peak_date` | `YYYY-MM-DD` | Joins to `drawdowns.csv`. |
| `trough_date` | `YYYY-MM-DD` | Joins to `drawdowns.csv`. |
| `rank` | int 1..5 | 1 = best peak→trough return. |
| `ticker` | str | yfinance-style symbol (dashes, e.g. `BRK-B`). |
| `return_pct` | float | Constituent's return over peak→trough, in percent. |
| `peak_px` | float | Constituent's adjusted close on (or near) `peak_date`. |
| `trough_px` | float | Constituent's adjusted close on (or near) `trough_date`. |
| `peak_obs_date` | `YYYY-MM-DD` | Actual trading day used for `peak_px` (within 5 calendar days of `peak_date`). |
| `trough_obs_date` | `YYYY-MM-DD` | Same idea for trough. |
| `sp500_drawdown_pct` | float | Copy of `max_dd_pct` from `drawdowns.csv` for convenience. |
| `membership_confidence` | `high`/`medium`/`low` | Quality flag for the point-in-time membership reconstruction at this peak date. |

70 rows in the current build (5 × 14 drawdowns with usable price data).

### `defensive_factors_per_winner.csv` — Stage 5 per-winner factor table

One row per top-5 winner.

| Column | Type | Meaning |
|---|---|---|
| `peak_date` | `YYYY-MM-DD` | Joins to `drawdowns.csv` / `top5_per_drawdown.csv`. |
| `trough_date` | `YYYY-MM-DD` | Same. |
| `ticker` | str | yfinance symbol. |
| `sector` | str | GICS sector (current, not point-in-time). `Unknown` if unresolved. |
| `industry` | str | GICS industry, same caveat. |
| `pre_dd_beta` | float | OLS beta vs SPX over the 252 trading days ending at `peak_date`. |
| `pre_dd_vol` | float | Annualized stdev of daily log-returns over the same window. |
| `pre_dd_momentum` | float | 12-1 momentum: return from (peak − 252d) to (peak − 21d). |
| `drawdown_return_pct` | float | Copy of `return_pct` from Stage 4. |

### `defensive_factors_summary.csv` — Stage 5 winners-vs-universe summary

One row per drawdown plus an `OVERALL` row.

| Column | Type | Meaning |
|---|---|---|
| `peak_date` | `YYYY-MM-DD` or `OVERALL` | Drawdown identifier or overall row. |
| `winners_n` | int | Number of winners contributing to this row (≤5 per drawdown). |
| `winners_median_beta` / `vol` / `momentum` | float | Median factor exposure among the winners. |
| `universe_n` | int | Number of point-in-time SPX constituents with valid factor data at this peak. |
| `universe_median_beta` / `vol` / `momentum` | float | Median factor exposure across the full universe — the baseline winners are compared against. |

### `defensive_factors_sector_counts.csv` — Stage 5 sector frequency

| Column | Type | Meaning |
|---|---|---|
| `sector` | str | GICS sector. |
| `count` | int | Number of winner-episodes in this sector. |
| `pct` | float | Share of total winner-episodes (sums to ~100). |

### `defensive_factors_report.md` — Stage 5 narrative

Markdown report combining the above artifacts with an honest "Limitations"
section.

### `regime_labels.csv` — Stage 6 regime classification

One row per drawdown peak (all 26, not just the 14 covered ones).

| Column | Type | Meaning |
|---|---|---|
| `peak_date` | `YYYY-MM-DD` | Joins to `drawdowns.csv`. |
| `regime` | `structural` / `cyclical` / `event-driven` | Hand-curated Goldman-taxonomy label. |
| `rationale` | str | One-line justification — preserved for auditability. |

### `regime_sector_counts.csv` — Stage 6 sector by regime

| Column | Type | Meaning |
|---|---|---|
| `regime` | str | One of the three regimes (or `unlabeled`). |
| `sector` | str | GICS sector. |
| `count` | int | Winner-episodes in this (regime, sector) cell. |
| `pct` | float | Share within the regime (sums to ~100 per regime). |

### `regime_factor_summary.csv` — Stage 6 factor exposures by regime

| Column | Type | Meaning |
|---|---|---|
| `regime` | str | Regime category. |
| `n_drawdowns` | int | Number of drawdowns in the regime (covered ones only). |
| `n_winner_episodes` | int | Number of winner rows aggregated. |
| `winners_median_beta` / `vol` / `momentum` | float | Median exposure. |
| `beta_ci95_lo` / `hi`, `vol_ci95_lo` / `hi` | float | 95% bootstrap CIs for the median (2,000 resamples). |
| `winners_median_dd_return_pct` | float | Median peak-to-trough return among regime winners. |

### `regime_report.md` — Stage 6 narrative

Markdown report combining the labels, regime-frequency counts, factor table
(with bootstrap CIs), and a sector-leadership pivot.

### `ff_sector_returns_per_drawdown.csv` — Stage 7 full industry returns

Cumulative compound return per Fama-French 12-industry portfolio over each
drawdown's peak→trough window. Covers all 26 drawdowns (including pre-1985,
which Stage 4/5/6 don't reach). 312 rows = 26 × 12.

| Column | Type | Meaning |
|---|---|---|
| `peak_date` | `YYYY-MM-DD` | Joins to `drawdowns.csv`. |
| `trough_date` | `YYYY-MM-DD` | Same. |
| `ff_industry` | str | One of `NoDur, Durbl, Manuf, Enrgy, Chems, BusEq, Telcm, Utils, Shops, Hlth, Money, Other`. |
| `gics_sector` | str | Approximate GICS sector for joining against Stage 5/6 sector tables. |
| `cum_return_pct` | float | Cumulative compound return over [peak, trough], in percent. Total returns (FF series include dividends). |

### `ff_sector_leaders.csv` — Stage 7 top-3 industries per drawdown

Three rows per drawdown — the FF 12-industry top-3 by peak-to-trough
cumulative return. 78 rows in the current build (26 × 3).

| Column | Type | Meaning |
|---|---|---|
| `peak_date` | `YYYY-MM-DD` | Joins to `drawdowns.csv`. |
| `trough_date` | `YYYY-MM-DD` | Same. |
| `rank` | int 1..3 | 1 = best peak→trough cumulative return. |
| `ff_industry` | str | Fama-French industry name. |
| `gics_sector` | str | Approximate GICS sector mapping. |
| `cum_return_pct` | float | Cumulative return over [peak, trough], in percent. |

**Caveat:** FF portfolios are cap-weighted across the **full CRSP universe**,
not restricted to S&P 500 constituents. This is a proxy that lets us see
sector leadership for pre-1985 drawdowns where Stage 4/5/6 (SPX-restricted)
have no data; it is not an apples-to-apples substitute for the top-5
constituent rankings.

### `drawdowns_2000.csv` — within-year drawdowns (calendar year 2000)

Same schema as `drawdowns.csv`, but produced under the **within-window**
definition. Trough must fall inside 2000; peak may be in late 1999
(lookback = 365 days). Currently has one row: 2000-03-24 → 2000-12-20
(-17.2%, unrecovered within 2000).

### `top5_per_drawdown_2000.csv` — within-year rankings

Same schema as `top5_per_drawdown.csv`, restricted to the within-2000
drawdowns. 5 rows.

### `report_2000.md` — within-year human-readable report

Markdown report for the within-2000 view. Same row format as `report.md`.

---

## Reading examples

**Eyeball the headline:** open `report.md` (Stage 4),
`defensive_factors_report.md` (Stage 5), or `regime_report.md` (Stage 6).
Each is self-contained.

**Pivot the top-5 table:**

```python
import pandas as pd
top = pd.read_csv("top5_per_drawdown.csv", parse_dates=["peak_date", "trough_date"])
pivot = top.pivot_table(index=["peak_date", "trough_date"], columns="rank", values="ticker", aggfunc="first")
```

**Find every drawdown where a given ticker appeared in the top 5:**

```python
top[top["ticker"] == "NEM"][["peak_date", "trough_date", "rank", "return_pct"]]
```

**Join Stage 5 factor exposures with Stage 6 regime labels:**

```python
factors = pd.read_csv("defensive_factors_per_winner.csv", parse_dates=["peak_date"])
labels = pd.read_csv("regime_labels.csv", parse_dates=["peak_date"])
joined = factors.merge(labels[["peak_date", "regime"]], on="peak_date")
joined.groupby("regime")[["pre_dd_beta", "pre_dd_vol"]].median()
```

---

## Reproducibility

The full pipeline is in `src/sp500_drawdowns/` (Click CLI). To reproduce
from scratch:

```bash
python -m sp500_drawdowns.cli run            # Stages 1-4 (all-history)
python -m sp500_drawdowns.cli factors        # Stage 5
python -m sp500_drawdowns.cli regimes        # Stage 6
python -m sp500_drawdowns.cli ff-sectors     # Stage 7
python -m sp500_drawdowns.cli year 2000      # within-year variant
```

A second run will be cache-only (no network) and produces byte-identical
outputs.
