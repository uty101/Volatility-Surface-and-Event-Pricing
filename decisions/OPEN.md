# Open decisions

Items are appended as they are found. Each has 2 concrete options; the reviewer picks one in the next instruction file. None is decided by Claude Code.

## Found in session 0 while writing PLAN.md

**O-1 Driver code and helpers not in Section 6.1** (capture health, EEP table, IV summary, daily surface run, tail and PIT tables, live correlation, live straddles). (a) Helpers live in the `volsurf/` module of their section, and drivers are stages of `scripts/run_all.py --stage <name>`. (b) One script per step, `scripts/build_<step>.py`, which `run_all.py` calls in order.

**O-2 Output file names the kickoff does not fix.** PLAN.md proposes: `tests/fixtures/underlying_sample.csv`, `tests/fixtures/earnings_sample.csv`, `data/raw/ssga/xlk_holdings_YYYY-MM-DD.csv`, and in `outputs/tables/`: `clean_log_fixture.csv`, `parity_forwards_fixture.csv`, `iv_summary.csv` (fixed), `svi_fits.csv`, `surface_daily.csv`, `calendar_violations.csv`, `tail_probs.csv`, `pit.csv`, `events.csv`, `event_summary.csv`, `cor3m_study.csv`, `implied_corr_live.csv`, `rv_screen.csv`, `vrp_monthly.csv`, `strategies.csv`, `strategy_stats.csv`, `live_straddles.csv`, `hedging_frequency.csv`, `attribution_live.csv`, `risk_grid.csv`, `limit_breaches.csv`; in `outputs/figures/`: `event_scatter.png`, `event_term_structures.png`, `vrp_vix2_vs_rv.png`, `vrp_cumulative.png`, `vrp_drawdowns.png`; and `outputs/reports/risk_{day}.pdf`. (a) Use these names. (b) The reviewer supplies the names in each section's instruction file.

**O-3 Price file layout and ticker set (1.1).** (a) Wide frames indexed by date: `close.parquet` holds unadjusted Close for the 31 captured underlyings other than `^SPX`; `index.parquet` has columns `^GSPC` (close) and `^SP500TR` (close); `sectors.parquet` adjusted close per sector SPDR; `dividends.csv` columns date, ticker, dividend; `^SPX` closes for macro events come from `^GSPC`. (b) Long frames (date, ticker, close, adj_close), with `^SPX` pulled under its own ticker and stored in `close.parquet`.

**O-4 Fixture day (1.2).** (a) 2026-10-28, the first capture day. (b) The latest accepted snapshot day when Section 1 runs.

**O-5 Accepted chains asset (Section 3.3 "snapshot day", 1.4 gap).** (a) A non-test chains asset exists for the session and its SNAPLOG shows at least `min_tickers_ok` tickers with status ok. (b) Any non-test chains asset exists; tickers are then used individually when their status is ok.

**O-6 Parsed XLK holdings CSV columns (1.1).** (a) ticker, name, weight (decimal), shares, as_of_date, rows with a blank ticker or cash lines dropped. (b) Every workbook column, snake-cased, rows kept as served.

**O-7 FRED missing values (1.3).** FRED marks holidays with `.`. (a) Drop missing rows per series and use each tenor's latest non-missing observation dated ≤ t − 1. (b) If any tenor's latest row dated ≤ t − 1 is missing, the whole curve for day t is blank and that day's IVs get a status.

**O-8 Moneyness bucket for the EEP table (2.3).** (a) k = ln(K/F) bins (−∞, −0.10], (−0.10, −0.02], (−0.02, 0.02], (0.02, 0.10], (0.10, ∞). (b) Black forward delta of the OTM option in bins [0, 0.10), [0.10, 0.25), [0.25, 0.40), [0.40, 0.50].

**O-9 Status and flag vocabularies.** Fixed so far: IV method `newton`, `brent`, `bounds`; SVI `too_few`, `butterfly_fail`; EVENTS `no_event_premium`; flags `stale`, `after_close`, `extrapolated`. Not fixed: IV flag for a `^SPX` expiry rejected by the parity gate, SVI status for an accepted fit and for one accepted after the penalised refit, SURFACE_DAILY status, EVENTS status for a missing straddle or missing pre-event snapshot, and how several flags on one IV row combine. (a) `parity_fail`; `ok` and `ok_refit`; `ok` or `too_few_expiries`; `no_straddle` and `no_pre_snapshot`; flags joined with `|`. (b) The reviewer supplies the vocabulary in each section's instruction file.

**O-10 SSVI fit details (4.2).** (a) SLSQP from 1 start (ρ, η, γ) = (−0.5, 1.0, 0.5), equal weights on every accepted quote, cumulative-maximum binding recorded as a boolean `theta_capped` in a table `outputs/tables/ssvi_theta.csv` (day, ticker, expiry, theta_svi, theta_used, theta_capped). (b) SLSQP from a 3 × 3 × 3 grid of starts keeping the lowest objective, weights 1 / n_quotes per expiry, binding counted in SURFACE_DAILY `status`.

**O-11 Straddle strike (5.7, 6.1).** At the strike nearest F the call or the put may have been removed by cleaning, and 2 strikes may be equally near. (a) Use the nearest strike among those with both clean mids; a tie goes to the lower strike. (b) Use the nearest listed strike; a missing side gives status `no_straddle` and blank M_s; a tie goes to the lower strike.

