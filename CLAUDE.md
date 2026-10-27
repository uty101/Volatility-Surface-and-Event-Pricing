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

## Amendments
