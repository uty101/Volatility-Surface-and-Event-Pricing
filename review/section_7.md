# Review: Section 7

## Section

Section 7: Correlation and relative value (`PLAN.md` steps 7.1 and 7.2), with instruction 07. That instruction adds step 7.0: the Section 6 pre-event snapshot correction, a per-day surface cache, and the new capture days.

The section is complete. The COR3M regression matches the reviewer's row to 3 decimals on every value. The live side has 2 days with an XLK vol (2026-10-29 and 2026-10-30), and every live row is `pending`, as instruction 07 expects. No new capture day had landed when the section ran (E3).

## Steps completed

- 7.0  4558168  step 7.0: last pre-event snapshot, surface cache, new capture days. It also commits `decisions/section_6_review.md` and the prices re-pulled to 2026-11-02.
- 7.1  a06f8e6  step 7.1: COR3M study against forward realised sector correlation. It adds O-40 to `decisions/OPEN.md`.
- 7.2  b2b50e5  step 7.2: live XLK implied correlation and RV screens. It adds O-41 and O-42.
- The wrap-up commit holds this file, the status file, and a fix to the 2 cache tests. Run alone, the fake `surface_day` called `_tables()`, which recursed into the patched function; the tests had passed only because an earlier test in the file had already filled `_tables()`. The fix fits the frames before patching. No assertion changed.

## Evidence

### E1. Step 7.0: tests

`.venv\Scripts\python -m pytest -p socket --disable-socket -v -s` on the 7.0 and Section 7 tests, after the fix above, 11 tests:

```
tests/test_events.py::test_last_snapshot_before_start_session PASSED
tests/test_events.py::test_events_schema PASSED
tests/test_events.py::test_missing_pre_snapshot_excluded_and_counted PASSED
tests/test_surface_run.py::test_cache_second_run_refits_nothing PASSED
tests/test_surface_run.py::test_cache_svi_edit_refits_all_days PASSED
tests/test_correlation.py::test_avg_pairwise_corr_known PASSED
tests/test_correlation.py::test_newey_west_matches_statsmodels PASSED
tests/test_correlation.py::test_cor3m_study_windows_and_columns PASSED
tests/test_correlation.py::test_implied_correlation_hand_value PASSED
tests/test_correlation.py::test_weights_renormalised_and_covered_weight PASSED
tests/test_correlation.py::test_rv_screen_blank_below_min_days PASSED
================= 11 passed, 10 warnings in 218.90s (0:03:38) =================
```

The instruction's test row, printed by `test_last_snapshot_before_start_session`: an AMC event on 2026-11-02 with snapshots on 2026-10-29 and 2026-10-30 takes 2026-10-30, with `pre_snap_age` = 1 and n1, n2 counted from 2026-10-30:

```
  ticker         group  event_date timing pre_snap_date  pre_snap_age          E1          E2  n1  n2  theta1  theta2      S      F  straddle_move   ts_move  realised_move     ratio  log_ratio status
0   PLTR  xlk_holdings  2026-11-02    AMC    2026-10-30             1  2026-11-06  2026-11-13   5  10   0.006   0.009  100.0  100.1          0.039  0.047873       0.083382  1.741722   0.554875     ok
```

The cache tests use the real fixture surface frames behind a counting fake `surface_day`, and check that frames read back from the cache equal the fitted ones in values and dtypes:

- **`test_cache_second_run_refits_nothing`.** 3 days fitted. A second run with nothing changed fits 0. `--force` fits 3. A fourth day added fits only that day.
- **`test_cache_svi_edit_refits_all_days`.** Editing the `[svi]` table (`max_rmse_volpts` + 1) fits all 3 days, and a repeat run fits 0. Editing `[surface]` (`delta` 0.2) fits all 3. A changed IV file changes its day's key.

### E2. Step 7.0: EVENTS status counts and every changed row

Status counts, session 6 (`5dae296`) against now:

```
                 session_6  session_7
status                               
pending                 16         19
unknown                 15         15
no_pre_snapshot          6          3
ok                       4          4
```

Rows whose status changed:

```
   ticker  event_date        status_s6 status_s7 pre_snap_date_s6 pre_snap_date_s7
0    AAPL  2026-11-02  no_pre_snapshot   pending              NaN       2026-10-30
28   PLTR  2026-11-02  no_pre_snapshot   pending              NaN       2026-10-30
29   SHOP  2026-11-03  no_pre_snapshot   pending              NaN       2026-10-30
```

The same rows in full:

```
   ticker         group  event_date timing pre_snap_date pre_snap_age          E1          E2  n1  n2          theta1          theta2            S            F  straddle_move        ts_move realised_move ratio log_ratio   status
7    AAPL  xlk_holdings  2026-11-02    AMC    2026-10-30            1  2026-11-04  2026-11-06   3   5  0.003134183001  0.003716780205  344.0400085  344.2188104  0.04563422745  0.04030372153           NaN   NaN       NaN  pending
8    PLTR  xlk_holdings  2026-11-02    AMC    2026-10-30            1  2026-11-13  2026-11-20  10  15   0.03108198515   0.03625318576  185.6849976  185.9758628   0.1435226343   0.1177354955           NaN   NaN       NaN  pending
10   SHOP       singles  2026-11-03    BMO    2026-10-30            1  2026-11-13  2026-11-20  10  15   0.03480134604   0.04053512479  155.3600006  155.6033217   0.1496524196   0.1248390906           NaN   NaN       NaN  pending
```

All 3 now have both implied moves. They are `pending` because their windows end on 2026-11-03, after the last close in `close.parquet` (2026-11-02). No other row changed in any column: `rows with the same status but other values changed: 0`. The 4 `ok` events have `pre_snap_age` 0.

Every row that is not `unknown`:

```
   ticker         group  event_date timing pre_snap_date  pre_snap_age          E1          E2    n1    n2    theta1    theta2           S           F  straddle_move   ts_move  realised_move     ratio  log_ratio           status
0   GOOGL       singles  2026-10-28    AMC           NaN           NaN         NaN         NaN   NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN  no_pre_snapshot
1    MSFT  xlk_holdings  2026-10-28    AMC           NaN           NaN         NaN         NaN   NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN  no_pre_snapshot
2    ^SPX         index  2026-10-28   FOMC           NaN           NaN         NaN         NaN   NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN  no_pre_snapshot
3    AMZN       singles  2026-10-29    AMC    2026-10-29           0.0  2026-11-04  2026-11-06   4.0   6.0  0.011354  0.011667  245.289993  245.455716       0.085919  0.083241       0.014211  0.170720  -1.767732               ok
4    INTC  xlk_holdings  2026-10-29    AMC    2026-10-29           0.0  2026-11-06  2026-11-13   6.0  11.0  0.016732  0.022077   91.849998   91.932557       0.104790  0.085143       0.336537  3.952634   1.374382               ok
5     CVX       singles  2026-10-30    BMO    2026-10-29           0.0  2026-10-30  2026-11-06   1.0   6.0  0.000862  0.002457  230.625000  230.631498       0.024304  0.023420       0.017389  0.742469  -0.297774               ok
6     XOM       singles  2026-10-30    BMO    2026-10-29           0.0  2026-10-30  2026-11-06   1.0   6.0  0.000917  0.002529  182.470001  182.479205       0.023867  0.024158       0.021375  0.884801  -0.122393               ok
7    AAPL  xlk_holdings  2026-11-02    AMC    2026-10-30           1.0  2026-11-04  2026-11-06   3.0   5.0  0.003134  0.003717  344.040008  344.218810       0.045634  0.040304            NaN       NaN        NaN          pending
8    PLTR  xlk_holdings  2026-11-02    AMC    2026-10-30           1.0  2026-11-13  2026-11-20  10.0  15.0  0.031082  0.036253  185.684998  185.975863       0.143523  0.117735            NaN       NaN        NaN          pending
9     AMD  xlk_holdings  2026-11-03    AMC           NaN           NaN         NaN         NaN   NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
10   SHOP       singles  2026-11-03    BMO    2026-10-30           1.0  2026-11-13  2026-11-20  10.0  15.0  0.034801  0.040535  155.360001  155.603322       0.149652  0.124839            NaN       NaN        NaN          pending
11   UBER       singles  2026-11-04    BMO           NaN           NaN         NaN         NaN   NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
12   ABNB       singles  2026-11-05    AMC           NaN           NaN         NaN         NaN   NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
13   ^SPX         index  2026-11-06    NFP           NaN           NaN         NaN         NaN   NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
14   ^SPX         index  2026-11-10    CPI           NaN           NaN         NaN         NaN   NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
15   AMAT  xlk_holdings  2026-11-12    AMC           NaN           NaN         NaN         NaN   NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
17    DIS       singles  2026-11-17    BMO           NaN           NaN         NaN         NaN   NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
18     HD       singles  2026-11-17    BMO           NaN           NaN         NaN         NaN   NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
19   NVDA  xlk_holdings  2026-11-17    AMC           NaN           NaN         NaN         NaN   NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
21    WMT       singles  2026-11-19    BMO           NaN           NaN         NaN         NaN   NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
23   ^SPX         index  2026-12-04    NFP           NaN           NaN         NaN         NaN   NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
25   ^SPX         index  2026-12-09   FOMC           NaN           NaN         NaN         NaN   NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
26   ^SPX         index  2026-12-10    CPI           NaN           NaN         NaN         NaN   NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
29    UNH       singles  2027-01-12    BMO           NaN           NaN         NaN         NaN   NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
30    JPM       singles  2027-01-14    BMO           NaN           NaN         NaN         NaN   NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
31    BAC       singles  2027-01-15    BMO           NaN           NaN         NaN         NaN   NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
```

Summary (`event_summary.csv`), unchanged from session 6:

```
  scope  n  mean_log_ratio  median_log_ratio  mean_lo  mean_hi  share_above  share_lo  share_hi       status
0   all  4       -0.203379         -0.210083      NaN      NaN         0.25       NaN       NaN  below_min_n
```

### E3. Step 7.0: new days and run 41622958662 (status 5)

`scripts/pull_snapshots.py`, run at 17:35 UTC on 2026-11-03:

```
8 assets in snapshots: 0 downloaded, 8 already present
```

The `snapshots` release holds the assets of 2026-10-29 and 2026-10-30 only:

```
chains_2026-10-29.parquet
chains_2026-10-30.parquet
earnings_2026-10-29.csv
earnings_2026-10-30.csv
snaplog_2026-10-29.json
snaplog_2026-10-30.json
underlying_2026-10-29.csv
underlying_2026-10-30.csv
```

So no new capture day was added. The IV, surface, density and tails stages had no new day to run on. EVENTS and the summary were rebuilt after `pull_data.py --stage prices`. That pull ends on 2026-11-02, the last completed session at 17:3x UTC. Only `sectors.parquet` and `MANIFEST.json` changed: the adjusted closes moved by at most 1.34e-6 relative, with the same 7,008 rows from 1998-12-22 to 2026-11-02.

Run 41622958662 (`workflow_dispatch`, created 10:53 UTC, success, 5 h 37 min). The lines of its log from `snapshot.py`:

```
2026-11-03T11:00:26.9685443Z 2026-11-03T11:00:26.803704+00:00 waiting 19800 seconds of 34173, then chaining
2026-11-03T16:30:30.0298627Z 2026-11-03T16:30:27.776447+00:00 chained: dispatched a new run with 14372 seconds still to wait
```

