# Review: Section 8

## Section

Section 8: Volatility risk premium (`PLAN.md` steps 8.1 and 8.2), with instruction 08. Step 8.0 comes first: adjusted closes, the realised side of the live correlation (O-42), the `[density]` table in the surface cache key, and the new capture days.

The section is complete. Every VRP_MONTHLY value the reviewer printed matches to 5 decimals. Three of the 24 strategy numbers miss at 2 decimals: BXM Sharpe (0.441 against 0.446), timed PUT Sharpe (0.803 against 0.808) and BXM excess kurtosis (5.243 against 5.25). All 3 come from this session's Cboe refresh, which instruction 08 asks for. On the reviewer's data (`b05fed2`), all 24 match to 4 decimals (E6). One reviewer number is not reproduced: signal positive in 90.7% of months. Here it is 362 of 395, or 91.6% (E4).

## Steps completed

- 8.0  8bcd92e  step 8.0: adjusted closes, realised side of live correlation, cache key. It also commits `decisions/section_7_review.md`, the refreshed Cboe files, and the COR3M study rerun on the re-pulled sector closes.
- 8.1  bc67b50  step 8.1: realised variance, GARCH forecasts, VRP_MONTHLY
- 8.2  b856bda  step 8.2: strategies, statistics, spec log, deflated Sharpe, live straddles. It adds O-43 and O-44, and marks O-40 to O-42 decided in `decisions/OPEN.md`.
- The wrap-up commit holds this file, the status file, and the outputs of the new capture day 2026-11-03. That day landed at 20:37 UTC, after the 3 step commits were pushed, and every stage was rerun for it (E2). Its stage code is that of `b856bda`, unchanged.

## Evidence

### E1. Step 8.0: tests

`.venv\Scripts\python -m pytest -p socket --disable-socket -v -s -W ignore` on the new and changed tests of step 8.0 and Section 8:

```
tests/test_vrp.py::test_realised_var_constant_returns PASSED
tests/test_vrp.py::test_garch_no_lookahead PASSED
tests/test_vrp.py::test_month_ends_completed_only PASSED
tests/test_vrp.py::test_level_on_or_before PASSED
tests/test_vrp.py::test_vrp_monthly_schema_and_identities PASSED
tests/test_vrp.py::test_switch_cost_applied_on_change PASSED
tests/test_vrp.py::test_deflated_sharpe_known_value PASSED
tests/test_vrp.py::test_spec_log_appends PASSED
tests/test_vrp.py::test_straddle_mark_atm PASSED
tests/test_correlation.py::test_realised_side_known_panel PASSED
tests/test_correlation.py::test_weights_renormalised_and_covered_weight PASSED
tests/test_pull_data.py::test_manifest_hashes_match_files PASSED
tests/test_pull_data.py::test_cboe_first_dates PASSED
tests/test_pull_data.py::test_close_has_every_captured_ticker_but_spx PASSED
tests/test_pull_data.py::test_xlk_weights_sum PASSED
tests/test_pull_data.py::test_xlk_names_in_holdings PASSED
tests/test_pull_data.py::test_xlk_names_cover_70_percent PASSED
tests/test_pull_data.py::test_pull_uses_fake_session PASSED
============================= 18 passed in 9.07s ==============================
```

And the surface cache tests with the `[density]` edit (`tests/test_surface_run.py` with `tests/test_pull_data.py`): `11 passed, 5 warnings in 400.86s`.

**`test_realised_side_known_panel` (O-42).** It builds 3 names over the 21 sessions after 2026-10-28. Their return columns are demeaned, have unit norm and are equicorrelated at 0.4, scaled by c = (0.02, 0.03, 0.05). So Σ r² = c², each realised vol is c √(252/21), and the Pearson correlations are exactly 0.4. XLK's returns are the weighted sum, so the implied correlation formula on realised vols also gives 0.4. The row it prints:

```
          day index  index_vol  n_names  covered_weight  implied_corr  realised_index_vol  realised_implied_corr  realised_avg_pairwise_corr status
0  2026-10-28   XLK       0.22        3             0.6      0.518175            0.076114                    0.4                         0.4     ok
```

The test asserts the realised vols to 1e-12 relative, and XLK's realised vol against √(252/21 × wᵀ diag(c) C diag(c) w). Both correlations are asserted to 1e-12. One session short of the window, the row stays `pending` with blank realised columns.

**Cache key.** `test_cache_svi_edit_refits_all_days` now also edits `[density] int_points` (200,001 to 100,001): all 3 days refit, and a repeat run refits 0.

**Prices stage.** `test_pull_uses_fake_session` asserts that `adj_close.parquet` has the same columns as `close.parquet` and holds the fake `Adj Close`. `test_close_has_every_captured_ticker_but_spx` asserts the same columns and index on the committed file.

`data/raw/MANIFEST.json`, the prices and refreshed Cboe entries:

