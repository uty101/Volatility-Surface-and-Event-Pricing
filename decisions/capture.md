# Capture

1. Snapshots run at 15:30 New York inside the session, with a start window of 15:25 to 16:30; rows captured after 16:00 are flagged (Correction 5).
2. Dagster is dropped. GitHub Actions cron is the primary; a Windows scheduled task on the owner's machine is the backup and uploads only on days the primary missed (Correction 6). *Replaced in instruction 04 step 4.0: GitHub Actions with `--wait` (instruction 03c) is the only scheduled capture. The local task is unregistered and `scripts/windows/` is deleted; `scripts/snapshot.py --runner local` stays usable by hand.*
3. Actions cron is UTC only, so 2 crons cover both sides of the 2026-11-01 US clock change and the script checks New York time itself (Correction 6).
4. Daily files are assets of the GitHub release `snapshots`, never committed; `scripts/pull_snapshots.py` downloads them and records hashes (Correction 7).
5. A stale last trade is a reported flag, not a drop rule, because far OTM wings often have live quotes and no recent trade (Correction 9).
6. **2026-11-02 is missing for good** (instruction 06 part C). GitHub started all 3 scheduled runs between 7 h 50 min and 10 h late (23:06 and 23:52 UTC, and 01:18 UTC on 2026-11-03), after the window, and each correctly logged a skip. Option chains cannot be captured after the fact. From instruction 06 step 6.0 the crons start at 09:17, 12:17, 15:17 and 18:17 UTC, and a run whose wait is above `[snapshot] max_wait_s` (330 minutes) sleeps that long and then dispatches a fresh run of itself to carry on the wait.
