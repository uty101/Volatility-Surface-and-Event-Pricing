# instructions/04b_section_4_continue.md: Session 4b (finish Section 4)

Read `CLAUDE.md`, `PLAN.md` and every earlier instruction file first. This file beats them where they differ (rule 13). Build step 4b.1, then steps 4.2 and 4.3 from instruction 04, in one session.

---

## A. Review of session 4

Step 4.0 is approved (the local task is gone, the one-sided flat rule passes, and the suite takes 85 s without the SVI gate). Step 4.1 is approved apart from the gate.

**The stop was correct, and the gate was the reviewer's error.** The bounds came from 1 run on 1 machine with a margin of 1 to 2 slices. The refits that reach a valid surface on short SPY expiries end at SLSQP's iteration limit, and the success flag then depends on the platform: Linux CI gives SPY 22 and Windows gives 20 on the same code. A fixed count of that kind was never going to hold.

---

## B. Decisions

| Item | Decision | Reason |
|---|---|---|
| O-32 | (a). A refit counts as converged if SLSQP reports success **or** stops at the iteration limit, provided the result meets every Section 5.4 bound and constraint, has min g ≥ −1e-10, and has RMSE ≤ `max_rmse_volpts`. Record which happened in a new `svi_fits.csv` column `exit` (`success` or `maxiter`). | A feasible, arbitrage-free fit within 2 vol points is a valid smile, however the optimiser stopped. The quality gate still catches bad fits. |
| The fixture gate | Replace the 3 fixed counts with a share: for each fixture ticker, accepted slices ÷ slices with at least `min_quotes` quotes ≥ `[svi] min_accept_share` = 0.75. Print the counts and shares on every run. | It holds across platforms. On Windows under (a) the shares are 34/36, 24/24 and 14/14; under the old rule they were 30/36, 20/24 and 14/14, still above 0.75. |
| O-31 | (a) | |
| Status 5 (interpretations) | All accepted, including the lowest objective over all starts for the first fit, and k ∈ [−2, 2] in `test_recovers_known_params`. | |

Record these in `decisions/section_4_review.md`, and add `min_accept_share` to `config.toml`.

---

## C. Steps

### Step 4b.1 (commit `step 4b.1: SVI refit exit rule and share gate`)

1. Apply O-32 (a) and the share gate.
2. Rerun step 4.1 on the fixture. Print the per-ticker counts, the shares, and every slice that is not `ok`, with its `exit`, RMSE and min g.
3. The suite must pass on Windows and in CI.

### Steps 4.2 and 4.3

As in instruction 04, unchanged.

- The days are the fixture day plus every real capture in `data/snapshots/`. Run `pull_snapshots.py` first.
- If the 2026-10-29 capture has landed (it runs at 19:30 UTC), include it.
- If it has not landed yet, the fixture day alone is enough. This is not a stop: say so in the status file and carry on.

---

## D. Review evidence (append to `review/section_4.md` under `## Session 4b`)

1. Step 4b.1: the per-ticker counts and shares, the non-`ok` slices, and the CI result.
2. All of instruction 04 D3 to D6.

Status file: `instructions/04b_section_4_continue.status.md`.
