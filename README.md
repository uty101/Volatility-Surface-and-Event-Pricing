# Volatility Surface and Event Pricing

Prices listed options and their Greeks, solves implied volatility, and fits an arbitrage-free SVI and SSVI surface per underlying.
Reads the risk-neutral distribution off the surface and measures the move options price around earnings and macro events.
Tests the volatility risk premium on S&P 500 history from 1990 and implied against realised correlation from Cboe COR3M.
Splits delta-hedged option P&L into Greeks and builds a 1-page daily risk report.
Option chains are captured daily from 2026-10-28, so every live result is a method demonstration with its N stated.

Results are in [`outputs/`](outputs/). [![ci](https://github.com/uty101/Volatility-Surface-and-Event-Pricing/actions/workflows/ci.yml/badge.svg)](https://github.com/uty101/Volatility-Surface-and-Event-Pricing/actions/workflows/ci.yml) 4,747 tests.

**Capture window:** 2026-10-28 to 2026-11-06, 7 days, 2026-11-02 missed. The first day holds `^SPX`, SPY and AAPL only, from an in-session test capture. The others hold all 37 underlyings.

## Run it

```bash
uv venv --python 3.12
uv pip install -r requirements-lock.txt
uv pip install -e . --no-deps
python scripts/run_all.py                  # every stage, in section order
pytest -p socket --disable-socket -q
```

`run_all.py` needs an authenticated `gh` to download the chains from the `snapshots` release. Long history is committed in `data/raw/`. Fitted surfaces are cached in `data/processed/surface/`, so only new days are fitted. Methods are in [`docs/METHODS.md`](docs/METHODS.md).

## 1. Does the pricer match QuantLib?

Yes. BSM matches QuantLib's analytic engine: the largest price gap is 3.9e-14 over 252 grid cases, against a bound of 1e-10. Black-76 equals BSM once S e^(−qT) = D F: the largest gap is 5.0e-14 over 252 cases. The American CRR tree at 2000 steps matches QuantLib's CRR engine: the largest gap is 6.8e-05 x S over 252 cases, against a bound of 1e-4 x S. Delta, gamma, vega, theta and rho match QuantLib: the largest gap is 4.4e-13 over 252 cases each, against a bound of 1e-8. Early exercise premium on SPY near the money puts: median 0.22 vol points (N = 496 contracts, fixture day). It grows on SPY deep in the money puts: median 1.39 vol points (N = 44 contracts). Early exercise premium on AAPL near the money puts: median 0.15 vol points (N = 47 contracts, fixture day). It grows on AAPL deep in the money puts: median 4.79 vol points (N = 109 contracts). On calls it is 0 to rounding: the largest median in any SPY or AAPL call bin is 8.4e-12 vol points. The single names captured later have no premium table, because the step runs on the fixture day, which holds SPY and AAPL only.

## 2. The S&P 500 surface

^SPX 30-day ATM vol was 13.44% on 2026-10-28 (N = 7 capture days). It was 18.08% on 2026-11-06, after sell-offs on 2026-10-30 and 2026-11-05. The 30-day 25-delta risk reversal went from −4.16 to −7.14 vol points, so skew steepened (N = 7 days). The term slope, ATM 90 days minus 30 days, went from 1.02 to −0.79 vol points, so the short end moved above the long end (N = 7 days). Butterfly: 3006 of 3275 SVI slices across every underlying and day are accepted; the rest are rejected or have too few quotes to fit (N = 7 days). Every accepted slice is free of butterfly arbitrage up to the check's tolerance: the smallest g on the acceptance grid is −9.6e-11, against −1e-10. Calendar: the per-expiry slices are not fully clean. 29 of 225 consecutive ^SPX pairs cross somewhere on their shared quoted range (N = 7 days). Across every underlying it is 78 of 2781 pairs. Slices are not refitted for this; SSVI is the calendar-consistent surface, because its theta is non-decreasing in T by construction. SSVI pays for that in fit: its ^SPX RMSE was 3.48 vol points on 2026-11-06, because 1 rho cannot hold the skew, so the daily metrics come from the slices.

| day | ATM 30d % | RR 25d, pts | BF 25d, pts | ATM 90d % | term slope, pts | expiries |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-10-28 | 13.44 | −4.16 | 0.63 | 14.46 | 1.02 | 36 |
| 2026-10-29 | 12.98 | −4.11 | 0.60 | 14.24 | 1.26 | 35 |
| 2026-10-30 | 16.54 | −6.36 | 0.82 | 16.26 | −0.28 | 34 |
| 2026-11-03 | 16.28 | −5.37 | 0.66 | 15.88 | −0.40 | 35 |
| 2026-11-04 | 13.22 | −3.77 | 0.57 | 14.12 | 0.89 | 35 |
| 2026-11-05 | 19.30 | −7.83 | 1.07 | 17.75 | −1.55 | 32 |
| 2026-11-06 | 18.08 | −7.14 | 0.82 | 17.29 | −0.79 | 25 |

The smile on the last day shows the skew the slices hold: the 30-day 25-delta risk reversal is −7.14 vol points.

![^SPX smiles](outputs/figures/spx_smiles_2026-11-06.png)

ATM vol jumped on 2026-10-30, fell back on 2026-11-04 and jumped again on 2026-11-05, ending at 18.08% with the term slope negative.

![^SPX metrics](outputs/figures/spx_metrics.png)

The density comes straight from each slice, and the shaded band marks where quotes exist. Tail probabilities outside it are labelled extrapolated.

![^SPX density](outputs/figures/spx_density_last.png)

## 3. Earnings events

With N = 11 completed events, fewer than the 20 the summary needs, the gap between implied and realised moves cannot be told apart from 0 at this N. AMZN AMC 2026-10-29: realised 1.42% against a term structure move of 8.32% and a straddle move of 8.59%, ratio 0.17. INTC AMC 2026-10-29: realised 33.65% against a term structure move of 8.51% and a straddle move of 10.48%, ratio 3.95. CVX BMO 2026-10-30: realised 1.74% against a term structure move of 2.34% and a straddle move of 2.43%, ratio 0.74. XOM BMO 2026-10-30: realised 2.14% against a term structure move of 2.40% and a straddle move of 2.39%, ratio 0.89. AAPL AMC 2026-11-02: realised 1.92% against a term structure move of 4.03% and a straddle move of 4.56%, ratio 0.48. PLTR AMC 2026-11-02: realised 1.66% against a term structure move of 11.77% and a straddle move of 14.35%, ratio 0.14. AMD AMC 2026-11-03: realised 1.00% against a term structure move of 7.76% and a straddle move of 9.47%, ratio 0.13. SHOP BMO 2026-11-03: realised 9.14% against a term structure move of 12.49% and a straddle move of 14.97%, ratio 0.73. UBER BMO 2026-11-04: realised 4.79% against a term structure move of 6.90% and a straddle move of 7.38%, ratio 0.69. ABNB AMC 2026-11-05: realised 11.04% against a term structure move of 10.00% and a straddle move of 11.03%, ratio 1.10. ^SPX NFP 2026-11-06: realised 0.31% against a term structure move of 1.78% and a straddle move of 2.24%, ratio 0.18. 35 more events have a window that ends after the last close in the data and stay pending. 3 events have no pre-event snapshot, because they fall before the capture could see them.

| ticker | date | timing | straddle % | term structure % | realised % | ratio |
| --- | --- | --- | --- | --- | --- | --- |
| AMZN | 2026-10-29 | AMC | 8.59 | 8.32 | 1.42 | 0.17 |
| INTC | 2026-10-29 | AMC | 10.48 | 8.51 | 33.65 | 3.95 |
| CVX | 2026-10-30 | BMO | 2.43 | 2.34 | 1.74 | 0.74 |
| XOM | 2026-10-30 | BMO | 2.39 | 2.40 | 2.14 | 0.89 |
| AAPL | 2026-11-02 | AMC | 4.56 | 4.03 | 1.92 | 0.48 |
| PLTR | 2026-11-02 | AMC | 14.35 | 11.77 | 1.66 | 0.14 |
| AMD | 2026-11-03 | AMC | 9.47 | 7.76 | 1.00 | 0.13 |
| SHOP | 2026-11-03 | BMO | 14.97 | 12.49 | 9.14 | 0.73 |
| UBER | 2026-11-04 | BMO | 7.38 | 6.90 | 4.79 | 0.69 |
| ABNB | 2026-11-05 | AMC | 11.03 | 10.00 | 11.04 | 1.10 |
| ^SPX | 2026-11-06 | NFP | 2.24 | 1.78 | 0.31 | 0.18 |

Points above the line moved more than the options priced. 11 points say nothing about the average.

![Implied against realised](outputs/figures/event_scatter.png)

## 4. The volatility risk premium

VIX squared sat above the variance that followed by 0.01037 of annualised variance on average, over 441 months from 1990. Over the 394 months that also have a GARCH forecast the mean gap is 0.00970. Implied variance is above the GARCH forecast in 362 of 395 month ends. The forecast says little about the size of the gap: the correlation of the signal with the later gap is 0.15 over 394 months. Selling puts paid, but less per unit of risk than holding the index: Cboe PUT has a Sharpe of 0.56 over 237 months from 2007, against 0.65 for the S&P 500 total return index and 0.44 for BXM. The index carries no trading costs of its own, so the only cost deducted here is the timed strategy's switching cost. PUT's worst month was −17.65%. PUT alone has a probabilistic Sharpe of 0.984 against 0 over 237 months, so it very likely pays. Timing on implied minus GARCH variance gives a raw Sharpe of 0.80 over 237 months, after the switching cost. Its deflated Sharpe on excess returns over T-bills is 0.994 (N = 5 trials, 237 months), so the timed PUT very likely pays too. The number of specifications tried is 5. Whether timing improves on selling puts is a question about the monthly series timed minus PUT. On its own the GARCH rule looks better: that series has an annualised Sharpe of 0.240 and a probabilistic Sharpe of 0.915 against 0 over 237 months. After counting the 5 rules tried, its deflated Sharpe is 0.412 (N = 5 trials, 237 months), so its gain over holding PUT cannot be told apart from luck. 4 of the other 4 rules did worse than PUT, with a negative annualised Sharpe of timed minus PUT: iv_minus_rv21 −0.051, iv_minus_rv63 −0.403, iv_minus_ewma −0.003, garch_above_median −0.158 (N = 5 trials, 237 months). The raw gain over PUT comes from sitting out 27 months.

| strategy | months | mean % | vol % | Sharpe | worst month % | worst drawdown % | skew | excess kurtosis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| put | 237 | 7.52 | 10.72 | 0.555 | −17.65 | −32.66 | −1.69 | 7.41 |
| bxm | 237 | 6.39 | 10.95 | 0.441 | −15.01 | −35.81 | −1.36 | 5.24 |
| sp500tr | 237 | 11.55 | 15.40 | 0.648 | −16.80 | −50.95 | −0.55 | 1.05 |
| timed_put | 237 | 8.85 | 9.06 | 0.803 | −13.42 | −20.75 | −1.03 | 5.48 |
| bxm_long | 295 | 6.57 | 10.64 | 0.455 | −15.01 | −35.81 | −1.26 | 5.11 |

`bxm_long` is BXM alone over its longer window. VIX squared sat above the variance that followed in 372 of 441 months.

![VIX squared against realised](outputs/figures/vrp_vix2_vs_rv.png)

The timed line ends highest of the option strategies, with a Sharpe of 0.80 against PUT's 0.56. That is 1 specification of 5, so read it with the deflated Sharpes above.

![Cumulative excess return](outputs/figures/vrp_cumulative.png)

Its worst drawdown is −20.8% against PUT's −32.7%, because it was out of the market for part of the falls.

![Drawdowns](outputs/figures/vrp_drawdowns.png)

## 5. Correlation

Yes, in part. Regressing the next 63 sessions' realised sector correlation on COR3M gives a slope of 0.713 (Newey-West se 0.074), N = 5167 days. R² is 0.439, so COR3M accounts for a bit under half of the variation in next quarter's realised correlation (N = 5167 days). The mean gap, implied minus realised, is −0.167. COR3M covers single stocks and this proxy uses sector ETFs, which correlate with each other more, so implied sits below realised; the gap is the proxy, not a correlation risk premium. The XLK chain priced an implied correlation of 0.497 on 2026-11-06, with 15 names covering 72.0% of the weight (N = 6 days with a value). It rose from 0.331 on 2026-10-29 to 0.565 on 2026-10-30, when the S&P 500 fell 1.8% and XLK 4.9%. Implied correlation rising in a sell-off is the textbook pattern.

| days | first | last | intercept | slope | slope se | R² |
| --- | --- | --- | --- | --- | --- | --- |
| 5167 | 2006-01-03 | 2026-08-10 | 0.2855 | 0.7130 | 0.0741 | 0.4388 |

| day | XLK vol % | names | covered weight % | implied correlation |
| --- | --- | --- | --- | --- |
| 2026-10-29 | 25.25 | 15 | 72.0 | 0.331 |
| 2026-10-30 | 33.72 | 13 | 66.1 | 0.565 |
| 2026-11-03 | 32.20 | 15 | 72.0 | 0.496 |
| 2026-11-04 | 26.25 | 15 | 72.0 | 0.331 |
| 2026-11-05 | 39.87 | 15 | 72.0 | 0.570 |
| 2026-11-06 | 35.88 | 15 | 72.0 | 0.497 |

Implied and realised move together, with a slope of 0.713 and an R² of 0.439. The shaded gap is the sector proxy, not a premium.

![COR3M against realised](outputs/figures/cor3m_vs_realised.png)

## 6. P&L attribution and hedging

On the live delta-hedged ^SPX straddles the median explained share is 0.931 (N = 21 position moves, a method demonstration). On a synthetic Black-Scholes path it is 0.952 (N = 21 daily steps). Gamma summed to −852.57 index points per straddle unit over the 21 live moves. Theta summed to 116.67 index points per straddle unit over the 21 live moves. Vega summed to −6.25 index points per straddle unit over the 21 live moves. The residual summed to 94.39 index points per straddle unit over the 21 live moves. Delta and the hedge cancel and vanna and volga are small, so the delta-hedged P&L summed to −631.17 over the same 21 moves. Hedging every step (k = 1) leaves an error sd of 0.241 under GBM. The same hedge leaves 0.813 under Heston: the hedge uses delta at the current vol but is blind to vol moves, so even continuous hedging leaves an unhedged vega P&L, and the error sd stops falling in proportion to the square root of k. The means are not comparable, because the 2 drifts differ. Hedging less often raises the GBM error sd to 1.763 at k = 65, 5 days between hedges. It cuts cost: the GBM mean cost falls from 0.106 at k = 1 to 0.014 at k = 65.

| model | k | error mean | error sd | cost mean |
| --- | --- | --- | --- | --- |
| gbm | 1 | 0.002 | 0.241 | 0.106 |
| gbm | 13 | 0.002 | 0.862 | 0.029 |
| gbm | 65 | 0.012 | 1.763 | 0.014 |
| heston | 1 | 0.001 | 0.813 | 0.104 |
| heston | 13 | −0.010 | 1.166 | 0.029 |
| heston | 65 | −0.008 | 1.947 | 0.014 |

## Risk report

[`outputs/reports/risk_2026-11-06.pdf`](outputs/reports/risk_2026-11-06.pdf) is the 1-page report for 2026-11-06 (N = 7 capture days). Each vol is the contract's own SVI slice at its strike.

| contract | side | contracts | vol % | vol source | dollar delta | dollar gamma 1% | vega per pt |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ^SPX 2026-12-04 P 7125 | −1 | 10 | 22.67 | svi | 1833746 | −372608 | −6485 |
| ^SPX 2026-12-04 C 7650 | −1 | 10 | 15.41 | svi | −1818539 | −545831 | −6456 |
| AAPL 2027-01-15 C 350 | 1 | 20 | 24.33 | svi | 331071 | 25760 | 1191 |
| NVDA 2026-12-18 P 174 | −1 | 15 | 54.58 | svi | 84063 | −5317 | −340 |

The worst cell of the grid loses 418.6 thousand dollars, at spot −10% and vol +5 points. 1 of 9 limits is breached: ^SPX dollar gamma of −918,440 against a limit of 250,000, which the short wings produce and the report is meant to show.

## What this does not do

- The live window is a few weeks, so nothing built on captured chains is a statistical result.
- Option prices are Yahoo's delayed quotes at 15:30 New York, not exchange data.
- The COR3M comparison is a sector proxy, because COR3M covers single stocks and the realised side uses sector ETFs.
- The timed PUT result is 1 specification of a family of 5, and its gain over PUT does not survive the deflation.
- The risk book is a sample, not a real portfolio.

`instructions/`, `review/`, `decisions/` and `PLAN.md` are the record of how this was built. The source outline is in [`project_outline/`](project_outline/). MIT licence, see [`LICENSE`](LICENSE).