**O-12 Which earnings row defines an event (6.1).** The earnings asset is captured daily and the timestamp can change. (a) The row from the pre-event snapshot day's earnings asset. (b) The row from the latest earnings asset that lists the event.

**O-13 Interval methods (5.7).** (a) Percentile bootstrap interval and Clopper-Pearson binomial interval. (b) BCa bootstrap interval and Wilson binomial interval.

**O-14 PIT slice, realised price and density figure (5.2).** (a) One u per expiry from the first snapshot day with an accepted slice for it; S_realised is the unadjusted close on the expiry date (`^SPX` from the O-3 source); the figure shows the accepted expiries nearest 30, 90 and 180 days on the last day. (b) One u per snapshot day and expiry; S_realised as in (a); the figure shows the first 3 accepted expiries on the last day.

**O-15 Live realised vol inputs and RV z-score (5.8, 7.2).** (a) Adjusted close log returns; z-score uses the mean and standard deviation (ddof 1) of the name's prior snapshot days, excluding today. (b) Unadjusted close log returns; z-score includes today in the mean and standard deviation (ddof 0).

**O-16 Timed PUT T-bill and switch rule (5.9).** (a) T-bill return for month m+1 is DTB3 averaged over month m+1 / 1200; holding PUT in the first month is not a switch. (b) DTB3 averaged over month m (known at the decision) / 1200; the first position counts as a switch.

**O-17 Sharpe units in the spec log and the deflated Sharpe (5.9).** (a) `spec_log.csv` stores annualised Sharpe; the deflated Sharpe converts every Sharpe to monthly (÷ √12) and uses n_obs in months. (b) `spec_log.csv` stores monthly Sharpe, and tables show annualised Sharpe separately.

**O-18 Hedging simulation (5.10, 9.2).** `[sim] days = 21` while the text says a 30-day straddle. (a) T = days / 252, time step 1 / (252 × `steps_per_day`); Heston by full-truncation Euler; straddle priced and hedged with BSM delta at σ (GBM) and at √θ (Heston); hedging error = terminal P&L of the short straddle sold at its model price, including hedge P&L, before costs. (b) T = 30/365 with 21 × `steps_per_day` steps; Heston by Andersen QE; Heston price and delta from QuantLib's analytic Heston engine; hedging error as in (a).

**O-19 Limits per underlying (5.11).** `[limits]` holds 1 value per measure. (a) Apply the same limits to every underlying. (b) The reviewer adds a per-underlying limits table to `config.toml`.

**O-20 Dollar gamma per 1% move (5.11).** (a) Γ × S² × 0.01 × 100 × contracts × side. (b) ½ × Γ × (0.01 × S)² × 100 × contracts × side (the P&L of a 1% move from gamma).

**O-21 Book position selection (5.11).** (a) Expiry with calendar days nearest `target_days` (tie to the shorter), then the strike on it whose BSM delta at the SSVI vol is nearest `target_delta` (tie to the lower strike), on the report day. (b) The reviewer fixes each position's contract once, on the first captured day, and holds it.

**O-23 Rule e for `^SPX` in Section 1 (1.3).** The European bounds need the parity D and F that Section 3.1 builds. (a) In Section 1, rule e for `^SPX` uses D and F from Conventions 4.6 and 4.8 with q = 0 only as a placeholder, and Section 3 reruns cleaning on the parity forward. (b) Rule e is skipped for `^SPX` in Section 1 (logged as 0 rows with a note) and applied in Section 3 after the parity forward exists.

**O-24 IV solvers for the EEP table (2.3).** `iv_american` and `iv_european` belong to Section 3. (a) Step 2.3 solves both vols with `scipy.optimize.brentq` on `crr` and `bsm` directly. (b) Step 2.3's table is built in Section 3 after step 3.2.

## Found in session 0 while building the capture (step 0.1)

**O-22 Capture details the kickoff leaves open.** Implemented as option (a) in each case so that capture could start on 2026-10-28; rule 15 means only an instruction file can change them. (a) is what runs now.
1. Window bounds: (a) inclusive at both ends, 15:25:00 ≤ New York time ≤ 16:30:00. (b) Start inclusive, end exclusive.
2. `snap_utc` in CHAINS: (a) the UTC time each expiry's chain was fetched, so T is exact per expiry. (b) 1 time per underlying, taken when its first chain is fetched.
3. Ticker success for `min_tickers_ok`: (a) status `ok` means the price and every kept expiry were fetched; `partial` (some expiries failed after retries) and `error` do not count. (b) `partial` also counts.
4. Retries: (a) 1 attempt plus `retries` retries, sleeping `backoff_s[i]` before retry i. (b) `retries` attempts in total.
5. Out-of-window log: (a) 1 line printed and appended to `<out>/snapshot.log`. (b) Printed only.
6. Upload failure: (a) files stay in `--out`, a line is logged, and the exit code is 2 (1 takes precedence when too few tickers succeeded). (b) Exit code 0 on upload failure.
7. `snap_utc` in UNDERLYING: (a) the UTC time the ticker's capture started (before its first chain). (b) The UTC time its 1-minute price was fetched (after its chains).
8. Ticker with a price and chain rows but a failed `options` listing cannot happen (no expiries means no rows); a ticker whose earnings call fails keeps its chain status and records `earnings_error` in SNAPLOG. (a) Earnings failures do not affect status. (b) They make the ticker `partial`.
