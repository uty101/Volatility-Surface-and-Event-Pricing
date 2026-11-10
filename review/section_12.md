# Review: Section 12

## Section

Section 12: specification family for question 4, and results refresh (`instructions/12_results_refresh.md`, steps 12.1 and 12.2). It is not a `PLAN.md` section; instruction 12 adds it after the 11 sections were approved.

Both steps are complete. The timed PUT now sits in a closed family of 5 specifications. Its deflated Sharpe on excess returns is 0.994, and the deflated Sharpe of its gain over PUT is 0.412 (N = 5 trials, 237 months), both equal to the reviewer's to 3 decimals. The refresh takes the tables to 7 capture days, 2026-10-28 to 2026-11-06, and question 3 to N = 11 completed events. Fresh clone: `4747 passed`.

3 things the reviewer should know first:

- **A capture day came in after the refresh.** 2026-11-09 reached the release while the rebuild ran, and is in no table here. A plain second `run_all.py` would have pulled it and then refitted every day, so the second run ran every stage but `snapshots`, over the same local data. See E7.
- **Session 11 priced every capture day on stale rates.** The FRED files it committed ended on 2026-10-26. The refresh appended later rows, which moved every day's rates, IVs and surface cache keys. That is why session 11's numbers move slightly, for example XOM's ratio from 0.88 to 0.89. See E6.
- **"The other 4 rules did worse than PUT" holds on timed minus PUT only.** On excess return 3 of the 4 have a Sharpe above PUT's 0.555. See E2.

## Steps completed

- 12.1  2f0c362  step 12.1: specification family and deflated Sharpe for question 4
- 12.2  1ee2a70  step 12.2: refresh to the latest close and capture day
- The wrap-up commit holds this file and the status file. Part A's `decisions/section_11_review.md` is in `2f0c362`, which also marks O-50 to O-55 decided.

## Evidence

### E1. Step 12.1: `spec_log.csv`

```
                run_utc             spec_id                                                                                                                                                                                          description                                                                                                                                                                                                               params_json    sharpe  n_months
0  2026-11-03T19:23:55Z      timed_put_main               timed PUT: hold Cboe PUT in month m+1 if (VIX/100)^2 minus the GARCH(1,1) 21-session forecast at month end m is above 0, else T-bills; switch cost on every change, the first included                         {"garch_min_obs": 1000, "horizon": 21, "signal": "iv_minus_garch", "strategy_start": "2007-01-31", "switch_cost_bp": 10, "tbill": "DTB3 on the last session of month m / 1200", "threshold": 0.0}  0.802559       237
1  2026-11-05T23:19:11Z       iv_minus_rv21    timed PUT: (VIX/100)^2 minus 252/21 x the sum of r^2 over the 21 sessions ending at m; hold Cboe PUT in month m+1 if it is above 0, else T-bills; switch cost on every change, the first included                                                    {"signal": "iv_minus_rv", "strategy_start": "2007-01-31", "switch_cost_bp": 10, "tbill": "DTB3 on the last session of month m / 1200", "threshold": 0.0, "window": 21}  0.624357       237
2  2026-11-05T23:19:11Z       iv_minus_rv63    timed PUT: (VIX/100)^2 minus 252/63 x the sum of r^2 over the 63 sessions ending at m; hold Cboe PUT in month m+1 if it is above 0, else T-bills; switch cost on every change, the first included                                                    {"signal": "iv_minus_rv", "strategy_start": "2007-01-31", "switch_cost_bp": 10, "tbill": "DTB3 on the last session of month m / 1200", "threshold": 0.0, "window": 63}  0.438769       237
3  2026-11-05T23:19:11Z       iv_minus_ewma                       timed PUT: (VIX/100)^2 minus 252 x the EWMA of r^2 from 1990-01-02; hold Cboe PUT in month m+1 if it is above 0, else T-bills; switch cost on every change, the first included                                {"adjust": false, "alpha": 0.06, "signal": "iv_minus_ewma", "strategy_start": "2007-01-31", "switch_cost_bp": 10, "tbill": "DTB3 on the last session of month m / 1200", "threshold": 0.0}  0.661870       237
4  2026-11-05T23:19:11Z  garch_above_median  timed PUT: the main signal minus its expanding median over month ends strictly before m; hold Cboe PUT in month m+1 if it is above 0, else T-bills; switch cost on every change, the first included  {"garch_min_obs": 1000, "horizon": 21, "signal": "iv_minus_garch_minus_expanding_median", "strategy_start": "2007-01-31", "switch_cost_bp": 10, "tbill": "DTB3 on the last session of month m / 1200", "threshold": 0.0}  0.587993       237
```

Row 0 is the session 6 row, kept: the main specification's `params_json` is unchanged, so `append_spec` does not add it again. Rows 1 to 4 are the new specifications.

### E2. Step 12.1: the family against the reviewer's run

Annualised Sharpes, before the refresh (`2f0c362`). Every gap is below 0.0005, so they match to 3 decimals.

```
              spec_id  reviewer_excess  ours_excess  gap_excess  reviewer_minus_put  ours_minus_put  gap_minus_put
0      timed_put_main            0.803     0.802559   -0.000441               0.240        0.240401       0.000401
1       iv_minus_rv21            0.624     0.624357    0.000357              -0.051       -0.051126      -0.000126
2       iv_minus_rv63            0.439     0.438769   -0.000231              -0.403       -0.402828       0.000172
3       iv_minus_ewma            0.662     0.661870   -0.000130              -0.003       -0.002940       0.000060
4  garch_above_median            0.588     0.587993   -0.000007              -0.158       -0.158444      -0.000444
```

PUT on excess has a Sharpe of 0.555359, so `iv_minus_rv21`, `iv_minus_ewma` and `garch_above_median` beat it on excess return and lose to it only on timed minus PUT.

### E3. Step 12.1: the 2 deflated Sharpes and their inputs

`outputs/tables/spec_family.csv` in full:

```
             series             spec_id  n_months    sharpe  sharpe_monthly      skew  kurt_pearson  n_trials    sr_var       sr0  deflated_sharpe  psr_zero
0            excess      timed_put_main       237  0.802559        0.231679 -0.971720      8.419778       5.0  0.001436  0.045190         0.993597  0.999007
1            excess       iv_minus_rv21       237  0.624357        0.180236 -0.887829      8.268730       NaN       NaN       NaN              NaN  0.993925
2            excess       iv_minus_rv63       237  0.438769        0.126662 -1.802849     12.599191       NaN       NaN       NaN              NaN  0.957585
3            excess       iv_minus_ewma       237  0.661870        0.191065 -0.921908      8.612228       NaN       NaN       NaN              NaN  0.995730
4            excess  garch_above_median       237  0.587993        0.169739 -0.767861     11.253131       NaN       NaN       NaN              NaN  0.991255
5            excess                 put       237  0.555359        0.160318 -1.638352     10.279254       NaN       NaN       NaN              NaN  0.983895
6   timed_minus_put      timed_put_main       237  0.240401        0.069398  6.958220     72.162949       5.0  0.004577  0.080679         0.411681  0.915146
7   timed_minus_put       iv_minus_rv21       237 -0.051126       -0.014759  6.156491     64.706805       NaN       NaN       NaN              NaN  0.414207
8   timed_minus_put       iv_minus_rv63       237 -0.402828       -0.116286 -0.033043     14.952447       NaN       NaN       NaN              NaN  0.040151
9   timed_minus_put       iv_minus_ewma       237 -0.002940       -0.000849  5.792598     59.509211       NaN       NaN       NaN              NaN  0.494812
10  timed_minus_put  garch_above_median       237 -0.158444       -0.045739  4.092218     33.169809       NaN       NaN       NaN              NaN  0.260968
```

