# instructions/00_kickoff.md: Session 0 instructions for Claude Code

Repo: https://github.com/uty101/Volatility-Surface-and-Event-Pricing
Project: Volatility Surface and Event Pricing (quant project 7 of the home-built series)
Source doc: `Project Outline/07_Volatility_Surface_and_Event_Pricing.md`
Workflow: `WORKFLOW.md` (already committed by the owner; do not rewrite it)

This document is the specification. Nothing in it is yours to redesign. Where it corrects or tightens the source doc, this document wins.

---

## 0. How this repo is run

**Session 0 is different from earlier projects.** Free sources only give today's option chains, so every trading day without a snapshot is history lost for good. Session 0 therefore writes the plan and scaffolding **and** builds and switches on the daily chain capture (Section 9). It writes no pricing, surface or analysis code. After session 0, session number equals section number: Session N builds all of Section N of `PLAN.md`, every step in it, in one session, and nothing from any other section. A reviewer (Claude in chat) reads the repo once per section and either approves it or returns fixes. You never start the next section until a new session tells you to.

Rules that hold for every session:

1. **No design choices.** Every parameter, definition, signature, schema, convention and file path is fixed in this document, in `PLAN.md` or in a later instruction file. If something is genuinely unspecified, append it to `decisions/OPEN.md` with 2 concrete options, finish every other step in the section that does not depend on it, and report it in the review file. Do not pick an option yourself.
2. **Commits.** One commit per step, message `step X.Y: <one line>`, on `main`. Push once at the end of the section. Never force push, never rewrite history, never amend a pushed commit. Stage files by explicit path; never `git add -A` or `git add .`.
3. **One review file per section**: `review/section_N.md`, following `review/TEMPLATE.md` exactly.
4. **Stop conditions.** Stop the section, write the review and status files, and push if any of these happen: a data pull fails; a test from an earlier section fails; a cross-check or gate in this document fails its stated threshold; a result can only be produced by making a design choice; a step would need a file or function outside that section's scope. Do not work around any of them.
5. **Tests are fixed.** Never loosen a tolerance, skip, xfail, or rewrite a test so that it passes. If a test in this document is wrong, stop under rule 4 and say why. A tolerance marked **MEASURE** is not yet fixed: the step measures the quantity, prints the measurement in the review file, and the test asserts the bound the reviewer sets in the next instruction file. Until then that test asserts only that the measurement is finite.
6. **Config is fixed.** Every parameter lives in `config.toml`. No numeric parameter is hard-coded in `volsurf/`. The only exception is a constant written inside a formula in this document or an instruction file, which may be a literal with a comment citing the section where the formula is written. Do not change a value set in this document.
7. **Tests build what they read.** No test may depend on `outputs/`, `data/processed/` or `data/snapshots/` already existing. Tests read only `data/raw/` (committed), `tests/fixtures/` (committed) or synthetic data they generate. The full suite runs offline: `pytest -p socket --disable-socket` must pass.
8. **No network outside `scripts/`.** Only `scripts/snapshot.py`, `scripts/pull_data.py` and `scripts/pull_snapshots.py` touch the network. Nothing in `volsurf/` or `tests/` does; tests drive any client with a fake session object.
9. **Determinism.** Every random draw uses `numpy.random.default_rng(seed)` with a seed from `config.toml`. Running the same section twice produces byte-identical CSV outputs and byte-identical PDFs. CSV float format is `%.10g`, line endings LF, UTF-8, no index column unless a schema in Section 6 names one.
10. **Evidence, not summaries.** Every numeric claim in a review file is backed by raw rows printed with `DataFrame.to_string()`, never by a description of them.
11. **Instructions and status live in the repo.** Every session's instructions are a file committed to `instructions/` before the session starts. The session prompt only names the file. Read it from the repo and follow it; never edit an instruction file. Reviewer comments arrive inside the next instruction file. Every session ends by writing `instructions/NN_<name>.status.md` with: outcome (completed or stopped), the last step reached, the reason for any stop, every question or blocker for the reviewer, and the output of `git log origin/main --oneline -3`; then commit and push it and stop. This applies to sessions that stop early: the status file is always written and always pushed. Nothing is relayed by chat.
12. **Fresh-clone check at the end of every section from Section 1 on.** Clone the pushed repo into a short temp path, `uv venv --python 3.12`, install from `requirements-lock.txt` then `pip install -e . --no-deps`, run `pytest -p socket --disable-socket -q`, and paste the full output into the review file.
13. **Precedence.** A later instruction file beats `PLAN.md`, which beats this document, which beats the source doc.
14. **Do not stage `CLAUDE.md` or `PLAN.md`** after session 0 unless an instruction file says to. If your own safety check refuses to edit `CLAUDE.md`, report it in the status file and the owner will commit it.
15. **The capture job is not touched after session 0** except by an instruction file that names it. No section may change `scripts/snapshot.py`, `.github/workflows/snapshot.yml`, the local scheduled task, or the `snapshots` release, because a broken change silently loses days of data that can never be recovered.
16. **Python 3.12 everywhere.** The lock is built with `uv pip compile pyproject.toml --extra dev --universal --python-version 3.12 -o requirements-lock.txt`; every venv with `uv venv --python 3.12`.

---

## 1. What the project answers

1. Does the pricer (Black-Scholes-Merton, Black-76, CRR tree) match QuantLib, and how large is the early exercise premium across the single-name chains?
2. What does the S&P 500 surface look like each day, does the fitted surface stay free of butterfly and calendar arbitrage, and how did ATM vol, skew and term structure move over the capture window?
3. For each earnings event caught live, what move did the options price (straddle and term structure methods), what move happened, and is the gap distinguishable from 0 at the sample size we have?
4. Over 1990 to 2026, does selling S&P 500 volatility pay after costs, and does timing it on the gap between implied variance and a GARCH forecast improve the deflated Sharpe ratio?
5. Does high implied correlation (Cboe COR3M) predict high realised correlation, and what correlation is the XLK chain pricing against its holdings?
6. On a delta-hedged option book, how does daily P&L split into delta, gamma, theta, vega and residual, and how does hedging frequency change hedging error and cost?

---

## 2. Corrections to the source doc (already applied below)

