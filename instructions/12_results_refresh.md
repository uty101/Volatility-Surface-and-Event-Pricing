# instructions/12_results_refresh.md: Session 12 (specification family for question 4, results refresh)

Read `CLAUDE.md`, `PLAN.md` and every earlier instruction file first. This file beats them where they differ (rule 13). Build steps 12.1 and 12.2 in one session.

---

## A. Approval of Section 11

Section 11 is approved, and with it the project's 11 sections. The reviewer read the README, `answers.csv` and the status from a fresh clone at `90be1cd`. CI is green with 4,729 tests.

| Item | Decision |
|---|---|
| O-50 to O-55 | All (a). |
| Status 1 | Accepted. The fix comes with a test. |
| Status 2 (NVDA slice 1.05 points from its mid) | Accepted. The slice passed the RMSE gate, and a 45-day single-name put 1 vol point off is within that gate. The slice stays the source. |
| Status 4 (question 4 blank) | **Changed.** This is the reviewer's gap. A deflated Sharpe needs the family of specifications that was tried, and the project tried only 1. Step 12.1 adds a small family, fixed here before any result is seen. |
| Status 5 and 6 | Step 12.2 refreshes prices and runs the newer capture days. |
| Status 9 and 10 | Accepted. The owner may delete `C:\vs4` to `C:\vs11`, `C:\vs11pre`, `data/processed/surface_s10_backup` and `data/processed/surface_cold1`. |

In the README's risk section, the breach sentence drops the sign that the table shows. Write it as "dollar gamma of −1,003,799 against a limit of 250,000".

---

## B. Steps

### Step 12.1 (commit `step 12.1: specification family and deflated Sharpe for question 4`)

These are the 5 specifications of the timed PUT. Each is the main rule with a different signal s_m at month end m, using only data up to and including m. Hold PUT in month m+1 if s_m > 0, else T-bills. Switch cost and T-bills are as in the main rule. The window is the same 237 months.

| spec_id | signal s_m |
|---|---|
| `timed_put_main` | (VIX/100)² minus the GARCH forecast. This is the existing rule. |
| `iv_minus_rv21` | (VIX/100)² minus 252/21 × Σ r² over the 21 sessions ending at m. |
| `iv_minus_rv63` | The same over 63 sessions, × 252/63. |
| `iv_minus_ewma` | (VIX/100)² minus 252 × the EWMA of r² with α = 0.06 (λ = 0.94), `adjust=False`, run from 1990-01-02. |
| `garch_above_median` | The main signal minus the expanding median of the main signal over month ends strictly before m. |

Log all 5 in `spec_log.csv`. The family is closed: do not add, drop or tune a specification after seeing results.

Then report 2 deflated Sharpes, both with N = 5 trials:

1. **Timed PUT.** The main specification's deflated Sharpe on excess returns over T-bills.
2. **Timing against holding PUT.** Take the monthly difference series, timed minus PUT, for each of the 5 specifications. Report the deflated Sharpe of the main one against the family's Sharpes of those differences, and its plain probabilistic Sharpe against 0. Question 4 asks whether timing *improves* on selling puts, and only this one answers that.

In both, the moments are skew and non-excess kurtosis of the series being tested, and Sharpes are monthly.

**Reviewer's independent run, as a check** (committed data, month ends up to 2026-10-30):

| spec | annualised Sharpe (excess) | annualised Sharpe of timed minus PUT |
|---|---|---|
| `timed_put_main` | 0.803 | 0.240 |
| `iv_minus_rv21` | 0.624 | −0.051 |
| `iv_minus_rv63` | 0.439 | −0.403 |
| `iv_minus_ewma` | 0.662 | −0.003 |
| `garch_above_median` | 0.588 | −0.158 |

- **The timed PUT is positive.** Its deflated Sharpe is 0.994. PUT alone has a probabilistic Sharpe of 0.984. Both very likely pay.
- **Timing is not shown to help.** The main specification's gain over PUT has a probabilistic Sharpe of 0.915 against 0, but a deflated Sharpe of 0.412 once the 5 specifications are counted.
- **The other 4 lose to PUT.** 4 of the 5 timing rules do worse than simply holding PUT.

The section's numbers should match these to 2 decimals, before the data refresh in step 12.2. If they do not, print both and explain the difference. That is reported, not a stop.

**Question 4's answer** says what these numbers show:
- selling puts paid;
- the GARCH timing rule looks better on its own;
- after counting the 5 rules tried, its gain over holding PUT cannot be told apart from luck;
- the other 4 rules did worse than PUT.

Give the numbers, with N = 5 trials and 237 months beside them.

### Step 12.2 (commit `step 12.2: refresh to the latest close and capture day`)

1. Refresh the prices, Cboe and FRED stages, so the pending events can complete.
2. Run `python scripts/run_all.py`. It pulls every capture day in the release and rebuilds every table, figure, the risk report for the last day, `answers.csv` and the README.
3. Print:
   - the capture window and day count;
   - the EVENTS status counts against session 11;
   - every newly completed event with its ratio;
   - question 3's new N.
4. Commit the refreshed outputs. `git status` must be clean after a second run.

---

## C. Review evidence (in `review/section_12.md`)

1. **Step 12.1:**
   - `spec_log.csv`;
   - the 2 deflated Sharpes with their inputs, against the reviewer's;
   - question 4's new answer rows.
2. **Step 12.2:**
   - the window;
   - the EVENTS counts and new rows;
   - the README diff;
   - `git status` after the second run.
3. **Wrap-up:**
   - the fresh-clone pytest;
   - `ruff`;
   - CI.

Status file: `instructions/12_results_refresh.status.md`.
