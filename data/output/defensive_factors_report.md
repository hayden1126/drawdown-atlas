# Defensive-Factor Aggregation of S&P 500 Drawdown Winners

Aggregates the top-5 best-performing point-in-time S&P 500 constituents across 14 drawdowns since 1928 (n=70 winner-episodes).

## Sector frequency among winners

| sector | count | pct |
| --- | --- | --- |
| Utilities | 12 | 17.1 |
| Healthcare | 12 | 17.1 |
| Energy | 10 | 14.3 |
| Consumer Defensive | 9 | 12.9 |
| Consumer Cyclical | 8 | 11.4 |
| Technology | 6 | 8.6 |
| Basic Materials | 3 | 4.3 |
| Communication Services | 3 | 4.3 |
| Industrials | 3 | 4.3 |
| Real Estate | 2 | 2.9 |
| Financial Services | 1 | 1.4 |
| Unknown | 1 | 1.4 |

## Factor exposures: winners vs full point-in-time SPX universe

Pre-drawdown factor proxies computed over the 252 trading days ending on the SPX peak date. Beta vs SPX daily log-returns; vol annualized; momentum = 12-1 (skip last ~1 month).

| metric | winners | universe |
| --- | --- | --- |
| Median beta | 0.676 | 0.877 |
| Median annualized vol | 0.269 | 0.253 |
| Median 12-1 momentum | 0.065 | 0.167 |

## Per-drawdown winners vs universe

| peak_date | winners_median_beta | universe_median_beta | winners_median_vol | universe_median_vol |
| --- | --- | --- | --- | --- |
| 1987-08-25 | 0.759 | 0.918 | 0.219 | 0.295 |
| 1989-10-09 | 0.213 | 0.811 | 0.529 | 0.218 |
| 1990-07-16 | 0.72 | 0.839 | 0.265 | 0.255 |
| 1997-10-07 | 0.344 | 0.72 | 0.414 | 0.262 |
| 1998-07-17 | 0.338 | 0.795 | 0.175 | 0.298 |
| 1999-07-16 | 1.063 | 0.743 | 0.717 | 0.411 |
| 2000-03-24 | 0.489 | 0.665 | 0.469 | 0.421 |
| 2007-10-09 | 0.927 | 1.013 | 0.194 | 0.238 |
| 2015-05-21 | 0.948 | 1.008 | 0.199 | 0.202 |
| 2018-01-26 | 1.066 | 1.007 | 0.271 | 0.186 |
| 2018-09-20 | 0.578 | 0.916 | 0.219 | 0.22 |
| 2020-02-19 | 0.567 | 1.016 | 0.207 | 0.229 |
| 2022-01-03 | 1.205 | 0.936 | 0.375 | 0.256 |
| 2025-02-19 | 0.121 | 0.66 | 0.187 | 0.252 |

## Limitations

- **Factor proxies are price-based, not fundamentals.** No profitability, leverage, or accruals — those require Compustat (paid). Treat beta/vol as noisy proxies for the canonical defensive-equity factors.
- **Sector classification uses _current_ GICS, not point-in-time.** A ticker classified today as Utilities may have been classified differently decades ago; we don't attempt historical GICS reconstruction.
- **Small sample.** n=70 winner-episodes across 14 drawdowns is too small for formal hypothesis testing. This is a descriptive atlas, not an inferential study.
- **No look-ahead correction within the drawdown.** Factor proxies are computed strictly _before_ the peak — but the _identity_ of the top-5 is still observed ex-post.
