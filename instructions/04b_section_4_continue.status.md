# Status: session 4b (`instructions/04b_section_4_continue.md`)

## Outcome

Completed. Section 4 is finished: step 4b.1 (`e92c2be`), step 4.2 (`dfc3d45`) and step 4.3 (`fd21334`) are committed and pushed. Evidence is in `review/section_4.md` under `## Session 4b`.

## Last step reached

Step 4.3, then the fresh-clone check, the review section and this file.

## Reason for any stop

None.

## Results

- **4b.1:** under O-32 (a) and the share gate, the fixture shares are `^SPX` 34/36, SPY 24/24 and AAPL 14/14, the reviewer's numbers. The rejected slices are `^SPX` 2026-10-29 and 10-30, both `poor_fit`. CI on `e92c2be`: success (run 40932005564).
- **Tonight's capture landed.** Run 40898405093 slept until 19:30:00 UTC (15:30 New York), captured 37 of 37 tickers `ok` (83,293 rows) and uploaded 4 assets to `snapshots` at 19:37 UTC. It is included, so the surface run covers 2026-10-28 (fixture) and 2026-10-29.
- **4.2 and 4.3:** 616 SVI slices over 2 days (405 `ok`, 158 `ok_refit`, 35 `poor_fit`, 18 `too_few`, 0 `butterfly_fail`). SSVI converged on all 40 ticker-days. SSVI RMSE in vol points on the fixture day: `^SPX` 2.72, SPY 3.51, AAPL 0.80; on 2026-10-29, `^SPX` 2.58 and SPY 3.38. `^SPX` ATM 30d went from 13.44% to 12.98%, and the 25d RR from −6.20 to −6.30 vol points. The 4 tables are byte-identical over 2 runs. All 5 figures are written.

## Questions and blockers for the reviewer

1. **O-33 (new): the SSVI optimiser settings.** Instruction 04 part B fixes SLSQP `maxiter = 1000`, `ftol = 1e-14` for SVI; O-10 (a) fixes only the optimiser and start for SSVI. With the part B settings, `^SPX` and SPY end with SLSQP status 8 at the same point and would be `ssvi_fail` on the fixture. With scipy's defaults they report success, with the same objective and parameters to 6 digits. Implemented as (a), scipy defaults. The cost: on noiseless synthetic quotes the defaults stop with η = 0.954 against a true 1.0 (largest parameter error 0.046, RMSE 3.7e-4); the part B settings get to 6e-5 (RMSE 1.1e-6). (b) is the part B settings, with `^SPX` and SPY `ssvi_fail`.
2. **γ sits on its bound 0.5** for `^SPX` and SPY on both days, and for 14 other names on 2026-10-29. The SSVI RMSE for `^SPX` and SPY (2.6 to 3.5 vol points) is far above the accepted SVI slices (0.11 to 0.92). Reported, not changed.
3. **Calendar violations are frequent:** 25 of 69 consecutive SVI pairs on the fixture day and 241 of 454 on 2026-10-29. For 251 of the 266 violating pairs, the worst point lies outside the quoted k range of that ticker-day's accepted slices (the padded grid wing). They are recorded only, as kickoff 5.4 says.
4. **The old fixed-count gate was also flaky between CI runs on Linux.** Identical code failed on `de9b908` and `3a6cad7` and passed on `124d922` (review 4b-D1). The share gate is unaffected.
5. **NFLX has 113 `no_root` IV rows out of 575** on 2026-10-29, against at most 22 for any other name. Reported, not investigated.
6. **Interpretations** to confirm are under `### Not verified (session 4b)` and `### 4b-D2` in the review: exact feasibility for a counting refit; the RMSE gate inside the refit choice, so a slice whose counting refits are all above 2.0 is `poor_fit`; SURFACE_DAILY in decimals; the 25-delta bracketing; closed SSVI bounds at η = 0 and γ = 0 (never reached).
7. **The machine slept for about 15 hours during the 2-run determinism check.** The second surface run resumed after wake-up and completed. Its 55,992 s wall time is mostly sleep (the first run took 1,061 s).
8. **Clones left on disk:** `C:\vs4` (session 4) and `C:\vs4b` (this session). Both are safe to delete.

## Tests

`pytest -p socket --disable-socket -q`: `4503 passed` on Windows at `fd21334` (601 s) and in a fresh clone (622 s). `ruff check .`: `All checks passed!` CI on `fd21334`: success (run 41048873958); on `e92c2be` (4b.1): success (run 40932005564).

## `git log origin/main --oneline -3` (before this commit)

```
fd21334 step 4.3: daily surface run and figures
dfc3d45 step 4.2: SSVI
e92c2be step 4b.1: SVI refit exit rule and share gate
```
