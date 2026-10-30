# instructions/05_section_5.md: Session 5 (fix the SVI slices, then Section 5: risk-neutral distribution)

Read `CLAUDE.md`, `PLAN.md` and every earlier instruction file first. This file beats them where they differ (rule 13). Build step 5.0, then every step of Section 5, in one session.

---

## A. Approval of Section 4

Section 4 is approved, with the fixes in step 5.0. The 2026-10-29 capture worked: it slept until 15:30 New York, captured 37 of 37 tickers and uploaded. Checked from a fresh clone at `71f0774`.

| Item | Decision |
|---|---|
| O-33 | (a), scipy defaults for SSVI. |
| Status 2 (γ on its bound, SSVI RMSE 2.6 to 3.5 vol points) | A real model limit, and it biases the daily metrics. Fixed in step 5.0 item 3. |
| Status 3 (calendar violations) | Check only where both slices have quotes. Step 5.0 item 4. |
| Status 4 | Noted. |
| Status 5 (NFLX `no_root`) | Correct as is. The reviewer read the 2026-10-29 chain: NFLX lists strikes up to 2,660 against a spot of 62 (legacy listings), and a 0.015 mid that far out needs a vol above `iv_hi`. No change. |
| Status 6 | All accepted. |
| Status 8 | The owner may delete `C:\vs4` and `C:\vs4b`; Claude Code does not. |

Record these in `decisions/section_4_review.md` under `## Session 4b`.

---

## B. What the reviewer measured, and the 4 corrections

**1. The kickoff's wing bound is wrong.** Kickoff 5.4 has b(1 + |ρ|) ≤ 4. Roger Lee's moment bound on total variance is a wing slope of at most 2, so the constraint is **b(1 + |ρ|) ≤ 2**. With 4, several accepted slices have right wing slopes up to 2.85, and their densities leak mass.

**2. The butterfly grid is too narrow.** The fit only checks g on [k_min − 0.5, k_max + 0.5]. Beyond that, g goes negative on 41 of 72 accepted fixture slices (as low as −1.26). The density in Section 5 integrates far into those wings, so the check must cover them. The new grid is 801 points on [min(k_min − 0.5, −L), max(k_max + 0.5, L)], with L = `[density] k_sd` × √w(0) and `k_sd` = 24 (was 8).

**3. Retry failed slices from their neighbours.** With corrections 1 and 2, SLSQP sometimes collapses to b ≈ 0 (a flat smile) from the configured starts: 11 of 36 `^SPX` fixture slices ended `poor_fit` that way. Retrying each from the parameters of the 3 nearest accepted expiries fixed all 11, with RMSE from 0.13 to 0.64 vol points. The warm start scales a and b by T / T_neighbour.

Measured on the fixture `^SPX` with corrections 1 to 3: 36 of 36 slices accepted, the largest RMSE 0.90 vol points, the density integral within 1.5e-4 of 1, and the mean within 5e-5 of F. Across all 57 accepted fixture slices of the first pass (all 3 tickers), the largest integral error is 2.0e-4. `[density] int_tol` = 1e-3 therefore holds as written.

**4. Daily metrics come from the SVI slices, not SSVI.** SSVI with one ρ cannot fit the S&P skew. On the fixture, it gives a 30-day 25-delta risk reversal of −6.20 vol points, against −4.15 from the accepted slices. ATM agrees, because both use the same θ. SURFACE_DAILY metrics are computed as follows:

- For a target τ, take the 2 accepted slices that bracket it. If there is no bracket, the metric is blank with status `no_bracket`.
- Find each slice's 25-delta call and put log-strikes with `brentq` on the Black forward delta, searching within that slice's quoted k range. If no root lies inside that range, the metric is blank with status `delta_outside_quotes`.
- Interpolate total variance linearly in T at the matched delta, then σ = √(w / τ).

Keep the SSVI parameters and RMSE, and add `ssvi_rr25_30` beside `rr25_30` as a check.

---

## C. Steps

### Step 5.0 (commit `step 5.0: SVI wing bound, wide butterfly grid, neighbour retry, slice metrics`)

1. Apply corrections 1 to 3 in `svi.py`.
   - Config: change the wing bound and `k_sd`, and add `[svi] neighbour_retries = 3`.
   - Status `ok_refit` covers both refit routes. A new column `route` (`first`, `refit`, `neighbour`) records which one produced the fit.
2. Rerun Section 4 for both days. Keep the share gate at 0.75.
   - Add a test that every accepted fixture slice has b(1 + |ρ|) ≤ 2 and min g ≥ −1e-10 on the wide grid.
3. Compute the slice-based metrics (correction 4). Test them on a synthetic 2-slice case with known parameters.
4. Limit `calendar_violations` to the overlap of the 2 slices' quoted k ranges, and print the new counts for both days.
5. Regenerate every Section 4 table and figure.

### Steps 5.1 and 5.2

As in PLAN.md Section 5, with kickoff 5.6 and these settings:

- Integration range [F e^(−L), F e^(L)], with L = `k_sd` × √w(0), using the trapezoid rule on at least 200,001 points in k.
- `int_tol` = 1e-3 for the integral and for mean = F.
- The analytic against finite-difference density bound stays MEASURE. Print the largest gap on the fixture.
- PIT: every captured expiry that has already expired by the latest capture day.

---

## D. Review evidence (in `review/section_5.md`)

1. Step 5.0:
   - per-ticker accepted counts for both days, split by `route`;
   - every slice that is not accepted;
   - the largest RMSE;
   - SURFACE_DAILY in full, with slice and SSVI risk reversals side by side;
   - the new calendar violation counts.
2. The density integral and mean errors for every accepted slice (largest and median per ticker).
3. The analytic against finite-difference measurement.
4. The tail table for the 30-day `^SPX` slice on the last day, and the PIT rows.
5. Every figure, listed by path. Then the fresh-clone check and the CI status.

Status file: `instructions/05_section_5.status.md`.
