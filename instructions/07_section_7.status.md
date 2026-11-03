# Status: session 7 (`instructions/07_section_7.md`)

## Outcome

Complete. Step 7.0 is `4558168`, step 7.1 is `a06f8e6` and step 7.2 is `b2b50e5`. The evidence is in `review/section_7.md`.

## Last step reached

Step 7.2. Then the review, this file, the fresh-clone check and CI.

## What changed

- **Step 7.0.**
  - The pre-event snapshot is now the last snapshot day no later than the window's start session. EVENTS gains `pre_snap_age`.
  - AAPL and PLTR (2026-11-02) and SHOP (2026-11-03) take the 2026-10-30 snapshot with age 1. They move from `no_pre_snapshot` to `pending`, with both implied moves filled. Their windows end on 2026-11-03, after the last close.
  - Counts against session 6:

    | status | session 6 | session 7 |
    |---|---|---|
    | ok | 4 | 4 |
    | no_pre_snapshot | 6 | 3 |
    | pending | 16 | 19 |
    | unknown | 15 | 15 |

    No other row changed.
  - The surface cache is `data/processed/surface/{day}.parquet`, keyed by sha256, with `--force` to refit every day.
  - No new capture day: the release still holds 2026-10-29 and 2026-10-30.
  - Prices were re-pulled to 2026-11-02. Only `sectors.parquet` moved, by at most 1.34e-6 relative.
- **Step 7.1.** The COR3M regression matches the reviewer's row to 4 decimals: n 5,163, 2006-01-03 to 2026-08-04, intercept 0.2862 (NW se 0.0371), slope 0.7115 (0.0740), R² 0.4373, mean gap −0.1672. The table and the figure say beside the gap that it is the proxy, not a correlation risk premium.
- **Step 7.2.**
  - XLK implied correlation: 0.331 on 2026-10-29 (covered weight 0.720, 15 names) and 0.565 on 2026-10-30 (0.661, 13 names; MU and PANW have no `atm_30`).
  - The fixture day has no XLK vol.
  - Every row is `pending`. Every RV z-score is `below_min_days`.

## Questions and blockers for the reviewer

1. **O-40 and O-41** (table columns and statuses for Section 7) are implemented as (a). The reviewer may switch them.
2. **O-42 (the realised side of the live implied correlation) is not decided and not built.** The price files have no adjusted closes for the single names, and the realised vol definition is not fixed. Every day is `pending`, so nothing depends on it yet. `live_implied_corr` raises when the first window completes, which is the fixture day's, with the close of 2026-11-27.
3. **Status 5.** Run 41622958662 waited 19,800 s and then chained: `chained: dispatched a new run with 14372 seconds still to wait`. It uploaded nothing. Run 41674897033 was in progress at 17:32 UTC. The 2026-11-03 assets had not landed when this section ran.
4. **Surface stage runtime with the cache: not measured on the real days.** The first run with an empty cache has to fit every day, which is the 155-minute run. It was started at 17:45 UTC and the section was finished without waiting for it, on the owner's instruction. The cache tests show 0 days refitted on a second run.
5. **The cache key does not cover `[density] int_points`**, which sets the SVI acceptance grid. This follows instruction 07's key exactly. Reported only.
6. **The 2 cache tests were fixed in the wrap-up commit.** Run on their own they recursed, because the fake `surface_day` called `_tables()`. The full suite had passed them only through test order. No assertion changed.
7. **Clones on disk.** `C:\vs7` from this session, plus `C:\vs4` to `C:\vs6`, which the owner may delete.

## Tests

- **Local.** Full suite at `b2b50e5`; recorded in the review's `## Tests run`. `ruff check .`: `All checks passed!`
- **Fresh clone and CI.** Recorded in `review/section_7.md`.

## `git log origin/main --oneline -3` (before this commit)

```
193f91b Add session 7 instructions
31c8874 session 6: fix the clone path in the status file
a572de6 session 6: review, status, fresh-clone check and CI
```
