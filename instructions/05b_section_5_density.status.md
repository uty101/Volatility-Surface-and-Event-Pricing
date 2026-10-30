# Status: session 5b (`instructions/05b_section_5_density.md`)

## Outcome

Stopped under rule 4 after step 5b.1, by the owner's choice when asked in session. Step 5b.1 is complete: committed as `fb87ee9`, Section 4 rerun for both days. Step 5.1 is not rebuilt and step 5.2 is not built. Evidence is in `review/section_5.md` under `## Session 5b`.

## Last step reached

Step 5b.1. Then the review section, this file, the fresh-clone check and CI.

## Reason for the stop

Instruction 05b says that `test_nonnegative_when_butterfly_passes` must pass as written. It does not.

- **Its g assertion now passes.** On the 200,001-point sinh grid, g ≥ −1e-10 on every accepted fixture slice; the smallest is −6.3e-11.
- **Its density assertion fails.** It asserts the density itself is ≥ 0, and on 14 of 74 accepted fixture slices the density is between −5.3e-12 and −2.3e-15. In each case g lies in [−6.3e-11, 0).

The two specs conflict. The density is g times a positive factor, and kickoff 5.4's butterfly check passes at g ≥ −1e-10. So a slice can pass the butterfly check and still have q slightly below 0, which kickoff 5.6's "q ≥ 0 when the slice passed the butterfly check" forbids. The reviewer's own run reported min g = −6.9e-11, so it would have hit the same thing.

I asked the owner whether to stop, to read q ≥ 0 as holding within the tolerance, or to finish with the test failing. The owner chose to stop. Rule 5 forbids changing the test so that it passes. This is O-37 in `decisions/OPEN.md`; the evidence is in review 5b-S1.

Apart from this, the instruction 05b fix does what it was meant to do (review 5b-D2):
- every accepted slice has g ≥ −1e-10 on the acceptance grid, computed at full precision;
- on both days, the largest |integral − 1| is 2.5e-9 and the largest |mean / F − 1| is 3.6e-4, both within `int_tol`;
- the largest `tail_mass` is 2.6e-3, on MU 2027 slices;
- 2 slices of 567 are `density_fail`.

## Questions and blockers for the reviewer

1. **O-37.** (a) q ≥ 0 holds up to the butterfly tolerance: the test asserts g ≥ −1e-10 on the integration grid, and q ≥ 0 wherever g ≥ 0. (b) The acceptance check requires g ≥ 0 exactly, so that q ≥ 0 holds exactly, and step 5b.1 is rerun.
2. **The 2 `density_fail` slices** are CSCO 2026-11-13 and SHOP 2026-11-20 on 2026-10-29. Both are `first`-route fits whose total variance w is slightly negative far out in a wing, beyond the quotes: −3.3e-13 near k = 3.7 on CSCO, and −1.3e-6 near k = 7.9 on SHOP. Their density there is NaN, so the integral is NaN.
   - Why they were accepted: g stays finite where w < 0, so the instruction 05b rule "a non-finite g (from w ≤ 0) counts as a failure" only catches w = 0 exactly. Also, the first-route fit is not held to the exact Section 5.4 constraints (O-32 (a) applies to refits only).
   - `density_fail` catches both, as part C intends. Reported, not changed (review 5b-D2).
3. **Changes against session 5.**
   - 3 slices are no longer accepted, all on 2026-10-29: `^SPX` 2026-11-06 (`butterfly_fail`, first-route g −0.017, and no neighbour retry passes), QQQ 2026-11-02 (`poor_fit`, 10.4 vol points) and AAPL 2026-10-30 (`poor_fit`).
   - QQQ 2026-11-03 is now accepted on the `neighbour` route with min g +3.0e-9. Fitted alone, it is `poor_fit`, and the new QQQ test passes.
   - Of the kept fits, 206 needed 1 cutting-plane round, 7 needed 2, and none needed 3.
   - SURFACE_DAILY moves by at most 8.1e-4 (CSCO ATM 30) and 1.4e-3 (CSCO BF).
   - Calendar violations: 1 of 71 pairs on 2026-10-28 and 10 of 456 on 2026-10-29.
4. **Fixture results against the reviewer's run.**
   - Accepted: 74 of 74, as the reviewer measured. The route split differs slightly: `^SPX` has 35 `refit` and 1 `neighbour`, against the reviewer's 1 `first`, 33 `refit` and 2 `neighbour`.
   - Largest RMSE: `^SPX` 0.818 (reviewer 0.82) and AAPL 1.084 (reviewer 1.08).
   - Fit time on Windows: `^SPX` 541 s, SPY 195 s and AAPL 68 s.
   - The full surface run takes 82 minutes.
5. **The analytic against finite-difference gap** is now a test with the 5e-3 bound, and passes. The largest gap is 4.48e-5 (SPY 2026-10-29), which is 1.05e-3 of the peak density.
6. **The prices are refreshed and kept.** Every committed row of `close.parquet` and `index.parquet` is unchanged, with 2026-10-28 and 2026-10-29 added. `dividends.csv` is identical. `sectors.parquet` adjusted closes moved by at most 6.1e-5 on 6,898 old rows (review 5b-D5).
7. **Interpretations** to confirm are under `### Not verified (session 5b)` in the review. The one that matters most: cutting points accumulate across rounds and are fixed values of k.
8. **The 2026-10-30 capture is not used.** It runs at 19:30 UTC, after this session's runs, and instruction 05b covers the 2 existing days.
9. **Clones on disk:** `C:\vs5` from session 5, and `C:\vs5b` from this session. Both are safe to delete.

## Tests

`.venv\Scripts\python -m pytest -p socket --disable-socket -q`: `1 failed, 4517 passed` on Windows at `fb87ee9` (26 min). The failure is `test_nonnegative_when_butterfly_passes`. `ruff check .`: `All checks passed!` The fresh-clone check and CI follow in the commit `session 5b: fresh-clone check and CI`.

## `git log origin/main --oneline -3` (before this commit)

```
85072e1 session 5: fresh-clone check and CI
d22bfa1 Add session 5b instructions
35d4f13 session 5: stopped at step 5.1, review and status
```
