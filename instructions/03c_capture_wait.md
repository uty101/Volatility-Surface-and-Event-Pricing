# instructions/03c_capture_wait.md: Session 3c (capture fix, urgent, before 19:25 UTC today)

This instruction names the capture job, so rule 15 allows the changes below and no others. It does not replace `03b`; if 03b work is in progress or committed locally, leave it as it is, stage only the files named here by explicit path, and finish 03b afterwards.

---

## A. What went wrong on 2026-10-28

No real snapshot exists. The `snapshots` release was never created. The reviewer read the Actions history:

| run | event | started (UTC) | New York time | duration |
|---|---|---|---|---|
| 40786854443 | schedule (cron 19:30 UTC) | 2026-10-28 23:22:05 | 19:22 | 19 s |
| 40792431105 | schedule (cron 20:30 UTC) | 2026-10-29 00:11:42 | 20:11 | 19 s |

GitHub started both scheduled runs nearly 4 hours late, after the 15:25 to 16:30 New York window, so the script correctly logged a skip. GitHub only promises best-effort timing for scheduled runs, and delays of hours happen at busy times. A cron that has to land inside a 65-minute window cannot be trusted on its own.

The local task did not upload either.

---

## B. The fix: start early, then wait

Scheduled runs start well before the window and the script sleeps until 15:30 New York. A run that starts 4 hours late still lands before the window, and Actions allows a job to run for up to 6 hours.

### Step 3c.1 (commit `step 3c.1: capture waits for 15:30 New York`)

1. `config.toml` `[snapshot]`: add `target_ny = "15:30"` and `cron_utc = ["17 15 * * 1-5", "17 17 * * 1-5", "47 18 * * 1-5"]` (replacing the old list).
2. `volsurf/snapshots.py`: add `seconds_until_target(now_utc: datetime, cfg) -> float | None`.
   - It returns `None` if the New York date is not a session, or if the New York time is after `window_end_ny`.
   - It returns 0.0 if the New York time is inside [`window_start_ny`, `window_end_ny`].
   - Otherwise it returns the seconds until `target_ny` on that New York date.
3. `volsurf/snapshots.py`: add `already_captured(existing_n_ok: int | None, min_ok: int) -> bool`, which is True when `existing_n_ok` is not None and is ≥ `min_ok`.
4. `scripts/snapshot.py`: add the flag `--wait`. When it is set and the run is not forced, the script does the following, logging each step:
   - (a) If the release already holds today's snaplog with `already_captured` True, log `skip: already captured n_ok=X` and exit 0.
   - (b) Compute `seconds_until_target`. If `None`, log the skip and exit 0. If above 0, log `waiting S seconds until 15:30 New York` and sleep.
   - (c) After waking, repeat check (a).
   - (d) Run the normal capture and upload as now (`better`).
   - Without `--wait` the script behaves exactly as today.
5. `.github/workflows/snapshot.yml`:
   - Use the 3 new crons.
   - Add `--wait` on `schedule` and on non-forced `workflow_dispatch` runs.
   - Set `timeout-minutes: 355`.
   - Add `concurrency: { group: snapshot, cancel-in-progress: false }`, so a later run queues behind a sleeping one and then exits at check (a).
6. The local task is unchanged (19:45 and 20:45 UTC, `--upload better`, no `--wait`).
7. Tests in `tests/test_snapshots.py`:
   - `seconds_until_target(2026-10-29 15:17 UTC)` is 15,180 (to 19:30 UTC, since New York is still on EDT);
   - `2026-11-02 15:17 UTC` gives 18,780 (to 20:30 UTC, EST);
   - `2026-10-29 19:40 UTC` gives 0.0;
   - `2026-10-29 20:31 UTC` gives `None`;
   - `2026-10-31 15:17 UTC` (Saturday) gives `None`;
   - `already_captured(None, 33)` is False, `(33, 33)` is True and `(20, 33)` is False.

### Step 3c.2: push and arm today's capture (no commit of its own)

1. Run the tests, then push.
2. Run `gh workflow run snapshot.yml` with no force input. This starts a non-forced run now that waits until 19:30 UTC and captures today, 2026-10-29.
3. Print `gh run list --workflow snapshot.yml -L 3`, and the first 20 log lines of the new run, showing the `waiting ... seconds` line.
4. Do not wait for the capture itself; the reviewer checks it after 19:45 UTC.

---

## C. Evidence and status

Append to `review/section_3.md` under `## Session 3c`: the test output, the diff of `snapshot.yml`, and the output of step 3c.2.

Status file: `instructions/03c_capture_wait.status.md`. Include the answers to 2 questions, read from the owner's machine:

- Is `volsurf-snapshot` registered? Give the output of `Get-ScheduledTaskInfo volsurf-snapshot` (LastRunTime, LastTaskResult, NextRunTime).
- What is in `data\local_capture\snapshot.log`? Give its last 20 lines, or say that it does not exist.
