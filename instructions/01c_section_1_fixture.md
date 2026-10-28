# instructions/01c_section_1_fixture.md: Session 1c (fixture from the first real capture)

Read `CLAUDE.md`, `instructions/01_section_1.md` and `instructions/01b_section_1_capture_fixes.md` first. This file beats them where they differ (rule 13).

**Gate.** Run `gh release view snapshots --json assets --jq '.assets[].name'` first. If `chains_2026-10-28.parquet` and `snaplog_2026-10-28.json` are not both listed, stop before step 1c.1, write the status file saying which is missing, push and stop. Do not use any `test_` asset in this session.

---

## A. Approval of session 1b

Approved. Checked independently on Linux from a fresh clone at `bd34c94`: 41 tests pass with sockets disabled; `[universe] xlk_holdings` has the 15 names, `min_tickers_ok` is 33, `local_task_times_utc` is `["19:45", "20:45"]` and the `[vrp]` dates are set; `close.parquet` has 36 columns ending 2026-10-27, with the 5 new names present; the PowerShell script builds each trigger from a UTC `DateTime`.

Handling the intraday row (O-27) by pinning the date was the right call, and keeping the unchanged files and their manifest entries was correct.

---

## B. Decisions

| Item | Decision | Reason |
|---|---|---|
| O-27 | (b), as step 1c.3 below. `pull_data.py` ends every Yahoo history at the last **completed** XNYS session, so a rerun during the US session can never store an intraday price as a close. | The same trap would come back on every future rerun; the fix belongs in the code, not in a one-off call. |
| O-28 | (a). A `bxm_long` row in `strategy_stats.csv` and a dashed line on `vrp_cumulative.png`, labelled as a separate window. | One table and one chart keep the comparison in one place. |

Record both in `decisions/section_1_review.md` under `## Session 1c`, and mark them decided in `decisions/OPEN.md`.

---

## C. Steps

### Step 1c.1: fixture (commit `step 1c.1: fixture from 2026-10-28`)

1. Run `scripts/pull_snapshots.py`. It downloads the 2026-10-28 assets into `data/snapshots/` and writes `data/raw/snapshot_manifest.csv`.
2. Build the fixture from the 2026-10-28 assets, rows for `^SPX`, SPY and AAPL only: `tests/fixtures/chains_sample.parquet`, `tests/fixtures/underlying_sample.csv`, `tests/fixtures/earnings_sample.csv` (AAPL rows; `^SPX` and SPY have none). Copy rows exactly as served, with no re-typing of columns.
3. Tests in `tests/test_fixture.py`:
   - every fixture `^SPX` `contract_symbol` starts with `SPXW`;
   - **timing check:** among fixture `^SPX` rows with |ln(K / S)| ≤ 0.10, where S is the `^SPX` price in the fixture UNDERLYING, more than 90% have bid > 0;
   - fixture CHAINS column order equals the CHAINS schema;
   - every fixture `snap_utc` is between 15:25 and 16:30 New York time on 2026-10-28.
4. If the timing check fails, do not loosen it. Stop under rule 4 and print the share of bid > 0 by |k| bucket (≤ 0.05, 0.05 to 0.10, 0.10 to 0.25, > 0.25) and by expiry, for `^SPX` and SPY.

### Step 1c.2: real capture health and cleaning (commit `step 1c.2: capture health and cleaning on 2026-10-28`)

1. Run the capture health builder over the downloaded snapshots and commit `outputs/tables/capture_health.csv`.
2. Run `clean_chain` on the fixture day for all 3 fixture tickers and commit `outputs/tables/clean_log_fixture.csv`.
3. Add a test that `clean_chain` on the committed fixture reproduces `clean_log_fixture.csv` exactly.

### Step 1c.3: last completed session (commit `step 1c.3: histories end at the last completed session`)

1. In `volsurf/data.py` add `last_completed_session(now_utc: datetime) -> date`: the latest XNYS session whose close (from `exchange_calendars`, which knows early closes) is at or before `now_utc`.
2. `scripts/pull_data.py` uses it as the end of every Yahoo history (`end` = that session + 1 day, since yfinance `end` is exclusive) and records it in `MANIFEST.json` as `last_session`.
3. Tests: `2026-10-28 14:56 UTC` gives 2026-10-27; `2026-10-28 20:01 UTC` gives 2026-10-28 (close 16:00 New York = 20:00 UTC on that date); `2026-11-27 18:30 UTC` gives 2026-11-27 (early close 13:00 New York = 18:00 UTC); `2026-11-26 23:00 UTC` gives 2026-11-25 (holiday).
4. Do not rerun the pulls; the committed data already ends on 2026-10-27.

---

## D. Review evidence (append to `review/section_1.md` under `## Session 1c`)

1. The gate output (asset list of `snapshots`).
2. The 2026-10-28 SNAPLOG run fields (run ID, runner, `ny_start`, `n_ok`, `n_partial`, `n_error`), and its per-ticker rows for every ticker that is not `ok`.
3. Which runner's files are in the release, and the snapshot log lines of every run that touched 2026-10-28 (Actions 19:30 and 20:30 UTC, and the local task if registered), showing which ones uploaded and which skipped.
4. Fixture row counts per ticker, and the timing check numbers: for `^SPX` and SPY, the share of rows with bid > 0 overall and within |k| ≤ 0.10.
5. `capture_health.csv` in full, and `clean_log_fixture.csv` in full with the share of rows surviving per ticker.
6. The full test output, the fresh-clone check, and CI status of the final commit.

Status file: `instructions/01c_section_1_fixture.status.md`.
