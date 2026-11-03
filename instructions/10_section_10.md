# instructions/10_section_10.md: Session 10 (theta fix, then Section 10: risk report)

Read `CLAUDE.md`, `PLAN.md` and every earlier instruction file first. This file beats them where they differ (rule 13). Build step 10.0, then every step of Section 10, in one session.

---

## A. Approval of Section 9

Section 9 is approved, with the theta fix in step 10.0. The reviewer read it from a fresh clone at `9ea9fc8`.

| Item | Decision |
|---|---|
| O-45 | (a). Explained share is on the delta-hedged position. |
| O-46 | (a). In the write-up, put the Heston and GBM error sd side by side, and say that the means are not comparable because the drifts differ. |
| Status 3 (late-path residual) | **This is the reviewer's spec error.** Instruction 09 fixed Θ as a reprice with only T shortened. That leaves the roll of F and D in the residual, and near expiry the roll dominates. See step 10.0. |
| Status 4 (k = 65 mean) | Accepted. The reviewer's −0.025 was a low draw; 10 seeds give +0.0117 with standard error 0.0048. |
| Status 5 (N = 6) | Accepted. |
| Status 6 | The owner may delete `C:\vs4` to `C:\vs9`. Claude Code does not. |

---

## B. Steps

### Step 10.0 (commit `step 10.0: theta includes the carry of F and D`)

1. **Θ.** It is the change in value over dt with S and σ fixed and the clock moved on. That means T − dt, D rolled to e^(−r(T − dt)), and F rolled to S e^((r − q)(T − dt)), with r and q implied by that day's D and F/S. This is the time decay a desk reports. Apply it to the live attribution and the synthetic path. Write the reasoning in the docstring.
2. **The MEASURE becomes a test.** Print the new median explained share on the synthetic path, and the share on each of its last 5 days. Turn `test_bs_path_explained_share_measure` into a bound: median share ≥ 0.90. If the new median is below 0.90, report it and keep the finite-only assertion. That is not a stop.
3. **Rerun** the attribution stage, and print the live median against session 9's 0.937.

### Step 10.1: shock grid and limits

As in PLAN 10.1 and kickoff 5.11, with O-19 (a), O-20 (a) and O-21 (a), on the last captured day. These points are fixed:

- **Revaluation.** Use the same pricer the project uses for each contract:
  - `^SPX`: Black-76 on the day's parity F and D;
  - AAPL and NVDA: CRR American at `n_prod` with the day's r and q.
- **Sticky strike.** Each contract keeps its own SSVI vol at its strike. A spot shock moves S and F, but not the vol. A vol shock adds the shock in points to that vol, floored at `iv_lo`.
- **Greeks for limits.** Use the same pricers. Dollar delta is Δ × S × 100 × contracts × side. Vega per vol point is ν / 100 × 100 × contracts × side. Dollar gamma is O-20 (a).
- **Missing contract.** If a position's underlying has no accepted surface on the day, it keeps its row with status `no_surface` and blank values, and the book total says how many positions it left out.
- **Grid P&L** is in dollars: value change × 100 × contracts × side, summed over the book. It is also given per position.

### Step 10.2: PDF report

As in PLAN 10.2, for the last captured day. The page has:

- the book table: contract, side, contracts, price, vol, dollar delta, dollar gamma and vega;
- the 9 × 5 grid as a heat table, in thousands of dollars;
- the limit breaches;
- 1 line stating the day, the data source and the N of capture days.

---

## C. Review evidence (in `review/section_10.md`)

1. **Step 10.0:**
   - the new MEASURE and the last 5 days;
   - the live median against session 9's.
2. **Step 10.1:**
   - the selected contracts with their days, delta and vol;
   - `risk_grid.csv` for the last day;
   - `limit_breaches.csv`;
   - the small-shock MEASURE.
3. **Step 10.2:** the page render PNG, and the 2-build byte check.
4. **Wrap-up:**
   - the fresh-clone check;
   - CI status.

Status file: `instructions/10_section_10.status.md`.