The 2 rows with N = 5, against the reviewer's figures:

```
            series         spec_id  n_months    sharpe  sharpe_monthly     skew  kurt_pearson  n_trials    sr_var       sr0  deflated_sharpe  psr_zero              reviewer
0           excess  timed_put_main       237  0.802559        0.231679 -0.97172      8.419778       5.0  0.001436  0.045190         0.993597  0.999007             DSR 0.994
6  timed_minus_put  timed_put_main       237  0.240401        0.069398  6.95822     72.162949       5.0  0.004577  0.080679         0.411681  0.915146  DSR 0.412, PSR 0.915
```

- `sharpe_monthly` is the monthly Sharpe of the series tested; `skew` is pandas' bias-corrected skew and `kurt_pearson` is non-excess kurtosis, both of that series.
- `sr_var` is the variance of the 5 monthly Sharpes in that series, and `sr0` is the expected maximum Sharpe of 5 trials at that variance.
- `deflated_sharpe` is the probabilistic Sharpe at `sr0`; `psr_zero` is the probabilistic Sharpe at 0.
- The refresh leaves the table unchanged: `spec_family.csv` at `1ee2a70` equals it at `2f0c362`: True. The window ends on 2026-10-30 either way.

### E4. Step 12.1: question 4's new answer rows

```
                                                                                                                                                                                                                                                  answer      value        source_table                                               source_row    source_column
38                                                                                                                                                      PUT alone has a probabilistic Sharpe of 0.984 against 0 over 237 months, so it very likely pays.   0.983895     spec_family.csv                                series=excess;spec_id=put         psr_zero
39                                                                                                                                          Timing on implied minus GARCH variance gives a raw Sharpe of 0.80 over 237 months, after the switching cost.   0.802559  strategy_stats.csv                                       strategy=timed_put           sharpe
40                                                                                                                        Its deflated Sharpe on excess returns over T-bills is 0.994 (N = 5 trials, 237 months), so the timed PUT very likely pays too.   0.993597  strategy_stats.csv                                       strategy=timed_put  deflated_sharpe
41                                                                                                                                                                                                              The number of specifications tried is 5.   5.000000        spec_log.csv                                                      all         count(*)
42  Whether timing improves on selling puts is a question about the monthly series timed minus PUT. On its own the GARCH rule looks better: that series has an annualised Sharpe of 0.240 and a probabilistic Sharpe of 0.915 against 0 over 237 months.   0.915146     spec_family.csv            series=timed_minus_put;spec_id=timed_put_main         psr_zero
43                                                                                               After counting the 5 rules tried, its deflated Sharpe is 0.412 (N = 5 trials, 237 months), so its gain over holding PUT cannot be told apart from luck.   0.411681     spec_family.csv            series=timed_minus_put;spec_id=timed_put_main  deflated_sharpe
44                              4 of the other 4 rules did worse than PUT, with a negative annualised Sharpe of timed minus PUT: iv_minus_rv21 -0.051, iv_minus_rv63 -0.403, iv_minus_ewma -0.003, garch_above_median -0.158 (N = 5 trials, 237 months).   4.000000     spec_family.csv  series=timed_minus_put;spec_id!=timed_put_main;sharpe<0         count(*)
45                                                                                                                                                                                               The raw gain over PUT comes from sitting out 27 months.  27.000000     vrp_monthly.csv    month_end>=2007-01-31;month_end<=2026-09-30;signal<=0         count(*)
```

Question 4 at `1ee2a70` equals it at `2f0c362`: True.

### E5. Step 12.2: the capture window

```
capture days: 7, 2026-10-28 to 2026-11-06 (the fixture day and 6 in the release)
```

`capture_health.csv`:

```
      session   runner  start_ny                          ny_start  minutes_after_1530  tickers_ok     rows  after_close_rows    gap
0  2026-10-28      NaN       NaN                               NaN                 NaN         NaN      NaN               NaN   True
1  2026-10-29  actions  15:30:00  2026-10-29T15:30:00.597894-04:00            0.009965        37.0  83293.0               0.0  False
2  2026-10-30  actions  15:55:48  2026-10-30T15:55:48.161205-04:00           25.802687        37.0  76611.0           17522.0  False
3  2026-11-02      NaN       NaN                               NaN                 NaN         NaN      NaN               NaN   True
4  2026-11-03  actions  15:30:00  2026-11-03T15:30:00.729543-05:00            0.012159        37.0  84673.0               0.0  False
5  2026-11-04  actions  15:30:00  2026-11-04T15:30:00.762509-05:00            0.012708        37.0  82316.0               0.0  False
6  2026-11-05  actions  15:30:01  2026-11-05T15:30:01.174377-05:00            0.019573        37.0  81858.0               0.0  False
7  2026-11-06  actions  15:30:01  2026-11-06T15:30:01.187476-05:00            0.019791        37.0  75759.0               0.0  False
```

Prices and Cboe end on 2026-11-06, FRED on 2026-11-05.

### E6. Step 12.2: EVENTS against session 11

```
                 session_11  session_12
status                                 
pending                  38          35
ok                        4          11
no_pre_snapshot           3           3
unknown                   1           1
total                    46          50
```

Newly completed, 7 events:

```
   ticker  event_date timing pre_snap_date  straddle_move   ts_move  realised_move     ratio status_s11
7    AAPL  2026-11-02    AMC    2026-10-30       0.045634  0.040320       0.019159  0.475159    pending
8    PLTR  2026-11-02    AMC    2026-10-30       0.143523  0.117739       0.016623  0.141183    pending
9     AMD  2026-11-03    AMC    2026-11-03       0.094727  0.077636       0.010034  0.129246    pending
10   SHOP  2026-11-03    BMO    2026-10-30       0.149652  0.124895       0.091432  0.732073    pending
11   UBER  2026-11-04    BMO    2026-11-03       0.073775  0.069023       0.047932  0.694438    pending
12   ABNB  2026-11-05    AMC    2026-11-05       0.110290  0.099962       0.110409  1.104502    pending
13   ^SPX  2026-11-06    NFP    2026-11-05       0.022450  0.017822       0.003140  0.176212    pending
```

New to the calendar, all pending:

```
   ticker  event_date timing   status
44    AMD  2027-02-02    AMC  pending
46   UBER  2027-02-03    BMO  pending
48   SHOP  2027-02-10    BMO  pending
49   ABNB  2027-02-11    AMC  pending
```

Session 11's 4 completed events, on the refreshed rates:

```
  ticker  event_date  ts_move_s11  ts_move_s12  ratio_s11  ratio_s12
0   AMZN  2026-10-29     0.083241     0.083242   0.170720   0.170718
1   INTC  2026-10-29     0.085143     0.085148   3.952634   3.952400
2    CVX  2026-10-30     0.023420     0.023419   0.742469   0.742492
3    XOM  2026-10-30     0.024158     0.024020   0.884801   0.889904
```

Question 3's new N:

```
                                                                                                                                                  answer  value       source_table source_row source_column
18  With N = 11 completed events, fewer than the 20 the summary needs, the gap between implied and realised moves cannot be told apart from 0 at this N.   11.0  event_summary.csv  scope=all             n
```

### E7. Step 12.2: `git status` after the second run

The second run ran these stages one at a time with `--stage`, every stage but `snapshots`:

```
capture_health pricer_check eep clean_log iv_tree iv surface density tails events cor3m live_corr vrp strategies attribution risk report answers readme
```

All exited 0. `data/snapshots/` still ended at 2026-11-06 when it started. Then, captured after the push of `1ee2a70` (before the push it read the same, with the branch 2 commits ahead):

