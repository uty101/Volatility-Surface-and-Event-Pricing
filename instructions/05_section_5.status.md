# Status: session 5 (`instructions/05_section_5.md`)

## Outcome

Stopped under rule 4 at step 5.1. Step 5.0 is complete (`80877ab`). Step 5.1 is built and committed (`9acf0df`), and its test `test_nonnegative_when_butterfly_passes` fails on the fixture. Step 5.2 is not built. Evidence is in `review/section_5.md`.

## Last step reached

Step 5.1: built, with 1 test failing. Then the review, this file, the fresh-clone check and CI.

## Reason for the stop

Kickoff 5.6 requires q ≥ 0 when a slice has passed the butterfly check. With the step 5.0 fit it does not hold where Section 5 uses the density, and the instruction 05 integral checks fail beyond the fixture (review S1 and D2, `decisions/OPEN.md` O-36):

1. **Between grid points.** On 45 of 74 accepted fixture slices (all `refit` route), g is negative between points of the 801-point wide grid, down to −7.6e-6. The hard constraint holds g ≥ 0 only at the grid points; the 200,001-point integration grid sees between them.
2. **Beyond ±L.** On short slices g is negative outside the wide grid. On the fixture this happens on 4 slices (down to −0.061 on `^SPX` 2026-11-06), so the closed-form P(S_T > 2F) is −4.6e-4. On 2026-10-29 it is larger: QQQ 2026-11-03 has g = −1.19 at k = −0.94 (L = 0.54), and its density integrates to 1.0697 over [−L, L] with a mean 4.4% above F.
3. **Range too narrow.** On long-dated slices (MU, NVDA, BAC 2027), L = 24√w(0) misses 0.1% to 0.24% of the mass.

The integral and mean checks hold on all 74 accepted fixture slices (largest errors 2.4e-4 and 4.7e-4). They fail on 23 of the 496 accepted slices of 2026-10-29. Instruction 05 says that `int_tol` = 1e-3 "holds as written", but that was measured on the fixture's 3 tickers. Fixing this means choosing a grid, a range or a gate, which is a design choice, so it is not done here.

## Questions and blockers for the reviewer

1. **O-36, the stop.**
   - (a) Change the fit: run the butterfly check on a denser and wider grid (for example `int_points` points over ±3L), take the integration range from the wings rather than from √w(0), then rerun step 5.0.
   - (b) Keep the fit and gate the density: a slice whose integral or mean misses `int_tol`, or whose density goes negative below a MEASURE bound, gets a density status and no tail table or PIT value, with tail probabilities by O-35 (b).
2. **O-34.** SURFACE_DAILY status when more than one thing fails. Implemented as (a): each failure blanks only its own values, and the statuses are joined with `|`. On the 2 days every row is `ok`.
3. **O-35.** Tail probabilities from the slice's closed-form distribution function (a), or from a trapezoid integral on the integration grid (b). Implemented as (a) in `tail_table`. It interacts with O-36: (a) counts every k, including the region beyond ±L.
4. **The MEASURE result.** On the fixture, the largest gap between the analytic density and the finite-difference one is 4.67e-5 (SPY 2026-10-29). That is 1.06e-3 of the slice's peak density (review D3). The bound for the test is yours to set.
5. **Step 5.0 results to note.**
   - The neighbour retry was needed on only 2 slices: the refit already reaches all 36 fixture `^SPX` slices.
   - On 2026-10-29, the accepted share is below 0.75 for XLE (0.714) and NFLX (0.700). The share gate is a fixture test, so this is reported only.
   - Calendar violations fell from 25 of 69 pairs to 4 of 71 on 10-28, and from 241 of 454 to 11 of 459 on 10-29.
   - The full surface run now takes 79 minutes, against 18 in session 4b. The full suite takes 31 minutes.
6. **Interpretations** to confirm are under Not verified in the review. The two that matter most:
   - The wing bound and the integration grid size are config keys: `[svi] wing_max`, and `[density] int_points` = 200,001.
   - L in the wide grid uses w(0) of the parameters being fitted, so the constraint grid moves with them.
7. **PIT data.** PIT needs closes on the expiry date. The only expiries that have expired are `^SPX` and SPY 2026-10-29, and the committed prices end on 2026-10-27. A rerun of `scripts/pull_data.py --stage prices` came back identical on every committed row of `close.parquet` and `index.parquet`; only `sectors.parquet` adjusted closes moved, by up to 6.9e-5. It was not kept, because step 5.2 is not built.

## Tests

`pytest -p socket --disable-socket -q`: `1 failed, 4515 passed` on Windows at `9acf0df` (31 min). The failure is `test_nonnegative_when_butterfly_passes`. `ruff check .`: `All checks passed!` Fresh clone at `35d4f13` (Windows, `C:\vs5`): `1 failed, 4515 passed`, the same. **CI on `35d4f13` (run 41080293255, Linux): failure, `3 failed, 4513 passed`.** On Linux, `test_integrates_to_one` and `test_mean_equals_forward` fail too. The fixture `^SPX` 2026-11-05 slice fits differently there and integrates to 1.0038 with a mean 0.53% above F, which is cause 2 of the stop (review D5). `C:\vs5` is left on disk and is safe to delete.

## `git log origin/main --oneline -3` (before this commit)

```
a4d7c57 Add session 5 instructions
71f0774 session 4b: review and status
fd21334 step 4.3: daily surface run and figures
```
