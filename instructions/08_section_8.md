# instructions/08_section_8.md: Session 8 (Section 7 follow-ups, then Section 8: volatility risk premium)

Read `CLAUDE.md`, `PLAN.md` and every earlier instruction file first. This file beats them where they differ (rule 13). Build step 8.0, then every step of Section 8, in one session.

---

## A. Approval of Section 7

Section 7 is approved. The reviewer checked it from a fresh clone at `b05fed2`.

- **COR3M.** The regression matches the reviewer's own to 4 decimals.
- **Live implied correlation.** The reviewer recomputed it from `surface_daily.csv` and the holdings file, with the same renormalisation. The result was 0.331 on 2026-10-29 (covered weight 0.721, 15 names) and 0.565 on 2026-10-30 (0.661, 13 names), matching the table.
- **The jump is real.** On 2026-10-30 the S&P 500 fell 1.8% and XLK fell 4.9%. XLK's 30-day ATM vol rose from 25.2% to 33.7%, `^SPX`'s from 13.0% to 16.5%. Implied correlation rising in a sell-off is the textbook pattern. The write-up should say so.

| Item | Decision |
|---|---|
| O-40 | (a). |
| O-41 | (a). |
| O-42 | (a) for the data, with the realised vol of (b). Add `data/raw/prices/adj_close.parquet` for every captured underlying to the prices stage. Realised vol is √(252/21 × Σ r²) over the 21 daily log returns, with no demeaning, the same as Section 5.9 RV. The average pairwise realised correlation uses ordinary demeaned Pearson correlations. Build it in step 8.0, so it is ready when the first window completes on 2026-11-27. |
| Status 3 (the chained run) | Working as designed: run 41622958662 chained into run 41674897033. Print that run's log in step 8.0, and add 2026-11-03 if it landed. |
| Status 4 | Run the empty-cache surface stage once, then measure the cached second run. |
| Status 5 (cache key) | Add the `[density]` table to the key, because `int_points` sets the acceptance grid. |
| Status 6 | Accepted. |
| Status 7 | The owner may delete `C:\vs4` to `C:\vs7`. Claude Code does not. |

Record these in `decisions/section_7_review.md`.

---

## B. Steps

### Step 8.0 (commit `step 8.0: adjusted closes, realised side of live correlation, cache key`)

1. **Prices stage.** Add `adj_close.parquet`, then rerun the stage.
2. **Realised side.** Build the O-42 realised side. Test it on a synthetic 3-name panel whose realised vols and correlations are known.
3. **Cache key.** Add `[density]` to the cache key.
4. **New days and Cboe data.**
   - Pull new capture days and run every stage for them. Rebuild EVENTS.
   - Refresh the Cboe files. `VIX.csv` currently ends on 2026-10-27.
5. **Print:**
   - the 2026-11-03 capture status;
   - the chained run log;
   - the surface stage runtime cold and cached.

### Steps 8.1 and 8.2

As in PLAN Section 8 and kickoff 5.9, with O-16 (b) as restated in `decisions/section_1_review.md` and O-17 (a). These 6 points are fixed here:

1. **Month ends** are the last `^GSPC` session of each completed calendar month (Convention 4.13). The current, incomplete month is never a month end. (Today the series ends on 2026-11-02, which is not a month end.)
2. **Index levels.** Each index level at a month end is the last available close on or before that session.
3. **Kurtosis.** `strategy_stats.csv` reports **excess** kurtosis. `deflated_sharpe` takes the **non-excess** (Pearson) kurtosis γ4, as in Bailey and López de Prado's formula, with (γ4 − 1)/4 × SR². Name the arguments to make this plain.
4. **Too few trials.** With fewer than 2 rows in `spec_log.csv`, the deflated Sharpe is blank with status `too_few_trials`. Log the main specification as row 1.
5. **Sharpe.** It uses excess returns over the T-bill month return of O-16 (b), for every strategy.
6. **Timed PUT.** It holds PUT in month m+1 if s_m > 0, else T-bills. Every change costs `switch_cost_bp`, and the first position counts as a change.

**Reviewer's independent run, as a check.** This uses the committed data, `arch` GARCH(1,1) with expanding fits from 1,000 observations, and month ends up to 2026-10-30.

- **VRP_MONTHLY.**
  - The first row with a GARCH forecast is 1993-12-31: IV 0.01360, GARCH 0.00471, signal 0.00889, RV 0.00505, VRP 0.00854.
  - Row 2026-09-30: IV 0.02670, GARCH 0.01512, signal 0.01158, RV 0.00942, VRP 0.01728.
  - The mean VRP over rows with both sides is 0.00971.
  - The signal is positive in 90.7% of months.
- **Strategies.** The window runs from 2007-02-28 to 2026-10-30 (237 months). The timed PUT holds PUT in 210 months and switches 41 times.

| | PUT | BXM | SP500TR | timed PUT |
|---|---|---|---|---|
| annualised mean | 0.0757 | 0.0645 | 0.1155 | 0.0890 |
| annualised vol | 0.1072 | 0.1095 | 0.1540 | 0.0906 |
| Sharpe | 0.560 | 0.446 | 0.648 | 0.808 |
| worst month | −0.1765 | −0.1501 | −0.1680 | −0.1342 |
| skew | −1.69 | −1.36 | −0.55 | −1.03 |
| excess kurtosis | 7.41 | 5.25 | 1.05 | 5.48 |

The section's numbers should match to 2 decimals. If any do not, print both and explain the difference. That is reported, not a stop.

**A note for the write-up.** The timed PUT's Sharpe of 0.81 against PUT's 0.56 comes from avoiding 27 months. It is 1 specification out of a family, so the deflated Sharpe is the honest number. The write-up gives the deflated Sharpe beside the raw one, and says how many specifications were tried.

**Live straddles.** Kickoff 5.9's live straddles are descriptive only, with 1 row per position per snapshot day. With only a few days of data, most positions stay open.

---

## C. Review evidence (in `review/section_8.md`)

1. **Step 8.0:**
   - the test output;
   - the capture status of 2026-11-03;
   - the chained run log;
   - cache runtimes;
   - the new EVENTS counts.
2. **Step 8.1:** the first and last 5 rows of VRP_MONTHLY, and a comparison with the reviewer's rows above.
3. **Step 8.2:**
   - `strategy_stats.csv` in full, against the reviewer's table;
   - `spec_log.csv`;
   - the 10 worst months of each strategy;
   - `live_straddles.csv`.
4. **Wrap-up:**
   - every figure, listed by path;
   - the fresh-clone check;
   - CI status.

Status file: `instructions/08_section_8.status.md`.
