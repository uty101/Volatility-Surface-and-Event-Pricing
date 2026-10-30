# Decisions from the Section 4 review (instruction 04b, part B)

One line per item: the choice made and the reviewer's reason where one was given.

- **The session 4 stop.** Correct; the fixed-count gate was the reviewer's error. Its bounds came from 1 run on 1 machine with a margin of 1 to 2 slices, and the success flag of refits that end at the iteration limit depends on the platform (Linux CI SPY 22, Windows 20 on the same code).
- **O-32.** (a). A refit counts as converged if SLSQP reports success or stops at the iteration limit, provided the result meets every Section 5.4 bound and constraint, has min g ≥ −1e-10, and has RMSE ≤ `max_rmse_volpts`. Which happened is recorded in a new `svi_fits.csv` column `exit` (`success` or `maxiter`). Reason: a feasible, arbitrage-free fit within 2 vol points is a valid smile, however the optimiser stopped; the quality gate still catches bad fits.
- **The fixture gate.** The 3 fixed counts are replaced by a share: for each fixture ticker, accepted slices ÷ slices with at least `min_quotes` quotes ≥ `[svi] min_accept_share` = 0.75, with the counts and shares printed on every run. Reason: it holds across platforms.
- **O-31.** (a).
- **Status 5 (interpretations).** All accepted, including the lowest objective over all starts for the first fit, and k ∈ [−2, 2] in `test_recovers_known_params`.

## Session 4b

Decisions from instruction 05 part A. Section 4 is approved, with the fixes in step 5.0.

- **O-33.** (a), scipy's default SLSQP settings for SSVI.
- **Status 2 (γ on its bound, SSVI RMSE 2.6 to 3.5 vol points).** A real model limit that biases the daily metrics. Fixed in step 5.0 item 3: SURFACE_DAILY metrics come from the accepted SVI slices, and SSVI's 25-delta risk reversal is kept beside them as `ssvi_rr25_30`.
- **Status 3 (calendar violations).** Checked only where both slices have quotes (step 5.0 item 4).
- **Status 4.** Noted.
- **Status 5 (NFLX `no_root`).** Correct as is. NFLX lists strikes up to 2,660 against a spot of 62 (legacy listings), and a 0.015 mid that far out needs a vol above `iv_hi`. No change.
- **Status 6.** All interpretations accepted.
- **Status 8.** The owner may delete `C:\vs4` and `C:\vs4b`; Claude Code does not.