```
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

Why not `snapshots`: the release gained `chains_2026-11-09.parquet` after the refresh. With it the second run would have rebuilt every table on a day that has no prices, and the surface stage would have refitted every day, as it did in run A (74,117 s), because the refresh moved the rates.

### E8. Step 12.2: the risk breach

```
          day underlying       measure          value    limit  breach status  left_out
0  2026-11-06       ^SPX  dollar_delta   15207.140250  2000000   False     ok         0
1  2026-11-06       ^SPX  dollar_gamma -918439.563200   250000    True     ok         0
2  2026-11-06       ^SPX       vega_pt  -12940.382910    50000   False     ok         0
3  2026-11-06       AAPL  dollar_delta  331070.657500  2000000   False     ok         0
4  2026-11-06       AAPL  dollar_gamma   25760.469410   250000   False     ok         0
5  2026-11-06       AAPL       vega_pt    1190.847330    50000   False     ok         0
6  2026-11-06       NVDA  dollar_delta   84063.069990  2000000   False     ok         0
7  2026-11-06       NVDA  dollar_gamma   -5316.832505   250000   False     ok         0
8  2026-11-06       NVDA       vega_pt    -339.919237    50000   False     ok         0
```

The README sentence keeps the sign, as Part A asks, but its value is now the last day's: "dollar gamma of −918,440 against a limit of 250,000". The −1,003,799 in Part A was 2026-11-03's.

### E9. Step 12.2: answer rows that changed

`left_only` is `2f0c362`, `right_only` is `1ee2a70`.

```
    question                                                                                                                                                                                                                                    answer         value      _merge
