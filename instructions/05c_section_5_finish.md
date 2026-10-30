# instructions/05c_section_5_finish.md: Session 5c (close O-37, then finish Section 5)

Read `CLAUDE.md`, `PLAN.md` and every earlier instruction file first. This file beats them where they differ (rule 13). Build step 5c.1, then step 5.1 again and step 5.2, in one session.

---

## A. Review of session 5b

Step 5b.1 is approved. The CI integral and mean failures that only showed on Linux are gone, and the 3 slices that are no longer accepted are honest rejections.

**The stop was correct, and the conflict is in the reviewer's spec.** "q ≥ 0 when the slice passed the butterfly check" cannot hold exactly while the check passes at g ≥ −1e-10. The reviewer checked every accepted slice in the committed `svi_fits.csv` on a 2,000,001-point uniform grid over |k| ≤ 10:

- 34 refit slices dip to between −1.0e-10 and −3.2e-10 between sinh points;
- the smallest w on any of those 34 slices is 6.4e-4.

These are rounding-level values. A density of −5e-12 carries no probability. Requiring g ≥ 0 exactly would only move the same rounding somewhere else.

The reviewer also confirmed the 2 `density_fail` slices: CSCO 2026-11-13 has a min w of −6.0e-13, and SHOP 2026-11-20 has −1.3e-6.

---

## B. Decisions

| Item | Decision |
|---|---|
| O-37 | (a). Kickoff 5.6 is restated: q ≥ 0 holds up to the butterfly tolerance. `test_nonnegative_when_butterfly_passes` asserts 2 things on the 200,001-point sinh grid of every accepted slice: g ≥ −1e-10, and p_k ≥ −1e-10 × the slice's largest p_k. The reviewer is changing the spec, so rule 5 is not engaged. Record the restated line in `CLAUDE.md` under Amendments. |
| 2 `density_fail` slices | A fit with w ≤ 0 is not a valid smile, so Section 4 must reject it. Do not leave it to the density stage. See step 5c.1. |
| Status 3 | All accepted. |
| Status 4 | Accepted. |
| Status 5 (FD bound test) | Accepted. |
| Status 6 (prices kept) | Accepted. |
| Status 7 (interpretations) | All accepted, including cutting points that accumulate across rounds as fixed values of k. |
| Status 8 (2026-10-30 capture) | If the 2026-10-30 capture is in the `snapshots` release when the session starts, include it as a third day. If it is not, use the 2 days and say so. Either way this is not a stop. |
| Status 9 | The owner may delete `C:\vs5` and `C:\vs5b`. Claude Code does not. |
| `tail_mass` up to 2.6e-3 (MU 2027) | Accepted. The wings of those slices really are fat, and the closed-form tail counts that mass. Print the 10 largest `tail_mass` values in the review. |

Record these in `decisions/section_5_review.md` under `## Session 5b`.

---

## C. Steps

### Step 5c.1 (commit `step 5c.1: q tolerance, positive w on every accepted fit`)

1. **Acceptance check, all 3 routes.** A fit counts only if:
   - w ≥ `W_FLOOR` (1e-12) at every point of the acceptance grid;
   - it meets every Section 5.4 bound and constraint exactly, as `_violation` = 0;
   - the first route meets that too, not only the refits.

   A first fit that fails either goes to the refit route, as a butterfly failure does.
2. **The O-37 test.** Apply O-37 (a) to `test_nonnegative_when_butterfly_passes`.
3. **Add a test** that CSCO 2026-11-13 and SHOP 2026-11-20 on 2026-10-29 come back either accepted with min w ≥ 1e-12 or rejected. Use small saved quote fixtures, as for QQQ.
4. **Rerun Section 4** for every day, and regenerate the tables and figures. Print every slice whose status or route changed against session 5b.

### Steps 5.1 and 5.2

As in instruction 05b part D, with the decisions above. PIT covers every captured expiry that has expired by the last close in `close.parquet` and `index.parquet`. That is at least `^SPX` and SPY 2026-10-29 from the fixture day.

---

## D. Review evidence (append to `review/section_5.md` under `## Session 5c`)

1. **Step 5c.1:**
   - the changed slices;
   - accepted counts per ticker per day;
   - the test output;
   - runtime.
2. **Instruction 05b part E items 2, 4 and 5**, for every day.
3. **The 10 largest `tail_mass` values**, with ticker, expiry and the right and left wing slopes.

Status file: `instructions/05c_section_5_finish.status.md`.
