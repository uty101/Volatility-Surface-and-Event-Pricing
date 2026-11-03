# instructions/09_section_9.md: Session 9 (Section 9: P&L attribution)

Read `CLAUDE.md`, `PLAN.md` and every earlier instruction file first. This file beats them where they differ (rule 13). Build every step of Section 9 in one session.

---

## A. Approval of Section 8

Section 8 is approved. The reviewer checked it from a fresh clone at `d39fa33`.

| Item | Decision |
|---|---|
| Status 1 (signal share) | **The session is right and the reviewer was wrong.** The reviewer's 90.7% came from 2 errors in the reviewer's own run. VIX was looked up on exact dates, so 1997-01-31 and 1999-12-31 got no IV. The incomplete month 2026-11-02 was also counted. 362 of 395 (91.6%) stands. |
| Status 2 (mean VRP) | VRP_t = IV − RV does not need the GARCH forecast, so the headline is over every row with IV and RV: 0.01037 over 441 months. Report the GARCH-era mean (0.00970, 394 months) beside it, labelled. |
| The 3 numbers that miss at 2 decimals | Accepted, as explained: October 2026 now ends on the 10-30 close after the Cboe refresh. |
| O-43 | (a). |
| O-44 | (a). |
| `kurt_pearson` | Accepted. Record the departure from the kickoff signature in `decisions/section_8_review.md`. |
| Status 5 | Noted. |
| Status 6 | The owner may delete `C:\vs4` to `C:\vs8`. Claude Code does not. |

The 2026-11-03 capture landed through the chained run (37 of 37 ok). The capture fix works.

---

## B. Steps

### Step 9.1: attribution identity

As in PLAN 9.1 and kickoff 5.10. These points are fixed:

- **Greeks.** They come from the same pricer and inputs as the live straddle marks of O-44 (a): Black-76 on the day's parity F and Treasury D, at the SSVI vol of the contract, and spot delta as in O-44 (a). Get Γ, vanna and volga from the same pricer by the chain rule in S. Get Θ by repricing with T shortened by dt and nothing else changed.
- **dσ** is the change in that contract's SSVI vol: at the same strike, at T on t1 minus at T on t0. The change in the vol from the shorter T, through the surface's term structure, falls into dσ. Say so in the docstring.
- **dt** is (t1 − t0) in years, as in Convention 4.1.
- **Explained share.** The kickoff measure is 1 − |residual| / |total|. Report it per position and day, plus its median over the live rows.
- **MEASURE.** On a synthetic Black-Scholes path (σ fixed, so dσ = 0), measure the share with daily steps. Print it.

### Step 9.2: hedging frequency and live attribution

As in PLAN 9.2, with O-18 (a) changed for Heston, as restated in `decisions/section_1_review.md`. Use T = 21/252, 13 steps a day and a short ATM straddle (K = S0). Cash accrues at r. The hedge rebalances at steps 0, k, 2k, and so on. Hedging error is cash plus hedge minus payoff at expiry. Cost is `hedge_cost_bp` × |shares traded| × S, summed.

**Reviewer's GBM run, as a check.** This uses 20,000 paths, σ 0.2, r 0.04, μ 0 and BSM delta at σ. Its random draws come in a different order from the session's, so expect differences within Monte Carlo error.

| hedge every | error mean | error sd | cost mean | cost sd |
|---|---|---|---|---|
| 1 step | −0.0008 | 0.243 | 0.105 | 0.039 |
| 13 steps (1 day) | −0.008 | 0.860 | 0.029 | 0.010 |
| 65 steps (5 days) | −0.025 | 1.776 | 0.014 | 0.005 |

The opening premium is 4.606. The error sd grows close to √k: ×3.54 for 13 times fewer hedges, against √13 = 3.61. The section's error sd and cost mean should be within 3% of these. Each error mean should be within 3 standard errors (sd / √20,000) of the reviewer's. A miss is reported, not a stop.

**Heston.** There is no reviewer check. The write-up says why the error sd stops falling in proportion to √k under Heston: the hedge uses delta at √v_t but is blind to vol moves, so even continuous hedging leaves an unhedged vega P&L. Print the error sd at k = 1 for both models side by side.

**Live attribution.** Attribute every live straddle mark-to-mark move in `live_straddles.csv`, over the 4 snapshot days. With 3 day-to-day moves per position, this is a method demonstration with its N stated, as kickoff Section 2 item 1 requires.

---

## C. Review evidence (in `review/section_9.md`)

1. **Step 9.1:** the test output and the MEASURE value.
2. **Step 9.2:**
   - `hedging_frequency.csv` in full, against the reviewer's table;
   - the Heston rows;
   - the attribution rows for 1 live position end to end;
   - the median explained share.
3. **Wrap-up:**
   - every figure, listed by path;
   - the fresh-clone check;
   - CI status.

Status file: `instructions/09_section_9.status.md`.
