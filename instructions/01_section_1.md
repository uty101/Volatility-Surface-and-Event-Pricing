# instructions/01_section_1.md: Session 1 (Section 1 of PLAN.md)

Read `CLAUDE.md`, `PLAN.md` and `instructions/00_kickoff.md` first. This file beats all three where they differ (rule 13).

**This session runs before the first real capture.** The fixture day 2026-10-28 is captured at 19:30 UTC today. Everything in this session that needs that day's files (the fixture in step 1.2, and the real-data evidence in step 1.4) moves to `instructions/01b_section_1_fixture.md`, which runs after the capture. Do not write tests that read fixture files in this session, and do not create placeholder fixtures. Every other part of Section 1 is built now.

**Push step 1.0 before 19:15 UTC** so tonight's scheduled capture already uses the `better` upload rule. If the session is still running at 19:15 UTC, push what is committed at that point (steps already complete and tested) and carry on.

---

## A. Approval of session 0

Approved. What the reviewer checked independently, on Linux, from a fresh clone and the release assets:

- The 4 assets in `snapshots-test` match the sha256 values in `test_snaplog_2026-10-27.json`, and the chains file holds 72,238 rows for 32 tickers with no duplicate `(ticker, contract_symbol)` pairs.
- `^SPX` rows are all `SPXW`: 45 expiries were kept by the 400-day rule, 37 of them have SPXW contracts, and 5,360 AM-settled rows were dropped. The 8 lost expiries are far-dated or AM-only dates; Nov 20 and Dec 18 (third Fridays) are present.
- After the close, only 4.4% of `^SPX` rows had bid > 0 against 58% to 96% for the American chains. This confirms Correction 5: the 15:30 snapshot is required, and the forced runs are a plumbing test, not usable data.
- The CI run on `6a8de21` and the forced Actions capture both succeeded; Yahoo answers from Actions.

**Correction to status item 4.** It is not true that every upcoming earnings date carries a 15:00 placeholder. In the test asset, confirmed dates carry their real time (MSFT 2026-10-28 16:00, classified AMC), and every past date carries a real time (16:00 appears 392 times, 06:00 155 times, 07:00 56 times). The 15:00 placeholder appears only on projected dates that the company has not yet confirmed (for example TSLA 2027-01-27), 14 rows in all. That decides O-12 below.

**Local task:** registered after review (commit `1ff108e`) with `--upload if-missing` and triggers at 19:30 and 20:30 UTC. Status question 1 is decided as (a): keep the UTC triggers, since they fire at the same instants as the Actions crons and so stay at 15:30 New York through every clock change. After step 1.0 changes the script to `--upload better`, the owner re-registers the task by hand.

---

## B. Decisions on OPEN items

