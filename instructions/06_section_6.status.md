# Status: session 6 (`instructions/06_section_6.md`)

## Outcome

Complete. Step 6.0 is `65fc151`, step 6.0b is `2ef343e`, step 6.1 is `d3d4293` and step 6.2 is `5dae296`. The evidence is in `review/section_6.md`.

## Last step reached

Step 6.2. Then the review, this file, the fresh-clone check and CI.

## What changed

- **Step 6.0.**
  - 4 crons: 09:17, 12:17, 15:17 and 18:17 UTC.
  - `max_wait_s = 19800`.
  - `snapshot.py --wait` sleeps `max_wait_s`, repeats check (a), dispatches `gh workflow run snapshot.yml --ref main`, logs `chained: ...` and exits 0.
  - `actions: write` added to the workflow's permissions.
  - 3 new tests. 15 of 15 pass in `test_snapshots.py`.
  - The capture for 2026-11-03 was armed as run 41622958662.
- **Step 6.0b.**
  - O-38 (b) and O-39 (a) are applied.
  - The fits are not stored, so the surface stage was rerun to rewrite `svi_fits.csv` at `%.17g`. Section 4 is otherwise byte-identical.
  - Density status per day:

    | day | ok | kink | fd_gap | density_fail |
    |---|---|---|---|---|
    | 2026-10-28 | 74 | 0 | 0 | 0 |
    | 2026-10-29 | 443 | 50 | 0 | 0 |
    | 2026-10-30 | 396 | 48 | 0 | 2 |

  - No `fd_gap` rows. The largest gap over non-kink slices is 1.78e-3 × peak (JPM 2026-11-27 on 2026-10-30), against the 5e-3 bound.
  - The tail tables cover 913 slices.
  - PIT has 53 rows, 51 of them new. They come from closes to 2026-11-02. The two Session 5c values are unchanged.
- **Steps 6.1 and 6.2.**
  - 41 events over the fixture day and the snapshot days 2026-10-29 and 2026-10-30:

    | status | count |
    |---|---|
    | ok | 4 |
    | no_pre_snapshot | 6 |
    | pending | 16 |
    | unknown | 15 |

  - The 4 `ok` events are AMZN, INTC, CVX and XOM.
  - The `no_pre_snapshot` events are GOOGL, MSFT and FOMC on 2026-10-28, AAPL and PLTR on 2026-11-02, and SHOP on 2026-11-03. SHOP is BMO, so its pre-event session is the missed 2026-11-02.
  - Summary: n = 4, `below_min_n`, descriptive only. Mean log ratio −0.203; 1 of 4 above.
  - `decisions/section_5_review.md` gains `## Session 5c`. `decisions/capture.md` item 6 records the 2026-11-02 gap.

## Questions and blockers for the reviewer

1. **Kink count, 98 against your 99.** By the stated rule, s ≤ s_min × (1 + 1e-6), 98 slices are `kink`. CVX 2026-11-06 on 2026-10-30 has s = 1.0000087e-4, so it falls just outside the band. It passes the FD bound and stays `ok`. It is also the E2 slice of the CVX event.
2. **AMZN's E1 slice is a `kink` slice.** O-38 removes kink slices from tails, PIT and the density figure only, so the event table uses it.
3. **INTC.** The realised move is |log return| 0.337 (92.07 to 65.76 on 2026-10-30), with ratio 3.95. This is the close as served, not checked against a second source.
4. **Interpretations.** The full list is under Deviations in the review. The two that decide the counts:
   - The pre-event snapshot is the one on the window's start session.
   - A window starting after the last close is `pending`, not `no_pre_snapshot`.
5. **Run 41622958662**, armed in step 6.0, was still in progress when this was written. Its log and any 2026-11-03 assets are not in this section.
6. **The surface stage over 3 days takes 155 min sequentially.** Running it across processes ran out of memory on this 16 GB machine.
7. **Clones on disk:** `C:\vs6` from this session, plus the earlier ones. All are safe to delete.

## Tests

- **Local.** `.venv\Scripts\python -m pytest -p socket --disable-socket -q` on Windows at `5dae296`: `4539 passed` in 19 min 25 s. `ruff check .`: `All checks passed!`
- **Fresh clone.** At `5dae296` (Windows, `C:\vs6`): `4539 passed` in 21 min 38 s.
- **CI.** On `5dae296` (run 41661762643, Linux): success, `4539 passed` in 14 min 45 s, ruff clean.

## `git log origin/main --oneline -3` (before this commit)

```
5dae296 step 6.2: events table, summary and figures
d3d4293 step 6.1: event windows, term structure and straddle moves
2ef343e step 6.0b: kink and fd_gap density statuses, full precision parameters
```