```
                          rows  first_date   last_date                        pulled_utc
cboe/BXM.csv              6191  2002-03-22  2026-11-02  2026-11-03T19:08:18.822290+00:00
cboe/PUT.csv              4997  1991-03-04  2026-11-02  2026-11-03T19:08:18.822290+00:00
cboe/VIX.csv              9307  1990-01-02  2026-11-02  2026-11-03T19:08:18.822290+00:00
prices/adj_close.parquet  9297  1989-12-01  2026-11-02  2026-11-03T19:07:50.315343+00:00
prices/close.parquet      9297  1989-12-01  2026-11-02  2026-11-03T19:07:50.315343+00:00
prices/dividends.csv      2479  1989-12-05  2026-10-14  2026-11-03T19:07:50.315343+00:00
prices/index.parquet      9297  1989-12-01  2026-11-02  2026-11-03T19:07:50.315343+00:00
prices/sectors.parquet    7008  1998-12-22  2026-11-02  2026-11-03T19:07:50.315343+00:00
```

`adj_close.parquet` has 36 columns, the same as `close.parquet`. Its last 3 rows for 4 names:

```
                   XLK        AAPL        NVDA          MU
date                                                      
2026-10-29  188.740005  348.910004  213.660004  934.270020
2026-10-30  179.509995  344.630005  204.639999  884.739990
2026-11-02  174.220001  338.320007  202.059998  833.590027
```

Of the price files, the re-pull changed only `sectors.parquet`; `close.parquet`, `index.parquet` and `dividends.csv` are byte-identical. The 7 Cboe files gained 4 rows each, 2026-10-28 to 2026-11-02, with no earlier row changed. `VIX.csv` now ends on 2026-11-02.

The re-pulled sector closes move the COR3M row in the 7th significant digit, so step 8.0 commits the rerun table:

```
                    b05fed2         now
n                      5163        5163
first_t          2006-01-03  2006-01-03
last_t           2026-08-04  2026-08-04
intercept          0.286233    0.286233
intercept_nw_se    0.037129    0.037129
slope               0.71146    0.711459
slope_nw_se        0.073969    0.073969
r2                 0.437345    0.437345
mean_gap          -0.167185   -0.167185
```

### E2. Step 8.0: capture status of 2026-11-03, the chained run, new days and EVENTS

**The chained run and the 2026-11-03 capture.** Run 41622958662 chained into run 41674897033 (`workflow_dispatch`, created 16:30:29 UTC). That run completed with success at 20:37:03 UTC, and the 2026-11-03 assets landed. The lines of its log from `snapshot.py`:

```
2026-11-03T16:30:47.744209+00:00 waiting 14352 seconds until 15:30 New York
2026-11-03T20:30:00.729543+00:00 start runner=actions ny=2026-11-03 15:30:00 forced=False tickers=37
^SPX   ok      rows= 11613 expiries= 44 failed=0   29.0s
SPY    ok      rows=  7207 expiries= 26 failed=0   17.2s
QQQ    ok      rows=  6228 expiries= 24 failed=0   15.9s
XLK    ok      rows=  1484 expiries= 12 failed=0    8.5s
... (33 more tickers, every one ok)
ABNB   ok      rows=   635 expiries= 12 failed=0    9.0s
2026-11-03T20:36:57.164290+00:00 done ok=37 partial=0 error=0 rows=84673
uploaded 4 files to release snapshots
```

`scripts/pull_snapshots.py` at 19:1x UTC gave `8 assets in snapshots: 0 downloaded, 8 already present`. Run again at 20:44 UTC, after the upload:

```
12 assets in snapshots: 4 downloaded, 8 already present
```

`capture_health.csv`. 2026-11-02 has no capture (a gap, as in session 7):

```
      session   runner  start_ny                          ny_start  minutes_after_1530  tickers_ok     rows  after_close_rows    gap
0  2026-10-28      NaN       NaN                               NaN                 NaN         NaN      NaN               NaN   True
1  2026-10-29  actions  15:30:00  2026-10-29T15:30:00.597894-04:00            0.009965        37.0  83293.0               0.0  False
2  2026-10-30  actions  15:55:48  2026-10-30T15:55:48.161205-04:00           25.802687        37.0  76611.0           17522.0  False
3  2026-11-02      NaN       NaN                               NaN                 NaN         NaN      NaN               NaN   True
4  2026-11-03  actions  15:30:00  2026-11-03T15:30:00.729543-05:00            0.012159        37.0  84673.0               0.0  False
```

**Every stage for the new day.** The capture_health, iv, surface, density, tails, events, live_corr and strategies stages ran from 20:44:37 to 21:25:45 UTC. The IV stage rewrote every day's IV file. The 3 earlier days were then read from the surface cache, so their IV files are byte-identical; only 2026-11-03 was fitted (`surface: 1 of 4 days fitted, 1811.3 s`). 2026-11-03 SVI statuses: ok 253, ok_refit 284, poor_fit 17, too_few 7, butterfly_fail 2. Density statuses: ok 497, kink 40. The new `^SPX` SURFACE_DAILY row:

