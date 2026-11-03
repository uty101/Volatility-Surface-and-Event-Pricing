# instructions/06_section_6.md: Session 6 (capture fix, Section 5 follow-ups, then Section 6: event pricing)

Read `CLAUDE.md`, `PLAN.md` and every earlier instruction file first. This file beats them where they differ (rule 13). Build steps 6.0 and 6.0b, then every step of Section 6, in one session. This instruction names the capture job, so rule 15 allows the changes in step 6.0.

---

## A. Approval of Section 5

Section 5 is complete and approved. The reviewer checked it from a fresh clone at `f43c758`.

- **PIT values.** The reviewer recomputed both from the committed `svi_fits.csv`, using a different method: a central difference of the Black put price on the slice, (P(K + h) − P(K − h)) / 2h at the realised close. The result was `^SPX` 0.411159 and SPY 0.411954, the same as `pit.csv` to 6 decimals.
- **`density_checks.csv`.** It holds 1,013 rows over the 3 days. The largest |int_err| is 2.5e-9.

---

## B. Decisions

| Item | Decision |
|---|---|
| O-38 | (b), in 2 parts. **1. Kinked slices.** The reviewer measured all 99 accepted slices with s at the 1e-4 floor. Each puts a median of 4.6 times, and up to 22 times, the probability that a flat smile at w(m) would put in the band m ± 20s. That is a corner in the fitted smile, not information in the quotes. Only 2 of the 913 other slices go above 2 times. These slices keep their Section 4 status, because their vols fit within the RMSE gate. Their density gets status `kink` when s ≤ `s_min` × (1 + 1e-6), and they are left out of `tail_probs.csv`, `pit.csv` and the density figure. **2. FD step.** The finite-difference step becomes dk = F × min(`bl_dk`, s / 10). The test runs on every non-`kink` accepted slice on every day, with the 5e-3 × peak bound. A slice that still misses the bound gets density status `fd_gap`, is left out like `kink`, and is listed in the review. This is not a stop. |
| O-39 | (a). Write the SVI parameters at full precision (`%.17g`) in `svi_fits.csv`, and have steps 5.1 and 5.2 read the parameters as they were fitted. |
| Status 3 (daily shares below 0.75) | Reported only, as before. |
| Status 4 (runtime) | Accepted. |
| Status 5 | Draw `spx_smiles_{day}.png` for every day, so no stale figure stays behind. |
| Status 6 | The owner may delete `C:\vs4`, `C:\vs4b`, `C:\vs5`, `C:\vs5b` and `C:\vs5c`. Claude Code does not. |

Record these in `decisions/section_5_review.md` under `## Session 5c`.

---

## C. The 2026-11-02 capture was lost

GitHub started all 3 scheduled runs on 2026-11-02 between 7 h 50 min and 10 h late: at 23:06 and 23:52 UTC, and at 01:18 UTC on 2026-11-03. All 3 correctly logged a skip. The 2026-10-30 run started 4 h 38 min late and still made the window by 7 minutes.

Waiting for a fixed target time from a fixed cron does not survive delays of that size. The fix in step 6.0 starts runs much earlier and lets a run hand over to a fresh run of itself when the wait is longer than a job may last. A `workflow_dispatch` run started with `GITHUB_TOKEN` starts at once; GitHub delays only scheduled runs.

Option chains cannot be captured after the fact, so 2026-11-02 stays missing. Record the gap in `decisions/capture.md`.

---

## D. Steps

### Step 6.0 (commit `step 6.0: early crons and self-dispatch for the capture`)

1. **`config.toml` `[snapshot]`.**
   - `cron_utc = ["17 9 * * 1-5", "17 12 * * 1-5", "17 15 * * 1-5", "17 18 * * 1-5"]`.
   - `max_wait_s = 19800` (330 minutes, below the 355-minute job limit).
2. **`scripts/snapshot.py --wait`.** After check (b), if the wait is above `max_wait_s`:
   - sleep `max_wait_s`;
   - repeat check (a);
   - run `gh workflow run snapshot.yml --ref main` with no force input;
   - log `chained: dispatched a new run with S seconds still to wait`;
   - exit 0.

   Otherwise, behave as now.
3. **`.github/workflows/snapshot.yml`.**
   - Use the 4 crons.
   - Add `actions: write` to `permissions`, so the job can dispatch itself.
   - Keep the concurrency group. At most 1 run waits in the queue, and any run in it carries on the chain.
4. **Tests.**
   - A run started at 09:17 UTC on 2026-11-04 chains, because it would wait 673 minutes until 20:30 UTC. Check this with a fake `gh` call and a fake sleep.
   - A run started at 17:17 UTC captures after waiting 193 minutes.
   - A run started at 22:00 UTC skips.