It chained as built in step 6.0 and uploaded no assets. The run it dispatched, 41674897033, was `in_progress` at 17:32 UTC. The 2026-11-03 assets had not landed when this section ran.

### E4. Step 7.0: surface stage runtime with the cache

Not measured on the 3 real days in this session. The cache starts empty, so the first run with it fits every day: that is the 155-minute run of session 6. That first run was started at 17:45 UTC to fill `data/processed/surface/`, and the session was finished without waiting for it, on the owner's instruction. The cache logic is evidenced by E1: a second run with nothing changed fits 0 days. Reading a day back is 1 parquet read per day, so a run with every day cached does no SVI or SSVI fitting.

### E5. Step 7.1: the regression row against the reviewer's

`outputs/tables/cor3m_study.csv` (O-40 (a)):

```
      n     first_t      last_t  horizon  maxlags  intercept  intercept_nw_se    slope  slope_nw_se        r2  mean_implied  mean_realised  mean_gap
0  5163  2006-01-03  2026-08-04       63       63   0.286233         0.037129  0.71146     0.073969  0.437345      0.412586       0.579771 -0.167185
```

`gap_note`, in the table beside `mean_gap`: "sector-level proxy: sector ETFs are diversified baskets and correlate with each other more than the single stocks behind COR3M, so implied sits below realised; the gap is the proxy, not a correlation risk premium".

Against the reviewer's row:

```
                   reviewer   section_7 section_7_3dp
n                      5163        5163          5163
first_t          2006-01-03  2006-01-03    2006-01-03
last_t           2026-08-04  2026-08-04    2026-08-04
intercept            0.2862    0.286233        0.2862
intercept_nw_se      0.0371    0.037129        0.0371
slope                0.7115     0.71146        0.7115
slope_nw_se           0.074    0.073969         0.074
r2                   0.4373    0.437345        0.4373
mean_gap            -0.1672   -0.167185       -0.1672
```

Every value matches to 4 decimals, so to 3 as well. The Newey-West errors come from the module's own Bartlett-kernel code with no small-sample correction. `test_newey_west_matches_statsmodels` checks it against statsmodels `OLS(...).fit(cov_type="HAC", cov_kwds={"maxlags": 63})`, to 1e-10 relative on the standard errors. The re-pulled `sectors.parquet` (E3) moves nothing at this precision.

Write-up note, as instruction 07 asks. The mean gap is negative, so implied sits below realised. That is the proxy, not a negative correlation risk premium. COR3M is the implied correlation of the 50 largest S&P 500 stocks, while sector ETFs are already diversified baskets and correlate with each other more than single stocks do. The usable result is the slope of 0.71 and the R² of 0.44: how much of the next quarter's correlation the index options anticipate.

First and last 3 rows of the series behind the figure:

```
           t  implied  realised       gap
0 2006-01-03   0.3134  0.503526 -0.190126
1 2006-01-04   0.3112  0.504920 -0.193720
2 2006-01-05   0.3092  0.504669 -0.195469
              t  implied  realised       gap
5160 2026-07-31   0.0971  0.163101 -0.066001
5161 2026-08-03   0.0908  0.160336 -0.069536
5162 2026-08-04   0.0964  0.146880 -0.050480
```

Figure: `outputs/figures/cor3m_vs_realised.png`. It plots implied and forward realised over time with the gap shaded, and carries the proxy sentence under the plot.

### E6. Step 7.2: `implied_corr_live.csv` in full

```
          day index  index_vol  n_names  covered_weight  implied_corr  realised_index_vol  realised_implied_corr  realised_avg_pairwise_corr                status
0  2026-10-28   XLK        NaN        1        0.146174           NaN                 NaN                    NaN                         NaN  no_index_vol|pending
1  2026-10-29   XLK   0.252422       15        0.720304      0.331092                 NaN                    NaN                         NaN               pending
2  2026-10-30   XLK   0.337191       13        0.661020      0.564891                 NaN                    NaN                         NaN               pending
```

