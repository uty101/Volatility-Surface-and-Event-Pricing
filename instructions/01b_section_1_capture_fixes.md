# instructions/01b_section_1_capture_fixes.md: Session 1b (capture fixes before the first real capture)

Read `CLAUDE.md` and `instructions/01_section_1.md` first. This file beats both where they differ (rule 13). It is short and must be **pushed before 19:15 UTC today (2026-10-28)** so tonight's capture runs with it. It names the capture job, so rule 15 allows the changes below and no others.

The fixture and the real-data evidence that instruction 01 deferred now move to `instructions/01c_section_1_fixture.md`, written after tonight's capture.

---

## A. Review of session 1

Session 1 is approved apart from the 2 problems fixed below. What the reviewer checked independently on Linux from a fresh clone at `fd1ce4c`:

- Installed from the lock and ran the suite with sockets disabled: 40 passed.
- `should_upload` and the `better` branch read the release's asset list before downloading, so a missing snaplog is told apart from a failed download. The workflow and the PowerShell script both pass `--upload better`.
- Confirmed from Cboe directly that PUT is daily only from 2007-01-03 (`PUT_History.csv` has the same 7 scattered points before that) and BXM from 2002-03-22. Status item 4 is right.
- Read `close.parquet` (31 columns, 1989-12-01 to 2026-10-27, last closes match the forced captures), `index.parquet`, `sectors.parquet` (complete from 1998-12-22) and the FRED files.

**Problem 1: the XLK names are the wrong ones.** The parsed SSGA file shows the 10 names in `[universe] xlk_holdings` cover only 59.8% of XLK. MU (4.0%), INTC (2.7%), PANW (1.9%), AMAT (1.8%) and LRCX (1.8%) are missing, while ORCL (1.3%), CRM (1.2%) and IBM (1.4%) rank 15th to 20th. Adding the 5 missing names takes coverage to 72.0%. This is the reviewer's error in the kickoff, not Claude Code's.

**Problem 2: the 2 capture runners can upload at the same moment.** Actions and the local task both start at 19:30 UTC. If both reach `--clobber` together, the release can end up with a chains file from one run and a snaplog from the other.

---

## B. Decisions

| Item | Decision | Reason |
|---|---|---|
| Status 1 (re-register the task) | The owner re-registers once, after this session, so the task gets the new times and `better` together. | Saves a second re-registration. |
| Status 4 (PUT and BXM history) | Research question 4 is restated (step 1b.3). The VIX and realised variance study and the GARCH signal still run from 1990. The 4 strategy backtests run on a common window from 2007-01-31, month end to month end. BXM is also reported alone from 2002-03-28, as a longer descriptive series. | 236 months that include 2008, 2020 and 2022 are enough to judge a short volatility strategy; scattered points before 2007 cannot be turned into monthly returns. |
| Status 5 (XLK futures line) | Accept as is. | Only captured names enter the implied correlation, renormalised, so a 0.0003% futures line never enters any calculation. |
| Status 6 (small interpretations) | All accepted as implemented. | Each matches the spec's intent. |
| O-25 | (a), a trailing `note` column. | |
| O-26 | (a), keep both. | |

Record these in `decisions/section_1_review.md` under a heading `## Session 1b`.

---

## C. Steps

### Step 1b.1: XLK universe (commit `step 1b.1: XLK top holdings`)

1. In `config.toml`, `[universe] xlk_holdings` becomes `["NVDA", "AAPL", "MSFT", "AMD", "AVGO", "MU", "INTC", "PLTR", "CSCO", "PANW", "AMAT", "LRCX", "ORCL", "CRM", "IBM"]` (15 names, the SSGA top 10 by weight, then the next 2, then the 3 already captured).
2. `[snapshot] min_tickers_ok` becomes `33` (37 underlyings, at most 4 failures, the same margin as before).
3. Run `scripts/pull_data.py --stage prices` again so `close.parquet` and `dividends.csv` include the 5 new names, and refresh `MANIFEST.json`. Nothing else in `data/raw/` changes.
4. Update the tests that count tickers. Add a test that the 15 configured XLK names cover at least 0.70 of the weight in the committed holdings CSV.
5. Review evidence: the new `[universe]` table, the coverage figure from the holdings CSV, and the first and last 3 rows of `close.parquet` for the 5 new columns.

### Step 1b.2: stagger the local task (commit `step 1b.2: local task 15 minutes after Actions`)

1. In `config.toml`, rename `[snapshot] local_task_times_london` to `local_task_times_utc` with the value `["19:45", "20:45"]`.
2. `scripts/windows/register_snapshot_task.ps1` reads the new key and registers triggers pinned to those UTC instants whatever the machine's time zone or season. Build each trigger time as a UTC `DateTime` and convert it to local time before calling `New-ScheduledTaskTrigger`, so the stored `StartBoundary` ends in `+00:00` or `Z`. Drop the check that the machine is on `GMT Standard Time`. The script prints each trigger's `StartBoundary` after registering.
3. Do not run the script. The owner runs it after this session.

Why these times work: the window is 15:25 to 16:30 New York. In US winter time (from 2026-11-01), 20:45 UTC is 15:45 New York, inside, and 19:45 UTC is outside and skips. In US summer time, 19:45 UTC is 15:45 New York, inside, and 20:45 UTC skips. Each day, exactly 1 local run captures, 15 minutes after Actions has uploaded, so `better` sees the Actions files.

### Step 1b.3: record the restated question and the window (commit `step 1b.3: VRP strategy window`)

1. In `config.toml` `[vrp]` add `strategy_start = "2007-01-31"` and `bxm_start = "2002-03-28"`.
2. Append to `CLAUDE.md` under `## Amendments` (this instruction allows staging `CLAUDE.md`):
   - "Instruction 01b. Research question 4 reads: Since 1990, how large is the gap between implied variance (VIX squared) and the realised variance that followed, does a GARCH forecast predict it, and from 2007 does selling S&P 500 puts (Cboe PUT) pay after costs, with or without timing on implied minus GARCH variance? Strategy backtests use month ends from `[vrp] strategy_start`; BXM is also shown alone from `[vrp] bxm_start`."
   - "Instruction 01b. `[universe] xlk_holdings` has 15 names; `[snapshot] min_tickers_ok` is 33; the local task runs at `[snapshot] local_task_times_utc`."
3. Update the PLAN.md paragraph for step 8.2 to match (this instruction allows staging `PLAN.md`).

### Step 1b.4: push and check (no commit of its own)

Push before 19:15 UTC. The push changes `scripts/` files only through the PowerShell script, and the workflow's `push` trigger watches `scripts/snapshot.py` and the workflow file, so no forced run is expected. Then trigger 1 forced run by hand with `gh workflow run snapshot.yml -f force=true`, wait for it, and print its last 5 log lines. It must show 37 tickers and at least 33 ok.

---

## D. Review evidence (append to `review/section_1.md` under `## Session 1b`)

1. The 5 items of step 1b.1.
2. The diff of `register_snapshot_task.ps1`.
3. The forced run's last 5 log lines and its run ID.
4. The full test output, the fresh-clone check, the CI status of the final commit, and the UTC time the last commit reached `origin/main`.

Status file: `instructions/01b_section_1_capture_fixes.status.md`.
