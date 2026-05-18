# Defensive Sectors Only Win Event-Driven Drawdowns

*A century of S&P 500 bear markets, survivorship-bias-free, episode by episode.*

---

## The question

"Which stocks hold up when the S&P 500 falls?" is a standard finance
question with a standard answer: utilities, consumer staples, healthcare —
the low-volatility, low-beta, dividend-paying defensives. AQR, MSCI, S&P,
and Robeco have all written it up; it's the implicit pitch behind every
min-vol ETF.

The problem with the standard answer is that it's an *average* across very
different events. Asking "what wins drawdowns?" pools 1929, 1973, 1987,
2000, 2008, and 2020 into a single number, as if a banking-system collapse,
a stagflation regime change, a portfolio-insurance microstructure failure,
a valuation reset, and a pandemic are the same kind of object. They are
not.

This post takes the question apart. Across every >=10% S&P 500 drawdown
since 1928 — 26 episodes — it identifies the five best-performing
constituents in each, using point-in-time membership (so the sample is
survivorship-bias-free), then classifies each drawdown as **structural**,
**cyclical**, or **event-driven** following Goldman Sachs' bear-market
taxonomy. The headline finding:

> **Defensive sectors only dominate in event-driven drawdowns. Structural
> bears reward Healthcare and Energy. Cyclical bears reward Technology and
> Basic Materials. The flat "defensives win" story is hiding three
> completely different stories.**