- **2026-10-28 (fixture day).** It has AAPL only and no XLK chain.
- **2026-10-30.** MU and PANW have a blank `atm_30` that day (E7), so their weights are renormalised away and the covered weight drops to 0.661.
- **Realised side.** Blank on every row: the first window, the fixture day's, completes with the close of 2026-11-27.

### E7. Step 7.2: RV screen on the last day (2026-10-30)

Top 5 by vol minus group median:

```
           day ticker         group    atm_30  n_prior  zscore  group_median  vol_minus_group_median          status
75  2026-10-30   SHOP       singles  0.750901        1     NaN      0.336437                0.414464  below_min_days
53  2026-10-30   PLTR  xlk_holdings  0.701080        1     NaN      0.498861                0.202219  below_min_days
49  2026-10-30    AMD  xlk_holdings  0.646844        1     NaN      0.498861                0.147983  below_min_days
56  2026-10-30   AMAT  xlk_holdings  0.623988        1     NaN      0.498861                0.125127  below_min_days
74  2026-10-30   UBER       singles  0.460572        1     NaN      0.336437                0.124135  below_min_days
```

Bottom 5:

```
           day ticker         group    atm_30  n_prior  zscore  group_median  vol_minus_group_median          status
41  2026-10-30    SPY          etfs  0.169682        2     NaN      0.261741               -0.092059  below_min_days
66  2026-10-30    JPM       singles  0.234088        1     NaN      0.336437               -0.102349  below_min_days
60  2026-10-30    IBM  xlk_holdings  0.333549        1     NaN      0.498861               -0.165312  below_min_days
47  2026-10-30   AAPL  xlk_holdings  0.296875        2     NaN      0.498861               -0.201986  below_min_days
48  2026-10-30   MSFT  xlk_holdings  0.275765        1     NaN      0.498861               -0.223095  below_min_days
```

Rows with no `atm_30`, and the status counts over all 77 rows:

```
           day ticker         group  atm_30  n_prior  zscore  group_median  vol_minus_group_median  status
51  2026-10-30     MU  xlk_holdings     NaN        1     NaN      0.498861                     NaN  no_vol
55  2026-10-30   PANW  xlk_holdings     NaN        1     NaN      0.498861                     NaN  no_vol
status
below_min_days    75
no_vol             2
```

No name has 20 prior snapshot days, so every z-score is blank.

## Tests run

`.venv\Scripts\python -m pytest -p socket --disable-socket -q` on Windows at `b2b50e5` (before the cache-test fix; the suite runs the cache tests after `test_surface_run_fixture`, which fills `_tables()` first):

```
recorded in the next commit, when the run ends
```

`.venv\Scripts\ruff check .`: `All checks passed!`

## Fresh-clone check

Recorded in the next commit, at the pushed head.

### CI

Recorded in the next commit.

## Runtime per step

- **7.0.** The events stage took about 1 min. The surface stage with an empty cache is the 155-minute run of session 6 (E4).
- **7.1.** The `cor3m` stage took about 30 s for 5,163 windows.
- **7.2.** The `live_corr` stage took a few seconds.

## Deviations from PLAN.md

1. **EVENTS gains `pre_snap_age`**, by instruction 07. `test_events_schema` asserts the instruction's column list. That assertion compares to the schema literal, and the literal changed with the schema the instruction sets; no tolerance moved.
2. **A window starting after the last close keeps status `pending` with blank results, unless its start session has a snapshot of its own.** A later snapshot can still arrive before that start session, so its pre-event snapshot is not yet known. This keeps the session 6 interpretation that the reviewer did not change. It decides the 16 future events: UBER through BAC above.
3. **Surface cache file layout.** Each `{day}.parquet` holds the 4 `surface_day` frames, each stored as its own parquet bytes in one row (columns `name`, `data`), with the key in the file metadata. The frames therefore come back with exact values and dtypes. The key is the sha256 of the concatenated sha256 digests of the 5 parts. The `[svi]` and `[surface]` tables enter as JSON with sorted keys.
4. **The cache key follows the instruction exactly,** so it does not cover `[density] int_points`. That key sets the acceptance grid of the SVI fit (instruction 05b part B). Editing it would not refit cached days. Reported, not changed.
5. **The 7.1 and 7.2 tests are in one file,** `tests/test_correlation.py`, as PLAN names. It adds `test_cor3m_study_windows_and_columns`.

