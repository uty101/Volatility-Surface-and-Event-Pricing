# instructions/13_github_page.md: Session 13 (README front page and results page)

Read `CLAUDE.md` and instruction 11 first. This is the last session. It changes only the README template, the `readme` stage, a new `results` stage and their tests. No model, table or figure changes, so the 7 capture days already in the tables are not refitted.

---

## A. Approval of session 12

Session 12 is approved. The 5-specification family matches the reviewer to 3 decimals, and status 3 and 5 are right: the answer now names the comparison it uses and does not claim the family was fixed blind.

The owner may delete `C:\vs4` to `C:\vs12` and `C:\vs11pre`, plus `data/processed/surface_s10_backup` and `data/processed/surface_cold1`. Claude Code does not.

---

## B. The goal

The repo's front page should read like the owner's other repos, especially Constrained-Portfolio-Optimiser and CDS-Pricing-and-Bootstrapping:

- a badge line under the title;
- a short intro;
- a "What it found" section that a visitor can read in 1 minute;
- the detail per question below that;
- a repo map;
- a results page in `outputs/` that shows every figure and headline table on 1 page.

---

## C. Step 13.1 (commit `step 13.1: front page and results page`)

### 1. README order

1. The title, then the CI badge on its own line, followed by "4,747 tests" (or the generated count).
2. The intro, as now. Then 1 line, matching the optimiser: "Every table, chart and the risk report are committed in `outputs/`, and [`outputs/results.html`](outputs/results.html) shows them on 1 page, so nothing needs to be run to see the results."
3. **The capture window line,** as now.
4. **`## What it found`.** 6 bold-led paragraphs, 1 per question, as in the optimiser's README:
   - Each paragraph opens with the question in bold, for example "**Question 4: does selling S&P 500 volatility pay, and does timing it help?**".
   - Then 2 to 4 sentences: the answer and the 2 or 3 numbers that carry it, with their N.
   - All numbers come from `answers.csv` through the `readme` stage, with nothing typed.
   - No paragraph over 90 words.
   - The current per-question sections already hold the detail, so these paragraphs do not repeat their tables.
5. **The 6 question sections,** as now, with 1 change. In section 3, drop the prose sentence per event: the table directly below holds the same numbers. Keep the first sentence (the N and what it means), the pending and no-snapshot counts, and the scatter.
6. **`## Risk report`,** as now.
7. **`## Run it`.** Move it here, from the top.
8. **`## What this does not do`,** as now.
9. **`## Repo map`.** A 2-column table in the optimiser's form, covering every top-level folder and file a visitor sees: `volsurf/`, `scripts/`, `tests/`, `data/raw/`, `data/manual/`, `outputs/tables/`, `outputs/figures/`, `outputs/reports/`, `docs/`, `decisions/`, `instructions/` and `review/`, `.github/workflows/` (CI and the daily capture), `config.toml` and `project_outline/`.
10. **`## Licence`.** 1 line.

`README.md` stays under 16 KB.

### 2. `outputs/results.html`

Add a `results` stage to `run_all.py`, after `readme`, that writes 1 self-contained page:

- **Charts.** Every chart is embedded as base64 PNG.
- **Styling.** Inline CSS only, with no external requests. Use the same type and table style as the risk report.
- **Sections.** They follow the README's 6 questions plus the risk report.
- **Section content.** Each section has:
  - the "What it found" paragraph;
  - its headline table, rendered from the CSV;
  - its figures.
- **Risk report.** It shows the book table, the shock grid and the breaches.
- **Header.** The capture window and the test count go at the top.
- **Footer.** It holds a link back to the repo.

The page is deterministic: 2 builds give the same bytes.

### 3. Tests

- **README order:** the README has the sections in the order above.
- **Results page:**
  - it contains every PNG under `outputs/figures/` that the README references;
  - it has no `http` request other than the footer link;
  - 2 builds match byte for byte.
- **Existing checks:** `test_readme_tables_match_csvs` and `test_no_banned_words` still pass, with the "What it found" paragraphs included.

### 4. Run and check

- Run `python scripts/run_all.py --stage readme` and `--stage results` only. No refit and no new capture day, so the numbers stay those of session 12.
- `git status` is clean after a second run.
- Then run the fresh-clone pytest, `ruff` and CI.

---

## D. Review evidence (in `review/section_13.md`)

1. The new README top section, as rendered text: from the title to the end of "What it found".
2. The size of `README.md` and of `results.html`.
3. A PNG render of the top of `results.html`.
4. The test output, `ruff`, the fresh-clone check and CI.

Status file: `instructions/13_github_page.status.md`.
