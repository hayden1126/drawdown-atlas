# Closing the Pre-1985 Gap: What the Full Century Actually Says

*Follow-up to ["Defensive Sectors Only Win Event-Driven Drawdowns"](./post_rotating_leadership.md).
The structural-bear claim went from 3 episodes to 6. The story got more
specific.*

---

## The objection

The first post's structural-bear cluster — "Healthcare and Energy dominate"
— rested on 3 data points: dot-com bust, GFC, and the 2022 rate-regime
reset. Everyone reading it had the same reaction: *three episodes isn't a
finding, it's a coincidence with a thesis*. The pre-1985 drawdowns
(including 1929, 1973 oil shock, 1980 Volcker disinflation — three of the
most important structural bears in modern history) were silent because
yfinance constituent data effectively starts in 1985.

That gap is now closed.

## The fix: Fama-French industry portfolios

Ken French's [12-industry value-weighted daily portfolios](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)
go back to 1926-07-01. They're free, publicly published, and cover the
entire CRSP universe value-weighted by industry. We can't tell you *which
stocks* led in 1973, but we can tell you which *industries* did.

The unit is honestly different: Stage 5/6 of the pipeline reports the
five best-performing *individual constituents* per drawdown; the FF view
reports the three best-performing *industry portfolios*. Top-5 individual
stocks captures outlier survivors (e.g., Newmont in 1973); FF portfolios
capture the cap-weighted median experience of every CRSP-listed stock in
the sector. Both are interesting; they answer different questions.

The new code is `src/sp500_drawdowns/ff_sectors.py`, CLI subcommand
`ff-sectors`. Five new tests pass. Output is in
`data/output/ff_sector_leaders.csv` and the longer
`data/output/ff_sector_returns_per_drawdown.csv` (cumulative return per
industry per drawdown — useful for joining).

## What the full 6-episode structural picture says

| Drawdown | Trigger | #1 leader | #2 | #3 |
|---|---|---|---|---|
| 1929-09 → 1932-06 (-86%) | Great Depression | Telcm (-64%) | NoDur (-67%) | Hlth (-72%) |
| 1973-01 → 1974-10 (-48%) | Oil shock + stagflation | Telcm (-23%) | Enrgy (-34%) | Chems (-40%) |
| 1980-11 → 1982-08 (-27%) | Volcker disinflation | Telcm (**+24%**) | NoDur (+16%) | Shops (+13%) |
| 2000-03 → 2002-10 (-49%) | Dot-com bust | NoDur (+23%) | Chems (+5%) | Enrgy (-6%) |
| 2007-10 → 2009-03 (-57%) | Global Financial Crisis | Hlth (-34%) | NoDur (-35%) | Shops (-40%) |
| 2022-01 → 2022-10 (-25%) | Inflation/rate-regime reset | Enrgy (**+53%**) | NoDur (-7%) | Utils (-10%) |

Numbers in parentheses are cumulative peak-to-trough total returns
(dividends reinvested). "Leader" in a structural bear often means
"least-bad performer," not "made money" — the 1929 leaders all lost
60–70% because the market lost 86%.

### Where the original claim survives

**Consumer Defensive (NoDur) is in the top-3 for 5 of 6 structural bears.**
That's actually a stronger version of the "defensives in structural bears"
claim than what the first post made. NoDur appears in every structural
episode except 1973.

### Where the original claim needed updating

**Healthcare's structural dominance was driven by GFC + dot-com.** Of
the original 3-episode cluster, Healthcare led 2 (dot-com and GFC). In
the full 6-episode sample, Healthcare appears in the top-3 of only 2 out
of 6 structural bears (1929 and 2007). It's *not* a universal
structural-bear leader — it's a financial-system structural-bear leader.

**Energy is regime-specific within "structural."** Energy leads in
commodity-driven structural bears (1973, 2000, 2022) but is absent from
the top-3 in financial-system structural bears (1929, 1980, 2007). The
structural bucket itself fractures: there are at least two sub-types —
*commodity/inflation structural* (1973, 2000, 2022) and *financial
structural* (1929, 1980, 2007) — and they have different leadership.

**Telecom dominates the pre-1985 leaderboard.** This was the biggest
surprise. Telecom (essentially AT&T pre-Bell-breakup, then incumbent
telcos) is the #1 sector leader in **7 of the 12 pre-1985 episodes**
across all regimes — 1928, 1929, 1955, 1959, 1973, 1980, plus tied
appearances. In the post-1985 sample Telcm is rank-1 just twice. This
is not just structural bears; it's a pre-1985-wide regularity, almost
certainly tied to AT&T being a regulated monopoly with reliable
dividends in a market that hadn't yet been overtaken by growth stocks.
After deregulation (1982) and the rise of growth-style investing, the
pattern dissolves.

## So what's the headline now?

Three sharper claims, each better supported than the first post's
version:

1. **Consumer Defensive (NoDur) is the closest thing to a universal
   structural-bear winner.** Top-3 in 5 of 6 structural episodes since
   1929. The standard "defensive equity" story holds up *for this
   sector* in structural bears — just not for Utilities or Healthcare
   uniformly.

2. **The structural-bear bucket isn't one cluster — it's two.**
   Financial-system structural bears (1929, 1980, 2007) and
   commodity/inflation structural bears (1973, 2000, 2022) have
   different leaders. Energy and Chemicals lead the commodity ones;
   Healthcare and Consumer Defensive lead the financial ones. Folding
   them into one "structural" row hides the substructure.

3. **Telecom's pre-1985 dominance is a regime change, not just a
   drawdown finding.** Telcm was the #1 leader in 7 of 12 pre-1985
   drawdowns and just 2 of 14 post-1985 ones. Something fundamental
   changed about which sectors lead bear markets around 1985 — most
   likely the breakup of AT&T (1984) plus the rise of growth investing.
   This is itself a research question worth a separate look.

## What this is and is not (still)

- **It is** an honest extension of the first post: same pipeline, real
  data, all 26 drawdowns now covered for sector leadership.
- **It is not** an apples-to-apples extension of Stage 5/6 work. FF
  portfolio leadership and top-5 individual constituent leadership are
  different units. Spot-check on 2007–2009: Stage 5/6 had Healthcare as
  40% of structural winners; FF says Healthcare was the #1 industry
  leader. Agreement.
- **It does not** prescribe a strategy. The financial-vs-commodity
  structural distinction is *ex-post* — you only know which sub-type
  you're in well after the fact.
- **It does not** rescue the pre-1985 *factor* work. Beta and vol of
  individual winners still aren't computable for those episodes
  without constituent prices. That gap remains.

## Repo

Full pipeline: [github.com/hayden1126/drawdown-atlas](https://github.com/hayden1126/drawdown-atlas)

```bash
python -m sp500_drawdowns.cli ff-sectors    # this post's data
```

Outputs: `data/output/ff_sector_leaders.csv` (top-3 per drawdown) and
`data/output/ff_sector_returns_per_drawdown.csv` (full 12-industry
cumulative returns). 30-test suite passes. Fama-French data fetched
once and cached locally; subsequent runs use no network.

---

*If you read the first post: thank you. This one is the version with
the obvious "only 3 data points" objection answered honestly. The
finding got sharper, smaller, and more interesting in the process —
which is how research is supposed to go.*