```
           day ticker    atm_30   rr25_30  ssvi_rr25_30   bf25_30    atm_90  term_slope  ssvi_rho  ssvi_eta  ssvi_gamma  ssvi_rmse  n_expiries status
77  2026-11-03   ^SPX  0.162841 -0.053724     -0.079515  0.006625  0.158814   -0.004028 -0.598729  1.250994         0.5   0.031648          34     ok
```

**EVENTS.** Rebuilt after the prices refresh and the new day. Prices still end on 2026-11-02, because 2026-11-03 had not closed when they were pulled. Status counts:

```
                 session_7  session_8
status                               
no_pre_snapshot          3          3
ok                       4          4
pending                 19         38
unknown                 15          1
```

Transitions, session 7 against session 8:

```
status_s8        no_pre_snapshot  ok  pending  unknown
status_s7                                             
(none)                         0   0        5        0
no_pre_snapshot                3   0        0        0
ok                             0   4        0        0
pending                        0   0       19        0
unknown                        0   0       14        1
```

Rows whose status, timing or pre-event snapshot changed:

```
   ticker  event_date timing_s7 timing_s8 status_s7 status_s8 pre_snap_date_s7 pre_snap_date_s8
4     AMD  2026-11-03       AMC       AMC   pending   pending              NaN       2026-11-03
6    AMZN  2027-02-04   unknown       AMC   unknown   pending              NaN              NaN
7    AVGO  2026-12-09   unknown       AMC   unknown   pending              NaN              NaN
9     CRM  2026-12-02   unknown       AMC   unknown   pending              NaN              NaN
10   CSCO  2026-11-12   unknown       AMC   unknown   pending              NaN              NaN
15  GOOGL  2027-02-03   unknown       AMC   unknown   pending              NaN              NaN
17    IBM  2027-01-27   unknown       AMC   unknown   pending              NaN              NaN
19   INTC  2027-01-28   unknown       AMC   unknown   pending              NaN              NaN
21   LRCX  2027-01-27   unknown       AMC   unknown   pending              NaN              NaN
22   META  2027-01-27   unknown       AMC   unknown   pending              NaN              NaN
24   MSFT  2027-01-27   unknown       AMC   unknown   pending              NaN              NaN
25     MU  2026-12-23   unknown       AMC   unknown   pending              NaN              NaN
26   NFLX  2027-01-19   unknown       AMC   unknown   pending              NaN              NaN
28   ORCL  2026-12-14   unknown       AMC   unknown   pending              NaN              NaN
34   TSLA  2027-01-27   unknown       AMC   unknown   pending              NaN              NaN
35   UBER  2026-11-04       BMO       BMO   pending   pending              NaN       2026-11-03
```

New events, from the 2026-11-03 earnings asset:

```
   ticker  event_date timing_s8 status_s8
1    AAPL  2027-01-28       AMC   pending
12    CVX  2027-01-29       BMO   pending
29   PANW  2026-11-18       AMC   pending
32   PLTR  2027-02-01       AMC   pending
39    XOM  2027-01-29       BMO   pending
```

- **The 14 `unknown` events now have a time.** The 2026-11-03 earnings asset is now the latest asset listing them, and it carries a confirmed time instead of Yahoo's 15:00 placeholder. Under O-12 (b), they become AMC.
- **PANW.** Its date moved from 2026-11-19 to 2026-11-18. The old row is listed only by the earlier assets, so it stays as the 1 `unknown` row, beside the new 2026-11-18 AMC event.
- **AMD and UBER** now have a pre-event snapshot, 2026-11-03. They stay `pending` until the 2026-11-03 close is in the price data. Their rows:

```
   ticker         group  event_date timing pre_snap_date  pre_snap_age          E1          E2   n1   n2    theta1    theta2           S           F  straddle_move   ts_move  realised_move  ratio  log_ratio   status
3     AMD  xlk_holdings  2026-11-03    AMC    2026-11-03           0.0  2026-11-09  2026-11-11  4.0  6.0  0.013762  0.016625  487.714996  488.042323       0.094727  0.077633            NaN    NaN        NaN  pending
4    UBER       singles  2026-11-04    BMO    2026-11-03           0.0  2026-11-06  2026-11-13  3.0  8.0  0.008323  0.010424   66.824997   66.847467       0.073775  0.069021            NaN    NaN        NaN  pending
```

- **The summary** (`event_summary.csv`) is unchanged: 4 events, `below_min_n`.

`implied_corr_live.csv` now runs through the O-42 code. Every row is still `pending`, since the first window ends with the close of 2026-11-27:

