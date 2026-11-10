# Status: session 12 (`instructions/12_results_refresh.md`)

## Outcome

Complete. Both steps are built, and the evidence is in `review/section_12.md`.

## Last step reached

Step 12.2, then the second run, the fresh-clone check, CI, the review and this file.

## What changed

- **Part A.** `decisions/section_11_review.md` records the Section 11 decisions. O-50 to O-55 are marked decided. The README's breach sentence keeps its sign. Nothing was deleted: `C:\vs4` to `C:\vs11`, `C:\vs11pre`, `data/processed/surface_s10_backup` and `data/processed/surface_cold1` are left for the owner.
- **Step 12.1** (`2f0c362`). 5 specifications in `spec_log.csv`, and a new table `outputs/tables/spec_family.csv` (O-56). With N = 5 trials and 237 months:

  | series | Sharpe | deflated Sharpe | probabilistic Sharpe against 0 | reviewer |
  |---|---|---|---|---|
  | timed PUT, excess over T-bills | 0.803 | 0.994 | 0.999 | DSR 0.994 |
  | timed minus PUT | 0.240 | 0.412 | 0.915 | DSR 0.412, PSR 0.915 |
  | PUT, excess over T-bills | 0.555 | | 0.984 | PSR 0.984 |

  Every Sharpe in the reviewer's table matches to 3 decimals. Question 4 now says selling puts paid, the GARCH rule looks better on its own, its gain over PUT cannot be told apart from luck after counting 5 rules, and the other 4 rules did worse than PUT.
- **Step 12.2** (`1ee2a70`). Prices and Cboe to the 2026-11-06 close, FRED to 2026-11-05.
  - Capture window: 2026-10-28 to 2026-11-06, 7 days, 2026-11-02 missed.
  - EVENTS: completed 4 to 11, pending 38 to 35, no pre-event snapshot 3 to 3, unknown 1 to 1. 4 February 2027 events are new to the calendar.
  - Newly completed, with ratios: AAPL 0.48, PLTR 0.14, AMD 0.13, SHOP 0.73, UBER 0.69, ABNB 1.10, `^SPX` NFP 0.18.
  - Question 3's N is 11.
  - The breach is now `^SPX` dollar gamma of −918,440 against 250,000, on 2026-11-06.
  - `README.md` is 15,226 bytes.

## Questions and blockers for the reviewer

No blockers.

1. **2026-11-09 is not in the tables.** It reached the release after the refresh. A plain second `run_all.py` would have pulled it. So the second run ran every stage but `snapshots`, over the same local data, and `git status` was clean after it. Rerunning `scripts/run_all.py` after a fresh price pull picks the day up.
2. **Session 11 used stale rates on every capture day.** Its committed FRED files ended on 2026-10-26. The refresh appended later rows, so every day's rates, IVs and surface fits moved slightly. For example, XOM's ratio went from 0.88 to 0.89. That rate change is also why run A refitted all 7 days.
3. **"The other 4 did worse than PUT" holds on timed minus PUT only.** On excess return, 3 of the 4 beat PUT's 0.555: `iv_minus_ewma` 0.662, `iv_minus_rv21` 0.624 and `garch_above_median` 0.588. The answer states the comparison it uses.
4. **The deflation of timed minus PUT is fragile.** That series has skew 6.96 and kurtosis 72.2, and the probabilistic Sharpe uses a normal approximation. I did not check it by bootstrap.
5. **N = 5 is a floor.** The family was fixed after the main rule's 0.80 was known, so I removed a sentence I had drafted saying it was fixed before any result was seen.
6. **2 sentences were rewritten because the new days made them false.** Question 2's "after the 2026-10-30 sell-off", and the template's "ATM vol jumped on 2026-10-30 and stayed up". Vol fell back to 13.22% on 2026-11-04 and jumped again on 2026-11-05.
7. **The breach value differs from Part A's text.** Part A wrote −1,003,799, which was 2026-11-03's value. The sentence is generated from the last day, so it now reads −918,440, with the sign.
8. **O-56 and O-57** are implemented as (a); the reviewer may switch either. O-57 removed `risk_2026-11-03.pdf`, so only the last day's report is committed.
9. **Runtimes.**
   - Run 1 was superseded when 2026-11-06 reached the release, and its 325,445 s surface time spans a machine sleep.
   - Run A's surface stage took 74,117 s, refitting 7 days.
   - In the second run, the surface stage took 6.1 s from cache.
10. **A transient in the first price pull.** Yahoo briefly dropped CSCO's 2026-10-02 dividend of 0.42. The re-pull restored it, and `dividends.csv` is unchanged from session 11.
11. **Left on disk:** the clone `C:\vs12`, for the owner to delete with the others.

## Tests

- **Local suite** (working tree that became `1ee2a70`): `4747 passed, 35 warnings in 841.79s`.
- `ruff check .`: `All checks passed!`
- **Fresh clone** (`C:\vs12`, `1ee2a70`): `4747 passed, 35 warnings in 2084.20s (0:34:44)`.
- **CI** (run 42862012228, `1ee2a70`): success, `4747 passed`.

## `git log origin/main --oneline -3` (before this commit)

```
1ee2a70 step 12.2: refresh to the latest close and capture day
2f0c362 step 12.1: specification family and deflated Sharpe for question 4
1b089ad Add session 12 instructions
```
