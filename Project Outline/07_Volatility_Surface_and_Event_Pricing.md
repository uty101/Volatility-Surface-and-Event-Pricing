# Volatility Surface and Event Pricing

**Repo name:** `Volatility-Surface-and-Event-Pricing`

## Purpose

Build a working view of how the listed options market prices risk and events: price options and their Greeks, back out implied volatility, fit an arbitrage-free volatility surface, read the implied probability distribution off it, measure the move the market expects around earnings and macro events, and test whether any of it can be traded after costs. Every number is validated, tested and reproducible, with QuantLib as the external check.

---

## Data

- **Option chains:** yfinance option chains for SPY, QQQ, sector ETFs (XLK, XLE, XLF) and 15 to 20 large single stocks, including the largest XLK holdings so index and constituent vols can be compared.
- **History is collected, not downloaded.** Free sources only give the current chain, so a scheduled job (Dagster with failure sensors, or a GitHub Actions cron) snapshots every chain once a day after the close into Parquet and DuckDB. This job is built first, since every module that studies change over time depends on the history it builds up.
- **Underlying prices and dividends:** yfinance daily history.
- **Rates:** SOFR or US Treasury bill yields from FRED (fredapi).
- **VIX and VIX futures term structure:** yfinance and CBOE published data.
- **Earnings dates:** yfinance calendar, cross-checked against company investor relations pages.
- **Cleaning rules, written down as invariants:** drop quotes with a zero bid, crossed markets, bid-ask spreads wider than a set share of mid, and stale last-trade times. Build the surface from out-of-the-money options only. Log every rule with a count of rows dropped.

---

## Modules

### 1. Pricing
- Black-Scholes-Merton with a continuous dividend yield, and Black-76 for options on futures.
- Cox-Ross-Rubinstein binomial tree for American exercise, reporting the early exercise premium per contract.
- Put-call parity used to back out the forward, implied dividend and implied rate for each expiry before any implied vol is solved.

### 2. Greeks
- Analytic delta, gamma, vega, theta and rho, plus vanna and volga.
- Every analytic Greek tested against a finite-difference bump; every price tested against QuantLib's `AnalyticEuropeanEngine` and binomial engine.
- Book-level Greeks aggregated by underlying and by expiry.

### 3. Implied volatility
- Newton-Raphson on vega with a Brenner-Subrahmanyam starting guess, falling back to Brent's method when vega is too small (deep in or out of the money, short-dated).
- No-arbitrage price bounds checked before solving; quotes outside them are flagged, not forced.
- Round-trip test: price at a known vol, solve, recover the vol to tolerance across a grid of strikes and maturities.

### 4. Volatility surface
- Each expiry fitted with Gatheral's raw SVI in total variance against log-moneyness.
- SSVI across expiries so the surface is one consistent object.
- Arbitrage checks as tests: no butterfly arbitrage (density stays non-negative) and no calendar arbitrage (total variance rises with maturity). Failed fits are rejected and logged.
- Daily outputs stored for study over time: ATM vol, 25-delta skew, risk reversal and butterfly, and term structure slope.

### 5. Risk-neutral distribution
- Breeden-Litzenberger: second derivative of call prices across strikes, taken from the fitted SVI smile so it is smooth.
- Full implied probability distribution per expiry, the probability of finishing above or below any level, and the probability of a move larger than a given size.
- Compared against the realised distribution of returns over the same horizon.

### 6. Event pricing
- **Straddle-implied move:** at-the-money straddle on the first expiry after the event, as a share of spot.
- **Term structure method:** split total variance into normal daily variance and a one-off event variance, using the expiries either side of the event date, to isolate the jump priced for that day.
- **Event study:** for each name and earnings date collected, compare the implied move with the realised move. Report how often moves are over- or under-priced, by sector and company size.
- The same method applied to macro events (CPI, FOMC) using SPY and the VIX futures curve.

### 7. Relative value and dispersion
- Implied correlation: index implied vol (XLK) against the index-weighted vols of its top holdings, backing out the correlation being priced.
- Implied against realised correlation tracked daily as the dispersion signal.
- Relative value screens: each name's implied vol against its own history and its sector, and skew against its history.

### 8. Volatility risk premium research
- Implied against realised volatility, with realised vol forecast by GARCH (`arch`).
- Backtests of a delta-hedged short straddle and a variance-style short volatility position, after bid-ask costs, reporting drawdowns and tail losses in full.
- Point-in-time data only, every specification logged, and results judged after costs and against the number of variants tried.

### 9. P&L attribution
- Delta-hedged option positions simulated day by day.
- Daily P&L split into delta, gamma, theta, vega and an unexplained residual using the Greeks from module 2.
- Hedging error and transaction cost compared across hedging frequencies.

### 10. Risk report
- Spot and vol shock grid (spot ±10%, vol ±5 points) on a sample book, with P&L for each cell.
- Greek limits per underlying, with breaches flagged.
- One-page daily PDF risk report (reportlab).

---

## Engineering standard

- `uv` with a lockfile, `ruff`, `pytest`, GitHub Actions on every commit.
- `CLAUDE.md` with written invariants, each tested before its code: put-call parity holds, implied vol round-trips, the surface is arbitrage-free, the density integrates to 1, Greeks match finite differences, and each attribution day reconciles to total P&L within tolerance.
- Validation against QuantLib for prices, Greeks and implied vols.
- Daily data snapshot as a Dagster job with failure sensors.
- Dashboard (TypeScript and Recharts, or Streamlit): surface plot, smile per expiry, term structure, implied distribution, upcoming earnings with implied against historical moves, and the risk grid.
- Dockerfile with the base image pinned by digest.
- README: what it does, how to run it, results with honest caveats, and what it does not do.

---

## Build order

**Phase 1:** the daily chain snapshot job; modules 1, 2 and 3 with QuantLib validation and tests.

**Phase 2:** modules 4, 5 and 6: surface, implied distributions and event moves.

**Phase 3, as history builds:** modules 7 to 10 and the dashboard.