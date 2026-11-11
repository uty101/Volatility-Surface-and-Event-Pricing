# Review: Section 13

## Section

Section 13: README front page and results page (`instructions/13_github_page.md`, step 13.1). It is not a `PLAN.md` section; instruction 13 adds it as the last session. No model, table or figure changed, so the numbers are session 12's: 7 capture days, 2026-10-28 to 2026-11-06.

Step 13.1 is complete. Fresh clone and CI: `4759 passed`.

3 things the reviewer should know first:

- **3 earlier tests were changed to the new layout.** Instruction 13 moves or replaces what they pinned. `test_readme_under_15_kb` became `test_readme_under_16_kb`, the instruction's 16 KB. `test_status_line_under_the_intro` became `test_readme_order`, because the "Results are in" line no longer exists. In `test_stages_run_in_section_order`, `stages[-2:] == ["answers", "readme"]` became `stages[-3:] == ["answers", "readme", "results"]`. See Deviations.
- **The README is 16,262 bytes against a limit of 16,384.** Instruction 11's sections are kept as they were, so the room came from keeping the 6 paragraphs and the repo map short. A refresh that lengthens any answer can cross the limit, and `test_readme_under_16_kb` will catch it.
- **GitHub shows `outputs/results.html` as source, not as a page.** The README link opens the HTML text on github.com. It renders when downloaded or opened from a clone. See Open questions.

## Steps completed

- 13.1  304954e  step 13.1: front page and results page
- The wrap-up commit holds this file, `review/section_13/results_top.png` and the status file.

## Evidence

### E1. The README top, as rendered text

From the title to the end of "What it found", as committed at `304954e`:

```markdown
# Volatility Surface and Event Pricing

[![ci](https://github.com/uty101/Volatility-Surface-and-Event-Pricing/actions/workflows/ci.yml/badge.svg)](https://github.com/uty101/Volatility-Surface-and-Event-Pricing/actions/workflows/ci.yml) 4,759 tests

Prices listed options and their Greeks, solves implied volatility, and fits an arbitrage-free SVI and SSVI surface per underlying.
Reads the risk-neutral distribution off the surface and measures the move options price around earnings and macro events.
Tests the volatility risk premium on S&P 500 history from 1990 and implied against realised correlation from Cboe COR3M.
Splits delta-hedged option P&L into Greeks and builds a 1-page daily risk report.
Option chains are captured daily from 2026-10-28, so every live result is a method demonstration with its N stated.

Every table, chart and the risk report are committed in [`outputs/`](outputs/), and [`outputs/results.html`](outputs/results.html) shows them on 1 page, so nothing needs to be run to see the results.

**Capture window:** 2026-10-28 to 2026-11-06, 7 days, 2026-11-02 missed. The first day holds `^SPX`, SPY and AAPL only, from an in-session test capture. The others hold all 37 underlyings.

## What it found

**Question 1: does the pricer match QuantLib?** Yes: over 252 grid cases each, the largest gap is 3.9e-14 for BSM prices, 4.4e-13 for the Greeks and 6.8e-05 x S for the American CRR tree.

**Question 2: how did the S&P 500 surface move, and is it free of arbitrage?** Over 7 capture days, ^SPX 30-day ATM vol went from 13.44% to 18.08% and the 25-delta risk reversal from −4.16 to −7.14 vol points, so skew steepened. All 3006 accepted SVI slices pass the butterfly arbitrage check.

**Question 3: do event moves differ from what the options priced?** With N = 11 completed events, fewer than the 20 the summary needs, the gap cannot be told apart from 0. 9 of the 11 moved less than the options priced.

**Question 4: does selling S&P 500 volatility pay, and does timing it help?** Selling puts paid: Cboe PUT has a Sharpe of 0.56 over 237 months from 2007. Timing it on implied minus GARCH variance gives 0.80, but after the 5 rules tried its gain over PUT has a deflated Sharpe of 0.412, so it cannot be told apart from luck.

**Question 5: does implied correlation predict realised correlation?** Yes, in part. Regressing next quarter's realised sector correlation on COR3M gives a slope of 0.713 and an R² of 0.439 (N = 5167 days).

**Question 6: how does hedged P&L split, and what does hedging frequency change?** The Greeks explain a median 0.931 of each live ^SPX straddle move (N = 21 moves). Hedging every step leaves an error sd of 0.241 under GBM but 0.813 under Heston, because the delta hedge is blind to vol moves.
```

### E2. Every number in "What it found" comes from `answers.csv`

`volsurf/readme.py` holds 1 `Finding` per question: regexes whose named groups are read from that question's answer text in `answers.csv`, and a sentence they fill. A pattern that does not match raises. Question 3's "9 of the 11" counts the per-event rows whose `value`, the ratio, is below 1. `test_what_it_found_from_answers` holds the README to a fresh build. The rows each paragraph reads, printed with `to_string()`:

