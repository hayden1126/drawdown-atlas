# S&P 500 Drawdown Regime Taxonomy

Classifies the 26 detected SPX drawdowns since 1928 into three categories following Goldman Sachs' bear-market taxonomy:

- **structural** — regime-level break (banking collapse, stagflation, valuation reset, monetary regime shift). Typically deepest and longest.
- **cyclical** — business-cycle correction. Late-cycle rate hikes, recessions without systemic break.
- **event-driven** — exogenous shock (geopolitical, pandemic, single-policy, microstructure). Typically sharp and short.

## Episode labels

| peak_date | regime | rationale |
| --- | --- | --- |
| 1928-05-14 | cyclical | Mild late-bull correction; pre-Crash noise. |
| 1929-09-16 | structural | Great Depression — banking collapse, deflationary spiral. |
| 1955-09-23 | event-driven | Eisenhower heart-attack shock; brief and sharp. |
| 1956-08-03 | cyclical | 1957 recession; tight monetary policy. |
| 1959-08-03 | cyclical | 1960 recession; Eisenhower-era credit tightening. |
| 1961-12-12 | event-driven | Kennedy 'steel crisis' policy shock; 1962 flash bear. |
| 1966-02-09 | cyclical | 1966 credit crunch; late-cycle rate squeeze. |
| 1967-09-25 | cyclical | Brief inflation/rate-anxiety dip. |
| 1968-11-29 | cyclical | 1969-70 recession. |
| 1973-01-11 | structural | Oil shock + stagflation + Nixon shock; macro regime change. |
| 1980-11-28 | structural | Volcker disinflation; monetary-policy regime shift. |
| 1983-10-10 | cyclical | Post-disinflation rate scare; mild cyclical. |
| 1987-08-25 | event-driven | Black Monday; portfolio-insurance microstructure shock. |
| 1989-10-09 | cyclical | Late-cycle S&L unease; minor. |
| 1990-07-16 | event-driven | Iraq invasion of Kuwait; oil shock + 1990 recession trigger. |
| 1997-10-07 | event-driven | Asian Financial Crisis; EM-FX contagion. |
| 1998-07-17 | event-driven | Russia default / LTCM blow-up. |
| 1999-07-16 | cyclical | Y2K + Fed-tightening cycle pre-2000 bust. |
| 2000-03-24 | structural | Dot-com bust; valuation reset and earnings collapse. |
| 2007-10-09 | structural | Global Financial Crisis; systemic credit failure. |
| 2015-05-21 | event-driven | China devaluation + oil collapse; commodity shock. |
| 2018-01-26 | event-driven | Vol-spike / XIV blow-up; microstructure event. |
| 2018-09-20 | cyclical | Fed-tightening scare into year-end 2018. |
| 2020-02-19 | event-driven | COVID-19 pandemic shock; fastest 30%+ in history. |
| 2022-01-03 | structural | Inflation/rate regime reset; end of zero-rate era. |
| 2025-02-19 | event-driven | 2025 tariff/policy shock. |

## Regime frequency

| regime | n_drawdowns |
| --- | --- |
| structural | 6 |
| cyclical | 10 |
| event-driven | 10 |

## Factor exposures by regime

Median pre-drawdown beta / vol / momentum of the top-5 winners, grouped by regime. 95% confidence intervals via 2,000-sample bootstrap of the median.

| regime | n_drawdowns | n_winner_episodes | winners_median_beta | beta_ci95_lo | beta_ci95_hi | winners_median_vol | vol_ci95_lo | vol_ci95_hi | winners_median_momentum | winners_median_dd_return_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| structural | 3 | 15 | 0.759 | 0.496 | 1.144 | 0.375 | 0.222 | 0.516 | 0.214 | 62.995 |
| cyclical | 3 | 15 | 0.579 | 0.213 | 0.965 | 0.529 | 0.26 | 0.639 | 0.098 | 32.773 |
| event-driven | 8 | 40 | 0.64 | 0.426 | 0.828 | 0.251 | 0.206 | 0.278 | 0.045 | 9.128 |

## Sector leadership by regime

Top-5 winner sector frequency, broken out by regime. Comparing across columns shows whether winners look the same in every kind of selloff, or whether leadership rotates with regime.

| sector | structural | cyclical | event-driven | total |
| --- | --- | --- | --- | --- |
| Utilities | 0 | 1 | 11 | 12 |
| Healthcare | 6 | 1 | 5 | 12 |
| Energy | 5 | 1 | 4 | 10 |
| Consumer Defensive | 1 | 0 | 8 | 9 |
| Consumer Cyclical | 2 | 2 | 4 | 8 |
| Technology | 0 | 5 | 1 | 6 |
| Basic Materials | 0 | 3 | 0 | 3 |
| Communication Services | 0 | 0 | 3 | 3 |
| Industrials | 1 | 1 | 1 | 3 |
| Real Estate | 0 | 0 | 2 | 2 |
| Financial Services | 0 | 0 | 1 | 1 |
| Unknown | 0 | 1 | 0 | 1 |

## Limitations

- **Regime labels are hand-curated, not algorithmic.** They follow published taxonomies (Goldman, Invesco, NDR) but every episode close to a category boundary involves judgment. Rationales are quoted in `regime_labels.csv` for auditability.
- **Small n.** 26 episodes across three regimes means ~7-10 per cell. Bootstrap CIs treat winner-episodes as the unit, which inflates effective sample size but does not fix the underlying scarcity of independent drawdowns.
- **GICS classification of constituents is current, not point-in-time.** Sector tilts pre-1999 are approximations.
- **No macro-covariate validation.** A richer version would correlate regimes with inflation, credit spreads, and the yield curve at each peak - out of scope here.
