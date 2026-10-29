# Decisions from the Section 3 review (instruction 03b, part B)

One line per item: the choice made and the reviewer's reason where one was given.

- **S1 stop (round-trip tests).** Replaced by the flat-price rule. After any solve, sens = |P(σ̂ + 0.01) − P(σ̂ − 0.01)| / 2 on the same pricer, both vols clipped to [`iv_lo`, `iv_hi`]. If sens < `[iv] flat_tol` = 1e-4, the row gets status `flat` and no vol. The round trips run on the full 2.1 grid: each case either returns a vol within `iv_roundtrip`, or returns no vol with status `flat`, `no_root` or `bounds`. The scalar solvers use `brentq` with `xtol = rtol = 1e-14`. The stop was correct; the fault was in the reviewer's spec.
- **Method name for batch-solved rows.** `batch`.
- **In-bounds row whose bracket has no root.** Method `no_root`, no vol.
- **Vega scale in `iv_european`.** The switch to Brent happens when vega < `min_vega` × F × D.
- **`^SPX` rows of a `parity_fail` expiry.** Flag `parity_fail`, no vol.
- **q on `^SPX` rows.** That expiry's `q_impl`. The Black-76 price itself uses F and D only.
- **`iv_summary.csv` columns.** day, ticker, n_in, n_solved, n_newton, n_brent, n_batch, n_bounds, n_no_root, n_flat, n_parity_fail.
- **`[iv] am_vol_tol`.** 1e-9, not the 1e-7 of instruction 03, so the batch solver stays inside the 1e-8 round trip.
- **Status 3 (SPY K 50 call, 42.96 vol points).** Accepted with no change. An American IV of 134% on SPY comes from a stale deep ITM quote; `premium_pct_mid` (0.55%) is the meaningful number, and the bin medians do not move.
- **Status 4 (interpretations).** All accepted.

## Session 3b and 3c

Decided in instruction 04 part A. Section 3 and session 3c are approved.

- **3b item 1 (the batch flat rule misses the P 130 edge case).** Use the one-sided rule in step 4.0: sens = min(|P(σ̂ + 0.01) − P(σ̂)|, |P(σ̂) − P(σ̂ − 0.01)|), both vols clipped to [`iv_lo`, `iv_hi`], `flat` if sens < `flat_tol`, for every solver. The reviewer reran its 504-case grid with it: 424 within 1e-8, 80 flagged, 0 wrong.
- **3b item 2 (64% Brent on `^SPX`).** Accepted.
- **3b item 3 (interpretations).** All accepted.
- **3b item 4 (6-minute suite).** The N = 2000 measurement becomes a script, `scripts/measure_iv_tree.py` (step 4.0).
- **3c items 2 and 3 (the local task).** Remove the local task completely (step 4.0). The owner asked for it to go; with the GitHub runs now waiting for the window it is no longer needed, and its 2026-10-28 runs were killed without writing a line.
- **3c item 4 (1 pending run).** Accepted.