| Item | Decision | Reason |
|---|---|---|
| O-1 | (a) | One entry point keeps `run_all.py` the single rebuild path. |
| O-2 | (a), every proposed name | They are clear and already in PLAN.md. |
| O-3 | (a) | `^GSPC` and `^SPX` are the same index; `^GSPC` has the long daily history. |
| O-4 | (a) 2026-10-28 | The first real capture; fixed so tests never move. |
| O-5 | (b) | A day is a snapshot day if any non-test chains asset exists; each ticker is used only if its status is `ok`. One bad ticker should not cost the other 31. |
| O-6 | (a) | Details in step 1.1 below. |
| O-7 | (a) | Each tenor uses its own latest valid observation dated ≤ t − 1. |
| O-8 | (a) | Log-moneyness bins apply to calls and puts alike and need no vol. |
| O-9 | (a) | |
| O-10 | (a) | |
| O-11 | (a) | |
| O-12 | (b), with a rule | Use the row from the latest earnings asset that lists the event. If that row's time is 15:00 New York, the timing is `unknown` whatever `classify_timing` says, because 15:00 is Yahoo's placeholder for unconfirmed dates. `unknown` events need an override to enter the study. |
| O-13 | (a) | |
| O-14 | (a) | |
| O-15 | (a) | |
| O-16 | (b), restated | The T-bill return for month m+1 is the DTB3 value on the last session of month m, divided by 1200 (the rate known at the decision). The first position counts as a switch. |
| O-17 | (a) | |
| O-18 | (a), changed for Heston | T = 21 / 252 (a 21-trading-day straddle; the kickoff's "30-day" means this), step 1 / (252 × `steps_per_day`), Heston by full-truncation Euler. The straddle is sold at its model price (BSM at σ for GBM; QuantLib `AnalyticHestonEngine` once at t = 0 for Heston). The hedge delta is BSM delta at σ for GBM and at √v_t, the path's current variance, for Heston. Hedging error is as in (a). |
| O-19 | (a) | |
| O-20 | (a) | Γ × S² × 0.01 × 100 × contracts × side is the standard desk measure. |
| O-21 | (a) | |
| O-22 | (a) on items 1 to 9, plus the upload change in step 1.0 | |
| O-23 | (b) | |
| O-24 | (a) | |

Record these in `decisions/section_1_review.md` (one line each with the reason). Mark each as decided in `decisions/OPEN.md` with a pointer to that file; do not delete the items.

---

## C. Steps for Section 1

### Step 1.0: capture upload rule (commit `step 1.0: upload only when better`)

This instruction names the capture job, so rule 15 allows these changes and no others.

**The problem.** Actions uploads with `--upload always` and `--clobber`. If the backup run uploads a good day first and Actions then has a bad run (for example 10 tickers ok after Yahoo throttles it), the bad files overwrite the good ones and the loss is permanent.

**The fix.**

1. In `volsurf/snapshots.py` add `should_upload(existing_n_ok: int | None, new_n_ok: int) -> bool`. It returns True when `existing_n_ok` is None (no asset for that date) or when `new_n_ok > existing_n_ok`, and False otherwise. A tie keeps the files already in the release.
2. In `scripts/snapshot.py` add the upload mode `better`. It reads the release's `snaplog_<day>.json` (or `test_snaplog_<day>.json` when forced) with `gh release download <tag> --pattern <name> --dir <tmp> --clobber`. A missing asset means `existing_n_ok = None`. It uploads all 4 files with `--clobber` only when `should_upload` is True; otherwise it logs `skipped: existing n_ok=X >= new n_ok=Y`. A failed download of an asset that does exist is an upload failure (exit code 2, files kept). Keep the modes `always`, `if-missing` and `never` unchanged.
3. `.github/workflows/snapshot.yml`: `--upload always` becomes `--upload better`.
4. `scripts/windows/register_snapshot_task.ps1`: `--upload if-missing` becomes `--upload better`. Do not run it; the owner re-registers.
5. Tests in `tests/test_snapshots.py`: `should_upload(None, 0)` True; `(30, 31)` True; `(31, 31)` False; `(32, 10)` False.

The push triggers a forced Actions run to `snapshots-test`. It uploads if `snapshots-test` has no snaplog for that New York date, or one with fewer tickers ok; otherwise it logs a skip. Either outcome passes. Print the run's last 3 log lines in the review.

### Step 1.1: long history pull (PLAN 1.1)

`scripts/pull_data.py --stage cboe|fred|prices|ssga`, plus `--stage all`.

- **cboe.** The 4 VIX family CSVs as served (header `DATE,OPEN,HIGH,LOW,CLOSE`, dates `MM/DD/YYYY`), saved to `data/raw/cboe/{name}.csv` unchanged. The 3 JSON series reduced to `date,close` with ISO dates, sorted, saved to `data/raw/cboe/{PUT,BXM,COR3M}.csv`. Endpoints answer with a 302 from `cdn.cboe.com` to `cdn-api.cboe.com`; call `cdn-api.cboe.com` directly.
- **fred.** `fredgraph.csv?id=<id>` for DGS1MO, DGS3MO, DGS6MO, DGS1 and DTB3, saved as served. Missing values arrive as `.` (or blank); keep them in the raw file and treat them as missing in code (O-7).
- **prices.** For each of the 31 captured tickers other than `^SPX`: `yf.Ticker(t).history(start="1989-12-01", end=<pull date + 1 day>, auto_adjust=False, actions=True)`. `close.parquet`: wide, index `date` (date only, no time zone), 1 column per ticker, unadjusted Close. `dividends.csv`: `date,ticker,dividend` for every nonzero dividend. `index.parquet`: columns `^GSPC` and `^SP500TR`, Close, same call. `sectors.parquet`: the 9 sector SPDRs, Adj Close.
- **ssga.** Download the XLK workbook to `data/raw/ssga/xlk_holdings_<pull date>.xlsx`. Parse the first sheet: the header row is the first row whose first cell is `Name`. Keep `Name`, `Ticker`, `Weight`, `Shares Held`. Weight is in percent; store it as a decimal. Drop rows with a blank ticker or the ticker `-` (cash and footer lines). Write `data/raw/ssga/xlk_holdings_<pull date>.csv` with columns `ticker,name,weight,shares,as_of_date`. `as_of_date` comes from the workbook's `Holdings:` line (as `As of <date>`). Gate: the kept weights sum to between 0.97 and 1.01; otherwise stop under rule 4 and print the workbook's first 10 rows.
- `MANIFEST.json` per kickoff Section 3.2.
- Tests (`tests/test_pull_data.py`, all offline against committed files): manifest hashes match; VIX first date 1990-01-02, PUT 1991-03-04, COR3M 2006-01-03; every captured ticker except `^SPX` is a column of `close.parquet`; XLK weights sum check; each of the 10 XLK names in `[universe] xlk_holdings` is in the holdings CSV.

### Step 1.2: snapshot download and fixture (PLAN 1.2)

Build `scripts/pull_snapshots.py` as in PLAN.md and run it. The `snapshots` release may not exist yet or may hold no assets; the script must handle both (write the manifest with a header only, exit 0, print a one-line message). Test it with a fake `gh` runner: 0 assets, 2 assets of which 1 is already present with a matching sha256 (skipped), and 1 present with a wrong sha256 (downloaded again).

The fixture itself is **not** built in this session. For the record, instruction 01b will ask for: fixture day 2026-10-28 (O-4); `tests/fixtures/chains_sample.parquet` (rows for `^SPX`, SPY and AAPL), `tests/fixtures/underlying_sample.csv` and `tests/fixtures/earnings_sample.csv`; a test that the fixture's `^SPX` rows all start with `SPXW`; and a test that more than 50% of fixture `^SPX` rows have bid > 0, which is the check that the 15:30 timing works.

### Step 1.3: loader and cleaning (PLAN 1.3)

As in PLAN.md, with:

- Rule e for `^SPX` is skipped in Section 1 and logged as `rows_dropped = 0` with the note `deferred to section 3` (O-23). For American underlyings rule e uses the American bounds of Section 5.3 with S from UNDERLYING.
- Rate test hand values: y = 4.00 gives r = 0.03960525459235946; y = 3.87 gives r = 0.03833033852202173, both to 1e-15.
- Session test: `sessions_between(2026-11-25, 2026-11-30) == 2` (2026-11-26 is closed; 2026-11-27 is an early close but a session) and `sessions_between(2026-12-24, 2026-12-28) == 1`.
- The `t − 1` rule test builds a synthetic FRED frame where day t has a value and day t − 1 is `.`; the rate for day t must come from day t − 2.
- `load_snapshot` raises a clear error naming the missing asset when a day has no chains file.

### Step 1.4: capture health (PLAN 1.4)

Build the capture health builder as in PLAN.md, with 2 extra columns: `ny_start` and `minutes_after_1530` (start time minus 15:30 New York, in minutes). Test it on synthetic SNAPLOG dicts: 1 normal day, 1 day with 2 tickers in error, and 1 session with no asset (a gap). Run it on whatever `data/snapshots/` holds now; an empty table with headers only is the expected result today. The real table and the fixture-day CLEAN_LOG come in instruction 01b.

---

## D. Review evidence (in `review/section_1.md`)

1. Step 1.0: the 4 new tests passing and the last 3 lines of the forced Actions run log after the push.
2. The `MANIFEST.json` contents, plus first and last 3 rows of every committed raw file.
3. The parsed XLK holdings CSV in full and its weight sum.
4. `data/raw/snapshot_manifest.csv` in full (header only is expected).
5. The synthetic capture health test output.
6. For each cleaning rule a to e, the synthetic input rows and which were dropped.
7. The fresh-clone check (rule 12), CI status of the final commit, and the time (UTC) step 1.0 reached `origin/main`.

Status file: `instructions/01_section_1.status.md`.
