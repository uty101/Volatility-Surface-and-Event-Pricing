# instructions/05b_section_5_density.md: Session 5b (make the butterfly check cover the density, then finish Section 5)

Read `CLAUDE.md`, `PLAN.md` and every earlier instruction file first. This file beats them where they differ (rule 13). Build step 5b.1, then step 5.1 again and step 5.2, in one session.

---

## A. Review of session 5

Step 5.0 is approved apart from the grid it uses for the butterfly check. Step 5.1 is approved apart from its integration range.

**The stop was correct, and the fault is in the reviewer's spec.** The reviewer checked the committed `svi_fits.csv` (570 accepted slices over the 2 days) on a dense grid over |k| ≤ 30. g is negative somewhere on 229 of them:

- 197 between the 801 grid points, down to −4.5e-3 (on the 2026-10-29 short slices, the smile's curvature is narrower than the grid step);
- 32 beyond the grid, down to −1.19 (QQQ 2026-11-03);
- 5 of those 32 lie beyond |k| = 10, where w falls to about 1e-13 and the mass is below 1e-13.

A grid in k with a fixed number of points spread evenly over a range in units of √w(0) is the wrong shape for SVI. The fix in Section B uses the slice's own scale.

---

## B. The fix, measured on the fixture

**1. Check on a sinh grid.** SVI's shape lives in the variable (k − m)/s. Points at k = m + s·sinh(u), with u evenly spaced, are dense where the curvature is and spread out geometrically in the wings. The grid covers k ∈ [−K, K], with K = `[svi] k_check` = 10, so S_T/F runs from 4.5e-5 to 22,026.

- **Constraint grid:** 801 sinh points.
- **Acceptance check:** the 200,001-point sinh grid that the density integrates on, so the check covers exactly what Section 5 uses.
- s is floored at `s_min` inside the grid formula.

**2. Cutting-plane refit.** If a constrained refit meets the constraint on its 801 points but fails the acceptance check, add the 10 points with the lowest g on the acceptance grid to the constraint and refit from the last result. Do this at most 3 more times. A refit that still fails does not count.

**3. Wing bound 1.98, not 2.** For a slope s of the wing, g tends to 1/4 − s²/16 as |k| grows. At 2 that limit is 0, so g can approach it from below. The mean also equals F only if the right wing slope is strictly below 2 (Lee, and Rogers and Tehranchi). At 1.98 the limit is 0.0049, which is above 0.

**4. Integration over the sinh grid.** The integral and the mean are trapezoid sums on the 200,001-point sinh grid over [−K, K]. Add the closed-form mass beyond ±K, P(S_T < F e^(−K)) + P(S_T > F e^(K)), to the integral, and report it in its own column `tail_mass`.

The reviewer ran exactly this on the fixture `^SPX` (monkeypatched over the code at `35d4f13`, with `[svi]` starts unchanged). The results:

- **Accepted slices:** 36 of 36 (1 `first`, 33 `refit`, 2 `neighbour`).
- **Fit error:** the largest RMSE is 0.82 vol points.
- **Butterfly check:** the smallest g on the dense check is −6.9e-11.
- **Density integral and mean:** the largest |integral − 1| is 5.7e-10 and the largest |mean/F − 1| is 5.7e-10, against about 1e-4 before.
- **Mass beyond ±10:** at most 6e-10.
- **Time:** 317 s for the 36 slices on Linux.

The same run on the fixture SPY and AAPL:

- **Accepted slices:** SPY 24 of 24 (6 `first`, 18 `refit`), and AAPL 14 of 14 (3 `first`, 11 `refit`).
- **Fit error:** the largest RMSE is 1.08 vol points.
- **Butterfly check:** the smallest g is −9.7e-11.
- **Density integral and mean:** the largest |integral − 1| is 7.0e-10, and the largest |mean/F − 1| is 4.9e-8 (AAPL 2027-09-17).
- **Time:** 173 s.

That gives 74 of 74 fixture slices accepted, the same count as session 5.

**Not measured by the reviewer:** the 2026-10-29 slices (QQQ, MSFT, TSLA, AAPL, NFLX and the others in S1). The session measures them.

---

## C. Decisions

| Item | Decision |
|---|---|
| O-36 | (a), in the form of Section B. A slice whose density still misses `int_tol` after step 5b.1 gets the density status `density_fail`. It has no tail table or PIT value, and it is reported. This is not a stop. |
| O-34 | (a). |
| O-35 | (a). It is now valid, because g ≥ 0 is checked out to ±10 and the mass beyond is reported. |
| MEASURE (D3) | The test bound is: the largest analytic against finite-difference gap is ≤ 5e-3 × the slice's peak density on the quoted range. The measured worst case is 1.06e-3. |
| Status 5 | All noted. Runtime is accepted. XLE and NFLX below 0.75 on 2026-10-29 are reported only. |
| Status 6 | Interpretations 1, 3, 4, 5 and 6 are accepted. Interpretation 2 is replaced by Section B: the sinh grid moves with m and s of the parameters being judged. |
| Status 7 (PIT data) | Rerun `scripts/pull_data.py --stage prices` and **keep** the refreshed files. PIT needs the 2026-10-29 closes. Print the row diff, as in session 5. |

Record these in `decisions/section_5_review.md`, and add the change to `CLAUDE.md` under Amendments.

---

## D. Steps

### Step 5b.1 (commit `step 5b.1: sinh butterfly grid, cutting-plane refit, wing bound 1.98`)

1. **Code.**
   - In `svi.py`, replace `wide_grid` with `check_grid(params, cfg, n)` as in B1, and use the B2 refit for the `refit` and `neighbour` routes.
   - `min_g` uses the acceptance grid. A non-finite g (from w ≤ 0) counts as a failure.
   - Config: `[svi] wing_max = 1.98`, `[svi] k_check = 10`, `[svi] cut_rounds = 3`, `[svi] cut_points = 10`.
   - Remove `[density] k_sd`. The calendar check keeps its own grid.
2. **Density.** In `density.py`, `density_check` uses the same 200,001-point sinh grid, and adds `tail_mass` to the integral (B4). Tail tables and PIT keep O-35 (a).
3. **Rerun.** Rerun Section 4 for both days and regenerate every Section 4 table and figure.
4. **Tests.**
   - `test_nonnegative_when_butterfly_passes` must pass as written, on the sinh grid.
   - Add a test that QQQ 2026-11-03 on 2026-10-29 is either accepted with min g ≥ −1e-10 or rejected. It must never be accepted with a negative g.
   - Use a small saved fixture of that slice's quotes, so the test needs no snapshot.

### Steps 5.1 and 5.2

- Step 5.1 again, with Section B and the decisions above.
- Step 5.2 as in instruction 05 and PLAN.md Section 5.
- PIT covers `^SPX` and SPY 2026-10-29, from the fixture day, using the kept closes. Any later capture whose expiries have passed is included too.

---

## E. Review evidence (append to `review/section_5.md` under `## Session 5b`)

1. **Step 5b.1:**
   - per-ticker accepted counts for both days, split by `route`, against session 5;
   - every slice that is not accepted;
   - the largest RMSE;
   - how many slices needed cutting-plane rounds, and how many rounds;
   - runtime.
2. **Every accepted slice:**
   - smallest g on the acceptance grid;
   - integral error, mean error and `tail_mass`;
   - the largest and median of each per ticker per day;
   - every `density_fail` slice.
3. **The S1 slices:** each with its new status, route, RMSE and min g.
4. **Section 5 outputs:**
   - the tail table for the 30-day `^SPX` slice on the last day;
   - the PIT rows;
   - the MEASURE result against its new bound.
5. **Wrap-up:**
   - every figure, listed by path;
   - the prices row diff;
   - the fresh-clone check;
   - CI status.

Status file: `instructions/05b_section_5_density.status.md`.
