# instructions/03_section_3.md: Session 3 (Section 3 of PLAN.md: forwards and implied volatility)

Read `CLAUDE.md`, `PLAN.md` and every earlier instruction file first. This file beats them where they differ (rule 13). Build every step below in one session. The step 3.0 fix to Section 2 comes first.

---

## A. Approval of Section 2

Approved, with 1 fix in step 3.0. Checked independently on Linux from a fresh clone at `860fb27`: 4,342 tests pass with sockets disabled. The reviewer re-solved 3 random SPY ITM puts from `eep_rows.csv` with its own CRR tree and `brentq`, and both vols matched the file to 6 decimals.

**Status 4 is a real flaw, and the reviewer's spec caused it.** Comparing a 200-step tree IV with a closed-form BSM IV mixes the early exercise premium with the tree's discretisation error. On the same 3 puts, using CRR European at 200 steps for the European IV moves the premium by up to 0.07 vol points. The fix is in step 3.0.

**Status 3 is composition, not an error.** The SPY ITM put bins mix very different expiries, and the medians follow that mix. The deep ITM call values (up to 42.9 vol points) come from rows with almost no vega, where a vol number means nothing. Step 3.0 blanks those rows.

| Item | Decision |
|---|---|
| O-29 | (a) |
| O-30 | (a) |
| Status 5 (small interpretations) | All accepted. |

Record these in `decisions/section_2_review.md`.

---

## B. Correction to kickoff Section 5.2 (the parity forward)

**The R² gate in Section 5.2 would reject most `^SPX` expiries.** The reviewer ran it on the fixture. Over the 10 strikes nearest spot (a 50-point span on a 7,730 index), C − P barely moves, so the slope D is badly identified. R² falls below 0.9999 on 29 of the 33 expiries with 10 pairs, and the implied rate swings from −91% to +74% on the shortest dates.

**Fix: take D from the Treasury curve and back out only F.** This is the Cboe VIX approach.

- D = exp(−r(T) T), with r(T) from `rate_curve` (Convention 4.6).
- For each of the `parity_n_strikes` strikes nearest S that have clean call and put mids: F_i = K_i + (C_i − P_i) / D. Then F = median of F_i, and mad_bp = 10,000 × median(|F_i − F|) / F.
- Gate: at least `parity_min_pairs` pairs and mad_bp ≤ `parity_mad_max_bp`, else the expiry is rejected for that day with status `parity_fail`.
- Reported, not gated: the implied dividend yield q_impl = r − ln(F / S) / T, and the regression implied r from the old method for expiries with T ≥ 30/365, as a diagnostic.

Measured on the fixture, 36 expiries: median mad_bp 0.46, largest 0.84. Every expiry had at least 8 pairs.

Config changes: remove `[forwards] parity_r2_min`; add `parity_min_pairs = 5` and `parity_mad_max_bp = 2.0`. The new signature is `parity_forward(calls, puts, spot, T, D, n, min_pairs, mad_max_bp) -> dict` with keys F, mad_bp, n_pairs, q_impl, r_reg, status. Add the correction to `CLAUDE.md` under Amendments (staging allowed).

---

## C. Steps

### Step 3.0: early exercise premium on one tree (commit `step 3.0: EEP on matched trees`)

1. The European IV in `eep_rows.csv` becomes `brentq` on **CRR European at `n_prod`** minus the mid, so discretisation error cancels between the 2 vols.
2. Add `premium_price` = CRR American − CRR European at `n_prod`, both at the American IV, and `premium_pct_mid` = premium_price / mid × 100.
3. `premium_vol_pts` is blank, with status `low_vega`, where BSM vega per vol point at the American IV is below `[eep] min_vega_pt` = 0.01 (1 cent per vol point). Add that config key.
4. Rerun and recommit both EEP tables. `eep_summary.csv` gains median and max `premium_pct_mid`, and counts n over rows with a vol premium.
5. Test: on the 2.1 grid, an American call with q = 0 has premium_price 0 to 1e-12 and premium_vol_pts 0 to 1e-6.

### Step 3.1: forwards (PLAN 3.1, with Section B)

- Tests: on a synthetic European chain built from known F and D, `parity_forward` recovers F to 1e-10 with mad_bp below 1e-6; and on the fixture, every `^SPX` expiry with at least `parity_min_pairs` pairs passes the gate.
- With the forward in hand, apply cleaning rule e to `^SPX`: European bounds with D and the parity F. Regenerate `outputs/tables/clean_log_fixture.csv` and its test. The `^SPX` rule e row loses its `deferred` note.

### Step 3.2: implied volatility (PLAN 3.2)

As in PLAN.md and kickoff 5.3, plus a batched American solver, because scalar `brentq` on the tree took 169 s for 7,108 rows in step 2.3 and a full day is about 80,000 rows.

- `iv_american_batch(prices, S, K, T, r, q, kind, cfg) -> (iv, status)`: bisection on [`iv_lo`, `iv_hi`] for all rows at once, with a CRR tree vectorised across options (arrays of shape options × nodes), stopping when the bracket is narrower than `[iv] am_vol_tol` = 1e-7 (add that key). Rows whose price is outside the American bounds get status `bounds`.
- Tests: on 200 random rows from the fixture, `iv_american_batch` matches scalar `iv_american` to 1e-6; and a fixture day of every American ticker solves in under 300 s (measured on the owner's machine and recorded in the review).
- MEASURE as in PLAN: the largest American IV gap between N = 200 and N = 2000 over the fixture SPY and AAPL OTM quotes. Print it; the test asserts only that it is finite.

### Step 3.3: IV on every captured day (PLAN 3.3)

- Solve OTM quotes only (calls with K ≥ F, puts with K < F; Convention 4.5), since only these feed the surface.
- Days: the fixture day plus every day in `data/snapshots/` after running `scripts/pull_snapshots.py`. If tonight's capture has landed, that day is included; if not, the fixture day alone is enough and is not a stop.
- Write `data/processed/iv/{day}.parquet` and `outputs/tables/iv_summary.csv`. For `^SPX`, also write `outputs/tables/parity_forwards_fixture.csv` (expiry, T, r, D, F, mad_bp, n_pairs, q_impl, r_reg, status).

---

## D. Review evidence (in `review/section_3.md`)

1. Step 3.0: `eep_summary.csv` before and after, and the change in OTM median vol points per bin.
2. `parity_forwards_fixture.csv` in full.
3. The `^SPX` rule e row of the regenerated clean log.
4. Batch-against-scalar IV gaps (largest, median), the batch timing, and the N = 200 against N = 2000 measurement.
5. `iv_summary.csv` in full, and 10 random solved rows with all inputs.
6. The fresh-clone check and the CI status of the final commit.

Status file: `instructions/03_section_3.status.md`.
