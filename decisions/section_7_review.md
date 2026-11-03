# Decisions from the Section 7 review (instruction 08, part A)

Section 7 is approved. The reviewer checked it from a fresh clone at `b05fed2`.

- **COR3M.** The regression matches the reviewer's own to 4 decimals.
- **Live implied correlation.** The reviewer recomputed it from `surface_daily.csv` and the holdings file, with the same renormalisation: 0.331 on 2026-10-29 (covered weight 0.721, 15 names) and 0.565 on 2026-10-30 (0.661, 13 names), matching the table.
- **The jump is real.** On 2026-10-30 the S&P 500 fell 1.8% and XLK fell 4.9%. XLK's 30-day ATM vol rose from 25.2% to 33.7%, `^SPX`'s from 13.0% to 16.5%. Implied correlation rising in a sell-off is the textbook pattern, and the write-up says so.
- **O-40** (a).
- **O-41** (a).
- **O-42** (a) for the data, with the realised vol of (b). `data/raw/prices/adj_close.parquet` holds the adjusted close of every captured underlying, written by the prices stage. Realised vol is √(252/21 × Σ r²) over the 21 daily log returns, with no demeaning, the same as Section 5.9 RV. The average pairwise realised correlation uses ordinary demeaned Pearson correlations. Built in step 8.0, ready for the first window completing on 2026-11-27.
- **Status 3 (the chained run).** Working as designed: run 41622958662 chained into run 41674897033. Print that run's log in step 8.0, and add 2026-11-03 if it landed.
- **Status 4.** Run the empty-cache surface stage once, then measure the cached second run.
- **Status 5 (cache key).** The `[density]` table is added to the cache key, because `int_points` sets the acceptance grid.
- **Status 6.** Accepted.
- **Status 7.** The owner may delete `C:\vs4` to `C:\vs7`. Claude Code does not.
