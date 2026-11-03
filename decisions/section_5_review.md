# Decisions from the Section 5 review (instruction 05b, parts A and C)

One line per item: the choice made and the reviewer's reason where one was given.

- **The session 5 stop.** Correct; the fault is in the reviewer's spec. A grid in k with a fixed number of evenly spread points over a range in units of √w(0) is the wrong shape for SVI. On the committed `svi_fits.csv` g was negative somewhere on 229 of 570 accepted slices: 197 between the 801 grid points (down to −4.5e-3), 32 beyond the grid (down to −1.19 on QQQ 2026-11-03), 5 of those beyond |k| = 10.
- **The fix (instruction 05b part B).** The butterfly check runs on a sinh grid k = m + s·sinh(u) over [−`k_check`, `k_check`] = [−10, 10], s floored at `s_min`: 801 points for the constraint, the 200,001-point grid that the density integrates on for the acceptance check. A refit that meets its constraint but fails the acceptance check gets the 10 lowest-g acceptance points added to its constraint and is refitted from itself, at most 3 more times. Wing bound 1.98 (g → 1/4 − s²/16 = 0.0049 > 0 in the wings; the mean equals F only for a right wing slope below 2). The integral and mean are trapezoid sums on the sinh grid, with the closed-form mass beyond ±10 added to the integral and reported as `tail_mass`.
- **O-36.** (a), in the form of part B. A slice whose density still misses `int_tol` gets density status `density_fail`, has no tail table or PIT value, and is reported; not a stop.
- **O-34.** (a).
- **O-35.** (a). It is now valid, because g ≥ 0 is checked out to ±10 and the mass beyond is reported.
- **MEASURE (session 5 D3).** The largest analytic against finite-difference gap is ≤ 5e-3 × the slice's peak density on the quoted range; the measured worst case was 1.06e-3.
- **Status 5.** All noted. Runtime accepted. XLE and NFLX below 0.75 on 2026-10-29 are reported only.
- **Status 6.** Interpretations 1, 3, 4, 5 and 6 accepted. Interpretation 2 is replaced by part B: the sinh grid moves with m and s of the parameters being judged.
- **Status 7 (PIT data).** Rerun `scripts/pull_data.py --stage prices` and keep the refreshed files; PIT needs the 2026-10-29 closes. The row diff is printed, as in session 5.

## Session 5b

Decisions from instruction 05c part B. Step 5b.1 is approved; the stop was correct and the conflict is in the reviewer's spec.

- **O-37.** (a). Kickoff 5.6 is restated: q ≥ 0 holds up to the butterfly tolerance. `test_nonnegative_when_butterfly_passes` asserts, on the 200,001-point sinh grid of every accepted slice, g ≥ −1e-10 and p_k ≥ −1e-10 × the slice's largest p_k. The reviewer changes the spec, so rule 5 is not engaged. Reason: the dips are rounding-level (34 refit slices between −1.0e-10 and −3.2e-10 between sinh points, smallest w on them 6.4e-4); a density of −5e-12 carries no probability.
- **The 2 `density_fail` slices.** A fit with w ≤ 0 is not a valid smile, so Section 4 rejects it: every route, the first included, counts only with w ≥ `W_FLOOR` (1e-12) on the acceptance grid and every Section 5.4 bound and constraint met exactly (`_violation` = 0); a first fit that fails goes to the refit route (step 5c.1). The reviewer confirmed min w −6.0e-13 on CSCO 2026-11-13 and −1.3e-6 on SHOP 2026-11-20.
- **Status 3, 4, 5 (the finite-difference bound test), 6 (prices kept) and 7 (interpretations, including cutting points that accumulate across rounds as fixed values of k).** All accepted.
- **Status 8 (the 2026-10-30 capture).** Included as a third day if it is in the `snapshots` release when the session starts; otherwise the 2 days, said so. Not a stop either way.
- **Status 9.** The owner may delete `C:\vs5` and `C:\vs5b`; Claude Code does not.
- **`tail_mass` up to 2.6e-3 (MU 2027).** Accepted: those wings are fat and the closed-form tail counts that mass. The 10 largest values are printed in the review.

## Session 5c

Decisions from instruction 06 part B. Section 5 is complete and approved; the reviewer recomputed both PIT values from the committed `svi_fits.csv` by a central difference of the Black put price and matched `pit.csv` to 6 decimals.

- **O-38.** (b), in 2 parts. 1. Kinked slices: an accepted slice with s ≤ `s_min` × (1 + 1e-6) keeps its Section 4 status (its vols fit within the RMSE gate), but its density gets status `kink` and it is left out of `tail_probs.csv`, `pit.csv` and the density figure. The reviewer measured the 99 accepted slices with s at the floor: each puts a median 4.6 times, and up to 22 times, the probability a flat smile at w(m) would put in m ± 20s, a corner in the fit and not information in the quotes. 2. The finite-difference step becomes dk = F × min(`bl_dk`, s / 10), and the 5e-3 × peak bound runs on every non-`kink` accepted slice on every day; a slice that still misses it gets density status `fd_gap`, is left out like `kink` and is listed in the review. Not a stop.
- **O-39.** (a). The SVI parameters in `svi_fits.csv` are written at full precision (`%.17g`), and steps 5.1 and 5.2 read them as fitted.
- **Status 3 (daily shares below 0.75).** Reported only, as before.
- **Status 4 (runtime).** Accepted.
- **Status 5.** `spx_smiles_{day}.png` is drawn for every day, so no stale figure stays behind.
- **Status 6.** The owner may delete `C:\vs4`, `C:\vs4b`, `C:\vs5`, `C:\vs5b` and `C:\vs5c`. Claude Code does not.
