# S&P 500 Drawdowns — Output Format Reference

This bundle contains six files. Two human-readable reports and four machine-readable CSVs. Everything is reproducible from the source pipeline at <https://github.com/your-fork-here> (or the local repo at `/home/hayden/analysis1`).

## What "drawdown" means here

A **drawdown** is a peak-to-trough decline in the S&P 500 (`^GSPC`, adjusted close from yfinance). We report drawdowns with magnitude **≥ 10%**.

Two definitions are used across the files:

| Mode | Used in | Rule |
|---|---|---|
| **All-time-high (ATH)** | `drawdowns.csv`, `top5_per_drawdown.csv`, `report.md` | A drawdown opens after each new ATH and closes only when the index reclaims that ATH. Produces a small number of large "mega" episodes (e.g., one row spanning 2000–2002). |
| **Within-window (reset-on-recovery)** | `drawdowns_<YYYY>.csv`, `top5_per_drawdown_<YYYY>.csv`, `report_<YYYY>.md` | The running peak resets after each *local* recovery, so each local peak→trough→recovery leg whose trough falls inside the year is its own episode. Recovery to the prior ATH is **not** required. |

For each drawdown we also report the **5 S&P 500 constituents with the highest total return over the same peak→trough window** (yfinance adjusted close, so dividends and splits are baked in). Universe = the actual point-in-time S&P 500 membership as of the **peak date**, reconstructed from Wikipedia's "Selected changes to the list of S&P 500 components" by walking changes backward from today's list.

### Caveats (read before drawing conclusions)

- **Pre-2000 membership reconstruction is incomplete.** Wikipedia's changes table only goes back to 1976-07-01 and is patchy until ~2000. Each ranking row carries a `membership_confidence` column: `high` (≥2000), `medium` (1976–1999), `low` (pre-1976). Rows with `low`/`medium` confidence may include current-set bias and should be treated with caution.
- **Delisted/acquired tickers** (Lehman, Wachovia, ABK, etc.) often have no yfinance history and are silently skipped during ranking. About 20% of the historical universe falls into this bucket.
- **Adjusted close** is used throughout. Returns are implicitly total returns (price + dividends, split-adjusted).
- **Peak → trough only.** Recovery-leg performance is out of scope.

---

## File-by-file

### `report.md` — human-readable, all of history

Markdown report. One section per ATH-mode drawdown ≥ 10% from 1928 onward. Each section contains:

- Header: `## <peak_date> → <trough_date>  (SPX <max_dd_pct>%)` plus a confidence note if applicable.
- Body: a 5-row table of `(rank, ticker, company, return)`.

Reads top-down chronologically.

### `drawdowns.csv` — machine-readable, all of history

One row per ATH-mode drawdown ≥ 10%. Columns:

| Column | Type | Meaning |
|---|---|---|
| `peak_date` | `YYYY-MM-DD` | Trading day on which the all-time high (that this drawdown will fall from) was set. |
| `trough_date` | `YYYY-MM-DD` | Trading day on which the lowest close of the drawdown occurred. |
| `recovery_date` | `YYYY-MM-DD` or blank | Trading day on which the index reclaimed `peak_close`. Blank if it never recovered before end-of-series. |
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
| `return_pct` | float | Constituent's return over peak→trough, in percent. Can be positive or negative — the top 5 are whichever ranked highest. |
| `peak_px` | float | Constituent's adjusted close on (or near) `peak_date`. |
| `trough_px` | float | Constituent's adjusted close on (or near) `trough_date`. |
| `peak_obs_date` | `YYYY-MM-DD` | Actual trading day used for `peak_px` (within 5 calendar days of `peak_date`; usually identical). |
| `trough_obs_date` | `YYYY-MM-DD` | Same idea for trough. |
| `sp500_drawdown_pct` | float | Copy of `max_dd_pct` from `drawdowns.csv` for convenience. |
| `membership_confidence` | `high`/`medium`/`low` | Quality flag for the point-in-time membership reconstruction at this peak date. |

70 rows in the current build (5 × 14 drawdowns with usable price data).

### `drawdowns_2000.csv` — within-year drawdowns (calendar year 2000)

Same schema as `drawdowns.csv`, but produced under the **within-window** definition. Trough must fall inside 2000; peak may be in late 1999 (lookback = 365 days). Currently has one row: 2000-03-24 → 2000-12-20 (-17.2%, unrecovered within 2000).

### `top5_per_drawdown_2000.csv` — within-year rankings

Same schema as `top5_per_drawdown.csv`, restricted to the within-2000 drawdowns. 5 rows.

### `report_2000.md` — within-year human-readable report

Markdown report for the within-2000 view. Same row format as `report.md`.

---

## Reading examples

**Eyeball the headline:** open `report.md`. It's ordered chronologically; each section is self-contained.

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

**Filter to high-confidence rankings only:**

```python
top[top["membership_confidence"] == "high"]
```

---

## Reproducibility

The full pipeline is in `src/sp500_drawdowns/` (Click CLI). To reproduce from scratch:

```bash
python -m sp500_drawdowns.cli run            # all-history report
python -m sp500_drawdowns.cli year 2000      # within-year report (any YYYY)
```

A second run will be cache-only (no network) and produces byte-identical outputs.