5. **Push, then arm today's capture.** Run `gh workflow run snapshot.yml` with no force input, so 2026-11-03 is covered whatever the cron does. Print the first 20 log lines.

### Step 6.0b (commit `step 6.0b: kink and fd_gap density statuses, full precision parameters`)

1. Apply O-38 and O-39.
2. Rerun steps 5.1 and 5.2 for every day.
3. Print:
   - the counts of `ok`, `kink`, `fd_gap` and `density_fail` per day;
   - every `fd_gap` row;
   - the new PIT rows.

Section 4 does not need a rerun: only the CSV writer changes. Rewrite `svi_fits.csv` from the stored fits. If the fits are not stored, rerun the surface stage.

### Steps 6.1 and 6.2

As in PLAN.md Section 6 and kickoff 5.7, with O-11 (a), O-12 (b) with the 15:00 rule, and O-13 (a). The 2 manual files are below. Commit them exactly as given.

- **Snapshot days.** Every snapshot day in `data/snapshots/` plus the fixture day. The fixture day has only `^SPX`, SPY and AAPL. Run `pull_snapshots.py` first.
- **Missing pre-event snapshot.** An event whose window has no pre-event snapshot under Convention 4.11 keeps its row with status `no_pre_snapshot` and blank results. The count of such events is printed. This covers 2026-11-02, the missed day.
- **Future events.** Events whose window ends after the last close in `close.parquet` keep their row with status `pending`. Rerun `pull_data.py --stage prices` first and keep the result.
- **Small samples.** With fewer than `[events] min_n` events, the summary is the descriptive table only, as kickoff 5.7 says. That is expected this early.

`data/manual/earnings_overrides.csv`:

```
ticker,event_date,timing,source_url
AAPL,2026-11-02,AMC,https://www.apple.com/newsroom/2026/11/apple-reports-fourth-quarter-results/
ABNB,2026-11-05,AMC,https://www.nasdaq.com/press-release/airbnb-announce-third-quarter-2026-results-2026-10-01
AMAT,2026-11-12,AMC,https://www.appliedmaterials.com/us/en/newsroom/press-releases/102226-applied-to-report-fourth-quarter-fiscal-2026-results.html
AMD,2026-11-03,AMC,https://ir.amd.com/news-events/press-releases/detail/1300/amd-to-report-fiscal-third-quarter-2026-financial-results
NVDA,2026-11-17,AMC,https://nvidianews.nvidia.com/news/nvidia-sets-conference-call-for-third-quarter-financial-results-6928873
PLTR,2026-11-02,AMC,https://www.businesswire.com/news/home/20261012995260/en/
```

`data/manual/macro_events.csv`:

```
date,kind,release_time_ny,source_url
2026-10-28,FOMC,14:00,https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
2026-11-06,NFP,08:30,https://www.bls.gov/schedule/news_release/empsit.htm
2026-11-10,CPI,08:30,https://www.bls.gov/schedule/news_release/cpi.htm
2026-12-04,NFP,08:30,https://www.bls.gov/schedule/news_release/empsit.htm
2026-12-09,FOMC,14:00,https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
2026-12-10,CPI,08:30,https://www.bls.gov/schedule/news_release/cpi.htm
```

Notes on the manual files:

- **Sources.** Every date and time comes from the company's own announcement or from the BLS and Federal Reserve calendars. ABNB uses Nasdaq's copy of its PR Newswire release.
- **Not yet listed.** AVGO, CRM, CSCO, ORCL and PANW have not yet announced a date, so they are left out and stay `unknown`. The reviewer adds them in a later instruction.
- **FOMC times.** The Fed calendar gives the meeting days. The 14:00 statement time is the Fed's standing practice.
- **Time of day.** Only the date matters for windows that run from close to close. `release_time_ny` is kept for the record.

---

## E. Review evidence (in `review/section_6.md`)

1. **Step 6.0:**
   - the test output;
   - the diff of `snapshot.yml`;
   - the log of the run armed in step 6.0 item 5.
2. **Step 6.0b:** the density status counts, every `fd_gap` row, and the PIT rows.
3. **Section 6:**
   - the full EVENTS table;
   - the summary rows;
   - every `unknown`, `no_pre_snapshot` and `pending` row;
   - for 2 events, a hand check of θ1, θ2, n1 and n2 against `svi_fits.csv` and the XNYS calendar.
4. **Wrap-up:**
   - every figure, listed by path;
   - the fresh-clone check;
   - CI status.

Status file: `instructions/06_section_6.status.md`.