```
Question 1
                                                                                                                                           answer      source_table                                                                                    source_row
0                    Yes. BSM matches QuantLib's analytic engine: the largest price gap is 3.9e-14 over 252 grid cases, against a bound of 1e-10.  pricer_check.csv                                                                         check=bsm_vs_quantlib
2  The American CRR tree at 2000 steps matches QuantLib's CRR engine: the largest gap is 6.8e-05 x S over 252 cases, against a bound of 1e-4 x S.  pricer_check.csv                                                       check=crr_american_vs_quantlib_rel_spot
3                      Delta, gamma, vega, theta and rho match QuantLib: the largest gap is 4.4e-13 over 252 cases each, against a bound of 1e-8.  pricer_check.csv  check=delta_vs_quantlib|gamma_vs_quantlib|vega_vs_quantlib|theta_vs_quantlib|rho_vs_quantlib

Question 2
                                                                                                                                                answer       source_table                  source_row
9                                                                                   ^SPX 30-day ATM vol was 13.44% on 2026-10-28 (N = 7 capture days).  surface_daily.csv  ticker=^SPX;day=2026-10-28
10                                                                          It was 18.08% on 2026-11-06, after sell-offs on 2026-10-30 and 2026-11-05.  surface_daily.csv  ticker=^SPX;day=2026-11-06
11                                              The 30-day 25-delta risk reversal went from -4.16 to -7.14 vol points, so skew steepened (N = 7 days).  surface_daily.csv  ticker=^SPX;day=2026-11-06
13  Butterfly: 3006 of 3275 SVI slices across every underlying and day are accepted; the rest are rejected or have too few quotes to fit (N = 7 days).       svi_fits.csv          status=ok|ok_refit

Question 3
                                                                                                                                                  answer       source_table source_row
18  With N = 11 completed events, fewer than the 20 the summary needs, the gap between implied and realised moves cannot be told apart from 0 at this N.  event_summary.csv  scope=all

Question 4
                                                                                                                                                                                                                                                                                                                   answer        source_table                                     source_row
36  Selling puts paid, but less per unit of risk than holding the index: Cboe PUT has a Sharpe of 0.56 over 237 months from 2007, against 0.65 for the S&P 500 total return index and 0.44 for BXM. The index carries no trading costs of its own, so the only cost deducted here is the timed strategy's switching cost.  strategy_stats.csv                                   strategy=put
39                                                                                                                                                                                                           Timing on implied minus GARCH variance gives a raw Sharpe of 0.80 over 237 months, after the switching cost.  strategy_stats.csv                             strategy=timed_put
43                                                                                                                                                                After counting the 5 rules tried, its deflated Sharpe is 0.412 (N = 5 trials, 237 months), so its gain over holding PUT cannot be told apart from luck.     spec_family.csv  series=timed_minus_put;spec_id=timed_put_main

Question 5
                                                                                                                                              answer     source_table source_row
46  Yes, in part. Regressing the next 63 sessions' realised sector correlation on COR3M gives a slope of 0.713 (Newey-West se 0.074), N = 5167 days.  cor3m_study.csv        all
47                      R² is 0.439, so COR3M accounts for a bit under half of the variation in next quarter's realised correlation (N = 5167 days).  cor3m_study.csv        all

Question 6
                                                                                                                                                                                                                                                                                                   answer           source_table                        source_row
51                                                                                                                                                                           On the live delta-hedged ^SPX straddles the median explained share is 0.931 (N = 21 position moves, a method demonstration).   attribution_live.csv                               all
58                                                                                                                                                                                                                                      Hedging every step (k = 1) leaves an error sd of 0.241 under GBM.  hedging_frequency.csv     model=gbm;hedge_every_steps=1
59  The same hedge leaves 0.813 under Heston: the hedge uses delta at the current vol but is blind to vol moves, so even continuous hedging leaves an unhedged vega P&L, and the error sd stops falling in proportion to the square root of k. The means are not comparable, because the 2 drifts differ.  hedging_frequency.csv  model=heston;hedge_every_steps=1

Question 3: the per-event rows; 'below' counts value < 1
                           source_row         value
19  ticker=AMZN;event_date=2026-10-29  0.1707179698
20  ticker=INTC;event_date=2026-10-29   3.952399543
21   ticker=CVX;event_date=2026-10-30  0.7424916157
22   ticker=XOM;event_date=2026-10-30  0.8899036809
23  ticker=AAPL;event_date=2026-11-02  0.4751587733
24  ticker=PLTR;event_date=2026-11-02  0.1411831659
25   ticker=AMD;event_date=2026-11-03  0.1292463435
26  ticker=SHOP;event_date=2026-11-03  0.7320733668
27  ticker=UBER;event_date=2026-11-04  0.6944380822
28  ticker=ABNB;event_date=2026-11-05    1.10450152
29  ticker=^SPX;event_date=2026-11-06  0.1762124713
below: 9
```