2          1                                                                                                                               Early exercise premium on AAPL near the money puts: median 0.15 vol points (N = 47 contracts, fixture day).  1.547601e-01  right_only
3          1                                                                                                                               Early exercise premium on AAPL near the money puts: median 0.16 vol points (N = 47 contracts, fixture day).  1.551960e-01   left_only
4          1                                                                                                                               Early exercise premium on SPY near the money puts: median 0.22 vol points (N = 496 contracts, fixture day).  2.164461e-01  right_only
5          1                                                                                                                               Early exercise premium on SPY near the money puts: median 0.22 vol points (N = 496 contracts, fixture day).  2.168924e-01   left_only
6          1                                                                                                                                                      It grows on AAPL deep in the money puts: median 4.79 vol points (N = 109 contracts).  4.792174e+00   left_only
7          1                                                                                                                                                      It grows on AAPL deep in the money puts: median 4.79 vol points (N = 109 contracts).  4.793599e+00  right_only
8          1                                                                                                                                                        It grows on SPY deep in the money puts: median 1.39 vol points (N = 44 contracts).  1.392394e+00  right_only
9          1                                                                                                                                                        It grows on SPY deep in the money puts: median 1.39 vol points (N = 44 contracts).  1.394652e+00   left_only
10         1       On calls it is 0 to rounding: the largest median in any SPY or AAPL call bin is 7.7e-12 vol points. The single names captured later have no premium table, because the step runs on the fixture day, which holds SPY and AAPL only.  7.685519e-12   left_only
11         1       On calls it is 0 to rounding: the largest median in any SPY or AAPL call bin is 8.4e-12 vol points. The single names captured later have no premium table, because the step runs on the fixture day, which holds SPY and AAPL only.  8.361367e-12  right_only
14         2                                                      Across every underlying it is 41 of 1436 pairs. Slices are not refitted for this; SSVI is the calendar-consistent surface, because its theta is non-decreasing in T by construction.  4.100000e+01   left_only
15         2                                                      Across every underlying it is 78 of 2781 pairs. Slices are not refitted for this; SSVI is the calendar-consistent surface, because its theta is non-decreasing in T by construction.  7.800000e+01  right_only
16         2                                                                                        Butterfly: 1550 of 1683 SVI slices across every underlying and day are accepted; the rest are rejected or have too few quotes to fit (N = 4 days).  1.550000e+03   left_only
17         2                                                                                        Butterfly: 3006 of 3275 SVI slices across every underlying and day are accepted; the rest are rejected or have too few quotes to fit (N = 7 days).  3.006000e+03  right_only
18         2                                                                                          Calendar: the per-expiry slices are not fully clean. 13 of 134 consecutive ^SPX pairs cross somewhere on their shared quoted range (N = 4 days).  1.300000e+01   left_only
19         2                                                                                          Calendar: the per-expiry slices are not fully clean. 29 of 225 consecutive ^SPX pairs cross somewhere on their shared quoted range (N = 7 days).  2.900000e+01  right_only
20         2                                                                                       Every accepted slice is free of butterfly arbitrage up to the check's tolerance: the smallest g on the acceptance grid is -9.5e-11, against -1e-10. -9.462312e-11   left_only
21         2                                                                                       Every accepted slice is free of butterfly arbitrage up to the check's tolerance: the smallest g on the acceptance grid is -9.6e-11, against -1e-10. -9.615574e-11  right_only
22         2                                                                                                                                                                               It was 16.28% on 2026-11-03, after the 2026-10-30 sell-off.  1.628415e-01   left_only
23         2                                                                                                                                                                It was 18.08% on 2026-11-06, after sell-offs on 2026-10-30 and 2026-11-05.  1.807626e-01  right_only
24         2                                                                                SSVI pays for that in fit: its ^SPX RMSE was 3.16 vol points on 2026-11-03, because 1 rho cannot hold the skew, so the daily metrics come from the slices.  3.164805e-02   left_only
25         2                                                                                SSVI pays for that in fit: its ^SPX RMSE was 3.48 vol points on 2026-11-06, because 1 rho cannot hold the skew, so the daily metrics come from the slices.  3.478748e-02  right_only
26         2                                                                                                                                    The 30-day 25-delta risk reversal went from -4.16 to -5.37 vol points, so skew steepened (N = 4 days). -5.372399e-02   left_only
27         2                                                                                                                                    The 30-day 25-delta risk reversal went from -4.16 to -7.14 vol points, so skew steepened (N = 7 days). -7.136426e-02  right_only
28         2                                                                                                    The term slope, ATM 90 days minus 30 days, went from 1.02 to -0.40 vol points, so the short end moved above the long end (N = 4 days). -4.027883e-03   left_only
29         2                                                                                                    The term slope, ATM 90 days minus 30 days, went from 1.02 to -0.79 vol points, so the short end moved above the long end (N = 7 days). -7.895489e-03  right_only
30         2                                                                                                                                                                        ^SPX 30-day ATM vol was 13.44% on 2026-10-28 (N = 4 capture days).  1.344428e-01   left_only
31         2                                                                                                                                                                        ^SPX 30-day ATM vol was 13.44% on 2026-10-28 (N = 7 capture days).  1.344412e-01  right_only
33         3                                                                                                                                                 35 more events have a window that ends after the last close in the data and stay pending.  3.500000e+01  right_only
34         3                                                                                                                                                 38 more events have a window that ends after the last close in the data and stay pending.  3.800000e+01   left_only
35         3                                                                                                                      AAPL AMC 2026-11-02: realised 1.92% against a term structure move of 4.03% and a straddle move of 4.56%, ratio 0.48.  4.751588e-01  right_only
36         3                                                                                                                   ABNB AMC 2026-11-05: realised 11.04% against a term structure move of 10.00% and a straddle move of 11.03%, ratio 1.10.  1.104502e+00  right_only
37         3                                                                                                                       AMD AMC 2026-11-03: realised 1.00% against a term structure move of 7.76% and a straddle move of 9.47%, ratio 0.13.  1.292463e-01  right_only
38         3                                                                                                                      AMZN AMC 2026-10-29: realised 1.42% against a term structure move of 8.32% and a straddle move of 8.59%, ratio 0.17.  1.707180e-01  right_only
39         3                                                                                                                      AMZN AMC 2026-10-29: realised 1.42% against a term structure move of 8.32% and a straddle move of 8.59%, ratio 0.17.  1.707198e-01   left_only
40         3                                                                                                                       CVX BMO 2026-10-30: realised 1.74% against a term structure move of 2.34% and a straddle move of 2.43%, ratio 0.74.  7.424694e-01   left_only
41         3                                                                                                                       CVX BMO 2026-10-30: realised 1.74% against a term structure move of 2.34% and a straddle move of 2.43%, ratio 0.74.  7.424916e-01  right_only
42         3                                                                                                                    INTC AMC 2026-10-29: realised 33.65% against a term structure move of 8.51% and a straddle move of 10.48%, ratio 3.95.  3.952400e+00  right_only
43         3                                                                                                                    INTC AMC 2026-10-29: realised 33.65% against a term structure move of 8.51% and a straddle move of 10.48%, ratio 3.95.  3.952634e+00   left_only
44         3                                                                                                                    PLTR AMC 2026-11-02: realised 1.66% against a term structure move of 11.77% and a straddle move of 14.35%, ratio 0.14.  1.411832e-01  right_only
45         3                                                                                                                    SHOP BMO 2026-11-03: realised 9.14% against a term structure move of 12.49% and a straddle move of 14.97%, ratio 0.73.  7.320734e-01  right_only
46         3                                                                                                                      UBER BMO 2026-11-04: realised 4.79% against a term structure move of 6.90% and a straddle move of 7.38%, ratio 0.69.  6.944381e-01  right_only
47         3                                                                                      With N = 11 completed events, fewer than the 20 the summary needs, the gap between implied and realised moves cannot be told apart from 0 at this N.  1.100000e+01  right_only
48         3                                                                                       With N = 4 completed events, fewer than the 20 the summary needs, the gap between implied and realised moves cannot be told apart from 0 at this N.  4.000000e+00   left_only
49         3                                                                                                                       XOM BMO 2026-10-30: realised 2.14% against a term structure move of 2.40% and a straddle move of 2.39%, ratio 0.89.  8.899037e-01  right_only
50         3                                                                                                                       XOM BMO 2026-10-30: realised 2.14% against a term structure move of 2.42% and a straddle move of 2.39%, ratio 0.88.  8.848006e-01   left_only
51         3                                                                                                                      ^SPX NFP 2026-11-06: realised 0.31% against a term structure move of 1.78% and a straddle move of 2.24%, ratio 0.18.  1.762125e-01  right_only
66         5                                                                       It rose from 0.331 on 2026-10-29 to 0.565 on 2026-10-30, when the S&P 500 fell 1.8% and XLK 4.9%. Implied correlation rising in a sell-off is the textbook pattern.  5.648914e-01   left_only
67         5                                                                       It rose from 0.331 on 2026-10-29 to 0.565 on 2026-10-30, when the S&P 500 fell 1.8% and XLK 4.9%. Implied correlation rising in a sell-off is the textbook pattern.  5.651227e-01  right_only
68         5                                                                                                              R² is 0.437, so COR3M accounts for a bit under half of the variation in next quarter's realised correlation (N = 5163 days).  4.373451e-01   left_only
69         5                                                                                                              R² is 0.439, so COR3M accounts for a bit under half of the variation in next quarter's realised correlation (N = 5167 days).  4.387697e-01  right_only
70         5                                                                                                 The XLK chain priced an implied correlation of 0.496 on 2026-11-03, with 15 names covering 72.0% of the weight (N = 3 days with a value).  4.959847e-01   left_only
71         5                                                                                                 The XLK chain priced an implied correlation of 0.497 on 2026-11-06, with 15 names covering 72.0% of the weight (N = 6 days with a value).  4.970752e-01  right_only
72         5  The mean gap, implied minus realised, is -0.167. COR3M covers single stocks and this proxy uses sector ETFs, which correlate with each other more, so implied sits below realised; the gap is the proxy, not a correlation risk premium. -1.671848e-01   left_only
73         5  The mean gap, implied minus realised, is -0.167. COR3M covers single stocks and this proxy uses sector ETFs, which correlate with each other more, so implied sits below realised; the gap is the proxy, not a correlation risk premium. -1.671231e-01  right_only
74         5                                                                                          Yes, in part. Regressing the next 63 sessions' realised sector correlation on COR3M gives a slope of 0.711 (Newey-West se 0.074), N = 5163 days.  7.114594e-01   left_only
75         5                                                                                          Yes, in part. Regressing the next 63 sessions' realised sector correlation on COR3M gives a slope of 0.713 (Newey-West se 0.074), N = 5167 days.  7.129958e-01  right_only
76         6                                                                                                               Delta and the hedge cancel and vanna and volga are small, so the delta-hedged P&L summed to -631.17 over the same 21 moves. -6.311728e+02  right_only
77         6                                                                                                                  Delta and the hedge cancel and vanna and volga are small, so the delta-hedged P&L summed to -9.92 over the same 6 moves. -9.921593e+00   left_only
78         6                                                                                                                                                              Gamma summed to -58.35 index points per straddle unit over the 6 live moves. -5.834575e+01   left_only
79         6                                                                                                                                                            Gamma summed to -852.57 index points per straddle unit over the 21 live moves. -8.525663e+02  right_only
84         6                                                                                                              On the live delta-hedged ^SPX straddles the median explained share is 0.931 (N = 21 position moves, a method demonstration).  9.307232e-01  right_only
85         6                                                                                                               On the live delta-hedged ^SPX straddles the median explained share is 0.977 (N = 6 position moves, a method demonstration).  9.767115e-01   left_only
86         6                                                                                                                                                         The residual summed to 4.19 index points per straddle unit over the 6 live moves.  4.190211e+00   left_only
87         6                                                                                                                                                       The residual summed to 94.39 index points per straddle unit over the 21 live moves.  9.439495e+01  right_only
89         6                                                                                                                                                             Theta summed to 116.67 index points per straddle unit over the 21 live moves.  1.166659e+02  right_only
90         6                                                                                                                                                               Theta summed to 59.76 index points per straddle unit over the 6 live moves.  5.975668e+01   left_only
91         6                                                                                                                                                               Vega summed to -17.37 index points per straddle unit over the 6 live moves. -1.737408e+01   left_only
92         6                                                                                                                                                               Vega summed to -6.25 index points per straddle unit over the 21 live moves. -6.245096e+00  right_only
```

2 of these are prose I rewrote, because the new days made them false: question 2's "after the 2026-10-30 sell-off" (vol fell back to 13.22% on 2026-11-04 and jumped again on 2026-11-05), and the template's "ATM vol jumped on 2026-10-30 and stayed up".

### E10. Step 12.2: the README diff

`2f0c362` to `1ee2a70`. `README.md` is now 15,226 bytes, against the test's 15,360.

```diff
diff --git a/README.md b/README.md
index 9a1e76f..cdcd55a 100644
--- a/README.md
+++ b/README.md
@@ -6,9 +6,9 @@ Tests the volatility risk premium on S&P 500 history from 1990 and implied again
 Splits delta-hedged option P&L into Greeks and builds a 1-page daily risk report.
 Option chains are captured daily from 2026-10-28, so every live result is a method demonstration with its N stated.
 
