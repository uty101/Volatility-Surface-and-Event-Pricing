# Status: session 11 (`instructions/11_section_11.md`)

## Outcome

Complete. This was the last section. The evidence is in `review/section_11.md`.

## Last step reached

Step 11.4, then the fix `6de2e14` to step 11.1, the 2 full runs, the fresh-clone check, CI, the review and this file.

## What changed

- **Part A.** `decisions/section_10_review.md` records the Section 10 decisions. O-47, O-48 and O-49 are marked decided.
- **Step 11.0** (`153c1e0`). Each contract's vol is its own expiry's accepted SVI slice. `risk_book.csv` has a `vol_source` column, and all 4 positions read `svi`.

  | position | contract | vol | gap to mid IV | session 10 gap |
  |---|---|---|---|---|
  | short 10 | `^SPX` 2026-12-03 P 7300 | 19.76% | −0.33 | +1.24 (P 7275) |
  | short 10 | `^SPX` 2026-12-03 C 7800 | 14.25% | +0.35 | −0.49 (C 7780) |
  | long 20 | AAPL 2027-01-15 C 335 | 24.56% | +0.03 | +0.01 |
  | short 15 | NVDA 2026-12-18 P 193 | 46.31% | −1.05 | +0.19 |

  - Grid: the worst cell is −447,394 at spot −10%, vol +5 points, against −430,446. The largest gain is 57,679 against 58,660.
  - **1 of 9 limits is still breached:** `^SPX` dollar gamma, −1,003,799 against 250,000.
  - **Small-shock bound:** `^SPX` 0.113% and 0.156% against 0.5%. AAPL 3.16% and NVDA 8.05%, report-only.
- **Step 11.1** (`c37e01b`, `6de2e14`). `scripts/run_all.py` covers 20 stages. Cold 15,587.6 s, warm 3,385.2 s, both exit 0, and `git status` clean after each. 4 capture days.
- **Step 11.2** (`9adb654`). `outputs/tables/answers.csv`, 51 rows.
- **Step 11.3** (`79f5c7f`). `README.md` is 12,957 bytes, generated from `docs/README.template.md`. `docs/METHODS.md` is new.
- **Step 11.4** (`813a2ac`). MIT `LICENSE`, `project_outline/`, 5 `.gitkeep` files deleted.

## Questions and blockers for the reviewer

No blockers.

1. **The first cold run failed.** It stopped at `answers` with exit 1 after 9,644 s, because U+2212 cannot be printed to a piped Windows stdout. My code caused it. `6de2e14` fixes it with a test that fails without the fix, and the cold run was repeated in full from an empty cache. The step 11.1 figures come from the repeat.
2. **NVDA's slice vol is further from its quote than SSVI's was:** −1.05 against +0.19 vol points. `^SPX` improved, as instruction 11 intended. The source is fixed by the instruction, so nothing was changed. The reviewer may want to look at this slice.
3. **O-50 to O-55** are implemented as (a) so that the steps could be built; the reviewer may switch any of them.
4. **The deflated Sharpe in question 4 is blank,** status `too_few_trials`: 1 specification was tried and the deflation needs at least 2. The answer says so beside the raw 0.80.
5. **Prices were not refreshed.** They end on 2026-11-02 and instruction 11 does not name a refresh, so 38 events stay pending and question 3 has N = 4.
6. **2026-11-04 is not in the tables.** `chains_2026-11-04.parquet` reached the release after both runs. Rerunning `scripts/run_all.py` picks it up.
7. **Runtimes are measured times on a shared machine.** The surface stage took 13,807 s in the repeat against 5,702 s in the failed run, and I did not establish why.
8. **Tests that read `outputs/tables/`** are the subject of O-54: rule 7 against PLAN 11.2 and 11.3.
9. **Kept, not deleted:** `tests/test_placeholder.py`, `review/.gitkeep`, `docs/CONVENTIONS_RESOLVED.md`. The old folder name remains only in `instructions/00_kickoff.md` and `instructions/11_section_11.md`, which are not edited.
10. **Left on disk, for the owner to delete if wanted:** the clones `C:\vs4` to `C:\vs11` and `C:\vs11pre`, and the ignored folders `data/processed/surface_s10_backup` and `data/processed/surface_cold1`.

## Tests

- **Pre-push suite** (`C:\vs11pre`, `813a2ac`): `4728 passed, 35 warnings in 3967.93s`.
- `ruff check .`: `All checks passed!`
- **Fresh clone** (`C:\vs11`, `6de2e14`): `4729 passed, 35 warnings in 2963.43s`.
- **CI** (run 42068655262, `6de2e14`): success, `4729 passed`.

## `git log origin/main --oneline -3` (before this commit)

```
6de2e14 step 11.1: run_all prints on a piped Windows stdout
813a2ac step 11.4: licence, outline folder renamed, unused files removed
79f5c7f step 11.3: README and methods
```
