# Capture

1. Snapshots run at 15:30 New York inside the session, with a start window of 15:25 to 16:30; rows captured after 16:00 are flagged (Correction 5).
2. Dagster is dropped. GitHub Actions cron is the primary; a Windows scheduled task on the owner's machine is the backup and uploads only on days the primary missed (Correction 6). *Replaced in instruction 04 step 4.0: GitHub Actions with `--wait` (instruction 03c) is the only scheduled capture. The local task is unregistered and `scripts/windows/` is deleted; `scripts/snapshot.py --runner local` stays usable by hand.*
3. Actions cron is UTC only, so 2 crons cover both sides of the 2026-11-01 US clock change and the script checks New York time itself (Correction 6).
4. Daily files are assets of the GitHub release `snapshots`, never committed; `scripts/pull_snapshots.py` downloads them and records hashes (Correction 7).
5. A stale last trade is a reported flag, not a drop rule, because far OTM wings often have live quotes and no recent trade (Correction 9).
