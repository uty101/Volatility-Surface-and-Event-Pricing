# Status: session 1b (`instructions/01b_section_1_capture_fixes.md`)

## Outcome

Completed. Steps 1b.1 to 1b.3 and the part B decisions record are committed and were pushed together at **2026-10-28 15:00:34 UTC**, before the 19:15 UTC deadline, so tonight's 19:30 and 20:30 UTC Actions runs capture 37 underlyings with `min_tickers_ok = 33`. The forced run then captured 37 of 37 ok. Review evidence is in `review/section_1.md` under `## Session 1b`.

## Last step reached

Step 1b.4, then the review evidence and this file.

## Reason for any stop

None.

## Forced run

Run 40711619617 (`gh workflow run snapshot.yml -f force=true`, on `5c013e5`): success, `done ok=37 partial=0 error=0 rows=84065`, `uploaded 4 files to release snapshots-test`. The test snaplog for 2026-10-28 now carries run 40711619617 and `n_ok` 37, replacing this morning's 32 under `better`. The push started no snapshot run, as expected.

## Tests

`pytest -p socket --disable-socket -q`: `41 passed, 5 warnings` on Windows and in a fresh clone at `5c013e5`. `ruff check .`: `All checks passed!` CI on `5c013e5`: success.

## Questions and blockers for the reviewer

1. **Owner action: re-register the local task now.** `scripts/windows/register_snapshot_task.ps1` was not run (step 1b.2 item 3). Until the owner runs it, the registered task still fires at 19:30 and 20:30 UTC with `--upload if-missing`, at the same instants as Actions, which is the race of problem 2. Running it prints each trigger's `StartBoundary`; both should end in `Z`.
2. **O-27 How the prices stage was rerun.** At 14:56 UTC yfinance returned a live intraday 2026-10-28 row, and `--stage prices` ends the history at the New York pull date + 1, so the plain command would have stored an intraday price as the 2026-10-28 close. Implemented as (a): `stage_prices` called with the pull date pinned to 2026-10-27, so every file still ends on 2026-10-27; the session 1 `sectors.parquet` (adjusted closes recomputed by Yahoo, at most 7.6e-5 apart) and `index.parquet` (re-pulled byte-identical) kept with their manifest entries, so only `close.parquet`, `dividends.csv` and their entries changed. The 31 old close columns and 2,181 old dividend rows are identical. (b) would add a `--pull-date` flag or end the history at the last completed session in `pull_data.py`.
3. **O-28 Where BXM alone from `[vrp] bxm_start` is reported.** Instruction 01b names no output for it. (a) A `bxm_long` row in `strategy_stats.csv` and a line on `vrp_cumulative.png`. (b) A separate `bxm_long.csv`. Nothing is built; Section 8 needs a decision. PLAN 8.2 now marks it **OPEN O-28**.
4. **Final commit.** The commit carrying this file and the review cannot record its own push time or CI result; they are in `git log origin/main` and the Actions page.

## `git log origin/main --oneline -3` (before this commit)

```
5c013e5 section 1b: review decisions recorded
c43e2e6 step 1b.3: VRP strategy window
9a24030 step 1b.2: local task 15 minutes after Actions
```