```
          day index  index_vol  n_names  covered_weight  implied_corr  realised_index_vol  realised_implied_corr  realised_avg_pairwise_corr                status
0  2026-10-28   XLK        NaN        1        0.146174           NaN                 NaN                    NaN                         NaN  no_index_vol|pending
1  2026-10-29   XLK   0.252422       15        0.720304      0.331092                 NaN                    NaN                         NaN               pending
2  2026-10-30   XLK   0.337191       13        0.661020      0.564891                 NaN                    NaN                         NaN               pending
3  2026-11-03   XLK   0.321828       15        0.720304      0.495985                 NaN                    NaN                         NaN               pending
```

On instruction 08's note: the jump from 0.331 on 2026-10-29 to 0.565 on 2026-10-30 is real. That day the S&P 500 fell 1.8% and XLK 4.9%. XLK's 30-day ATM vol rose from 25.2% to 33.7%, and `^SPX`'s from 13.0% to 16.5%. Implied correlation rising in a sell-off is the textbook pattern.

### E3. Step 8.0: surface stage runtime, cold and cached

Both runs are on the new key, which adds `[density]`. The cold run was the first with that key, so no cached day matched. It was timed with `time .venv/Scripts/python -u scripts/run_all.py --stage surface`, from 19:07:23 to 20:43:42 UTC:

```
2026-10-28: fitted
2026-10-29: fitted
2026-10-30: fitted
surface: 3 of 3 days fitted, 5751.6 s
real	96m18.657s
```

The cached second run followed at once, from 20:43:48 to 20:43:53 UTC:

```
2026-10-28: read from cache
2026-10-29: read from cache
2026-10-30: read from cache
surface: 0 of 3 days fitted, 0.1 s
real	0m5.535s
```

The 5.5 s is almost all tables, printouts and figures. Neither run changed a committed file: `svi_fits.csv`, `surface_daily.csv`, `calendar_violations.csv`, `ssvi_theta.csv` and the Section 4 figures are byte-identical.

The cold run shared the machine with 2 other jobs for part of the time: the full test suite (19:35 to 19:56 UTC) and the session 7 surface process. That process was started at 17:43 UTC with the old key, and the session could not stop it. So 96 min is an upper bound for 3 days on this machine. Session 6 measured 155 min with the old code.

### E4. Step 8.1: VRP_MONTHLY, first and last 5 rows, against the reviewer

`outputs/tables/vrp_monthly.csv`, 442 completed month ends from 1990-01-31 to 2026-10-30. November 2026 is the current, incomplete month, so it is not a month end. First 5 rows:

```
    month_end    vix        iv  garch_fc  signal  rv_fwd_21       vrp
0  1990-01-31  25.36  0.064313       NaN     NaN   0.013015  0.051298
1  1990-02-28  21.99  0.048356       NaN     NaN   0.012269  0.036087
2  1990-03-30  19.73  0.038927       NaN     NaN   0.011864  0.027064
3  1990-04-30  19.52  0.038103       NaN     NaN   0.016090  0.022013
4  1990-05-31  17.37  0.030172       NaN     NaN   0.016269  0.013903
```

Last 5 rows. 2026-10-30 has no forward RV yet:

```
      month_end    vix        iv  garch_fc    signal  rv_fwd_21       vrp
437  2026-06-30  16.45  0.027060  0.024023  0.003037   0.013557  0.013504
438  2026-07-31  15.99  0.025568  0.023217  0.002351   0.010774  0.014794
439  2026-08-31  14.92  0.022261  0.013367  0.008894   0.011151  0.011110
440  2026-09-30  16.34  0.026700  0.015119  0.011580   0.009423  0.017276
441  2026-10-30  19.42  0.037714  0.022201  0.015513        NaN       NaN
```

Against the reviewer's independent run:

```
                                     row     column    reviewer   section_8
0                        first GARCH row  month_end  1993-12-31  1993-12-31
1                        first GARCH row         iv      0.0136      0.0136
2                        first GARCH row   garch_fc     0.00471     0.00471
3                        first GARCH row     signal     0.00889     0.00889
4                        first GARCH row  rv_fwd_21     0.00505     0.00505
5                        first GARCH row        vrp     0.00854     0.00854
6                             2026-09-30         iv      0.0267      0.0267
7                             2026-09-30   garch_fc     0.01512     0.01512
8                             2026-09-30     signal     0.01158     0.01158
9                             2026-09-30  rv_fwd_21     0.00942     0.00942
10                            2026-09-30        vrp     0.01728     0.01728
11     mean vrp, 441 rows with IV and RV        vrp     0.00971     0.01037
12  mean vrp, 394 rows with GARCH and RV        vrp     0.00971      0.0097
13         signal > 0, 362 of 395 months      share       0.907       0.916
```

