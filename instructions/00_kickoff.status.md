# Status: session 0 (`instructions/00_kickoff.md`)

## Outcome

Completed. Steps 0.0, 0.1 and 0.2 are committed and pushed. Live check 0.2.4b (registering the local scheduled task) was refused by Claude Code's permission system on the first attempt. It was registered afterwards, on the owner's instruction in the same session.

## Last step reached

Step 0.2, including live checks a and c, and this status file.

## Reason for any stop

None.

## Placeholder test output

`.venv/Scripts/pytest -p socket --disable-socket -q` on Windows: `7 passed, 5 warnings in 1.10s` (full output in `review/section_0.md`, Tests run). The `ci` workflow on the pushed commit passed on ubuntu-latest (run 40606139930). `ruff check .`: `All checks passed!`

## Live checks (details in `review/section_0.md`, Evidence)

- **a. Forced local run:** 32 of 32 underlyings ok, 72,610 CHAINS rows, exit 0, 6m15s. It ran at 20:01 New York, after the close, so only 620 of 12,182 `^SPX` rows have bid > 0 (Correction 5). The UNDERLYING table and the per-ticker rows, bid > 0 count and expiry range are printed in full.
- **b. Local task:** `gh` 2.101.0 is installed and authenticated as uty101, so the task was registered. The first attempt was denied by the permission classifier and not worked around; the owner then said to register it. `volsurf-snapshot` is Ready, Monday to Friday, next run 2026-10-28 19:30. Its triggers are stored as 19:30 and 20:30 **UTC** (StartBoundary `+00:00`), the same instants as the Actions crons, not London wall-clock times. From 2027-03-28 (BST) they fire at 20:30 and 21:30 London time. Reported, not changed.
- **c. Actions run:** run 40606139956 (push, forced) concluded **success** in 6m11s: 32 of 32 ok, 72,238 rows, 4 files uploaded to release `snapshots-test` (`test_chains_2026-10-27.parquet`, `test_earnings_2026-10-27.csv`, `test_snaplog_2026-10-27.json`, `test_underlying_2026-10-27.csv`). Yahoo did not refuse requests from Actions, so Actions stays the primary. Release `snapshots-test` is left in place.

## Questions and blockers for the reviewer

1. **Local task triggers are pinned to UTC** (check b, above). It works for the US clock change, but it does not follow `local_task_times_london` once the UK moves to BST. Options: (a) keep UTC triggers, which match the Actions crons; (b) re-register with triggers that follow London wall-clock time.
2. **OPEN items O-1 to O-24** in `decisions/OPEN.md`, each with 2 options: O-1 driver and helper location; O-2 output file names; O-3 price file layout and `^SPX` closes; O-4 fixture day; O-5 accepted chains asset; O-6 XLK holdings CSV columns; O-7 FRED missing values; O-8 EEP moneyness buckets; O-9 status and flag vocabularies; O-10 SSVI fit details; O-11 straddle strike; O-12 which earnings row defines an event; O-13 interval methods; O-14 PIT slice and density figure; O-15 live realised vol inputs and z-score; O-16 timed PUT T-bill and switch rule; O-17 Sharpe units for the deflated Sharpe; O-18 hedging simulation (`[sim] days = 21` against a 30-day straddle); O-19 per-underlying limits; O-20 dollar gamma definition; O-21 book position selection; O-23 rule e for `^SPX` before the parity forward exists; O-24 IV solvers for the 2.3 EEP table.
3. **O-22: capture interpretations already running** (option (a) of each). These are window bounds, CHAINS and UNDERLYING `snap_utc`, ticker status, retries, the skip log, the upload failure exit code, earnings failures and the task's power settings. Rule 15 means only an instruction file that names the capture job can change them.
4. **Earnings times:** every upcoming earnings date is served with a 15:00 New York placeholder time and classifies as `unknown` (16 rows printed in the review). This bears on O-12, and on how much `data/manual/earnings_overrides.csv` must cover.
5. **Expiry listing instability:** Yahoo listed 1 more expiry for `^SPX` (2026-12-10) and for SPY (2027-04-30) in the local run than in the Actions run 55 seconds later. A day's capture can miss an expiry without an error. This bears on O-5.

## `git log origin/main --oneline -3` (before this commit)

```
6a8de21 step 0.2: capture schedule
01c1dcd step 0.1: snapshot capture
a079d2a step 0.0: plan and scaffolding
```