1. **History is the binding constraint.** Capture starts on 2026-10-28, so the live window is weeks, not years. Every result built only on captured chains (surface dynamics, event study, live implied correlation, P&L attribution on real marks) is labelled a method demonstration with its N stated. Results that need years (question 4 and the long half of question 5) are built on published Cboe and FRED series with decades of history instead.
2. **Volatility risk premium backtest.** A delta-hedged short straddle backtest on a few months of captured chains says nothing. Module 8 uses VIX against forward realised S&P 500 variance from 1990, and the Cboe PUT and BXM indices as investable short-volatility return series, with captured chains used only for a live out-of-sample delta-hedged straddle shown descriptively.
3. **Correlation history.** Module 7's long history uses Cboe COR3M (daily from 2006-01-03) against forward realised correlation of the 9 original Select Sector SPDRs, labelled a sector-level proxy. The XLK implied correlation from captured chains is the live part.
4. **Put-call parity is an inequality for American options.** SPY, QQQ, sector ETF and single-stock options are American. The forward is backed out by parity only for `^SPX` (European, PM-settled SPXW contracts only). For American underlyings the forward is F = S exp((r − q)T) with r from Treasury yields and q from trailing dividends, and implied vols are American implied vols solved on the CRR tree (Section 5.3), which is what "de-Americanising" means here.
5. **Snapshot timing.** Option quotes on Yahoo after the close frequently show a zero bid, which the cleaning rules would drop. Snapshots run at 15:30 New York time, inside the session, with a start window of 15:25 to 16:30 to absorb scheduler delay; rows captured after 16:00 are flagged.
6. **Scheduler.** Dagster is dropped (no always-on host). The primary capture is a GitHub Actions cron; a Windows Task Scheduler job on the owner's machine is the backup and uploads only on days the primary missed. GitHub Actions cron is UTC only, so 2 crons cover both sides of the US clock change on 2026-11-01 and the script itself checks the New York time.
7. **Storage.** Daily snapshot files are uploaded as assets of a GitHub release tagged `snapshots`, never committed to git history. `scripts/pull_snapshots.py` downloads them and records their hashes.
8. **DuckDB, Dockerfile and the TypeScript dashboard are dropped.** pandas and Parquet are enough for this data size; the dashboard is replaced by committed figures and the README.
9. **Stale last-trade rule.** Far OTM options often have no recent trade but a live two-sided quote, and they are exactly the wings SVI needs. Staleness is a reported flag, not a drop rule.
10. **Earnings timing.** The realised move depends on whether a company reports before the open (BMO) or after the close (AMC). Timing comes from the time of day in yfinance earnings timestamps (Section 4.11) and is overridden from investor relations pages via `data/manual/earnings_overrides.csv`, filled by the reviewer.
11. **Tail probabilities.** Beyond the last quoted strike the density is the SVI wing, not market information. Tail probabilities are reported only inside the quoted strike range; anything beyond is labelled extrapolated.
12. **Breeden-Litzenberger.** The density is computed analytically from the SVI fit (Gatheral's formula, Section 5.6) and cross-checked against a finite-difference second derivative of call prices.
13. **VIX futures curve.** Historical VIX futures settlements are not needed; the term structure uses the Cboe VIX9D, VIX, VIX3M and VIX6M indices.
14. **Dispersion with partial constituents.** XLK weights cover only the names captured. Weights are renormalised over captured names and the covered weight is reported beside every implied correlation.
15. **Rates.** FRED series are read from `fredgraph.csv` (no API key). Value for snapshot day t uses the latest FRED observation dated t − 1 or earlier, so nothing is used before it was published.
16. **CRR against QuantLib.** QuantLib's `"crr"` binomial engine uses a drift-approximated up probability, so it does not match the textbook CRR tree exactly at a given step count. The reviewer measured both against each other: at 2000 steps the largest gap over a 252-case grid was 6.8e-5 × S, and the textbook European tree was within 3.9e-5 × S of the analytic price. Tolerances in Section 8 are set from these measurements.

---

## 3. Universe, data and sample

### 3.1 Captured underlyings (`config.toml [universe]`)

| group | tickers |
|---|---|
| index (European, cash settled) | `^SPX` |
| ETFs | SPY, QQQ, XLK, XLE, XLF |
| XLK holdings | NVDA, AAPL, MSFT, AVGO, ORCL, AMD, CSCO, CRM, IBM, PLTR |
| other single names | AMZN, META, GOOGL, TSLA, NFLX, JPM, BAC, XOM, CVX, UNH, WMT, HD, DIS, UBER, SHOP, ABNB |

32 underlyings. Expiries captured: every listed expiry with 0 < calendar days to expiry ≤ 400. For `^SPX` keep only contracts whose `contractSymbol` starts with `SPXW` (PM-settled); drop `SPX` AM-settled contracts and count them in the log.

### 3.2 Sources

| need | source | stored as |
|---|---|---|
| option chains | yfinance `Ticker(t).options`, `Ticker(t).option_chain(expiry)` | release asset `chains_YYYY-MM-DD.parquet` |
| underlying at snapshot | yfinance `Ticker(t).history(period="1d", interval="1m")` last row (price, timestamp) | release asset `underlying_YYYY-MM-DD.csv` |
| earnings calendar | yfinance `Ticker(t).get_earnings_dates(limit=12)` for single names | release asset `earnings_YYYY-MM-DD.csv` |
| daily prices and dividends | yfinance `auto_adjust=False`, daily, 1989-12-01 to the pull date | `data/raw/prices/close.parquet`, `data/raw/prices/dividends.csv` |
| S&P 500 history | yfinance `^GSPC` (close), `^SP500TR` | `data/raw/prices/index.parquet` |
| sector SPDRs | yfinance XLB, XLE, XLF, XLI, XLK, XLP, XLU, XLV, XLY, adjusted close | `data/raw/prices/sectors.parquet` |
| VIX family | `https://cdn-api.cboe.com/api/global/us_indices/daily_prices/{VIX,VIX9D,VIX3M,VIX6M}_History.csv` | `data/raw/cboe/{name}.csv` |
| PUT, BXM, COR3M | `https://cdn-api.cboe.com/api/global/delayed_quotes/charts/historical/_{PUT,BXM,COR3M}.json` (`data` array of date, open, high, low, close) | `data/raw/cboe/{name}.csv` (date, close) |
| Treasury yields | `https://fred.stlouisfed.org/graph/fredgraph.csv?id={DGS1MO,DGS3MO,DGS6MO,DGS1,DTB3}` | `data/raw/fred/{id}.csv` |
| XLK holdings | `https://www.ssga.com/us/en/intermediary/library-content/products/fund-data/etfs/us/holdings-daily-us-en-xlk.xlsx` | `data/raw/ssga/xlk_holdings_YYYY-MM-DD.xlsx` and a parsed CSV |
| NYSE sessions | `exchange_calendars` `XNYS` | computed, not stored |

The reviewer confirmed on 2026-10-27 that the Cboe endpoints answer: VIX history starts 1990-01-02, PUT 1991-03-04, COR3M 2006-01-03. Every pull writes `data/raw/MANIFEST.json` (pull time UTC, URL, library versions, row counts, first and last date, sha256 per file).

### 3.3 Samples

- **Capture window:** every NYSE session from 2026-10-28 on. A snapshot day is a session with an accepted `chains` asset.
- **Long history:** VRP from 1990-01-02, COR3M study from 2006-01-03, both to the last full month before the pull.
- **Earnings events:** every single-name earnings announcement whose event window (Section 4.11) lies inside the capture window and has a snapshot on the last session before the event.

---

## 4. Conventions

1. **Time to expiry.** T = (expiry at 16:00 New York − snapshot timestamp) / (365 × 86400 s), ACT/365 with intraday precision, using the snapshot time of that underlying's chain.
2. **Trading-day counts** (event method only): n(t, E) = number of XNYS sessions s with t < s ≤ E.
3. **Quote mid** = (bid + ask) / 2. Prices are per share (Yahoo's convention), contract multiplier 100 recorded but unused.
4. **Cleaning rules, applied in this order, each logged with rows dropped:** (a) bid ≤ 0; (b) ask ≤ bid; (c) mid < `min_mid`; (d) (ask − bid) / mid > `max_rel_spread`; (e) mid outside the no-arbitrage bounds of Section 5.3. Flags (kept, counted): `stale` if `lastTradeDate` is more than `stale_sessions` sessions before the snapshot or missing; `after_close` if captured after 16:00 New York.
5. **OTM selection for the surface:** calls with K ≥ F, puts with K < F.
6. **Rates.** CMT yields y (percent, bond-equivalent) from DGS1MO, DGS3MO, DGS6MO, DGS1 at tenors 1/12, 0.25, 0.5, 1 year, converted to continuous r = 2 ln(1 + y/200). Linear in T between tenors, flat beyond. Observation date ≤ t − 1 (Correction 15).
7. **Dividend yield (American underlyings).** q = (sum of cash dividends with ex-date in (t − 365 days, t]) / S_t, continuous. 0 if none.
8. **Forward.** `^SPX`: from parity regression (Section 5.2). Others: F = S exp((r − q)T).
9. **Log-moneyness** k = ln(K / F). Total implied variance w = σ² T.
10. **Units.** Vega per 1.00 of vol in code; tables report vega per vol point (÷ 100) and theta per calendar day (÷ 365). Rates and vols are decimals in code, percent only in tables.
11. **Earnings timing.** From the yfinance timestamp in New York time: before 09:30 → BMO; at or after 16:00 → AMC; 00:00 exactly or anything else → `unknown` (excluded until an override sets it). Event window: BMO on date D runs close(prev session of D) to close(D); AMC on D runs close(D) to close(next session). The **pre-event snapshot** is the last snapshot on a session strictly before the window's end close and no later than the window's start session. Realised move = ln(close_end / close_start), using unadjusted close.
12. **Constant-maturity vol.** σ_cm(τ) = √(w(τ)/τ), with w linear in T between the 2 bracketing accepted expiries' ATM total variance θ; no extrapolation (blank if τ is outside the accepted range).
13. **Calendar months** for any monthly aggregation use calendar-month periods, never `DateOffset`.
14. **Annualisation.** 252 trading days. Daily variance × 252; monthly return series × 12 for means, √12 for vol.
15. **Failed fits and failed gates** keep their rows with a `status` column and blank results, never a fallback number.

---

## 5. Methods (fixed)

Parameter names in backticks refer to `config.toml` keys; a prefix names the table (`svi_starts` is `[svi] starts`, `event_min_n` is `[events] min_n`, `sim_paths` is `[sim] paths`, `density_int_tol` is `[density] int_tol`). Where a key appears under one table only, the bare name is used.

### 5.1 Pricing (`volsurf/pricing.py`)

- BSM: d1 = [ln(S/K) + (r − q + σ²/2)T] / (σ√T), d2 = d1 − σ√T. C = S e^(−qT) N(d1) − K e^(−rT) N(d2); P = K e^(−rT) N(−d2) − S e^(−qT) N(−d1).
- Black-76: F, discount D = e^(−rT): C = D[F N(d1) − K N(d2)], d1 = [ln(F/K) + σ²T/2]/(σ√T).
- CRR: Δt = T/N, u = e^(σ√Δt), d = 1/u, p = (e^((r−q)Δt) − d)/(u − d), backward induction with early exercise max(continuation, intrinsic) at every node for American. Vectorised over nodes with numpy. Raise if p ∉ (0, 1).
- Early exercise premium = CRR American − CRR European at the same N.
- `N_validate` = 2000, `N_prod` = 200.

### 5.2 Forward from parity, `^SPX` only (`volsurf/forwards.py`)

Per expiry, take the `parity_n_strikes` strikes nearest spot that have clean call and put mids. OLS of C − P on K: C − P = D F − D K, so slope = −D and intercept = D F. Outputs D, F, implied r = −ln(D)/T, and the R². Gate: R² ≥ `parity_r2_min`, else the expiry is rejected for that day. The gap between implied r and the Treasury r (Convention 4.6) is reported per expiry, not tested.

### 5.3 Implied volatility (`volsurf/iv.py`)

- Bounds before solving (European): call max(0, D(F − K)) < C < D F; put max(0, D(K − F)) < P < D K. American: call ≥ max(S − K, 0), put ≥ max(K − S, 0), and below S (call) or K (put). Outside → flag `bounds`, no vol.
- European solver: Brenner-Subrahmanyam start σ0 = √(2π/T) × C/(D F) using the OTM price; Newton on vega for at most `newton_max_iter` steps with tolerance `iv_tol` on price; if vega < `min_vega` × S at any step or Newton leaves [`iv_lo`, `iv_hi`], switch to Brent (`scipy.optimize.brentq`) on [`iv_lo`, `iv_hi`].
- American solver: Brent on [`iv_lo`, `iv_hi`] of CRR American price at `N_prod` steps minus mid.
- Which: `^SPX` uses European on the parity forward; every other underlying uses American on S, r, q.

### 5.4 SVI per expiry (`volsurf/svi.py`)

- Raw SVI: w(k) = a + b[ρ(k − m) + √((k − m)² + s²)].
- Fit: minimise Σ (√(w(k_i)/T) − σ_i)² over OTM clean quotes with an implied vol, with constraints b ≥ 0, |ρ| ≤ 0.999, s ≥ `svi_s_min`, a + b s √(1 − ρ²) ≥ 0, b(1 + |ρ|) ≤ 4. SLSQP from the `svi_starts` start vectors in config; keep the lowest objective. Expiries with fewer than `svi_min_quotes` quotes are skipped with status `too_few`.
- Butterfly check: g(k) = (1 − k w′/(2w))² − (w′²/4)(1/w + 1/4) + w″/2 on a grid of 401 points over [k_min − 0.5, k_max + 0.5]; pass if min g ≥ −1e-10. On fail, refit once adding penalty `svi_penalty` × Σ max(0, −g)² on that grid; still failing → status `butterfly_fail`, rejected.
- Calendar check between consecutive accepted expiries: w_{i+1}(k) ≥ w_i(k) − 1e-10 on the union grid. Violations are recorded per pair (no refit); SSVI below is the calendar-consistent surface.

### 5.5 SSVI across expiries (`volsurf/ssvi.py`)

- θ_i = accepted per-expiry SVI w_i(0), made non-decreasing in T by cumulative maximum (recorded where it binds).
- w(k, θ) = (θ/2)[1 + ρ φ k + √((φ k + ρ)² + 1 − ρ²)], φ(θ) = η / (θ^γ (1 + θ)^(1 − γ)).
- Fit ρ, η, γ by least squares on implied vol over all accepted expiries' quotes, with |ρ| ≤ 0.999, η > 0, 0 < γ ≤ 0.5 and η(1 + |ρ|) ≤ 2 (Gatheral-Jacquier sufficient condition for no butterfly arbitrage; with θ non-decreasing it is free of calendar arbitrage).
- Daily metrics from SSVI at τ = 30/365 and 90/365 (θ by Convention 4.12): ATM vol; 25-delta call and put vols, with strikes solved from the Black forward delta N(d1) = 0.25 (call) and N(d1) − 1 = −0.25 (put); RR = σ_25c − σ_25p; BF = (σ_25c + σ_25p)/2 − σ_ATM; term slope = σ_ATM(90d) − σ_ATM(30d).

### 5.6 Risk-neutral density (`volsurf/density.py`)

- From an SVI slice: d− = −k/√w − √w/2, p_k(k) = g(k) / √(2π w) × exp(−d−²/2), density in K: q(K) = p_k(ln(K/F)) / K.
- Cross-check: q_fd(K) = e^(rT) ∂²C/∂K² by central differences of Black prices from the same slice, step `bl_dk` × F.
- Tests: ∫ q dK = 1 within `density_int_tol` over [F e^(−8√w), F e^(8√w)]; ∫ K q dK = F within the same relative tolerance; q ≥ 0 when the slice passed the butterfly check.
- Reported per expiry: P(S_T > x) and P(S_T < x) for x on a grid of moves ±2.5%, ±5%, ±10%, ±20%, and P(|ln(S_T/F)| > m); each flagged `extrapolated` when x lies outside [K_min, K_max] of the quotes used.
- Realised comparison: probability integral transform u = P_Q(S_T ≤ S_realised) for every captured expiry that has expired; histogram of u (descriptive; uniform only if risk-neutral = physical, which it is not expected to be).

### 5.7 Event pricing (`volsurf/events.py`)

For each event with a pre-event snapshot (Convention 4.11), with E1 < E2 the first 2 accepted expiries ending at or after the window's end session, and θ1, θ2 their ATM total variances from per-expiry SVI:

- **Straddle move** M_s = (C_K + P_K) / S at the strike K nearest F on E1 (mids; American as quoted).
- **Term structure move:** daily diffusive variance v_d = (θ2 − θ1) / (n2 − n1), event variance v_e = θ1 − v_d (n1 − 1), with n_i = n(t, E_i). If v_e ≤ 0 → status `no_event_premium`, M_t blank. Else M_t = √(2/π) × √v_e (expected absolute log move under a normal jump).
- **Realised move** R = |ln(close_end / close_start)|.
- Per event: R, M_s, M_t, ratio R/M_t, ln(R/M_t).
- Summary (only if N ≥ `event_min_n`, else descriptive table only): mean of ln(R/M_t) with an iid bootstrap 90% interval (`event_boot_reps` draws, seed from config), share of events with R > M_t with a binomial 90% interval, and the same split by group (Section 3.1) only where a group has ≥ `event_min_group_n` events.
- Macro events: `^SPX` with dates from `data/manual/macro_events.csv` (date, kind, release time), supplied by the reviewer in instruction 06; same formulas with the event window close(prev session) to close(event date).

### 5.8 Implied correlation (`volsurf/correlation.py`)

- Live: ρ_impl = (σ_I² − Σ w_i² σ_i²) / (Σ_{i≠j} w_i w_j σ_i σ_j), σ = 30-day constant-maturity ATM vol (Convention 4.12), I = XLK, weights = XLK holdings weights renormalised over captured names; covered weight reported. Realised over the next 21 sessions computed the same way from realised vols, plus the average pairwise realised correlation.
- Long history: COR3M (÷ 100) on day t against realised average pairwise correlation of daily log returns of the 9 sector SPDRs over sessions t+1 to t+63. OLS of realised on implied with Newey-West standard errors (`maxlags` = 63). Report slope, intercept, R², mean gap. Labelled a sector-level proxy.
- RV screens (live): per name, z-score of today's 30d ATM vol against its own captured history (only once ≥ `rv_min_days` snapshots), and the name's 30d ATM vol minus its group median.

### 5.9 Volatility risk premium (`volsurf/vrp.py`)

- Realised variance RV_t,21 = (252/21) Σ_{j=1..21} r_{t+j}², r = daily log return of `^GSPC`.
- Implied variance IV_t = (VIX_t/100)².
- GARCH forecast: `arch` GARCH(1,1), constant mean, normal errors, on daily `^GSPC` log returns × 100, fitted on data up to and including the last session of each month (expanding window from `garch_min_obs` observations), forecast variance summed over horizons 1 to 21, annualised as × 252/21 / 10000.
- VRP_t = IV_t − RV_t,21 (ex post) and signal s_m = IV − GARCH forecast at each month end (ex ante).
- Strategies on monthly returns, month-end to month-end: (a) PUT index; (b) BXM; (c) `^SP500TR`; (d) timed PUT: hold PUT in month m+1 if s_m > 0 else T-bills (DTB3, month-average yield / 1200), switching cost `switch_cost_bp` each change. T-bill is the risk-free rate for excess returns.
- Report per strategy: annualised mean, vol, Sharpe, worst month, worst drawdown, skew, kurtosis, 1% and 5% monthly quantiles. Every specification run is appended to `outputs/tables/spec_log.csv`; the deflated Sharpe ratio (Bailey and López de Prado) of the timed strategy uses N = number of rows in the spec log and the variance of their Sharpe ratios.
- Live descriptive: on each snapshot day a short 30-day ATM `^SPX` straddle (expiry nearest 30 days, strike nearest F), delta hedged at each snapshot close until expiry or the last snapshot, marked off SSVI; P&L reported per position, no statistics.

### 5.10 P&L attribution (`volsurf/attribution.py`)

- Daily, per option position between snapshots t and t+1: ΔV = Δ dS + ½ Γ dS² + Θ dt + ν dσ + vanna dS dσ + ½ volga dσ² + residual, Greeks at t, dσ = change in that contract's IV from the surface, dt in years. The hedge leg adds −Δ_t dS. Identity: components + residual = total, exactly (residual is defined as the difference); reported explained share = 1 − |residual| / |total| distribution.
- Real book: the live straddles of Section 5.9.
- Hedging frequency study on simulated paths: GBM and Heston (parameters in config), 30-day short ATM straddle, `sim_steps_per_day` steps a day, hedges every 1 step, every day, every 5 days; `sim_paths` paths, seed from config; cost = `hedge_cost_bp` of traded notional. Report mean and standard deviation of hedging error and of cost per frequency.

### 5.11 Risk report (`volsurf/risk.py`, `volsurf/report.py`)

- Sample book in `config.toml [book]` (positions chosen by underlying, side, call or put, target delta, target days).
- Grid: spot shocks −10% to +10% step 2.5%, parallel vol shocks −5 to +5 vol points step 2.5, full revaluation, sticky strike.
- Limits per underlying in config on dollar delta, dollar gamma per 1% move, vega per vol point; breaches flagged.
- PDF: reportlab, A4, Helvetica, `invariant=1`, 1 page.

---

## 6. Signatures and schemas (fixed)

### 6.1 Signatures

```python
# volsurf/config.py
@dataclass(frozen=True)
class Config: ...                                   # one nested frozen dataclass per config table
def load_config(path: str | Path = "config.toml") -> Config

# volsurf/snapshots.py (pure functions used by scripts/snapshot.py; no network)
def in_window(now_utc: datetime, cfg) -> bool
def is_session(day: date) -> bool
def chain_frame(raw_calls: pd.DataFrame, raw_puts: pd.DataFrame, ticker: str, expiry: str, snap_utc: datetime) -> pd.DataFrame   # CHAINS
def filter_expiries(expiries: list[str], today: date, max_days: int) -> list[str]
def keep_spxw(df: pd.DataFrame) -> tuple[pd.DataFrame, int]
def earnings_frame(raw: pd.DataFrame, ticker: str, snap_date: date) -> pd.DataFrame        # EARNINGS
def classify_timing(ts_ny: pd.Timestamp) -> str                                          # BMO, AMC, unknown
def snapshot_log(rows: list[dict]) -> dict

# volsurf/data.py
def load_snapshot(day: date, root: Path) -> dict[str, pd.DataFrame]
def clean_chain(chains: pd.DataFrame, underlying: pd.DataFrame, cfg) -> tuple[pd.DataFrame, pd.DataFrame]   # (clean, CLEAN_LOG)
def rate_curve(fred: dict[str, pd.DataFrame], day: date) -> Callable[[float], float]
def dividend_yield(divs: pd.DataFrame, spot: float, day: date) -> float
def sessions_between(t: date, e: date) -> int

# volsurf/pricing.py
def bsm(S, K, T, r, q, sigma, kind) -> np.ndarray
def black76(F, K, T, D, sigma, kind) -> np.ndarray
def crr(S, K, T, r, q, sigma, kind, n, american) -> float
def early_exercise_premium(S, K, T, r, q, sigma, kind, n) -> float

# volsurf/greeks.py
def greeks(S, K, T, r, q, sigma, kind) -> dict[str, np.ndarray]     # delta gamma vega theta rho vanna volga
def fd_greeks(S, K, T, r, q, sigma, kind, h: dict) -> dict[str, np.ndarray]
def book_greeks(positions: pd.DataFrame) -> pd.DataFrame            # by underlying and expiry

# volsurf/forwards.py
def parity_forward(calls: pd.DataFrame, puts: pd.DataFrame, spot: float, T: float, n: int) -> dict   # D F r_impl r2

# volsurf/iv.py
def price_bounds(price, S, F, K, D, kind, american) -> bool
def iv_european(price, F, K, T, D, kind, cfg) -> tuple[float, str]   # vol, method (newton, brent, bounds)
def iv_american(price, S, K, T, r, q, kind, cfg) -> tuple[float, str]
def iv_chain(clean: pd.DataFrame, cfg) -> pd.DataFrame               # IV

# volsurf/svi.py
def svi_w(k, a, b, rho, m, s) -> np.ndarray
def svi_g(k, params) -> np.ndarray
def fit_svi(k, iv, T, cfg) -> dict                                    # params, rmse, status
def calendar_violations(slices: list[dict], grid) -> pd.DataFrame

# volsurf/ssvi.py
def ssvi_w(k, theta, rho, eta, gamma) -> np.ndarray
def fit_ssvi(slices: list[dict], quotes: pd.DataFrame, cfg) -> dict
def surface_metrics(fit: dict, cfg) -> dict                           # SURFACE_DAILY row

# volsurf/density.py
def svi_density(K, F, T, params) -> np.ndarray
def fd_density(K, F, T, D, params, dk) -> np.ndarray
def tail_table(params, F, T, k_range, moves) -> pd.DataFrame

# volsurf/events.py
def event_windows(earnings: pd.DataFrame, overrides: pd.DataFrame) -> pd.DataFrame
def straddle_move(chain: pd.DataFrame, F: float, S: float, expiry) -> float
def term_structure_move(theta1, theta2, n1, n2) -> tuple[float, str]
def event_table(...) -> pd.DataFrame                                  # EVENTS
def event_summary(events: pd.DataFrame, cfg) -> pd.DataFrame

# volsurf/correlation.py
def implied_correlation(sig_index: float, sig: pd.Series, w: pd.Series) -> float
def avg_pairwise_corr(returns: pd.DataFrame) -> float
def cor3m_study(cor3m: pd.Series, sectors: pd.DataFrame, horizon: int, maxlags: int) -> dict

# volsurf/vrp.py
def realised_var(returns: pd.Series, h: int) -> pd.Series
def garch_monthly_forecasts(returns: pd.Series, h: int, min_obs: int) -> pd.Series
def strategy_returns(...) -> pd.DataFrame
def deflated_sharpe(sr: float, n_obs: int, skew: float, kurt: float, sr_trials: pd.Series) -> float

# volsurf/attribution.py
def attribute_day(pos: pd.Series, t0: dict, t1: dict) -> dict
def simulate_hedging(model: str, cfg) -> pd.DataFrame

# volsurf/risk.py and volsurf/report.py
def shock_grid(book: pd.DataFrame, surface, cfg) -> pd.DataFrame
def limit_breaches(book_greeks: pd.DataFrame, cfg) -> pd.DataFrame
def build_risk_report(day: date, grid, greeks, breaches, out_path: Path) -> Path
```

`event_table` and `strategy_returns` take arguments fixed in `PLAN.md` from Section 5.7 and 5.9; listing them is part of session 0's PLAN work, and any argument this document does not imply goes to OPEN.

### 6.2 Schemas (column order fixed)

- **CHAINS** (`chains_YYYY-MM-DD.parquet`): snap_utc, ticker, expiry, kind (C or P), contract_symbol, strike, last_price, bid, ask, change, pct_change, volume, open_interest, yahoo_iv, in_the_money, last_trade_utc, contract_size, currency
- **UNDERLYING** (`underlying_YYYY-MM-DD.csv`): ticker, snap_utc, price, price_time_utc, n_expiries_listed, n_expiries_kept, n_rows, n_spx_am_dropped, error
- **EARNINGS** (`earnings_YYYY-MM-DD.csv`): snap_date, ticker, event_ts_ny, timing, eps_estimate, reported_eps, surprise_pct
- **SNAPLOG** (`snaplog_YYYY-MM-DD.json`): run id, runner (actions or local), start and end UTC, New York start time, in_window, forced, per-ticker status and timing, library versions, sha256 of each asset
- **CLEAN_LOG**: day, ticker, rule, rows_before, rows_dropped
- **IV**: day, ticker, expiry, kind, strike, T, S, F, r, q, mid, iv, method, flag
- **SVI_FITS**: day, ticker, expiry, T, n_quotes, a, b, rho, m, s, rmse_vol, min_g, status
- **SURFACE_DAILY**: day, ticker, atm_30, rr25_30, bf25_30, atm_90, term_slope, ssvi_rho, ssvi_eta, ssvi_gamma, ssvi_rmse, n_expiries, status
- **EVENTS**: ticker, group, event_date, timing, pre_snap_date, E1, E2, n1, n2, theta1, theta2, S, F, straddle_move, ts_move, realised_move, ratio, log_ratio, status
- **VRP_MONTHLY**: month_end, vix, iv, garch_fc, signal, rv_fwd_21, vrp
- **STRATEGIES**: month_end, put, bxm, sp500tr, timed_put, tbill
- **spec_log.csv**: run_utc, spec_id, description, params_json, sharpe, n_months

---

## 7. config.toml contents

```toml
[run]
seed = 20261028

[universe]
index = ["^SPX"]
etfs = ["SPY", "QQQ", "XLK", "XLE", "XLF"]
xlk_holdings = ["NVDA", "AAPL", "MSFT", "AVGO", "ORCL", "AMD", "CSCO", "CRM", "IBM", "PLTR"]
singles = ["AMZN", "META", "GOOGL", "TSLA", "NFLX", "JPM", "BAC", "XOM", "CVX", "UNH", "WMT", "HD", "DIS", "UBER", "SHOP", "ABNB"]
max_days_to_expiry = 400
sector_spdrs = ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"]

[snapshot]
window_start_ny = "15:25"
window_end_ny = "16:30"
close_ny = "16:00"
cron_utc = ["30 19 * * 1-5", "30 20 * * 1-5"]
local_task_times_london = ["19:30", "20:30"]
request_interval_s = 0.5
retries = 3
backoff_s = [5, 15, 45]
release_tag = "snapshots"
test_release_tag = "snapshots-test"
min_tickers_ok = 28

[clean]
min_mid = 0.05
max_rel_spread = 0.5
stale_sessions = 5

[pricing]
n_validate = 2000
n_prod = 200

[iv]
iv_lo = 0.005
iv_hi = 5.0
iv_tol = 1e-10
newton_max_iter = 50
min_vega = 1e-6

[forwards]
parity_n_strikes = 10
parity_r2_min = 0.9999

[svi]
min_quotes = 8
s_min = 1e-4
penalty = 1e4
starts = [[0.01, 0.1, -0.5, 0.0, 0.1], [0.01, 0.3, -0.8, 0.05, 0.2], [0.0, 0.05, 0.0, 0.0, 0.05], [0.02, 0.2, -0.3, -0.05, 0.3], [0.005, 0.5, -0.95, 0.1, 0.5]]
grid_points = 401
grid_pad = 0.5

[surface]
tenors_days = [30, 90]
delta = 0.25

[density]
bl_dk = 0.001
int_tol = 1e-3
moves = [0.025, 0.05, 0.10, 0.20]
k_sd = 8

[events]
min_n = 20
min_group_n = 8
boot_reps = 10000
ci = 0.90

[correlation]
cor3m_horizon = 63
nw_maxlags = 63
live_horizon = 21
rv_min_days = 20

[vrp]
start = "1990-01-02"
horizon = 21
garch_min_obs = 1000
switch_cost_bp = 10
straddle_target_days = 30

[sim]
paths = 20000
steps_per_day = 13
days = 21
hedge_every_steps = [1, 13, 65]
hedge_cost_bp = 1.0
gbm = { s0 = 100.0, mu = 0.0, sigma = 0.2, r = 0.04 }
heston = { s0 = 100.0, v0 = 0.04, kappa = 2.0, theta = 0.04, xi = 0.5, rho = -0.7, r = 0.04 }

[book]
positions = [
  { underlying = "^SPX", side = -1, kind = "P", target_delta = -0.25, target_days = 30, contracts = 10 },
  { underlying = "^SPX", side = -1, kind = "C", target_delta = 0.25, target_days = 30, contracts = 10 },
  { underlying = "AAPL", side = 1, kind = "C", target_delta = 0.50, target_days = 60, contracts = 20 },
  { underlying = "NVDA", side = -1, kind = "P", target_delta = -0.30, target_days = 45, contracts = 15 },
]

[limits]
dollar_delta = 2000000
dollar_gamma_1pct = 250000
vega_per_point = 50000

[risk]
spot_shocks = [-0.10, -0.075, -0.05, -0.025, 0.0, 0.025, 0.05, 0.075, 0.10]
vol_shocks_pts = [-5.0, -2.5, 0.0, 2.5, 5.0]

[tolerances]
bsm_vs_quantlib = 1e-10
crr_amer_vs_quantlib_rel_spot = 1e-4
crr_euro_vs_analytic_rel_spot = 5e-5
greeks_fd_rel = 1e-5
fd_h_spot_rel = 1e-4
fd_h_vol = 1e-4
fd_h_t = 1e-5
fd_h_rate = 1e-5
iv_roundtrip = 1e-8
parity_european = 1e-10

[tolerances.greeks_fd_abs]
delta = 1e-6
gamma = 4e-6
vega = 6e-5
vanna = 1.2e-5
volga = 5e-4
```

`data/manual/earnings_overrides.csv` columns: ticker, event_date, timing, source_url. `data/manual/macro_events.csv` columns: date, kind, release_time_ny, source_url. Both start with the header only.

---

## 8. Section list (PLAN.md expands exactly these; add or remove nothing)

### Section 1: Long history data and the snapshot loader
- 1.1 `scripts/pull_data.py --stage cboe|fred|prices|ssga`: every source in Section 3.2 except chains, plus `MANIFEST.json`. Test: manifest hashes match committed files; VIX first date 1990-01-02, PUT first date 1991-03-04, COR3M first date 2006-01-03.
- 1.2 `scripts/pull_snapshots.py`: download every asset of the `snapshots` release into `data/snapshots/` (gitignored) and write `data/raw/snapshot_manifest.csv` (asset, size, sha256, downloaded_utc). Commit 1 real day's chains for `^SPX`, SPY and AAPL as `tests/fixtures/chains_sample.parquet` with its underlying and earnings rows.
- 1.3 `volsurf/data.py`: loader, `clean_chain`, `rate_curve`, `dividend_yield`, `sessions_between`. Tests: each cleaning rule on a synthetic chain drops exactly the rows it names; rate conversion 2 ln(1 + y/200) on a hand value; interpolation and flat extrapolation; t − 1 publication rule; session count across the 2026-11-26 holiday.
- 1.4 Capture health table `outputs/tables/capture_health.csv`: one row per session since 2026-10-28 with runner, start time New York, tickers ok, rows, after_close rows, and gaps. Review evidence: the full table and the CLEAN_LOG for the fixture day.

### Section 2: Pricing and Greeks
- 2.1 `pricing.py`. Tests: BSM against QuantLib `AnalyticEuropeanEngine` to `bsm_vs_quantlib` on a grid (S 100; K 70 to 130 step 10; days 7, 30, 91, 182, 365, 730; σ 0.15, 0.30, 0.60; r 0.045; q 0.015; call and put); Black-76 equals BSM with S e^(−qT) = D F to 1e-12; European parity C − P = S e^(−qT) − K e^(−rT) to `parity_european`; CRR American against QuantLib `BinomialVanillaEngine("crr", 2000)` within `crr_amer_vs_quantlib_rel_spot` × S and CRR European against analytic within `crr_euro_vs_analytic_rel_spot` × S on the same grid at N = 2000; American call with q = 0 has premium 0 to 1e-12.
- 2.2 `greeks.py`. Tests: every analytic Greek against `fd_greeks` on the 2.1 grid with S = 100, central differences with bumps h_S = `fd_h_spot_rel` × S, h_σ = `fd_h_vol`, h_T = `fd_h_t`, h_r = `fd_h_rate` (gamma and volga by second differences, vanna by the 4-point cross difference), passing when |analytic − fd| ≤ `greeks_fd_rel` × |analytic| + the Greek's absolute tolerance in `[tolerances.greeks_fd_abs]`. The reviewer measured the largest absolute gaps on this grid at these bumps: delta 9.1e-8, gamma 3.7e-7, vega 5.5e-6, vanna 1.1e-6, volga 4.8e-5; the config bounds are 10 times those. Theta and rho bounds are MEASURE. Delta, gamma, vega, theta, rho also against QuantLib analytic engine Greeks to 1e-8 (theta converted to QuantLib's per-year convention).
- 2.3 Early exercise premium table on the latest fixture day for every American chain: `outputs/tables/eep_summary.csv` (ticker, kind, moneyness bucket, median and max premium in vol points of the American IV minus the European IV on the same mid). Review evidence: the table and 5 worst contracts.

### Section 3: Forwards and implied volatility
- 3.1 `forwards.py`. Tests: synthetic European chain recovers D and F to 1e-12; a fixture `^SPX` expiry passes the R² gate. Review evidence: per-expiry D, F, implied r and Treasury r for the fixture day.
- 3.2 `iv.py`. Tests: round trip on the 2.1 grid recovers σ to `iv_roundtrip` (European) and American round trip at `n_prod` recovers σ to `iv_roundtrip`; bounds flagging on synthetic violations; Brent fallback triggers for a 7-day 30% OTM put. MEASURE: max American IV gap between N = 200 and N = 2000 over the fixture chains.
- 3.3 `iv_chain` over every captured day; writes `data/processed/iv/{day}.parquet` and `outputs/tables/iv_summary.csv` (day, ticker, quotes in, solved, by method, flagged). Review evidence: summary table and 10 random solved rows with inputs.

### Section 4: Volatility surface
- 4.1 `svi.py`. Tests: recovers known parameters from noiseless synthetic quotes to 1e-6; g(k) analytic against finite differences to 1e-6; a deliberately arbitrageable parameter set fails the butterfly check; calendar check flags a crossing pair.
- 4.2 `ssvi.py`. Tests: η(1 + |ρ|) ≤ 2 respected; fitted surface has no calendar violation on the grid; 25-delta strikes give forward delta 0.25 to 1e-10.
- 4.3 Daily run over every captured day for every underlying: `svi_fits.csv`, `surface_daily.csv`, figures `outputs/figures/spx_smiles_{day}.png` for the first and last captured day, `outputs/figures/spx_surface_last.png` (3D), `outputs/figures/spx_metrics.png` (ATM 30d, RR, BF, term slope over the window). Review evidence: fit status counts by underlying, every rejected fit row, the SURFACE_DAILY rows for `^SPX`.

### Section 5: Risk-neutral distribution
- 5.1 `density.py`. Tests per Section 5.6 (integrates to 1, mean equals F, non-negative), analytic against finite-difference density within MEASURE on the fixture.
- 5.2 Tail tables and PIT values for every expired captured expiry; `outputs/figures/spx_density_last.png` (density for 3 expiries with quoted range shaded). Review evidence: tail table for the 30-day `^SPX` slice on the last day, PIT rows.

### Section 6: Event pricing
- 6.1 `events.py`. Tests: hand-worked term structure example in the docstring; BMO and AMC windows on fixed dates; `no_event_premium` path; events lacking a pre-event snapshot are excluded and counted.
- 6.2 Apply `earnings_overrides.csv` and `macro_events.csv` from instruction 06; build EVENTS for earnings and macro; summary per Section 5.7. Figures: implied against realised scatter with the 45-degree line; one panel per event for the 4 largest events by implied move showing the term structure θ against T before the event. Review evidence: the full EVENTS table, the summary rows, every `unknown` timing row.

### Section 7: Correlation and relative value
- 7.1 COR3M study (Section 5.8). Test: `avg_pairwise_corr` on a synthetic 3-asset panel with known correlation; Newey-West matches a direct statsmodels call.
- 7.2 Live XLK implied correlation and RV screens. Review evidence: COR3M regression rows, the live implied correlation series with covered weight, top and bottom 5 RV screen rows on the last day.

### Section 8: Volatility risk premium
- 8.1 `vrp.py` realised variance, GARCH forecasts. Tests: realised variance of a synthetic constant-return series; the GARCH forecast at a month end uses no data after it (truncate and refit gives the same number).
- 8.2 Strategies, statistics, spec log, deflated Sharpe; live straddles. Figures: VIX² against forward RV; cumulative excess return of the 4 strategies (log scale); drawdowns. Review evidence: statistics table, spec log, the 10 worst months of each strategy.

### Section 9: P&L attribution
- 9.1 `attribute_day` with the exact identity test, and a synthetic Black-Scholes path test where explained share exceeds MEASURE.
- 9.2 Hedging-frequency simulation (GBM and Heston) and attribution of the live straddles. Review evidence: frequency table, attribution rows for 1 live position end to end.

### Section 10: Risk report
- 10.1 `risk.py`: grid and limits. Tests: 0-shock cell equals 0 P&L; a 1-position book's small-shock P&L matches delta × dS within MEASURE.
- 10.2 `report.py`: 2 builds byte-identical; 1 page; PDF for the last captured day committed to `outputs/reports/`. Review evidence: page render PNG.

### Section 11: Write-up and reproducibility
- 11.1 `scripts/run_all.py` regenerates every table, figure and report from `data/raw/`, `data/manual/` and `data/snapshots/`; running it twice leaves `git status` clean.
- 11.2 `outputs/tables/answers.csv`: one or more rows per research question, each with source table and row.
- 11.3 `README.md`: what it is, how to run it, answers, tables generated from the CSVs (test that the README matches them), figures with one callout each in the prose before the figure, the capture window and N for every live result, and what the project does not do. `docs/METHODS.md`: Sections 4 and 5 of this document with the corrections in Section 2.
- 11.4 Final fresh-clone run and tidy.

Writing rules for README, docs and report text: plain English, conversational but technical; numerals, not words, for numbers; no hyphens joining sentences; none of the words robust, resilient, rigorous, leveraging, grounded; no filler.

---

## 9. What session 0 must produce

`instructions/00_kickoff.md` (this file), `WORKFLOW.md` and `Project Outline/07_Volatility_Surface_and_Event_Pricing.md` are already committed. If any is missing, stop and say so in the status file; do not recreate them.

### Step 0.0: plan and scaffolding (commit `step 0.0: plan and scaffolding`)

1. `PLAN.md`: Sections 1 to 11 from Section 8. For each step, one paragraph stating what is built, the file, the signatures from Section 6 it implements, the tests (file and test name), the outputs, and the review evidence. Expand, do not summarise, add or remove no step. Anything left unspecified is marked OPEN in `PLAN.md` and listed in `decisions/OPEN.md` and the status file, not decided.
2. `CLAUDE.md`: Sections 0, 4 and 6 of this document verbatim, then an empty `## Amendments` heading.
3. `config.toml`: Section 7 exactly.
4. `review/TEMPLATE.md`, headings in this order: Section; Steps completed (one line each with commit hash); Evidence (one subsection per numeric claim, raw rows via `to_string()`); Tests run (exact command and full output); Fresh-clone check; Runtime per step; Deviations from PLAN.md; Not verified; Open questions; Files changed; Reviewer reads (ordered, shortest sufficient set).
5. `decisions/OPEN.md` (header only, items appended as found), and `decisions/data_and_history.md`, `decisions/american_options.md`, `decisions/capture.md`, `decisions/dropped_scope.md`, each restating its decisions from Section 2 in 5 lines or fewer.
6. `docs/CONVENTIONS_RESOLVED.md`: Section 4 items 1 to 15 numbered as here, plus 16 SPXW only, 17 parity forward on `^SPX` only, 18 American IV on the CRR tree, 19 tail probabilities only inside the quoted range.
7. `pyproject.toml`: `[build-system]` setuptools ≥ 68 with `setuptools.build_meta`; `[project]` name `volsurf`, version `0.1.0`, requires-python ≥ 3.12; runtime numpy, pandas, scipy, statsmodels, arch, QuantLib, yfinance, exchange_calendars, requests, pyarrow, openpyxl, matplotlib, reportlab; dev extra pytest, pytest-socket, ruff, pypdf, pymupdf; `[tool.setuptools] packages = ["volsurf"]`; `[tool.pytest.ini_options] pythonpath = ["."]`.
8. `requirements-lock.txt` per rule 16.
9. `.gitattributes`: `* text=auto eol=lf`, `*.png binary`, `*.pdf binary`, `*.parquet binary`, `*.xlsx binary`, `data/raw/** -text`, `tests/fixtures/** -text`.
10. `.gitignore`: `data/processed/**`, `data/snapshots/**`, `data/local_capture/**`, `.env`, `__pycache__/`, `*.py[cod]`, `.venv/`, `venv/`, `.pytest_cache/`, `*.egg-info/`, `.DS_Store`, `Thumbs.db`, `~$*`, `.vscode/`, `.ruff_cache/`.
11. `.github/workflows/ci.yml`: on push and pull request, ubuntu-latest, Python 3.12 via `astral-sh/setup-uv`, install from the lock then `pip install -e . --no-deps`, run `ruff check .` and `pytest -p socket --disable-socket -q`.
12. `README.md` with a 5-line description and "results pending"; `volsurf/__init__.py`; `data/manual/earnings_overrides.csv` and `data/manual/macro_events.csv` with headers only; `.gitkeep` in `data/raw`, `outputs/tables`, `outputs/figures`, `outputs/reports`, `review`, `tests/fixtures`.

### Step 0.1: snapshot capture code (commit `step 0.1: snapshot capture`)

1. `volsurf/snapshots.py`: the pure functions in Section 6.1 under `# volsurf/snapshots.py`.
2. `scripts/snapshot.py` with flags `--force` (ignore the window and session checks, write `test_` prefixed names, upload to `test_release_tag`), `--runner {actions,local}`, `--out <dir>`, `--upload {always,if-missing,never}`. Flow: check session and window (unless forced; outside → write a one-line log and exit 0); for each underlying in config order: list expiries, filter by `max_days_to_expiry`, fetch each chain with `request_interval_s` between calls and the retry and backoff rule; fetch the underlying's last 1-minute price; build CHAINS, UNDERLYING, EARNINGS; write the 4 files to `--out`; upload per `--upload` with `gh release upload <tag> <files> --clobber` after creating the release if it does not exist (`gh release create <tag> --title <tag> --notes "daily option chain snapshots"`). `if-missing` uploads only when the release has no `chains_` asset for that date. Exit code 1 if fewer than `min_tickers_ok` underlyings succeeded (files are still written and uploaded, so a partial day is kept).
3. `tests/test_snapshots.py`: `in_window` across the clock change (2026-10-30 19:30 UTC is 15:30 New York and inside; 2026-11-02 19:30 UTC is 14:30 New York and outside; 2026-11-02 20:30 UTC is inside); `is_session` false on 2026-11-26 and on a Saturday; `filter_expiries`; `keep_spxw` on a synthetic frame; `classify_timing` for 07:00, 16:05 and 00:00; `chain_frame` column order equals CHAINS.

### Step 0.2: switch the capture on (commit `step 0.2: capture schedule`)

1. `.github/workflows/snapshot.yml`: triggers `schedule` with both `cron_utc` lines, `workflow_dispatch` with a boolean input `force`, and `push` to `main` on paths `.github/workflows/snapshot.yml` and `scripts/snapshot.py`. `permissions: contents: write`. On `push`, run with `--force`; on `workflow_dispatch`, `--force` only if the input is true; on `schedule`, no force. Runner ubuntu-latest, Python 3.12 with uv, install from the lock, then `python scripts/snapshot.py --runner actions --out snap --upload always`, with `GH_TOKEN: ${{ github.token }}`. Timeout 45 minutes. Upload the `snap/` folder as a workflow artifact too, retention 7 days.
2. `scripts/windows/register_snapshot_task.ps1`: registers a Windows scheduled task `volsurf-snapshot` that runs, Monday to Friday at each time in `local_task_times_london`, the repo's venv Python on `scripts/snapshot.py --runner local --out data/local_capture --upload if-missing`, with "run whether user is logged on or not" left off (runs when logged on), "start when available" on, and the working directory set to the repo. Plus `scripts/windows/unregister_snapshot_task.ps1`.
3. Push `main` (this push triggers the forced test run on Actions).
4. **Live checks, all printed in full in `review/section_0.md`:**
   - a. Run `python scripts/snapshot.py --force --runner local --out data/local_capture --upload never` on this machine now. Print the UNDERLYING table and, per ticker, the number of CHAINS rows, rows with bid > 0, and the earliest and latest expiry.
   - b. Check whether `gh` is installed and authenticated on this machine (`gh auth status`). If it is, run the PowerShell registration script and print `Get-ScheduledTask volsurf-snapshot | Format-List` and its next run time. If it is not, do not register the task; write the 2 options (install and authenticate `gh`, or register with `--upload never` and upload weekly by hand) to `decisions/OPEN.md` and the status file.
   - c. Wait for the Actions run triggered by the push (`gh run list --workflow snapshot.yml` and `gh run watch`, or poll the Actions page if `gh` is missing). Print its conclusion, its log lines for the per-ticker status, and the asset list of the `snapshots-test` release. If Yahoo refused requests from Actions (HTTP 401, 403 or 429 on most tickers), say so plainly in the status file: the local task is then the primary and that changes nothing else in this session.
5. Do not delete the `snapshots-test` release; the reviewer reads it.

Then write `review/section_0.md` (TEMPLATE headings), `instructions/00_kickoff.status.md` per rule 11 with the placeholder test output and the 3 live check results summarised with pointers to the review file, commit both, push, stop.

Do not pull long-history data in session 0. Do not write anything in `volsurf/` beyond `__init__.py`, `config.py` (only if `snapshot.py` needs it to read config; otherwise leave for Section 1 and read TOML directly with `tomllib`) and `snapshots.py`.