- **The 2 rows** match to 5 decimals.
- **Return series.** The GARCH and RV returns are `^GSPC` log returns from the close of `[vrp] start` (1990-01-02), so the first return is 1990-01-03. That puts the 1,000th return in December 1993: 1,012 returns by 1993-12-31 and 990 by 1993-11-30. With returns from the start of `index.parquet` (1989-12-01), the first forecast would fall on 1993-11-30, and the 1993-12-31 forecast would be 0.00479, not 0.00471.
- **Mean VRP.** Over the 441 rows with IV and RV, it is 0.01037. Over the 394 rows that also have a GARCH forecast, it is 0.009699, which rounds to 0.00970 and is within 1e-5 of the reviewer's 0.00971. So the reviewer's "rows with both sides" appears to mean the GARCH era. Both are reported.
- **Signal positive.** Not reproduced. The signal is positive in 362 of the 395 months with a forecast (91.6%), against the reviewer's 90.7%. The nearest whole-month fit is 362 of 399. On the `b05fed2` data it is the same 362 of 395. The 2007 to 2026 signs agree exactly, since the timed PUT holds PUT in 210 months and switches 41 times, as in the reviewer's run (E5). So any difference lies before 2007. The 5 months with the smallest |signal| are 2000-06-30 (+1.5e-5), 2017-05-31, 2016-07-29, 2022-07-29 and 2024-08-30, all within 3e-4.

### E5. Step 8.2: `strategy_stats.csv` in full, against the reviewer

The common window runs from 2007-02-28 to 2026-10-30, 237 months. The timed PUT holds PUT in 210 of them, with 41 changes (the first position counts):

```
    strategy first_month  last_month  n_months  ann_mean   ann_vol    sharpe  worst_month  worst_drawdown      skew  excess_kurtosis       q01       q05  n_trials  deflated_sharpe      dsr_status
0        put  2007-02-28  2026-10-30       237  0.075176  0.107151  0.555359    -0.176502       -0.326574 -1.687062         7.405914 -0.095296 -0.047884       NaN              NaN             NaN
1        bxm  2007-02-28  2026-10-30       237  0.063934  0.109520  0.441059    -0.150119       -0.358145 -1.359215         5.242587 -0.096096 -0.055223       NaN              NaN             NaN
2    sp500tr  2007-02-28  2026-10-30       237  0.115501  0.154038  0.648408    -0.167951       -0.509488 -0.551221         1.048731 -0.101302 -0.073372       NaN              NaN             NaN
3  timed_put  2007-02-28  2026-10-30       237  0.088485  0.090610  0.802559    -0.134165       -0.207525 -1.025093         5.481031 -0.077910 -0.040433       1.0              NaN  too_few_trials
4   bxm_long  2002-04-30  2026-10-30       295  0.065715  0.106364  0.455002    -0.150119       -0.358145 -1.263277         5.108749 -0.084762 -0.055138       NaN              NaN             NaN
```

Against the reviewer's table:

```
     strategy             stat  reviewer  section_8  equal_2dp
0         put         ann_mean    0.0757     0.0752       True
1         bxm         ann_mean    0.0645     0.0639       True
2     sp500tr         ann_mean    0.1155     0.1155       True
3   timed_put         ann_mean    0.0890     0.0885       True
4         put          ann_vol    0.1072     0.1072       True
5         bxm          ann_vol    0.1095     0.1095       True
6     sp500tr          ann_vol    0.1540     0.1540       True
7   timed_put          ann_vol    0.0906     0.0906       True
8         put           sharpe    0.5600     0.5554       True
9         bxm           sharpe    0.4460     0.4411      False
10    sp500tr           sharpe    0.6480     0.6484       True
11  timed_put           sharpe    0.8080     0.8026      False
12        put      worst_month   -0.1765    -0.1765       True
13        bxm      worst_month   -0.1501    -0.1501       True
14    sp500tr      worst_month   -0.1680    -0.1680       True
15  timed_put      worst_month   -0.1342    -0.1342       True
16        put             skew   -1.6900    -1.6871       True
17        bxm             skew   -1.3600    -1.3592       True
18    sp500tr             skew   -0.5500    -0.5512       True
19  timed_put             skew   -1.0300    -1.0251       True
20        put  excess_kurtosis    7.4100     7.4059       True
21        bxm  excess_kurtosis    5.2500     5.2426      False
22    sp500tr  excess_kurtosis    1.0500     1.0487       True
23  timed_put  excess_kurtosis    5.4800     5.4810       True
```

### E6. Why 3 strategy numbers miss at 2 decimals: the Cboe refresh

The reviewer ran on the committed data at `b05fed2`, where `PUT.csv` and `BXM.csv` end on 2026-10-27. Under instruction 08 point 2, the October 2026 level was therefore the 2026-10-27 close: PUT 3718.37 and BXM 2573.02. Step 8.0 refreshed the Cboe files, so October now ends on the 2026-10-30 close: PUT 3681.76, after the 1.8% fall in the S&P 500 that day. October's PUT return drops by about 1%, which over 237 months is 0.0005 a year on the mean, the gap in rows 0 to 3 above. `^SP500TR` comes from `index.parquet`, which already ended on 2026-11-02, so its row is unchanged.

Run on the `b05fed2` files (`PUT.csv`, `BXM.csv`, `VIX.csv`, `index.parquet`) with the section's code, every number matches the reviewer's to 4 decimals:

```
           ann_mean  ann_vol  sharpe  worst_month    skew  excess_kurtosis
strategy                                                                  
put          0.0757   0.1072  0.5600      -0.1765 -1.6904           7.4098
bxm          0.0645   0.1095  0.4459      -0.1501 -1.3637           5.2535
sp500tr      0.1155   0.1540  0.6484      -0.1680 -0.5512           1.0487
timed_put    0.0890   0.0906  0.8081      -0.1342 -1.0295           5.4839
```

The section keeps the refreshed data, because step 8.0 says to refresh the Cboe files.

**Write-up note, as instruction 08 asks.** The timed PUT's Sharpe ratio of 0.80, against 0.56 for PUT, comes from staying out of 27 of the 237 months. It is 1 specification out of a family, so the deflated Sharpe is the honest number. **1 specification has been tried**: the main one, row 1 of the spec log. The deflated Sharpe needs at least 2 trials for a variance of their Sharpe ratios, so it is blank, with status `too_few_trials`. It fills in once a second specification is logged.

### E7. Step 8.2: `spec_log.csv`

```
                run_utc         spec_id                                                                                                                                                                             description                                                                                                                                                                                        params_json    sharpe  n_months
0  2026-11-03T19:23:55Z  timed_put_main  timed PUT: hold Cboe PUT in month m+1 if (VIX/100)^2 minus the GARCH(1,1) 21-session forecast at month end m is above 0, else T-bills; switch cost on every change, the first included  {"garch_min_obs": 1000, "horizon": 21, "signal": "iv_minus_garch", "strategy_start": "2007-01-31", "switch_cost_bp": 10, "tbill": "DTB3 on the last session of month m / 1200", "threshold": 0.0}  0.802559       237
```

The Sharpe ratio is annualised (O-17 (a)). `deflated_sharpe` divides every Sharpe ratio by √12 and takes n_obs in months. Rerunning the stage leaves the file byte-identical (O-43 (a)).

### E8. Step 8.2: the 10 worst months of each strategy

```
=== put
      month_end       put     tbill
20   2008-10-31 -0.176502  0.000750
157  2020-03-31 -0.134165  0.001042
21   2008-11-28 -0.097915  0.000367
39   2010-05-28 -0.090639  0.000133
54   2011-08-31 -0.080200  0.000083
142  2018-12-31 -0.075627  0.001933
156  2020-02-28 -0.073839  0.001267
187  2022-09-30 -0.059060  0.002392
140  2018-10-31 -0.055883  0.001792
24   2009-02-27 -0.055127  0.000200
=== bxm
      month_end       bxm     tbill
20   2008-10-31 -0.150119  0.000750
157  2020-03-31 -0.149040  0.001042
21   2008-11-28 -0.106659  0.000367
142  2018-12-31 -0.077318  0.001933
156  2020-02-28 -0.075563  0.001267
54   2011-08-31 -0.071243  0.000083
187  2022-09-30 -0.065678  0.002392
24   2009-02-27 -0.063377  0.000200
39   2010-05-28 -0.061470  0.000133
16   2008-06-30 -0.059900  0.001542
=== sp500tr
      month_end   sp500tr     tbill
20   2008-10-31 -0.167951  0.000750
157  2020-03-31 -0.123513  0.001042
24   2009-02-27 -0.106478  0.000200
187  2022-09-30 -0.092099  0.002392
142  2018-12-31 -0.090290  0.001933
19   2008-09-30 -0.089106  0.001408
182  2022-04-29 -0.087202  0.000425
16   2008-06-30 -0.084305  0.001542
23   2009-01-30 -0.084289  0.000092
184  2022-06-30 -0.082544  0.000942
=== timed_put
      month_end  timed_put     tbill
157  2020-03-31  -0.134165  0.001042
39   2010-05-28  -0.090639  0.000133
54   2011-08-31  -0.080200  0.000083
156  2020-02-28  -0.073839  0.001267
187  2022-09-30  -0.060060  0.002392
24   2009-02-27  -0.056127  0.000200
140  2018-10-31  -0.055883  0.001792
11   2008-01-31  -0.053740  0.002742
16   2008-06-30  -0.049536  0.001542
217  2025-03-31  -0.047471  0.003500
```

The timed PUT sat in T-bills through October and November 2008, PUT's worst and third worst months. It held PUT through March 2020 and May 2010. Its 2022-09-30 and 2009-02-27 returns are PUT's less 10 bp, because those were switch months.

### E9. Step 8.2: `live_straddles.csv`

1 row per position per snapshot day (O-44 (a)). There are 4 `^SPX` days with 2026-11-03, so 4 positions and 10 rows. All are `open`, because the expiries (2026-11-27, 2026-11-30 and 2026-12-03) fall after the last snapshot.

