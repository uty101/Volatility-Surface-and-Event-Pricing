# Status: session 3 (`instructions/03_section_3.md`)

## Outcome

Stopped under rules 4 and 5. Parts A and B and steps 3.0 and 3.1 are committed and pushed (`e53507e`, `2f7a4ad`, `b3b330d`). Steps 3.2 and 3.3 are not built. Review evidence is in `review/section_3.md`.

## Last step reached

Step 3.1 complete. Step 3.2 stopped before any code was written, when a check of its fixed tests showed they cannot pass.

## Reason for the stop

PLAN 3.2 fixes `test_european_roundtrip_grid` and `test_american_roundtrip_grid`: σ recovered to `iv_roundtrip` = 1e-8 on the full 2.1 grid. That cannot be done on 8 of 252 European cases and 27 of 252 American cases. At those points the price at the true σ equals, to float64 rounding, the price at `iv_lo` or the intrinsic floor. Examples are the deep ITM 7-day calls whose time value is below the resolution of a price near 30, and the deep ITM American puts priced at immediate exercise. The price carries no vol information there, so no solver can recover σ. Several of these prices also sit exactly on, or a few e-12 below, the Section 5.3 bounds. Rule 5 forbids narrowing or skipping the cases, so the section stops. The full list of cases, with the probe that produced it, is in `review/section_3.md`, S1.

## Questions and blockers for the reviewer

1. **The S1 stop.** For the 3.2 round-trip tests: (a) keep the full grid, and state the rule that marks a case as unidentified, which must then return no vol; or (b) run the round trips on the OTM half of the grid only (Convention 4.5). Every failing case is ITM. The step 3.0 item 5 test meets the same problem once: the K 70, 30-day, σ 0.15 call has no IV. It is handled and explained in review D1.
2. **Choices step 3.2 and 3.3 will need** (listed in the review under Open questions; nothing is built on them yet): the IV method name for batch-solved rows and for in-bounds rows with no root; the vega scale in `iv_european`, which has no S; the `^SPX` rows of a `parity_fail` expiry, and q for `^SPX` rows; the by-method column names of `iv_summary.csv`.
3. **Deep ITM SPY calls keep the largest vol premiums after step 3.0.** For example, K 50 shows 42.96 vol points: at its American IV of 1.34, vega is 0.054 per vol point, above `min_vega_pt`. Its `premium_pct_mid` is 0.55%. Reported, not changed.
4. **Interpretations** to confirm are under Not verified in the review: which columns `low_vega` blanks; that the summary statistics are over `ok` rows; the strike tie rule in `parity_forward`; diagnostics kept on `parity_fail`; rows of `parity_fail` expiries kept unchecked by rule e; strict European bounds.
5. **Captured days.** The `snapshots` release does not exist yet (`gh release view snapshots`: `release not found` at 16:29 UTC), so only the fixture day exists. Step 3.3 did not run anyway.

## Results

- **3.0:** `eep_rows.csv` and `eep_summary.csv` are regenerated. OTM call medians are now 0 to within 1e-14, against −0.027 to +0.016 before. Status counts: 6,860 `ok`, 30 `low_vega`, 217 `both_fail`, 1 `american_fail`.
- **3.1:** all 36 fixture `^SPX` expiries pass the parity gate (median mad_bp 0.454, largest 0.838, at least 8 pairs). Rule e for `^SPX` now drops 335 rows, all ITM.
- Outputs are byte-identical over 2 runs.

## Tests

`pytest -p socket --disable-socket -q`: `4475 passed` on Windows and in a fresh clone at `b3b330d`. `ruff check .`: `All checks passed!` CI on `b3b330d`: success (run 40730251845).

## `git log origin/main --oneline -3` (before this commit)

```
b3b330d step 3.1: forwards
2f7a4ad step 3.0: EEP on matched trees
e53507e section 3: section 2 decisions recorded, parity forward amendment
```
