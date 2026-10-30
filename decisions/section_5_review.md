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