```
     open_day      expiry  strike    mark_day         T            S            F         D       vol       value     delta  option_pnl  hedge_pnl  total_pnl status
0  2026-10-28  2026-11-27    7750  2026-10-28  0.082874  7730.430176  7752.375314  0.996634  0.134528  238.700000  0.021749    0.000000   0.000000   0.000000   open
1  2026-10-28  2026-11-27    7750  2026-10-29  0.079623  7698.669922  7719.755807  0.996766  0.125637  219.397142 -0.073716   19.302858  -0.690762  18.612096   open
2  2026-10-28  2026-11-27    7750  2026-10-30  0.076834  7557.560059  7578.018656  0.996879  0.139911  274.896850 -0.423836  -36.196850   9.711344 -26.485506   open
3  2026-10-28  2026-11-27    7750  2026-11-03  0.065810  7561.450195  7578.755094  0.997326  0.138063  257.605807 -0.460047  -18.905807   8.062564 -10.843243   open
4  2026-10-29  2026-11-27    7720  2026-10-29  0.079623  7698.669922  7719.755807  0.996766  0.130585  226.220391  0.014007    0.000000   0.000000   0.000000   open
5  2026-10-29  2026-11-27    7720  2026-10-30  0.076834  7557.560059  7578.018656  0.996879  0.143961  268.559717 -0.343696  -42.339326  -1.976590 -44.315916   open
6  2026-10-29  2026-11-27    7720  2026-11-03  0.065810  7561.450195  7578.755094  0.997326  0.141358  248.730951 -0.376478  -22.510560  -3.313614 -25.824174   open
7  2026-10-30  2026-11-30    7580  2026-10-30  0.085053  7557.560059  7578.588313  0.996545  0.163742  287.761927  0.015927    0.000000   0.000000   0.000000   open
8  2026-10-30  2026-11-30    7580  2026-11-03  0.074029  7561.450195  7579.656666  0.996993  0.159152  261.078061  0.016429   26.683865   0.061958  26.745823   open
9  2026-11-03  2026-12-03    7575  2026-11-03  0.082248  7561.450195  7580.025029  0.996659  0.163738  282.963376  0.029968    0.000000   0.000000   0.000000   open
```

A hand check of row 2: hedge_pnl = 0.021749 × (7698.67 − 7730.43) + (−0.073716) × (7557.56 − 7698.67) = −0.6908 + 10.4021 = 9.7113. The 2026-10-28 position had lost 26.49 index points by 2026-10-30, the day the S&P 500 fell 1.8% and 30-day vol rose. It recovered to −10.84 by 2026-11-03, as vol eased and 4 calendar days of theta accrued. This is descriptive only, with no statistics.

## Tests run

`.venv\Scripts\python -m pytest -p socket --disable-socket -q` on Windows at `b856bda`. It ran alongside the cold surface run (E3):

```
4558 passed, 35 warnings in 1231.56s (0:20:31)
```

`.venv\Scripts\ruff check .`: `All checks passed!`

## Fresh-clone check

At `b856bda` (Windows, `C:\vs8`): `git clone`, `uv venv --python 3.12`, `uv pip install -r requirements-lock.txt`, `uv pip install -e . --no-deps`, then `.venv\Scripts\python -m pytest -p socket --disable-socket -q`:

```
4558 passed, 35 warnings in 1547.15s (0:25:47)
```

### CI

On `b856bda` (run 41707679472, Linux): success. Ruff `All checks passed!`; pytest `4558 passed, 35 warnings in 934.56s (0:15:34)`.

## Runtime per step

- **8.0.** The prices stage took about 1 min and the Cboe stage a few seconds. The surface stage took 96 min cold for 3 days and 5.5 s cached (E3). For the new day 2026-11-03, the 8 stages took 41 min: iv 8 min, surface 30 min (1 day fitted), density 2 min, the rest seconds (E2).
- **8.1.** The `vrp` stage took 31.3 s: 395 GARCH fits, expanding up to 9,000 returns.
- **8.2.** The `strategies` stage took a few seconds.

## Deviations from PLAN.md

1. **`deflated_sharpe`'s 4th argument is named `kurt_pearson`, not `kurt`.** Instruction 08 point 3 asks the arguments to make the kurtosis convention plain. The call site passes every argument by name, `kurt_pearson=excess_kurtosis + 3`.
2. **`live_implied_corr` takes the adjusted closes**: `live_implied_corr(surface, weights, prices, last_price, cfg)`. `test_weights_renormalised_and_covered_weight` passes an empty frame for the new argument. That call changed with the signature; no assertion changed.
3. **The return series.** The VRP returns start at the close of `[vrp] start`, 1990-01-02. That puts the first GARCH row on 1993-12-31, as the reviewer's (E4).
4. **`adj_close.parquet` holds the 36 tickers of `close.parquet`.** These are every captured underlying but `^SPX`, whose level is `^GSPC` in `index.parquet` (O-3 (a)).
5. **`volsurf/vrp.py` lands whole in step 8.1.** The 8.2 functions (`strategy_returns`, `strategy_stats`, `deflated_sharpe`, `append_spec`, `live_straddles`) are in the 8.1 commit, while the 8.2 stage, tests and outputs are in the 8.2 commit. The 8.0 and 8.1 commits hold only their own parts of `scripts/run_all.py` and `tests/test_vrp.py`.
6. **Choices not fixed anywhere, implemented and listed as O-43 and O-44.** These are the `strategy_stats.csv` columns, which series each statistic uses, how the switch cost enters, the trial variance, the spec log on rerun, and every convention of the live straddles.

