# sp500-drawdowns

Pipeline: find every period where the S&P 500 fell **≥ 10% peak-to-trough**, and
for each such drawdown report the **5 constituents that performed best**
over the peak → trough window — using **point-in-time S&P 500 membership**
(not today's list).

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
python -m sp500_drawdowns.cli run
```

Outputs:

- `data/output/drawdowns.csv` — every detected peak-to-trough drawdown ≥10%.
- `data/output/top5_per_drawdown.csv` — top 5 constituents per drawdown.
- `data/output/report.md` — human-readable report.

Individual stages are independently re-runnable:

```bash
python -m sp500_drawdowns.cli drawdowns
python -m sp500_drawdowns.cli constituents
python -m sp500_drawdowns.cli prices
python -m sp500_drawdowns.cli rank
python -m sp500_drawdowns.cli report
python -m sp500_drawdowns.cli factors
python -m sp500_drawdowns.cli regimes
```

The `factors` stage (Stage 5) aggregates sector and pre-drawdown factor proxies
(beta, vol, 12-1 momentum) across the top-5 winners and compares them to the
full point-in-time SPX universe baseline. Outputs four files under
`data/output/`: `defensive_factors_per_winner.csv`,
`defensive_factors_summary.csv`, `defensive_factors_sector_counts.csv`, and
`defensive_factors_report.md`. Factor proxies are price-based only;
see the report's Limitations section for the honest scope.

The `regimes` stage (Stage 6) classifies each drawdown as **structural**,
**cyclical**, or **event-driven** following Goldman Sachs' bear-market
taxonomy, joins those labels onto the factor output, and produces
regime-conditional sector and factor breakdowns with bootstrapped median
CIs. Outputs: `regime_labels.csv`, `regime_sector_counts.csv`,
`regime_factor_summary.csv`, `regime_report.md`. Regime labels are
hand-curated with rationales preserved in the CSV.

## Caveats

- **Membership reconstruction** uses Wikipedia's "Selected changes" table walked
  backward from today's list. Coverage is solid from ~2000 onward; pre-2000 is
  patchy. Drawdowns with low-confidence membership are flagged in the report.
- **Adjusted close** from yfinance is used throughout — returns implicitly
  include dividends and split adjustments.
- **Peak→trough only.** Recovery-leg analysis is out of scope.
