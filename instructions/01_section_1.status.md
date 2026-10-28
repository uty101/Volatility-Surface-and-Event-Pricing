# Status: session 1 (`instructions/01_section_1.md`)

## Outcome

Completed. Steps 1.0 to 1.4 are committed and pushed, everything that needs the 2026-10-28 capture is left for instruction 01b, as instruction 01 says, and the part B decisions are recorded in `decisions/section_1_review.md` and marked in `decisions/OPEN.md`.

## Last step reached

Step 1.4, then the part B decisions record, the fresh-clone check, `review/section_1.md` and this file.

## Reason for any stop

None.

## Step 1.0 timing

Step 1.0 (`494de82`) reached `origin/main` at **2026-10-28 12:40:06 UTC**, before the 19:15 UTC deadline. Tonight's 19:30 and 20:30 UTC Actions runs use `--upload better`. The forced Actions run from that push (40689704608) succeeded: 32 of 32 ok, 70,424 rows, uploaded to `snapshots-test` because no snaplog for 2026-10-28 was there yet (last 3 log lines in `review/section_1.md`, D1).

## Tests

`pytest -p socket --disable-socket -q`: `40 passed, 5 warnings` on Windows and in the fresh clone at `fcf3ad4` (full output in `review/section_1.md`). `ruff check .`: `All checks passed!` CI on `fcf3ad4`: success.

## Questions and blockers for the reviewer

1. **Owner action: re-register the local task.** `scripts/windows/register_snapshot_task.ps1` now passes `--upload better`, but it was not run (instruction 01, step 1.0 item 4). Until the owner reruns it, the registered task still uses `--upload if-missing`.
2. **O-25 CLEAN_LOG note column.** The instruction puts a note on the `^SPX` rule e row, and the CLEAN_LOG schema has no note column. Implemented as (a), a trailing `note` column after the 5 schema columns. (b) would put the note into `rule`.
3. **O-26 `start_ny` and `ny_start`.** PLAN 1.4 has `start_ny` and instruction 01 adds `ny_start`. Implemented as (a), keeping both: wall time `HH:MM:SS` and SNAPLOG's full timestamp. (b) would keep one.
4. **PUT and BXM history start (bears on Section 8).** The Cboe chart JSON gives PUT daily only from 2007-01-03; before that it holds 7 scattered values between 1991-03-04 and 2004-03-16. BXM starts on 2002-03-22. Question 4 assumes monthly PUT and BXM returns from 1990. The rows are in `review/section_1.md`, D2b.
5. **XLK holdings keep 1 futures line** (`IXTZ6`, XAK TECHNOLOGY DEC26, weight 0.00000331), because the rule drops only blank and `-` tickers. Weights sum to 0.999488.
6. **Small interpretations to confirm.** These are listed in `review/section_1.md` under Not verified. They cover the NaN bid and ask handling under rules a to d, the bounds in American rule e, the session count for `stale`, how `better` tells a missing snaplog from a failed download, the New York pull date, and where `load_snapshot` puts the snaplog run fields.
7. **The first FRED request timed out** because of a `User-Agent: Mozilla/5.0` header in `pull_data.py`. It was a fault in the client code, not a failed pull: the header was removed, all stages reran cleanly, and nothing was worked around.

## `git log origin/main --oneline -3` (before this commit)

```
fcf3ad4 section 1: review decisions recorded
b1be0ec step 1.4: capture health
2557f5b step 1.3: loader and cleaning
```