### E3. Sizes

```
README.md                16,262 bytes  (limit 16 KB = 16,384)
outputs/results.html  3,464,694 bytes
```

The page embeds all 17 PNGs under `outputs/figures/`, 2.6 MB of PNG and about 3.5 MB once base64 encoded: the 8 README figures and the other 9, which are the 6 earlier daily smiles, the SVI fits on 2026-10-28, the SSVI surface and the event term structures.

### E4. A PNG render of the top of `results.html`

`review/section_13/results_top.png`, rendered by headless Edge at 1100 x 1500. It shows the header with the capture window and test count, section 1 with the pricer table, and section 2 with the surface table and the first chart.

### E5. Second run

`python scripts/run_all.py --stage readme` then `--stage results`, twice. The sha256 of `README.md` and `outputs/results.html` after the second run equal those after the first:

```
IDENTICAL
```

`git status --short` after it, before the commit, listed only the files of step 13.1. After the commit it listed only `review/section_13/`.

## Tests run

```
.venv/Scripts/python.exe -m pytest -p socket --disable-socket -q
.venv/Scripts/python.exe -m ruff check .
```

The tail, at the working tree before the Question 2 wording fix below:

```
tests/test_snapshots.py::test_wait_chains_when_above_max_wait
  C:\Utkarsh\10. Quant Projects\7) Volatility Surface and Event Pricing\Volatility-Surface-and-Event-Pricing\.venv\Lib\site-packages\pytest_socket\__init__.py:138: UserWarning: A test tried to use socket.socket.
    raise SocketBlockedError()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
4759 passed, 35 warnings in 2035.23s (0:33:55)
All checks passed!
```

