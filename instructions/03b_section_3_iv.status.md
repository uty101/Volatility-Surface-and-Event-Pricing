# Status: session 3b (`instructions/03b_section_3_iv.md`)

## Outcome

Completed. Section 3 is finished: the part B decisions, step 3.2 and step 3.3 are committed and pushed (`4c1fcf9`, `b02f724`, `75ec927`). Evidence is in `review/section_3.md` under `## Session 3b`. Session 3c (the capture fix) ran in between, after `4c1fcf9` was written and before step 3.2; its commits are `a96f353` and `a149d82`.

## Last step reached

Step 3.3, then the fresh-clone check, the review section and this file.

## Reason for any stop

None.

## Results

- **Round trips (3b-D1):** on the full 2.1 grid, no returned vol misses `iv_roundtrip`. European: 116 `newton` and 102 `brent` (largest error 4.6e-12); 28 `flat` and 6 `bounds`. American: 206 `brent` (largest error 2.5e-11); 33 `flat`, 8 `bounds` and 5 `no_root`. The totals (424 solved, 80 flagged) match the reviewer's. The split differs because the bounds check runs before any solve.
- **Batch against scalar (3b-D2):** on the 200 test rows, statuses match and the largest gap is 2.9e-10. On all 7,108 clean American fixture rows they match too, with the same largest gap. The batch solver takes 38.8 s on the 3,992 American OTM rows (bound 300 s).
- **MEASURE N = 200 against N = 2000 (3b-D3):** largest American IV gap 0.00335 (0.34 vol points), median 0.00015, over 3,992 OTM rows; every row converged in 6 Newton iterations at N = 2000.
- **Step 3.3 (3b-D5):** fixture day only, since the `snapshots` release does not exist yet. 10,833 OTM rows, every one solved: `^SPX` 6,841 (2,473 `newton`, 4,368 `brent`), SPY 3,531 and AAPL 461 (`batch`). `parity_forwards_fixture.csv` is written: 36 expiries, all `ok`. The CSVs are byte-identical over 2 runs.

## Questions and blockers for the reviewer

1. **The batch flat rule misses 1 synthetic ITM case** (3b-D1). On the P 130, 365-day, σ 0.15 grid put, which is at immediate exercise, bisection ends at the edge of the flat price region, at 0.2099. Its sens there, 0.024, passes the rule, so batch returns a vol where the scalar solver returns `flat`. No fixture row and no test is affected, and `iv_chain` solves OTM quotes only. If batch and scalar should agree on such cases too, the flat rule could require low sensitivity on either side of σ̂.
2. **64% of `^SPX` rows fall back to Brent** (3b-D5). The share rises with |k|, because the Brenner-Subrahmanyam start is an ATM approximation. This is the Section 5.3 switch working as written, and is reported only.
3. **Interpretations** to confirm are under `### 3b not verified` in the review: the literals `BRENT_TOL` and `FLAT_BUMP`; the bisection midpoint; Newton starting only from an in-range start; `n_in` counting OTM rows plus `parity_fail` rows.
4. **The full suite now takes about 6 minutes** on Windows (7 in the fresh clone), mostly the N = 2000 MEASURE test.

## Tests

`pytest -p socket --disable-socket -q`: `4488 passed` on Windows and in a fresh clone at `75ec927`. `ruff check .`: `All checks passed!` CI on `75ec927`: success (run 40910469696).

## `git log origin/main --oneline -3` (before this commit)

```
75ec927 step 3.3: IV on every captured day
b02f724 step 3.2: implied volatility
4c1fcf9 section 3b: section 3 review decisions recorded
```