The full pipeline and outputs are open source:
[github.com/hayden1126/drawdown-atlas](https://github.com/hayden1126/drawdown-atlas).

## Methodology, briefly

1. **Drawdown detection.** Daily SPX close from yfinance, 1928 to present.
   A drawdown is any period from an all-time-high peak to a subsequent
   trough where the cumulative decline reaches >=10%, ending when SPX
   recovers to a new high. Result: 26 episodes.
2. **Point-in-time membership.** S&P 500 constituents at each drawdown
   peak are reconstructed by walking Wikipedia's "Selected changes" table
   backward from today's list. No survivorship bias: a stock that was in
   the index in 1987 and got deleted in 1992 is considered for the 1987
   and 1990 drawdowns, not for the 2000 drawdown.
3. **Top-5 ranking.** For each drawdown, rank every point-in-time
   constituent by its peak-to-trough return; take the top 5. Across 26
   drawdowns this would be 130 winner-episodes; in practice only 14
   drawdowns have constituent price coverage in yfinance (the pre-1985
   ones don't), giving 70 winner-episodes in the analysis.
4. **Factor proxies.** For each winner, compute beta against SPX,
   annualized realized volatility, and 12-1 momentum over the 252 trading
   days *ending* at the SPX peak — strictly pre-drawdown, no look-ahead.
   Sector from current GICS (a known limitation; pre-1999 reconstruction
   was out of scope).
5. **Regime labels.** Hand-curated using published taxonomies (Goldman,
   Invesco, NDR), with rationales for each label preserved in the
   `regime_labels.csv` artifact for auditability.

## The flat result first

Pooled across all 14 covered drawdowns:

| Metric | Top-5 winners | Full SPX universe |
|---|---|---|
| Median pre-DD beta | 0.68 | 0.88 |
| Median annualized vol | 0.27 | 0.25 |
| Median 12-1 momentum | 6.5% | 16.7% |

Beta is meaningfully lower for winners than for the index universe. That's
the canonical "defensive" result — winners walked into each drawdown with
~22% less systematic risk than the typical SPX name. Top sectors in the
pooled view: Utilities 17%, Healthcare 17%, Energy 14%, Consumer Defensive
13%. Exactly the textbook list.

If you stop here, you have the standard finding. The standard finding is
not wrong; it's just incomplete.

## The same data, sliced by regime

When the 14 covered drawdowns are split by Goldman's three-category
taxonomy, the picture fractures:

### Sector leadership

| Sector | Event-driven (40 episodes) | Structural (15 episodes) | Cyclical (15 episodes) |
|---|---|---|---|
| Utilities | **27.5%** | 0% | 6.7% |
| Consumer Defensive | **20.0%** | 6.7% | 0% |
| Healthcare | 12.5% | **40.0%** | 6.7% |
| Energy | 10.0% | **33.3%** | 6.7% |
| Technology | 2.5% | 0% | **33.3%** |
| Basic Materials | 0% | 0% | **20.0%** |
| Consumer Cyclical | 10.0% | 13.3% | 13.3% |
| Industrials | 2.5% | 6.7% | 6.7% |

Three completely different stories:

- **Event-driven** (Black Monday, LTCM, Asian crisis, 2018 vol-mageddon,
  COVID, 2025 tariff shock): Utilities + Consumer Defensive + Healthcare
  account for **60%** of winners. This is the textbook playbook. When the
  shock is exogenous and short, dividend-paying low-beta names cushion the
  best.
- **Structural** (dot-com bust, GFC, 2022 rate-regime reset — only 3 of
  ~6 structural episodes in the analysis window have price coverage):
  Healthcare 40% + Energy 33% account for nearly three-quarters of
  winners. Energy makes sense in 1973/1980, but in the modern sample it
  shows up in 2022. Pharma was relatively stable in the dot-com bust and
  defensive within the GFC. Utilities — the defensive flagship — appear
  *zero* times in the structural cluster.
- **Cyclical** (1989 S&L unease, 1999 pre-bust, 2018 Fed-tightening
  scare): Technology 33% + Basic Materials 20%. These are pro-cyclical
  names. They are winners in *late-cycle* bears because they had momentum
  going into the peak and the selloff didn't kill the underlying business
  cycle.

### Factor exposures

| Regime | Median winner beta | Median winner vol | Median winner DD return |
|---|---|---|---|
| Structural | 0.76 [0.50, 1.14] | 37.5% [22.2%, 51.6%] | **+63.0%** |
| Cyclical | 0.58 [0.21, 0.97] | 52.9% [26.0%, 63.9%] | +32.8% |
| Event-driven | 0.64 [0.43, 0.83] | 25.1% [20.6%, 27.8%] | +9.1% |

*95% bootstrap CIs for the median in brackets.*

A few things to notice:

- **Structural-bear winners are not low-beta.** Median beta of 0.76 is
  closer to "market" than to "defensive." The textbook defensive
  description (low-beta, low-vol) does not describe winners of structural
  drawdowns.
- **Cyclical-bear winners are high-vol.** Median realized vol of 53% means
  these were not quiet stocks — they were the names that ran hot into the
  selloff and kept running.
- **Drawdown returns differ by an order of magnitude.** Structural-bear
  winners returned +63% from the SPX peak to the SPX trough because
  structural bears last *years*. Event-driven winners returned only +9%
  because event bears are short and there's less time for any name to
  pull away.

## Why this matters

Three implications:

1. **"Defensive equity" is a misnomer if you can't tell what kind of bear
   is coming.** Buying USMV (MSCI Min Vol) before a structural bear has a
   meaningfully different expected outcome than buying it before an
   event-driven one. The min-vol pitch implicitly conditions on
   event-driven; consumers may not realize that.

2. **The "buy the trough winners" trap is even worse than Daniel-Moskowitz
   (2016) made it look.** Their "Momentum Crashes" paper shows that
   cross-sectional winners *crash on the rebound*. This data adds a layer:
   the winners aren't even the same kind of stocks across drawdowns, so
   "the strategy" doesn't exist — there are at least three different
   strategies, picked ex-post.

3. **Sector-rotation models that ignore drawdown taxonomy are leaving
   signal on the table.** Fidelity's business-cycle framework, NDR's
   cyclical/secular split, and Goldman's taxonomy converge on the idea
   that *the kind of selloff* matters more than *the fact of selloff*.
   The numbers here support that strongly enough that a flat "what wins
   drawdowns" view should be retired.

## What this is and is not

- **It is** a descriptive atlas: 26 labeled episodes, 70 covered
  winner-episodes, all open-source and reproducible.
- **It is not** a hypothesis test. Three regimes x 3-8 covered episodes
  each is too small for formal inference. Confidence intervals on medians
  are wide.
- **It is not** point-in-time at the sector level. GICS classification
  uses current sector tags. Pharma in 1968 is not perfectly comparable to
  Pharma in 2008.
- **It does not** address the pre-1985 coverage gap. yfinance's
  constituent price data effectively starts in 1985, which is why 1929,
  1956, 1962, 1966, 1968, 1973, and 1980 are labeled but not factored.
  Closing that gap (Shiller, Fama-French portfolios, paid CRSP) is the
  obvious next step.
- **It does not** prescribe a strategy. The leadership-by-regime pattern
  is *ex-post* — you only know which regime you're in after the bear is
  over. A genuine strategy would need a real-time regime classifier,
  which is a much harder problem.

## Repo

Full pipeline, intermediate data, and reports:
**[github.com/hayden1126/drawdown-atlas](https://github.com/hayden1126/drawdown-atlas)**

The relevant CLI invocations:

```bash
python -m sp500_drawdowns.cli run       # Stages 1-4: detect drawdowns, rank top-5
python -m sp500_drawdowns.cli factors   # Stage 5: factor proxies + sectors
python -m sp500_drawdowns.cli regimes   # Stage 6: regime taxonomy + this analysis
```

The 25-test suite passes. The `data/output/regime_*.csv` files are
machine-readable. The `regime_report.md` is the longer technical version
of this post.

---

*Feedback, corrections, and "you missed X" suggestions welcome via GitHub
issues.*
