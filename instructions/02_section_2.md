# instructions/02_section_2.md: Session 2 (Section 2 of PLAN.md: pricing and Greeks)

Read `CLAUDE.md`, `PLAN.md` and every earlier instruction file first. This file beats them where they differ (rule 13). Build every step of Section 2 in one session.

---

## A. Approval of Section 1

Section 1 is complete and approved. Checked independently on Linux from a fresh clone at `df41e5a`: 49 tests pass with sockets disabled, and the fixture CLEAN_LOG matches the committed file.

**Status item 3 (rule e drops) is checked and needs no change.** The reviewer recomputed rule e on the fixture. Every dropped row is in the money by construction (mid below intrinsic), so none of them could reach the surface, which uses OTM quotes only. The drops come in 2 kinds:

- **Spot timing.** Most gaps are tiny: the median shortfall below intrinsic is 0.03% of spot for SPY and 0.06% for AAPL. These come from the 1-minute bar against quotes fetched up to 50 s later.
- **Stale deep ITM quotes.** The rest are real stale quotes, such as SPY 2026-12-18 245 calls bid 424.91 against an intrinsic of 525.38. Only 143 of the 361 SPY drops have an ask below intrinsic, the clear arbitrage case.

Rule e stays as built.

**Status items 1 and 2.** This instruction allows staging `PLAN.md`: update PLAN 1.1 to say the Yahoo histories end at the last completed session, and PLAN 8.2 to show O-28 decided as (a). `last_session` appears in `MANIFEST.json` on the next prices pull; no pull is needed now.

---

## B. Measured tolerances for this section

The reviewer measured these on the 2.1 grid (S 100; K 70 to 130 step 10; days 7, 30, 91, 182, 365, 730; σ 0.15, 0.30, 0.60; r 0.045; q 0.015; calls and puts):

| check | largest gap measured | bound to use |
|---|---|---|
| analytic theta against central difference in T, h_T = 1e-5 | 2.94e-6 absolute | `[tolerances.greeks_fd_abs] theta = 3e-5` |
| analytic rho against central difference in r, h_r = 1e-5 | 8.75e-8 absolute | `[tolerances.greeks_fd_abs] rho = 1e-6` |
| delta, gamma, vega, theta, rho against QuantLib `AnalyticEuropeanEngine` | 4.4e-13 (theta), others smaller | 1e-8 as written |

Add the 2 new keys to `config.toml`. The theta and rho bounds in the kickoff are no longer MEASURE.

**QuantLib conventions, to avoid a false failure.** Build QuantLib dates as `today + days` with `Actual365Fixed` and use T = days / 365 in your own functions. QuantLib's `theta()` is per year and its `vega()` and `rho()` are per unit, the same as ours in code, so compare them directly with no conversion. (The kickoff's note about converting theta is wrong; this line replaces it.) The textbook CRR tree and QuantLib's `"crr"` engine differ by up to 6.8e-5 × S at 2000 steps (kickoff Correction 16); the configured bound is 1e-4 × S.

---

## C. Steps

As in PLAN.md Section 2, with these additions.

### Step 2.1: pricing

- Test grid exactly as Section B. Tests are parametrised so a failure names the grid point.
- `crr` must take under 1 second for N = 2000 on 1 option (vectorised backward induction, no Python loop over nodes within a step). Record the measured time in the review.
- Extra test: CRR American put with q = 0 is above the European put by more than 1e-4 for K = 120, 365 days, σ 0.30, r 0.045 (the premium must be positive where it should be).

### Step 2.2: Greeks

- `fd_greeks` bumps: h_S = `fd_h_spot_rel` × S, h_σ = `fd_h_vol`, h_T = `fd_h_t`, h_r = `fd_h_rate`. Theta in code is −∂V/∂T per year.
- Pass rule: |analytic − fd| ≤ `greeks_fd_rel` × |analytic| + the Greek's `greeks_fd_abs`.
- `book_greeks(positions)`: input columns `underlying, expiry, kind, strike, quantity, S, T, r, q, sigma`; output 1 row per (underlying, expiry) plus 1 total row per underlying, with each Greek multiplied by quantity × 100. Test: a long call and a short call on the same contract net to 0 to 1e-12.

### Step 2.3: early exercise premium table

- Fixture day 2026-10-28, American chains SPY and AAPL from the fixture, rows after cleaning (Section 1), OTM and ITM both included.
- Inputs: S from the fixture UNDERLYING; r from `rate_curve` for 2026-10-28 (so FRED observations dated ≤ 2026-10-27); q from `dividend_yield` with `dividends.csv`; T by Convention 4.1.
- American IV: `brentq` on CRR American at `n_prod` minus mid. European IV: `brentq` on BSM minus the same mid (O-24 (a)). Rows where either solve fails get a status and stay in the row table with blank vols.
- Premium in vol points = (European IV − American IV) × 100. The European IV is the higher one, because a European model has to explain the early exercise value with extra vol.
- Moneyness bins by O-8 (a). Write `outputs/tables/eep_summary.csv` (ticker, kind, k_bin, n, median_vol_pts, max_vol_pts) and `outputs/tables/eep_rows.csv` (every contract with its inputs, both vols and the status).
- Sanity checks, printed and not tested: deep ITM puts should carry the largest premium; OTM calls on AAPL should be close to 0.

---

## D. Review evidence (in `review/section_2.md`)

1. The test output grouped by test file, with the counts per parametrised test.
2. The largest gap found in each grid test (BSM against QuantLib, CRR against QuantLib, CRR European against analytic, each Greek against fd, each Greek against QuantLib), with the grid point where it occurs.
3. The CRR timing.
4. `eep_summary.csv` in full and the 5 contracts with the largest premium from `eep_rows.csv`, with every input.
5. The fresh-clone check and the CI status of the final commit.

Status file: `instructions/02_section_2.status.md`.