## Not verified

- **The surface stage runtime with every day cached** (E4).
- **The realised side of the live implied correlation** (O-42): every day is `pending`.
- **The 2026-11-03 capture.** It had not landed (E3).

## Open questions

- **O-40 Columns of `cor3m_study.csv`.**
  - (a) 1 row: n, first_t, last_t, horizon, maxlags, intercept, intercept_nw_se, slope, slope_nw_se, r2, mean_implied, mean_realised, mean_gap, gap_note.
  - (b) 1 row per coefficient, plus r2 and mean_gap rows, with the note on the mean_gap row.

  Implemented as (a).
- **O-41 Columns and statuses of `implied_corr_live.csv` and `rv_screen.csv`; the fixture-day row; whether `rv_min_days` counts today.**
  - (a) As built: 1 row per SURFACE_DAILY day or row, the fixture day included. Statuses are `ok`, `no_index_vol`, `pending`, `below_min_days` and `no_vol`. `rv_min_days` counts prior days only.
  - (b) Snapshot days only, `rv_min_days` counting today, and separate implied and realised statuses.

  Implemented as (a).
- **O-42 Realised side of the live implied correlation.**
  - (a) Add `adj_close.parquet` for the 31 underlyings to the prices stage. Realised vol is the standard deviation (ddof 1) of the 21 log returns × √252.
  - (b) Build adjusted returns from `close.parquet` and `dividends.csv`. Realised vol is √(252/21 × Σ r²).

  Not built. `live_implied_corr` raises when a complete window appears, first with the close of 2026-11-27.

## Files changed

- `volsurf/events.py`: `pre_event_snapshot`, `pre_snap_age`, and the precedence of `pending`.
- `volsurf/correlation.py`: new.
- `scripts/run_all.py`: the surface cache (`surface_key`, `cached_surface_day`) and `--force`; the events stage on the pre-event snapshot day; the `cor3m` and `live_corr` stages; the `cor3m_vs_realised.png` figure.
- `tests/test_events.py`, `tests/test_surface_run.py` and `tests/test_correlation.py` (new).
- `outputs/tables/events.csv`, `cor3m_study.csv`, `implied_corr_live.csv` and `rv_screen.csv`.
- `data/raw/prices/sectors.parquet` and `data/raw/MANIFEST.json`.
- `decisions/section_6_review.md` (new) and `decisions/OPEN.md` (O-40 to O-42).

### Figures, by path

- `outputs/figures/cor3m_vs_realised.png` (new)
- `outputs/figures/event_term_structures.png`: redrawn. SHOP and PLTR now have implied moves, so they enter the 4 largest.
- `outputs/figures/event_scatter.png`: unchanged
- `outputs/figures/spx_density_last.png`, `spx_metrics.png`, `spx_smile_fits_2026-10-28.png`, `spx_smiles_2026-10-28.png`, `spx_smiles_2026-10-29.png`, `spx_smiles_2026-10-30.png` and `spx_surface_last.png`: unchanged

## Reviewer reads

1. E5 (the regression row) and E6 (`implied_corr_live.csv`).
2. E2, the 3 changed EVENTS rows, and deviation 2.
3. `volsurf/correlation.py`.
4. `cached_surface_day` and `surface_key` in `scripts/run_all.py`, and deviation 4.
5. O-40 to O-42 in `decisions/OPEN.md`.
