# instructions/04_section_4.md: Session 4 (Section 4 of PLAN.md: the volatility surface)

Read `CLAUDE.md`, `PLAN.md` and every earlier instruction file first. This file beats them where they differ (rule 13). Build step 4.0 and every step of Section 4 in one session.

---

## A. Approval of Section 3 and session 3c

Section 3 is complete and approved. Session 3c is approved. Checked on Linux from a fresh clone at `94e1dbf`: CI is green on `75ec927`, and the reviewer rebuilt `iv_summary.csv` with `run_all.py --stage iv` and got the same counts. The workflow has the 3 early crons, `--wait`, a 355-minute timeout and the concurrency group. Run 40898405093 is sleeping until 19:30 UTC to capture 2026-10-29.

| 3b item | Decision |
|---|---|
| 1 (batch flat rule misses the P 130 edge case) | Use the one-sided rule in step 4.0. The reviewer reran its 504-case grid with it and got the same result: 424 within 1e-8, 80 flagged, 0 wrong. |
| 2 (64% Brent on `^SPX`) | Accepted. |
| 3 (interpretations) | All accepted. |
| 4 (6-minute suite) | The N = 2000 measurement becomes a script (step 4.0). |

| 3c item | Decision |
|---|---|
| 2 and 3 (the local task) | **Remove the local task completely** (step 4.0). The owner has asked for it to go. With the GitHub runs now waiting for the window, it is no longer needed, and its 2026-10-28 runs were killed without writing a line. |
| 4 (1 pending run) | Accepted. |

Record these in `decisions/section_3_review.md` under `## Session 3b and 3c`.

---

## B. Corrections to kickoff Section 5.4 (SVI), measured on the fixture

The reviewer fitted raw SVI to every fixture expiry of `^SPX`, SPY and AAPL (74 slices with at least 8 OTM quotes), from the 5 configured starts, using SLSQP and the Section 5.4 constraints.

**The penalty refit does not work.** With `penalty` = 1e4 times the sum of squared negative g, a violation of g = −1e-6 adds about 1e-8 to the objective, which is far too little to matter. As specified, 44 of 74 slices end as `butterfly_fail`, including 32 of 36 `^SPX` slices. Almost all of them miss by only 1e-7 to 1e-4 in the far wings.

**Replace it with a constrained refit.** When the first fit has min g < −1e-10, refit with g(k) ≥ 0 at every point of the 401-point grid as a hard SLSQP inequality constraint (vector valued), starting from the first fit's parameters and then from each configured start. Keep the best refit that converges with min g ≥ −1e-10; status `ok_refit`. If none does, status `butterfly_fail`.

**Add a fit-quality gate.** A converged fit can still be poor. 3 `^SPX` slices of 7 days or less (2026-10-29, 11-02 and 11-04) came back with RMSE of 8.2, 20.6 and 22.6 vol points. Reject any fit with RMSE over `[svi] max_rmse_volpts` = 2.0, with status `poor_fit`.

Measured outcome with both changes:

| ticker | ok | ok_refit | butterfly_fail | poor_fit |
|---|---|---|---|---|
| `^SPX` | 2 | 28 | 3 | 3 |
| SPY | 11 | 13 | 0 | 0 |
| AAPL | 9 | 5 | 0 | 0 |

All 6 rejected slices are `^SPX` expiries within 12 days, where the smile is too sharp for 5 SVI parameters. That is a known limit of SVI and is reported as such, not worked around.

Config: remove `[svi] penalty`; add `max_rmse_volpts = 2.0`. Fit settings: SLSQP `maxiter = 1000`, `ftol = 1e-14`. The objective uses w clipped below at 1e-12 inside the square root. Add the correction to `CLAUDE.md` under Amendments (staging allowed).

---

## C. Steps

### Step 4.0: carry-over fixes (commit `step 4.0: remove local task, one-sided flat rule, measurement script`)

1. **Remove the local task.**
   - Run `scripts\windows\unregister_snapshot_task.ps1` on the owner's machine.
   - Print `Get-ScheduledTask volsurf-snapshot` to show it is gone.
   - Delete `scripts/windows/` and `[snapshot] local_task_times_utc`.
   - Update `decisions/capture.md` to say that GitHub Actions with `--wait` is the only scheduled capture.
   - `scripts/snapshot.py --runner local` stays usable by hand.
   - Add a line to `CLAUDE.md` Amendments.
2. **One-sided flat rule** for every solver: sens = min(|P(σ̂ + 0.01) − P(σ̂)|, |P(σ̂) − P(σ̂ − 0.01)|), with both vols clipped to [`iv_lo`, `iv_hi`]; `flat` if sens < `flat_tol`.
   - Add a test that the P 130, 365-day, σ 0.15 American grid put is `flat` from both the scalar and the batch solver.
   - The round-trip tests must still pass; print the status counts.
3. **Measurement script.** Move the N = 200 against N = 2000 measurement into `scripts/measure_iv_tree.py`. It writes `outputs/tables/iv_tree_convergence.csv` (ticker, expiry, kind, strike, iv_200, iv_2000, gap). The test now only reads the committed CSV and asserts the gaps are finite. Report the new suite runtime.
4. **Rerun the IV stage** so the fixture IVs use the new rule, and print the change in `iv_summary.csv`, if any.

### Step 4.1: SVI per expiry (PLAN 4.1, with Section B)

- Tests as in PLAN 4.1.
- Add a fixture test: on the fixture day, the number of accepted slices (`ok` plus `ok_refit`) is at least 28 for `^SPX`, 23 for SPY and 13 for AAPL (the reviewer's counts minus a margin of 1 to 2 for optimiser differences). If it falls short, the session stops under rule 4 with the per-slice table printed. Do not lower the bounds.
- `svi_fits.csv` adds `refit` (bool) and `rmse_volpts`.

### Step 4.2: SSVI (PLAN 4.2)

As in PLAN 4.2 and O-10 (a), fitted on `ok` and `ok_refit` slices only.

- A day where SSVI fails to converge gets SURFACE_DAILY status `ssvi_fail` with blank metrics. This is reported, not a stop.
- A day with fewer than 3 accepted slices gets status `too_few_expiries`.
- Print the SSVI RMSE in vol points for each fixture ticker.

### Step 4.3: daily run and figures (PLAN 4.3)

- Days: the fixture day plus every real capture in `data/snapshots/`. Run `pull_snapshots.py` first; the 2026-10-29 capture should be there.
- Figures as in PLAN 4.3. If only 1 or 2 days exist, `spx_metrics.png` still plots them as points.
- Add `outputs/figures/spx_smile_fits_{day}.png`: for the fixture day, a panel per accepted `^SPX` expiry (first 12 by T), showing market IVs as dots and the SVI fit as a line, with rejected slices listed in the title.

---

## D. Review evidence (in `review/section_4.md`)

1. Step 4.0: the unregister output, the flat-rule test, round-trip counts, the suite runtime and the `iv_summary.csv` change.
2. Fixture fit status counts per ticker, and every slice row that is not `ok`, with RMSE and min g.
3. The SSVI parameters and RMSE per ticker per day, and every `SURFACE_DAILY` row.
4. The 25-delta strike test output.
5. Every figure produced, listed with its path.
6. The fresh-clone check, the CI status of the final commit, and the result of tonight's 2026-10-29 capture (the `snapshots` asset list and the SNAPLOG run fields).

Status file: `instructions/04_section_4.status.md`.