-Results are in [`outputs/`](outputs/). [![ci](https://github.com/uty101/Volatility-Surface-and-Event-Pricing/actions/workflows/ci.yml/badge.svg)](https://github.com/uty101/Volatility-Surface-and-Event-Pricing/actions/workflows/ci.yml) 4,740 tests.
+Results are in [`outputs/`](outputs/). [![ci](https://github.com/uty101/Volatility-Surface-and-Event-Pricing/actions/workflows/ci.yml/badge.svg)](https://github.com/uty101/Volatility-Surface-and-Event-Pricing/actions/workflows/ci.yml) 4,747 tests.
 
-**Capture window:** 2026-10-28 to 2026-11-03, 4 days, 2026-11-02 missed. The first day holds `^SPX`, SPY and AAPL only, from an in-session test capture. The others hold all 37 underlyings.
+**Capture window:** 2026-10-28 to 2026-11-06, 7 days, 2026-11-02 missed. The first day holds `^SPX`, SPY and AAPL only, from an in-session test capture. The others hold all 37 underlyings.
 
 ## Run it
 
@@ -24,24 +24,27 @@ pytest -p socket --disable-socket -q
 
 ## 1. Does the pricer match QuantLib?
 
-Yes. BSM matches QuantLib's analytic engine: the largest price gap is 3.9e-14 over 252 grid cases, against a bound of 1e-10. Black-76 equals BSM once S e^(−qT) = D F: the largest gap is 5.0e-14 over 252 cases. The American CRR tree at 2000 steps matches QuantLib's CRR engine: the largest gap is 6.8e-05 x S over 252 cases, against a bound of 1e-4 x S. Delta, gamma, vega, theta and rho match QuantLib: the largest gap is 4.4e-13 over 252 cases each, against a bound of 1e-8. Early exercise premium on SPY near the money puts: median 0.22 vol points (N = 496 contracts, fixture day). It grows on SPY deep in the money puts: median 1.39 vol points (N = 44 contracts). Early exercise premium on AAPL near the money puts: median 0.16 vol points (N = 47 contracts, fixture day). It grows on AAPL deep in the money puts: median 4.79 vol points (N = 109 contracts). On calls it is 0 to rounding: the largest median in any SPY or AAPL call bin is 7.7e-12 vol points. The single names captured later have no premium table, because the step runs on the fixture day, which holds SPY and AAPL only.
+Yes. BSM matches QuantLib's analytic engine: the largest price gap is 3.9e-14 over 252 grid cases, against a bound of 1e-10. Black-76 equals BSM once S e^(−qT) = D F: the largest gap is 5.0e-14 over 252 cases. The American CRR tree at 2000 steps matches QuantLib's CRR engine: the largest gap is 6.8e-05 x S over 252 cases, against a bound of 1e-4 x S. Delta, gamma, vega, theta and rho match QuantLib: the largest gap is 4.4e-13 over 252 cases each, against a bound of 1e-8. Early exercise premium on SPY near the money puts: median 0.22 vol points (N = 496 contracts, fixture day). It grows on SPY deep in the money puts: median 1.39 vol points (N = 44 contracts). Early exercise premium on AAPL near the money puts: median 0.15 vol points (N = 47 contracts, fixture day). It grows on AAPL deep in the money puts: median 4.79 vol points (N = 109 contracts). On calls it is 0 to rounding: the largest median in any SPY or AAPL call bin is 8.4e-12 vol points. The single names captured later have no premium table, because the step runs on the fixture day, which holds SPY and AAPL only.
 
 ## 2. The S&P 500 surface
 
-^SPX 30-day ATM vol was 13.44% on 2026-10-28 (N = 4 capture days). It was 16.28% on 2026-11-03, after the 2026-10-30 sell-off. The 30-day 25-delta risk reversal went from −4.16 to −5.37 vol points, so skew steepened (N = 4 days). The term slope, ATM 90 days minus 30 days, went from 1.02 to −0.40 vol points, so the short end moved above the long end (N = 4 days). Butterfly: 1550 of 1683 SVI slices across every underlying and day are accepted; the rest are rejected or have too few quotes to fit (N = 4 days). Every accepted slice is free of butterfly arbitrage up to the check's tolerance: the smallest g on the acceptance grid is −9.5e-11, against −1e-10. Calendar: the per-expiry slices are not fully clean. 13 of 134 consecutive ^SPX pairs cross somewhere on their shared quoted range (N = 4 days). Across every underlying it is 41 of 1436 pairs. Slices are not refitted for this; SSVI is the calendar-consistent surface, because its theta is non-decreasing in T by construction. SSVI pays for that in fit: its ^SPX RMSE was 3.16 vol points on 2026-11-03, because 1 rho cannot hold the skew, so the daily metrics come from the slices.
+^SPX 30-day ATM vol was 13.44% on 2026-10-28 (N = 7 capture days). It was 18.08% on 2026-11-06, after sell-offs on 2026-10-30 and 2026-11-05. The 30-day 25-delta risk reversal went from −4.16 to −7.14 vol points, so skew steepened (N = 7 days). The term slope, ATM 90 days minus 30 days, went from 1.02 to −0.79 vol points, so the short end moved above the long end (N = 7 days). Butterfly: 3006 of 3275 SVI slices across every underlying and day are accepted; the rest are rejected or have too few quotes to fit (N = 7 days). Every accepted slice is free of butterfly arbitrage up to the check's tolerance: the smallest g on the acceptance grid is −9.6e-11, against −1e-10. Calendar: the per-expiry slices are not fully clean. 29 of 225 consecutive ^SPX pairs cross somewhere on their shared quoted range (N = 7 days). Across every underlying it is 78 of 2781 pairs. Slices are not refitted for this; SSVI is the calendar-consistent surface, because its theta is non-decreasing in T by construction. SSVI pays for that in fit: its ^SPX RMSE was 3.48 vol points on 2026-11-06, because 1 rho cannot hold the skew, so the daily metrics come from the slices.
 
 | day | ATM 30d % | RR 25d, pts | BF 25d, pts | ATM 90d % | term slope, pts | expiries |
 | --- | --- | --- | --- | --- | --- | --- |
 | 2026-10-28 | 13.44 | −4.16 | 0.63 | 14.46 | 1.02 | 36 |
-| 2026-10-29 | 12.98 | −4.11 | 0.60 | 14.25 | 1.26 | 34 |
+| 2026-10-29 | 12.98 | −4.11 | 0.60 | 14.24 | 1.26 | 35 |
 | 2026-10-30 | 16.54 | −6.36 | 0.82 | 16.26 | −0.28 | 34 |
-| 2026-11-03 | 16.28 | −5.37 | 0.66 | 15.88 | −0.40 | 34 |
+| 2026-11-03 | 16.28 | −5.37 | 0.66 | 15.88 | −0.40 | 35 |
+| 2026-11-04 | 13.22 | −3.77 | 0.57 | 14.12 | 0.89 | 35 |
+| 2026-11-05 | 19.30 | −7.83 | 1.07 | 17.75 | −1.55 | 32 |
+| 2026-11-06 | 18.08 | −7.14 | 0.82 | 17.29 | −0.79 | 25 |
 
-The smile on the last day shows the skew the slices hold: the 30-day 25-delta risk reversal is −5.37 vol points.
+The smile on the last day shows the skew the slices hold: the 30-day 25-delta risk reversal is −7.14 vol points.
 
-![^SPX smiles](outputs/figures/spx_smiles_2026-11-03.png)
+![^SPX smiles](outputs/figures/spx_smiles_2026-11-06.png)
 
-ATM vol jumped on 2026-10-30 and stayed up, ending at 16.28%, with the term slope turning negative.
+ATM vol jumped on 2026-10-30, fell back on 2026-11-04 and jumped again on 2026-11-05, ending at 18.08% with the term slope negative.
 
 ![^SPX metrics](outputs/figures/spx_metrics.png)
 
@@ -51,16 +54,23 @@ The density comes straight from each slice, and the shaded band marks where quot
 
 ## 3. Earnings events
 
-With N = 4 completed events, fewer than the 20 the summary needs, the gap between implied and realised moves cannot be told apart from 0 at this N. AMZN AMC 2026-10-29: realised 1.42% against a term structure move of 8.32% and a straddle move of 8.59%, ratio 0.17. INTC AMC 2026-10-29: realised 33.65% against a term structure move of 8.51% and a straddle move of 10.48%, ratio 3.95. CVX BMO 2026-10-30: realised 1.74% against a term structure move of 2.34% and a straddle move of 2.43%, ratio 0.74. XOM BMO 2026-10-30: realised 2.14% against a term structure move of 2.42% and a straddle move of 2.39%, ratio 0.88. 38 more events have a window that ends after the last close in the data and stay pending. 3 events have no pre-event snapshot, because they fall before the capture could see them.
+With N = 11 completed events, fewer than the 20 the summary needs, the gap between implied and realised moves cannot be told apart from 0 at this N. AMZN AMC 2026-10-29: realised 1.42% against a term structure move of 8.32% and a straddle move of 8.59%, ratio 0.17. INTC AMC 2026-10-29: realised 33.65% against a term structure move of 8.51% and a straddle move of 10.48%, ratio 3.95. CVX BMO 2026-10-30: realised 1.74% against a term structure move of 2.34% and a straddle move of 2.43%, ratio 0.74. XOM BMO 2026-10-30: realised 2.14% against a term structure move of 2.40% and a straddle move of 2.39%, ratio 0.89. AAPL AMC 2026-11-02: realised 1.92% against a term structure move of 4.03% and a straddle move of 4.56%, ratio 0.48. PLTR AMC 2026-11-02: realised 1.66% against a term structure move of 11.77% and a straddle move of 14.35%, ratio 0.14. AMD AMC 2026-11-03: realised 1.00% against a term structure move of 7.76% and a straddle move of 9.47%, ratio 0.13. SHOP BMO 2026-11-03: realised 9.14% against a term structure move of 12.49% and a straddle move of 14.97%, ratio 0.73. UBER BMO 2026-11-04: realised 4.79% against a term structure move of 6.90% and a straddle move of 7.38%, ratio 0.69. ABNB AMC 2026-11-05: realised 11.04% against a term structure move of 10.00% and a straddle move of 11.03%, ratio 1.10. ^SPX NFP 2026-11-06: realised 0.31% against a term structure move of 1.78% and a straddle move of 2.24%, ratio 0.18. 35 more events have a window that ends after the last close in the data and stay pending. 3 events have no pre-event snapshot, because they fall before the capture could see them.
 
 | ticker | date | timing | straddle % | term structure % | realised % | ratio |
 | --- | --- | --- | --- | --- | --- | --- |
 | AMZN | 2026-10-29 | AMC | 8.59 | 8.32 | 1.42 | 0.17 |
 | INTC | 2026-10-29 | AMC | 10.48 | 8.51 | 33.65 | 3.95 |
 | CVX | 2026-10-30 | BMO | 2.43 | 2.34 | 1.74 | 0.74 |
-| XOM | 2026-10-30 | BMO | 2.39 | 2.42 | 2.14 | 0.88 |
+| XOM | 2026-10-30 | BMO | 2.39 | 2.40 | 2.14 | 0.89 |
+| AAPL | 2026-11-02 | AMC | 4.56 | 4.03 | 1.92 | 0.48 |
+| PLTR | 2026-11-02 | AMC | 14.35 | 11.77 | 1.66 | 0.14 |
+| AMD | 2026-11-03 | AMC | 9.47 | 7.76 | 1.00 | 0.13 |
+| SHOP | 2026-11-03 | BMO | 14.97 | 12.49 | 9.14 | 0.73 |
+| UBER | 2026-11-04 | BMO | 7.38 | 6.90 | 4.79 | 0.69 |
+| ABNB | 2026-11-05 | AMC | 11.03 | 10.00 | 11.04 | 1.10 |
+| ^SPX | 2026-11-06 | NFP | 2.24 | 1.78 | 0.31 | 0.18 |
 
-Points above the line moved more than the options priced. 4 points say nothing about the average.
+Points above the line moved more than the options priced. 11 points say nothing about the average.
 
 ![Implied against realised](outputs/figures/event_scatter.png)
 
@@ -90,25 +100,28 @@ Its worst drawdown is −20.8% against PUT's −32.7%, because it was out of the
 
 ## 5. Correlation
 
-Yes, in part. Regressing the next 63 sessions' realised sector correlation on COR3M gives a slope of 0.711 (Newey-West se 0.074), N = 5163 days. R² is 0.437, so COR3M accounts for a bit under half of the variation in next quarter's realised correlation (N = 5163 days). The mean gap, implied minus realised, is −0.167. COR3M covers single stocks and this proxy uses sector ETFs, which correlate with each other more, so implied sits below realised; the gap is the proxy, not a correlation risk premium. The XLK chain priced an implied correlation of 0.496 on 2026-11-03, with 15 names covering 72.0% of the weight (N = 3 days with a value). It rose from 0.331 on 2026-10-29 to 0.565 on 2026-10-30, when the S&P 500 fell 1.8% and XLK 4.9%. Implied correlation rising in a sell-off is the textbook pattern.
+Yes, in part. Regressing the next 63 sessions' realised sector correlation on COR3M gives a slope of 0.713 (Newey-West se 0.074), N = 5167 days. R² is 0.439, so COR3M accounts for a bit under half of the variation in next quarter's realised correlation (N = 5167 days). The mean gap, implied minus realised, is −0.167. COR3M covers single stocks and this proxy uses sector ETFs, which correlate with each other more, so implied sits below realised; the gap is the proxy, not a correlation risk premium. The XLK chain priced an implied correlation of 0.497 on 2026-11-06, with 15 names covering 72.0% of the weight (N = 6 days with a value). It rose from 0.331 on 2026-10-29 to 0.565 on 2026-10-30, when the S&P 500 fell 1.8% and XLK 4.9%. Implied correlation rising in a sell-off is the textbook pattern.
 
 | days | first | last | intercept | slope | slope se | R² |
 | --- | --- | --- | --- | --- | --- | --- |
-| 5163 | 2006-01-03 | 2026-08-04 | 0.2862 | 0.7115 | 0.0740 | 0.4373 |
+| 5167 | 2006-01-03 | 2026-08-10 | 0.2855 | 0.7130 | 0.0741 | 0.4388 |
 
 | day | XLK vol % | names | covered weight % | implied correlation |
 | --- | --- | --- | --- | --- |
-| 2026-10-29 | 25.24 | 15 | 72.0 | 0.331 |
+| 2026-10-29 | 25.25 | 15 | 72.0 | 0.331 |
 | 2026-10-30 | 33.72 | 13 | 66.1 | 0.565 |
-| 2026-11-03 | 32.18 | 15 | 72.0 | 0.496 |
+| 2026-11-03 | 32.20 | 15 | 72.0 | 0.496 |
+| 2026-11-04 | 26.25 | 15 | 72.0 | 0.331 |
+| 2026-11-05 | 39.87 | 15 | 72.0 | 0.570 |
+| 2026-11-06 | 35.88 | 15 | 72.0 | 0.497 |
 
-Implied and realised move together, with a slope of 0.711 and an R² of 0.437. The shaded gap is the sector proxy, not a premium.
+Implied and realised move together, with a slope of 0.713 and an R² of 0.439. The shaded gap is the sector proxy, not a premium.
 
 ![COR3M against realised](outputs/figures/cor3m_vs_realised.png)
 
 ## 6. P&L attribution and hedging
 
-On the live delta-hedged ^SPX straddles the median explained share is 0.977 (N = 6 position moves, a method demonstration). On a synthetic Black-Scholes path it is 0.952 (N = 21 daily steps). Gamma summed to −58.35 index points per straddle unit over the 6 live moves. Theta summed to 59.76 index points per straddle unit over the 6 live moves. Vega summed to −17.37 index points per straddle unit over the 6 live moves. The residual summed to 4.19 index points per straddle unit over the 6 live moves. Delta and the hedge cancel and vanna and volga are small, so the delta-hedged P&L summed to −9.92 over the same 6 moves. Hedging every step (k = 1) leaves an error sd of 0.241 under GBM. The same hedge leaves 0.813 under Heston: the hedge uses delta at the current vol but is blind to vol moves, so even continuous hedging leaves an unhedged vega P&L, and the error sd stops falling in proportion to the square root of k. The means are not comparable, because the 2 drifts differ. Hedging less often raises the GBM error sd to 1.763 at k = 65, 5 days between hedges. It cuts cost: the GBM mean cost falls from 0.106 at k = 1 to 0.014 at k = 65.
+On the live delta-hedged ^SPX straddles the median explained share is 0.931 (N = 21 position moves, a method demonstration). On a synthetic Black-Scholes path it is 0.952 (N = 21 daily steps). Gamma summed to −852.57 index points per straddle unit over the 21 live moves. Theta summed to 116.67 index points per straddle unit over the 21 live moves. Vega summed to −6.25 index points per straddle unit over the 21 live moves. The residual summed to 94.39 index points per straddle unit over the 21 live moves. Delta and the hedge cancel and vanna and volga are small, so the delta-hedged P&L summed to −631.17 over the same 21 moves. Hedging every step (k = 1) leaves an error sd of 0.241 under GBM. The same hedge leaves 0.813 under Heston: the hedge uses delta at the current vol but is blind to vol moves, so even continuous hedging leaves an unhedged vega P&L, and the error sd stops falling in proportion to the square root of k. The means are not comparable, because the 2 drifts differ. Hedging less often raises the GBM error sd to 1.763 at k = 65, 5 days between hedges. It cuts cost: the GBM mean cost falls from 0.106 at k = 1 to 0.014 at k = 65.
 
 | model | k | error mean | error sd | cost mean |
 | --- | --- | --- | --- | --- |
@@ -121,16 +134,16 @@ On the live delta-hedged ^SPX straddles the median explained share is 0.977 (N =
 
 ## Risk report
 
-[`outputs/reports/risk_2026-11-03.pdf`](outputs/reports/risk_2026-11-03.pdf) is the 1-page report for 2026-11-03 (N = 4 capture days). Each vol is the contract's own SVI slice at its strike.
+[`outputs/reports/risk_2026-11-06.pdf`](outputs/reports/risk_2026-11-06.pdf) is the 1-page report for 2026-11-06 (N = 7 capture days). Each vol is the contract's own SVI slice at its strike.
 
 | contract | side | contracts | vol % | vol source | dollar delta | dollar gamma 1% | vega per pt |
 | --- | --- | --- | --- | --- | --- | --- | --- |
-| ^SPX 2026-12-03 P 7300 | −1 | 10 | 19.76 | svi | 1845546 | −418425 | −6800 |
-| ^SPX 2026-12-03 C 7800 | −1 | 10 | 14.25 | svi | −1876786 | −585374 | −6862 |
-| AAPL 2027-01-15 C 335 | 1 | 20 | 24.56 | svi | 334438 | 24075 | 1186 |
-| NVDA 2026-12-18 P 193 | −1 | 15 | 46.31 | svi | 92455 | −6670 | −388 |
+| ^SPX 2026-12-04 P 7125 | −1 | 10 | 22.67 | svi | 1833746 | −372608 | −6485 |
+| ^SPX 2026-12-04 C 7650 | −1 | 10 | 15.41 | svi | −1818539 | −545831 | −6456 |
+| AAPL 2027-01-15 C 350 | 1 | 20 | 24.33 | svi | 331071 | 25760 | 1191 |
+| NVDA 2026-12-18 P 174 | −1 | 15 | 54.58 | svi | 84063 | −5317 | −340 |
 
-The worst cell of the grid loses 447.4 thousand dollars, at spot −10% and vol +5 points. 1 of 9 limits is breached: ^SPX dollar gamma of −1,003,799 against a limit of 250,000, which the short wings produce and the report is meant to show.
+The worst cell of the grid loses 418.6 thousand dollars, at spot −10% and vol +5 points. 1 of 9 limits is breached: ^SPX dollar gamma of −918,440 against a limit of 250,000, which the short wings produce and the report is meant to show.
 
 ## What this does not do
```

## Tests run

```
.venv/Scripts/python.exe -m pytest -p socket --disable-socket -q
.venv/Scripts/python.exe -m ruff check .
```

The tail, at the working tree that became `1ee2a70`:

```
  C:\Utkarsh\10. Quant Projects\7) Volatility Surface and Event Pricing\Volatility-Surface-and-Event-Pricing\.venv\Lib\site-packages\pytest_socket\__init__.py:138: UserWarning: A test tried to use socket.socket.
    raise SocketBlockedError()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
4747 passed, 35 warnings in 841.79s (0:14:01)
All checks passed!

[exited with code 0]
```

## Fresh-clone check

```
git clone <local repo> C:\vs12          (HEAD 1ee2a70)
uv venv --python 3.12
uv pip install -r requirements-lock.txt
uv pip install -e . --no-deps
.venv/Scripts/python.exe -m pytest -p socket --disable-socket -q
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
........................................................................ [ 47%]
........................................................................ [ 48%]
........................................................................ [ 50%]
........................................................................ [ 51%]
........................................................................ [ 53%]
........................................................................ [ 54%]
........................................................................ [ 56%]
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
........................................................................ [ 91%]
........................................................................ [ 92%]
........................................................................ [ 94%]
........................................................................ [ 95%]
........................................................................ [ 97%]
........................................................................ [ 98%]
...................................................................      [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:894
  C:\vs12\.venv\Lib\site-packages\_pytest\config\__init__.py:894: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

tests/test_capture_health.py: 4 warnings
tests/test_correlation.py: 4 warnings
tests/test_vrp.py: 24 warnings
  C:\vs12\.venv\Lib\site-packages\pandas\core\series.py:848: Pandas4Warning: Series.values returning an ndarray that drops timezone information for DatetimeTZDtype is deprecated. In a future version, this will return the underlying DatetimeArray instead. Use 'Series.dt.tz_convert(None).to_numpy()' to get a NumPy array of UTC values, or 'Series.array' to get the ExtensionArray.
  See https://pandas.pydata.org/docs/dev/whatsnew/v3.1.0.html#whatsnew-310-deprecations-values for more details.
    warnings.warn(

tests/test_correlation.py::test_rv_screen_blank_below_min_days
  C:\vs12\volsurf\correlation.py:205: RuntimeWarning: invalid value encountered in scalar divide
    z = (r.atm_30 - prior.mean()) / prior.std(ddof=1)  # O-15 (a): ddof 1, today excluded

tests/test_snapshots.py::test_wait_chains_when_above_max_wait
  C:\vs12\.venv\Lib\site-packages\pytest_socket\__init__.py:138: UserWarning: A test tried to use socket.socket.
    raise SocketBlockedError()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
4747 passed, 35 warnings in 2084.20s (0:34:44)
```

CI: run 42862012228 on `1ee2a70`, success, `4747 passed, 35 warnings in 337.91s (0:05:37)`.

## Runtime per step

Seconds, from each run's `runtime` lines.

```
                run 1 (superseded)  run A (committed)  second run
stage                                                            
snapshots                     19.7                4.9         NaN
capture_health                 0.6                0.8         0.5
pricer_check                  21.5               28.1        17.7
eep                          314.6              540.9       531.0
clean_log                      1.4                2.0         4.0
iv_tree                      400.6              402.4       552.0
iv                          1169.0             1727.9      2136.3
surface                   325445.3            74117.0         6.1
density                      235.3              208.6       290.4
tails                         33.5               22.5        41.2
events                        12.9                7.4        15.8
cor3m                          9.6                5.5        10.8
live_corr                      0.6                0.2         0.3
vrp                           30.4               14.7        32.6
strategies                     2.4                1.5         2.5
attribution                    2.5                1.3         1.8
risk                           1.2                0.5         0.4
report                         0.1                0.1         0.1
answers                        0.8                0.5         0.3
readme                        31.9               11.4        12.4
total                     327734.0            77098.2      3656.2
```

- **Run 1 is superseded.** It covered 6 days before 2026-11-06 reached the release. Its surface time, 325,445 s, spans a machine sleep, so it is not a fit time.
- **Run A is the run committed in `1ee2a70`.** Its surface stage refitted all 7 days in 74,117 s, because the re-pulled FRED rows changed every day's rates.
- **In the second run** the surface stage hit its cache in 6.1 s. Each stage ran as its own process, so its total is the sum of the stages.

These are measured times on a shared machine, not benchmarks; the second run shared it with the fresh-clone pytest.

## Deviations from PLAN.md

- The second run skipped the `snapshots` stage. See E7.
- The README's breach value is −918,440, not the −1,003,799 written in Part A, because the last day moved.
- `outputs/reports/risk_2026-11-03.pdf` is removed and `risk_2026-11-06.pdf` added (O-57).

## Not verified

- The family's selection: instruction 12 fixed it, but after the main specification's 0.80 was known, so N = 5 is a floor on the trials, not a count of every idea considered. The answers do not claim the family was fixed blind.
- The probabilistic and deflated Sharpes of timed minus PUT use a normal approximation on a series with skew 6.96 and kurtosis 72.2. I did not check them by bootstrap.
- I did not cross-check the ^GSPC close of 2026-11-05 (−4.4% on the day) against the captured spot.

## Open questions

- **O-56** Where the family's results live. (a) A new table `spec_family.csv`. (b) A column in `spec_log.csv` and rows in `strategy_stats.csv`. Implemented as (a).
- **O-57** Which risk reports are kept. (a) Only the last day's. (b) Every last-day report a session committed. Implemented as (a).

## Files changed

`1b089ad` to `1ee2a70`:

```
 README.md                                     |    67 +-
 data/raw/MANIFEST.json                        |   148 +-
 data/raw/cboe/BXM.csv                         |     4 +
 data/raw/cboe/COR3M.csv                       |     4 +
 data/raw/cboe/PUT.csv                         |     4 +
 data/raw/cboe/VIX.csv                         |     4 +
 data/raw/cboe/VIX3M.csv                       |     4 +
 data/raw/cboe/VIX6M.csv                       |     4 +
 data/raw/cboe/VIX9D.csv                       |     4 +
 data/raw/fred/DGS1.csv                        |     8 +
 data/raw/fred/DGS1MO.csv                      |     8 +
 data/raw/fred/DGS3MO.csv                      |     8 +
 data/raw/fred/DGS6MO.csv                      |     8 +
 data/raw/fred/DTB3.csv                        |     8 +
 data/raw/prices/adj_close.parquet             |   Bin 1761916 -> 1763141 bytes
 data/raw/prices/close.parquet                 |   Bin 1507429 -> 1508323 bytes
 data/raw/prices/index.parquet                 |   Bin 192721 -> 192783 bytes
 data/raw/prices/sectors.parquet               |   Bin 478111 -> 478513 bytes
 data/raw/snapshot_manifest.csv                |    12 +
 decisions/OPEN.md                             |    12 +
 decisions/section_11_review.md                |    11 +
 docs/METHODS.md                               |     3 +-
 docs/README.template.md                       |     8 +-
 outputs/figures/cor3m_vs_realised.png         |   Bin 174926 -> 175631 bytes
 outputs/figures/event_scatter.png             |   Bin 52894 -> 63609 bytes
 outputs/figures/event_term_structures.png     |   Bin 111662 -> 110866 bytes
 outputs/figures/spx_density_last.png          |   Bin 106028 -> 107128 bytes
 outputs/figures/spx_metrics.png               |   Bin 95803 -> 110751 bytes
 outputs/figures/spx_smile_fits_2026-10-28.png |   Bin 263503 -> 263524 bytes
 outputs/figures/spx_smiles_2026-10-28.png     |   Bin 154672 -> 154277 bytes
 outputs/figures/spx_smiles_2026-10-29.png     |   Bin 139331 -> 145029 bytes
 outputs/figures/spx_smiles_2026-10-30.png     |   Bin 171039 -> 169110 bytes
 outputs/figures/spx_smiles_2026-11-03.png     |   Bin 130863 -> 134220 bytes
 outputs/figures/spx_smiles_2026-11-04.png     |   Bin 0 -> 138766 bytes
 outputs/figures/spx_smiles_2026-11-05.png     |   Bin 0 -> 183347 bytes
 outputs/figures/spx_smiles_2026-11-06.png     |   Bin 0 -> 152247 bytes
 outputs/figures/spx_surface_last.png          |   Bin 165599 -> 175332 bytes
 outputs/reports/risk_2026-11-03.pdf           |   Bin 4766 -> 0 bytes
 outputs/reports/risk_2026-11-06.pdf           |   Bin 0 -> 4773 bytes
 outputs/tables/answers.csv                    |    77 +-
 outputs/tables/attribution_live.csv           |    27 +-
 outputs/tables/calendar_violations.csv        |  4217 +++++---
 outputs/tables/capture_health.csv             |     3 +
 outputs/tables/cor3m_study.csv                |     2 +-
 outputs/tables/density_checks.csv             |  4556 +++++---
 outputs/tables/eep_rows.csv                   | 14216 ++++++++++++-------------
 outputs/tables/eep_summary.csv                |    40 +-
 outputs/tables/event_summary.csv              |     2 +-
 outputs/tables/events.csv                     |    26 +-
 outputs/tables/implied_corr_live.csv          |     9 +-
 outputs/tables/iv_summary.csv                 |   113 +-
 outputs/tables/iv_tree_convergence.csv        |  7984 +++++++-------
 outputs/tables/limit_breaches.csv             |    18 +-
 outputs/tables/live_straddles.csv             |    38 +-
 outputs/tables/parity_forwards_fixture.csv    |    72 +-
 outputs/tables/pit.csv                        |   106 +-
 outputs/tables/risk_book.csv                  |     8 +-
 outputs/tables/risk_grid.csv                  |   450 +-
 outputs/tables/rv_screen.csv                  |   339 +-
 outputs/tables/spec_family.csv                |    12 +
 outputs/tables/spec_log.csv                   |     4 +
 outputs/tables/ssvi_theta.csv                 |  4556 +++++---
 outputs/tables/strategy_stats.csv             |     2 +-
 outputs/tables/surface_daily.csv              |   339 +-
 outputs/tables/svi_fits.csv                   |  4896 ++++++---
 outputs/tables/tail_probs.csv                 | 83260 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++-------------------------------------------------
 scripts/run_all.py                            |    61 +-
 tests/test_vrp.py                             |    83 +
 volsurf/answers.py                            |    27 +-
 volsurf/readme.py                             |     2 +-
 volsurf/vrp.py                                |    89 +-
 71 files changed, 79723 insertions(+), 46240 deletions(-)
```

## Reviewer reads

1. This file, E2 to E4 and E6.
2. `outputs/tables/spec_family.csv`.
3. `volsurf/vrp.py`: `spec_signals`, `series_moments`, `expected_max_sharpe`, `probabilistic_sharpe`, `deflated_sharpe`, `family_table`.
4. `scripts/run_all.py`: `stage_strategies`.
5. `README.md`, question 4 and question 3.
6. `instructions/12_results_refresh.status.md`.
