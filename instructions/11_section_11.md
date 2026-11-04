# instructions/11_section_11.md: Session 11 (risk vols from the slices, then Section 11: write-up and reproducibility)

Read `CLAUDE.md`, `PLAN.md` and every earlier instruction file first. This file beats them where they differ (rule 13). Build step 11.0, then every step of Section 11, in one session. This is the last section.

---

## A. Approval of Section 10

Section 10 is approved, with the vol change in step 11.0. The reviewer read it from a fresh clone at `7118cf5`, including the page render.

- **Dollar gamma.** The `^SPX` figure checks by hand. A 30-day 25-delta `^SPX` option has Γ of about 0.0008. Then Γ × S² × 0.01 × 100 × 10 contracts comes to roughly 0.46m per leg, and the 2 legs give about 0.9m. The table's −1,008,798 is the sum of −381,876 and −626,921.
- **The breach.** The book's config produces it. The book is short 20 `^SPX` wings against a 250,000 limit. Keep the book as it is. The breach is a result the report is meant to show.

| Item | Decision |
|---|---|
| O-47 | (a). |
| O-48 | (a). |
| O-49 | (a). Record the signature change in `decisions/section_10_review.md`. |
| Status 4 (small-shock MEASURE) | Bound the `^SPX` positions at 0.5% of delta × dS. Keep the tree positions as report-only, with the piecewise-linear reason written in the test. |
| Status 5 (SSVI misprices the wings) | **Changed.** Section 4 already moved the daily metrics from SSVI to the accepted per-expiry SVI slices, for this reason. The risk book does the same. Each contract's vol is its own expiry's accepted SVI slice at its strike. SSVI is the fallback only when that expiry has no accepted slice, with a `vol_source` column (`svi` or `ssvi`). See step 11.0. |
| Status 6 | Accepted. |
| Status 7 | The owner may delete `C:\vs4` to `C:\vs10`. Claude Code does not. |

---

## B. Steps

### Step 11.0 (commit `step 11.0: risk vols from the expiry's SVI slice`)

1. Apply status 5 to `volsurf/risk.py`, with the O-21 selection and the sticky-strike shocks running on the slice vol.
2. Set the small-shock bound from status 4.
3. Rerun steps 10.1 and 10.2 for the last day.
4. Print each position's vol against its quote mid IV, and the new grid corners against session 10's.

### Steps 11.1 to 11.4

As in PLAN Section 11 and kickoff Section 8 item 11.

**11.1 Run all.**
- `scripts/run_all.py` covers every stage, with the surface cache in place.
- The days are every capture day in the `snapshots` release when it runs. Print the day count.
- 2 runs leave `git status` clean. Report both runtimes: cold (empty cache) and warm.

**11.2 Answers.** `answers.csv` answers the 6 questions of kickoff Section 1, each row tied to a source table and row. The answers state what the numbers show, with the N beside every live result. These framings are fixed:
- **Question 3.** With fewer than `[events] min_n` completed events, the answer is that the gap cannot be told apart from 0 at this N. Give the events that exist, each with its ratio.
- **Question 4.** Give the raw Sharpe and the deflated Sharpe side by side, with the number of specifications tried.
- **Question 5.** Answer with the slope and R². The mean gap appears only with the proxy sentence from instruction 07.
- **Question 6.** Use the step 10.0 explained shares, and the GBM against Heston error sd at k = 1.

**11.3 README and methods.** As in PLAN 11.3, with these additions:
- **Layout.** The README is under 15 KB. Longer material goes to `docs/`.
- **Status line.** Under the intro, add 1 line pointing to `outputs/`, plus the CI badge and the test count.
- **Capture window.** State it as "2026-10-28 to {last day}, {N} days, 2026-11-02 missed", written from the data at build time.
- **Dashes.** No em or en dashes anywhere in the README, `docs/METHODS.md` or the report. Ranges read "2006 to 2026". Hyphens appear only inside compound words.
- **The limits section ("what this does not do") must say:**
  - the live window is a few weeks;
  - option prices are Yahoo's delayed quotes at 15:30 New York;
  - the COR3M comparison is a sector proxy;
  - the timed PUT result is 1 specification of a family;
  - the risk book is a sample.

**11.4 Tidy and final check.**
- Add an MIT `LICENSE` with the holder Utkarsh Malhotra.
- Rename `Project Outline/` to `project_outline/` and update every reference to it.
- Delete unused files. `instructions/`, `review/`, `decisions/` and `PLAN.md` stay as the historical record.
- Run `ruff check .`, then the full fresh-clone pytest under rule 12, then CI.
- The capture workflow keeps running after this session. Do not touch it.

---

## C. Review evidence (in `review/section_11.md`)

1. **Step 11.0:**
   - each position's vol against its mid IV;
   - the grid corners, old against new;
   - the bound test output.
2. **Step 11.1:** `git status` after 2 runs, and both runtimes.
3. **Step 11.2:** `answers.csv` in full.
4. **Step 11.3:** the README diff, and the output of `test_readme_tables_match_csvs` and `test_no_banned_words`.
5. **Step 11.4:**
   - the full fresh-clone pytest output;
   - the `ruff` output;
   - CI status;
   - the list of deleted files.

Status file: `instructions/11_section_11.status.md`.
