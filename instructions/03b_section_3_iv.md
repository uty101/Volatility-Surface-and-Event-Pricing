# instructions/03b_section_3_iv.md: Session 3b (finish Section 3: steps 3.2 and 3.3)

Read `CLAUDE.md`, `PLAN.md` and every earlier instruction file first. This file beats them where they differ (rule 13). Build steps 3.2 and 3.3 in one session.

---

## A. Review of session 3

Steps 3.0 and 3.1 are approved. Checked on Linux from a fresh clone at `0558512`: 4,475 tests pass with sockets disabled.

**The stop was correct, and the fault is in the reviewer's spec.** The round-trip tests asked for σ back to 1e-8 everywhere on the grid, including cases where the price carries no vol information at all. Examples are a 7-day call 30% in the money, or an American put sitting at immediate exercise. The reviewer reproduced S1 independently, then tested the rule in Section B on the same grid. Every case either comes back to within 1e-8 or is flagged; no case returns a wrong vol.

---

## B. Decisions

### The flat-price rule (replaces the round-trip requirement in PLAN 3.2)

After any solve (Newton, Brent, scalar American, batch American), compute the price sensitivity on the **same pricer** at the solved vol:

> sens = |P(σ̂ + 0.01) − P(σ̂ − 0.01)| / 2, with both vols clipped to [`iv_lo`, `iv_hi`]

If sens < `[iv] flat_tol` = 1e-4 (a 1-vol-point move changes the price by less than 0.01 cent), the row gets status `flat` and no vol. Add the key.

**Round-trip tests, restated.** Run them on the full 2.1 grid, European (Black-76 on F and D) and American (CRR at `n_prod`, scalar solver). For each case, either:

- a vol is returned and |σ̂ − σ| ≤ `iv_roundtrip` = 1e-8; or
- no vol is returned, with status `flat`, `no_root` or `bounds`.

A returned vol that misses the tolerance fails the test. The test also prints the count of each status.

The reviewer's run of exactly this rule used `brentq` with `xtol = 1e-14` and `rtol = 1e-14` for both models. Of the 504 cases, 424 came back within 1e-8, 78 were `flat` (34 European, 44 American), 2 American were `no_root`, and none were wrong. Every flagged European case has a true vega below 2e-5 per vol point. Use the same Brent tolerances in the scalar solvers.

### Other choices raised in status item 2

| Question | Decision |
|---|---|
| Method name for batch-solved rows | `batch` |
| In-bounds row whose bracket has no root | method `no_root`, no vol |
| Vega scale in `iv_european` (no S) | the switch to Brent happens when vega < `min_vega` × F × D |
| `^SPX` rows of a `parity_fail` expiry | flag `parity_fail`, no vol |
| q on `^SPX` rows | that expiry's `q_impl`; the Black-76 price itself uses F and D only |
| `iv_summary.csv` columns | day, ticker, n_in, n_solved, n_newton, n_brent, n_batch, n_bounds, n_no_root, n_flat, n_parity_fail |
| `[iv] am_vol_tol` | 1e-9, not the 1e-7 in instruction 03, so the batch solver stays inside the 1e-8 round trip |

**Status item 3 (SPY K 50 call, 42.96 vol points).** Accepted with no change. An American IV of 134% on SPY comes from a stale deep ITM quote; `premium_pct_mid` (0.55%) is the meaningful number, and the bin medians do not move.

**Status item 4 (interpretations).** All accepted.

Record these in `decisions/section_3_review.md`.

---

## C. Steps

### Step 3.2: implied volatility

As in instruction 03, step 3.2, with Section B. Tests:

1. Round trips as restated in Section B, for European and American.
2. `iv_american_batch` matches scalar `iv_american` to 1e-6 on 200 random fixture rows (status must also match).
3. The flat rule: a deep ITM 7-day call returns `flat`, and an ATM 30-day option returns a vol.
4. Bounds flagging on synthetic violations, and a Brent fallback test for a 7-day 30% OTM put that is not flat. Choose σ so that sens is at least 1e-3, and print it.
5. Timing: the batch solver on the fixture's American OTM rows; record the seconds.
6. MEASURE: the largest American IV gap between N = 200 and N = 2000 on fixture SPY and AAPL OTM rows. Print it; assert only that it is finite.

### Step 3.3: IV on every captured day

As in instruction 03, step 3.3. Run `scripts/pull_snapshots.py` first. If the `snapshots` release now exists (the first scheduled capture is at 19:30 UTC tonight), include that day; if not, the fixture day alone is enough. Write `parity_forwards_fixture.csv` as well.

---

## D. Review evidence (in `review/section_3.md`, appended under `## Session 3b`)

1. Round-trip status counts for both models, and every returned vol's largest error.
2. Batch against scalar: largest and median gap, status agreement, and timing.
3. The N = 200 against N = 2000 measurement.
4. `parity_forwards_fixture.csv` in full.
5. `iv_summary.csv` in full and 10 random solved rows with all inputs.
6. The fresh-clone check and the CI status of the final commit.

Status file: `instructions/03b_section_3_iv.status.md`.