## Not verified

- **Realised moves for AMD, UBER and the 2026-11-02 and 2026-11-03 events.** Their windows end on or after the 2026-11-03 close, and prices were pulled before it.
- **The realised side of the live correlation on real data.** It is built and tested on the synthetic panel, but every live day is `pending` until 2026-11-27.
- **The deflated Sharpe on real data.** It is blank (`too_few_trials`) with 1 specification in the log. The formula is tested on the hand case.
- **The reviewer's 90.7% signal share** (E4).

## Open questions

- **O-43 Columns of `strategy_stats.csv` and the statistics conventions.**
  - (a) As built: the columns in E5. Every statistic but the Sharpe ratio uses raw monthly returns. The deflated Sharpe sits on the `timed_put` row, from the table's skew and excess kurtosis + 3, with ddof 1 on the trial variance. The cost comes off that month's return. A rerun of the same spec updates its row in place.
  - (b) Statistics on excess returns, the deflated Sharpe in its own table, the cost as (1 + r)(1 − c) − 1, and every run appended to the spec log.

  Implemented as (a).
- **O-44 The live straddles.**
  - (a) As built: opened and marked at the SSVI value, spot delta D (F/S)(2N(d1) − 1), hedged in the index with no financing, strikes from the IV table, ties to the shorter expiry and the lower strike.
  - (b) Opened at market mids, Black-76 forward delta hedged with the future, and cash financed at r.

  Implemented as (a).

## Files changed

- `scripts/pull_data.py`: `adj_close.parquet` in the prices stage.
- `volsurf/correlation.py`: `window_returns`, `realised_vol` and `realised_side`. `live_implied_corr` takes the adjusted closes and fills the realised side once a window completes.
- `volsurf/vrp.py`: new.
- `scripts/run_all.py`: `[density]` in `surface_key`; adjusted closes in `stage_live_corr`; the `vrp` and `strategies` stages and the 3 Section 8 figures.
- `tests/test_vrp.py`: new. Also `tests/test_correlation.py`, `tests/test_pull_data.py` and `tests/test_surface_run.py`.
- `data/raw/prices/adj_close.parquet` (new), `sectors.parquet`, the 7 Cboe files and `MANIFEST.json`.
- `outputs/tables/vrp_monthly.csv`, `strategies.csv`, `strategy_stats.csv`, `spec_log.csv` and `live_straddles.csv` (new), and `cor3m_study.csv`.
- For the new day (wrap-up commit): `data/raw/snapshot_manifest.csv`, `capture_health.csv`, `iv_summary.csv`, `svi_fits.csv`, `surface_daily.csv`, `calendar_violations.csv`, `ssvi_theta.csv`, `density_checks.csv`, `tail_probs.csv`, `events.csv`, `implied_corr_live.csv`, `rv_screen.csv` and `live_straddles.csv`.
- `decisions/section_7_review.md` (new), and `decisions/OPEN.md` (O-40 to O-42 decided, O-43 and O-44 added).

### Figures, by path

- `outputs/figures/vrp_vix2_vs_rv.png` (new): IV, forward RV and the GARCH forecast at each month end, log scale.
- `outputs/figures/vrp_cumulative.png` (new): cumulative excess return over T-bills of the 4 strategies, log scale, with BXM from 2002 dashed as a separate window (O-28 (a)).
- `outputs/figures/vrp_drawdowns.png` (new).
- `outputs/figures/cor3m_vs_realised.png`: redrawn on the re-pulled sector closes.
- `outputs/figures/spx_smiles_2026-11-03.png` (new), and `spx_density_last.png`, `spx_metrics.png` and `spx_surface_last.png`: redrawn with the new last day 2026-11-03.
- `outputs/figures/event_scatter.png`, `event_term_structures.png`, `spx_smile_fits_2026-10-28.png`, `spx_smiles_2026-10-28.png`, `spx_smiles_2026-10-29.png` and `spx_smiles_2026-10-30.png`: unchanged.

## Reviewer reads

1. E5 and E6 (the strategy table, and the Cboe refresh behind the 3 misses).
2. E4 (VRP_MONTHLY against the reviewer, and the 90.7% not reproduced).
3. `volsurf/vrp.py`: `strategy_returns`, `deflated_sharpe` and `live_straddles`.
4. O-43 and O-44 in `decisions/OPEN.md`.
5. E1, `test_realised_side_known_panel`, and `realised_side` in `volsurf/correlation.py`.