After the fix (Question 2 now says the accepted slices "pass the butterfly arbitrage check", which is what the answer's tolerance supports), the README and page were rebuilt and `tests/test_readme.py`, `tests/test_results.py` and `tests/test_run_all.py` rerun: `44 passed`. `ruff check .`: `All checks passed!`. The fresh clone and CI below ran the full suite on the committed state.

CI, run 43054849296 at `304954e`: success.

```
test	Ruff	2026-11-11T16:05:52.7695227Z All checks passed!
test	Pytest	2026-11-11T16:13:52.1825715Z 4759 passed, 35 warnings in 477.22s (0:07:57)
```

## Fresh-clone check

```
git clone https://github.com/uty101/Volatility-Surface-and-Event-Pricing C:\vs13    # 304954e
cd C:\vs13
uv venv --python 3.12
uv pip install -r requirements-lock.txt
uv pip install -e . --no-deps
.venv/Scripts/python -m pytest -p socket --disable-socket -q
```

```
........................................................................ [  1%]
........................................................................ [  3%]
........................................................................ [  4%]
........................................................................ [  6%]
........................................................................ [  7%]
........................................................................ [  9%]
........................................................................ [ 10%]
........................................................................ [ 12%]
........................................................................ [ 13%]
........................................................................ [ 15%]
........................................................................ [ 16%]
........................................................................ [ 18%]
........................................................................ [ 19%]
........................................................................ [ 21%]
........................................................................ [ 22%]
........................................................................ [ 24%]
........................................................................ [ 25%]
........................................................................ [ 27%]
........................................................................ [ 28%]
........................................................................ [ 30%]
........................................................................ [ 31%]
........................................................................ [ 33%]
........................................................................ [ 34%]
........................................................................ [ 36%]
........................................................................ [ 37%]
........................................................................ [ 39%]
........................................................................ [ 40%]
........................................................................ [ 42%]
........................................................................ [ 43%]
........................................................................ [ 45%]
........................................................................ [ 46%]
........................................................................ [ 48%]
........................................................................ [ 49%]
........................................................................ [ 51%]
........................................................................ [ 52%]
........................................................................ [ 54%]
........................................................................ [ 55%]
........................................................................ [ 57%]
........................................................................ [ 59%]
........................................................................ [ 60%]
........................................................................ [ 62%]
........................................................................ [ 63%]
........................................................................ [ 65%]
........................................................................ [ 66%]
........................................................................ [ 68%]
........................................................................ [ 69%]
........................................................................ [ 71%]
........................................................................ [ 72%]
........................................................................ [ 74%]
........................................................................ [ 75%]
........................................................................ [ 77%]
........................................................................ [ 78%]
........................................................................ [ 80%]
........................................................................ [ 81%]
........................................................................ [ 83%]
........................................................................ [ 84%]
........................................................................ [ 86%]
........................................................................ [ 87%]
........................................................................ [ 89%]
........................................................................ [ 90%]
........................................................................ [ 92%]
........................................................................ [ 93%]
........................................................................ [ 95%]
........................................................................ [ 96%]
........................................................................ [ 98%]
........................................................................ [ 99%]
.......                                                                  [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:894
  C:\vs13\.venv\Lib\site-packages\_pytest\config\__init__.py:894: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

tests/test_capture_health.py: 4 warnings
tests/test_correlation.py: 4 warnings
tests/test_vrp.py: 24 warnings
  C:\vs13\.venv\Lib\site-packages\pandas\core\series.py:848: Pandas4Warning: Series.values returning an ndarray that drops timezone information for DatetimeTZDtype is deprecated. In a future version, this will return the underlying DatetimeArray instead. Use 'Series.dt.tz_convert(None).to_numpy()' to get a NumPy array of UTC values, or 'Series.array' to get the ExtensionArray.
  See https://pandas.pydata.org/docs/dev/whatsnew/v3.1.0.html#whatsnew-310-deprecations-values for more details.
    warnings.warn(

tests/test_correlation.py::test_rv_screen_blank_below_min_days
  C:\vs13\volsurf\correlation.py:205: RuntimeWarning: invalid value encountered in scalar divide
    z = (r.atm_30 - prior.mean()) / prior.std(ddof=1)  # O-15 (a): ddof 1, today excluded

tests/test_snapshots.py::test_wait_chains_when_above_max_wait
  C:\vs13\.venv\Lib\site-packages\pytest_socket\__init__.py:138: UserWarning: A test tried to use socket.socket.
    raise SocketBlockedError()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
4759 passed, 35 warnings in 2033.37s (0:33:53)
```

## Runtime per step

- `--stage readme`: 12.1 s, most of it `pytest --collect-only` for the test count.
- `--stage results`: 8.1 s, most of it the same collection.
- Full suite: 2,035 s locally and 2,033 s in the fresh clone, against 842 s locally in session 12. The machine was busy with other work.

## Deviations from PLAN.md

- **Changed tests,** in `tests/test_readme.py` and `tests/test_run_all.py`:
  - `test_readme_under_15_kb` to `test_readme_under_16_kb`: the bound is instruction 13's 16 KB.
  - `test_status_line_under_the_intro` removed. `test_readme_order` replaces it and checks more: the badge line with the count under the title, then the intro, the outputs line, the capture window and the 12 `##` sections in order.
  - `test_stages_run_in_section_order`: the last 3 stages are `answers`, `readme` and `results`.
- **New tests.** In `tests/test_readme.py`: `test_what_it_found`, `test_what_it_found_from_answers`, `test_section_3_without_per_event_prose` and `test_repo_map`. In `tests/test_results.py`: every README figure embedded, every chart embedded, no request but the footer link, 2 builds byte for byte, the committed page equal to a build, sections in README order, the header, and the risk section's 3 tables.
- **The results tests read the committed `outputs/`,** as the README tests do under PLAN 11.3. Instruction 13's checks are about those files.
- **Each paragraph carries 2 or 3 numbers,** so some detail stays only in the sections below. Question 1 leaves out the early exercise premium.
- **Badge line.** The CI badge is followed by "4,759 tests" with no full stop, on its own line under the title.
- **Tables on the page use the README's column specs.** The pricer table, which the README does not have, adds an `exp` option to `Column` for e notation. The shock grid uses the risk report's colours and labels.
- **The repo map lists the paths the instruction names.** `PLAN.md`, `CLAUDE.md`, `WORKFLOW.md` and `LICENSE` have no row, to stay under 16 KB.

## Not verified

- The page was rendered in Edge only.
- Its layout below 1100 px was not checked by render. It sets the viewport, and tables sit in horizontal scrollers.

## Open questions

None added to `decisions/OPEN.md`. 1 for the reviewer, in the status file: how a visitor on github.com should reach the rendered page.

## Files changed

- `docs/README.template.md`
- `README.md`
- `volsurf/readme.py`
- `volsurf/results.py` (new)
- `scripts/run_all.py`
- `outputs/results.html` (new)
- `tests/test_readme.py`, `tests/test_run_all.py`, `tests/test_results.py` (new)
- `review/section_13.md`, `review/section_13/results_top.png`, `instructions/13_github_page.status.md`

## Reviewer reads

1. E1 here, or `README.md` down to "## 1.".
2. `review/section_13/results_top.png`, then `outputs/results.html` from a clone.
3. `volsurf/readme.py` (`FINDINGS` and `findings`) and `volsurf/results.py`.
4. Deviations, for the 3 changed tests.
