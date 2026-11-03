# Review: Section 6

## Section

Section 6: Event pricing (`PLAN.md` steps 6.1 and 6.2), with instruction 06. That instruction adds step 6.0, the capture fix, and step 6.0b, the O-38 (b) and O-39 (a) follow-ups to Section 5.

The section is complete. The sample is small: 4 events have a pre-event snapshot and a realised move. So the summary is descriptive only (`below_min_n`), which the instruction expects this early.

## Steps completed

- 6.0   65fc151  step 6.0: early crons and self-dispatch for the capture
- 6.0b  2ef343e  step 6.0b: kink and fd_gap density statuses, full precision parameters. It also commits the decisions in `decisions/section_5_review.md` (`## Session 5c`), `decisions/capture.md` (item 6) and `decisions/OPEN.md` (O-38 and O-39 decided), and prices re-pulled to 2026-11-02.
- 6.1   d3d4293  step 6.1: event windows, term structure and straddle moves. It includes the 2 manual files, as given.
- 6.2   5dae296  step 6.2: events table, summary and figures

## Evidence

### E1. Step 6.0: tests

`.venv\Scripts\python -m pytest -p socket --disable-socket -v -s tests/test_snapshots.py` (tail):

```
tests/test_snapshots.py::test_should_upload_more_tickers_ok PASSED
tests/test_snapshots.py::test_should_upload_tie_keeps_existing PASSED
tests/test_snapshots.py::test_should_upload_fewer_tickers_ok PASSED
tests/test_snapshots.py::test_seconds_until_target PASSED
tests/test_snapshots.py::test_already_captured PASSED
tests/test_snapshots.py::test_wait_chains_when_above_max_wait 2026-11-04T09:17:00+00:00 waiting 19800 seconds of 40380, then chaining
2026-11-04T14:47:00+00:00 chained: dispatched a new run with 20580 seconds still to wait
2026-11-04T09:17:00+00:00 waiting 19800 seconds of 40380, then chaining
2026-11-04T14:47:00+00:00 chained: dispatched a new run with 20580 seconds still to wait
PASSED
tests/test_snapshots.py::test_wait_captures_after_193_minutes 2026-11-04T17:17:00+00:00 waiting 11580 seconds until 15:30 New York
2026-11-04T17:17:00+00:00 waiting 11580 seconds until 15:30 New York
PASSED
tests/test_snapshots.py::test_wait_skips_after_the_window 2026-11-04T22:00:00+00:00 skip runner=actions ny=2026-11-04 17:00:00 wait: not a session or after the window
2026-11-04T22:00:00+00:00 skip runner=actions ny=2026-11-04 17:00:00 wait: not a session or after the window
PASSED
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:894
tests/test_snapshots.py::test_is_session
tests/test_snapshots.py::test_is_session
tests/test_snapshots.py::test_is_session
tests/test_snapshots.py::test_is_session
tests/test_snapshots.py::test_wait_chains_when_above_max_wait
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 15 passed, 6 warnings in 2.80s ========================
```

### E2. Step 6.0: `snapshot.yml` diff

```
diff --git a/.github/workflows/snapshot.yml b/.github/workflows/snapshot.yml
index a5f1f5d..580d2ef 100644
--- a/.github/workflows/snapshot.yml
+++ b/.github/workflows/snapshot.yml
@@ -2,9 +2,10 @@ name: snapshot
 
 on:
   schedule:
+    - cron: "17 9 * * 1-5"
+    - cron: "17 12 * * 1-5"
     - cron: "17 15 * * 1-5"
-    - cron: "17 17 * * 1-5"
-    - cron: "47 18 * * 1-5"
+    - cron: "17 18 * * 1-5"
   workflow_dispatch:
     inputs:
       force:
@@ -19,6 +20,7 @@ on:
 
 permissions:
   contents: write
+  actions: write
 
 concurrency:
   group: snapshot
```

### E3. Step 6.0: the armed run

The run armed in step 6.0 item 5 is 41622958662 (`workflow_dispatch`, started 10:53:10 UTC). GitHub serves a job's log only after the run ends, and this run is still waiting inside its Capture step, so there are no log lines to print. Below is its state as recorded, step list included:

```
Tue Nov  3 11:23:03 UTC 2026
in_progress		snapshot	snapshot	main	workflow_dispatch	41622958662	29m55s	2026-11-03T10:53:10Z
completed	success	step 6.0: early crons and self-dispatch for the capture	snapshot	main	push	41622937498	7m11s	2026-11-03T10:53:01Z
completed	success	snapshot	snapshot	main	schedule	41558850469	20s	2026-11-03T01:18:17Z
1 Set up job completed success 2026-11-03T11:00:15Z
2 Run actions/checkout@v4 completed success 2026-11-03T11:00:16Z
3 Run astral-sh/setup-uv@v6 completed success 2026-11-03T11:00:18Z
4 Install from the lock completed success 2026-11-03T11:00:21Z
5 Capture in_progress  2026-11-03T11:00:23Z
6 Run actions/upload-artifact@v4 pending  0001-01-01T00:00:00Z
11 Post Run astral-sh/setup-uv@v6 pending  0001-01-01T00:00:00Z
12 Post Run actions/checkout@v4 pending  0001-01-01T00:00:00Z
```

Run 41622958662 is still `in_progress` at the time of writing. Its log, and the 2026-11-03 assets if it captures, are not part of this review. See Not verified.

### E4. Step 6.0b: density status per day

Every accepted slice on every day, from `density_checks.csv` after the rerun of steps 5.1 and 5.2. `svi_fits.csv` was rewritten with the parameters at `%.17g`. The fits are not stored, so the surface stage was rerun, as the instruction allows.

#### Density status per day

```
density_status   ok  kink  fd_gap  density_fail
day                                            
2026-10-28       74     0       0             0
2026-10-29      443    50       0             0
2026-10-30      396    48       0             2
```

#### fd_gap rows

```
Empty DataFrame
Columns: [day, ticker, expiry, T, F, integral, int_err, tail_mass, mean, mean_rel_err, min_g, min_density, fd_rel_gap, density_status]
Index: []
```

#### density_fail rows

```
            day ticker      expiry         T           F  integral       int_err  tail_mass        mean  mean_rel_err         min_g   min_density density_status
744  2026-10-30     MU  2027-08-20  0.805483  914.076736       1.0  7.324674e-11   0.000017  913.084029     -0.001086  1.233041e-14  3.807343e-18   density_fail
745  2026-10-30     MU  2027-09-17  0.882195  917.250484       1.0  8.779266e-11   0.000004  915.684706     -0.001707  9.511449e-11  6.946117e-14   density_fail
```

Largest fd_rel_gap over non-kink accepted slices: 0.00177671 (['2026-10-30', 'JPM', '2026-11-27']), bound 5e-3.

#### PIT rows (pit.csv, all)

```
   ticker      expiry         day         T            F   S_realised         u             status
0    AAPL  2026-10-30  2026-10-28  0.006045   345.558577   344.630005  0.412319                 ok
1    ABNB  2026-10-30         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
2    AMAT  2026-10-30         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
3     AMD  2026-10-30         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
4     AMD  2026-11-02         NaN       NaN          NaN          NaN       NaN               kink
5    AMZN  2026-10-30         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
6    AMZN  2026-11-02         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
7    AVGO  2026-10-30  2026-10-29  0.002792   344.061822   326.079987  0.042150                 ok
8    AVGO  2026-11-02  2026-10-29  0.011126   344.156813   322.230011  0.053760                 ok
9     BAC  2026-10-30         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
10    CRM  2026-10-30  2026-10-29  0.002789   229.659522   229.169998  0.485073                 ok
11   CSCO  2026-10-30         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
12    CVX  2026-10-30  2026-10-29  0.002786   230.631498   235.520004  0.767276                 ok
13    DIS  2026-10-30         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
14  GOOGL  2026-10-30  2026-10-29  0.002788   282.914696   279.839996  0.356672                 ok
15  GOOGL  2026-11-02  2026-10-29  0.011121   283.003458   278.989990  0.368661                 ok
16     HD  2026-10-30         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
17    IBM  2026-10-30         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
18   INTC  2026-10-30         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
19    JPM  2026-10-30         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
20   LRCX  2026-10-30         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
21   META  2026-10-30  2026-10-29  0.002788   628.950490   614.989990  0.172474                 ok
22   META  2026-11-02  2026-10-29  0.011121   629.146250   606.729981  0.147354                 ok
23   MSFT  2026-10-30  2026-10-29  0.002793   528.319883   521.909973  0.262701                 ok
24   MSFT  2026-11-02  2026-10-29  0.011126   528.468683   507.119995  0.063201                 ok
25     MU  2026-10-30         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
26     MU  2026-11-02  2026-10-29  0.011125   932.625756   833.590027  0.028388                 ok
27   NFLX  2026-10-30         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
28   NVDA  2026-10-30         NaN       NaN          NaN          NaN       NaN               kink
29   NVDA  2026-11-02  2026-10-29  0.011127   213.190707   202.059998  0.048138                 ok
30   ORCL  2026-10-30         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
31   PANW  2026-10-30         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
32   PLTR  2026-10-30         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
33    QQQ  2026-10-30         NaN       NaN          NaN          NaN       NaN               kink
34    QQQ  2026-11-02  2026-10-30  0.008340   688.247680   681.090027  0.263418                 ok
35   SHOP  2026-10-30  2026-10-29  0.002784   166.668869   157.490005  0.064361                 ok
36    SPY  2026-10-29  2026-10-28  0.003308   770.453590   769.359985  0.411954                 ok
37    SPY  2026-10-30  2026-10-28  0.006047   770.518690   755.719971  0.081330                 ok
38    SPY  2026-11-02  2026-10-28  0.014381   770.716739   752.099976  0.067418                 ok
39   TSLA  2026-10-30  2026-10-29  0.002787   404.190819   399.809998  0.312779                 ok
40   TSLA  2026-11-02  2026-10-29  0.011121   404.327874   403.820007  0.494971                 ok
41   UBER  2026-10-30         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
42    UNH  2026-10-30         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
43    WMT  2026-10-30         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
44    XLE  2026-10-30         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
45    XLE  2026-11-02         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
46    XLF  2026-10-30         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
47    XLF  2026-11-02         NaN       NaN          NaN          NaN       NaN  no_accepted_slice
48    XLK  2026-10-30         NaN       NaN          NaN          NaN       NaN               kink
49    XOM  2026-10-30  2026-10-29  0.002786   182.479205   187.250000  0.811183                 ok
50   ^SPX  2026-10-29  2026-10-28  0.003309  7731.925259  7720.390137  0.411159                 ok
51   ^SPX  2026-10-30  2026-10-28  0.006048  7733.927196  7580.069824  0.065765                 ok
52   ^SPX  2026-11-02  2026-10-28  0.014382  7735.347279  7541.399902  0.054724                 ok
```

**Kink count, 98 against the reviewer's 99.** The rule `s ≤ s_min × (1 + 1e-6)` marks 98 slices. 2 more slices sit just above the band:

- CVX 2026-11-06 on 2026-10-30: s = 1.0000087e-4, 8.7e-6 above the floor relative to it. This is probably the reviewer's 99th.
- UBER 2026-12-04 on 2026-10-30: s = 1.000116e-4.

Both pass the 5e-3 × peak bound, so both are `ok` and stay in the tail and PIT tables.

**Section 4 unchanged.** After the surface rerun, against copies taken before it:

- In `svi_fits.csv`, only the 5 parameter columns differ. The largest relative change is 4.9e-10, which is the `%.10g` rounding.
- `surface_daily.csv`, `ssvi_theta.csv`, `calendar_violations.csv`, `iv_summary.csv` and `capture_health.csv` are byte-identical.

**PIT.** The two Session 5c values are unchanged: `^SPX` 0.4111586111 and SPY 0.411953891. The 51 new rows come from `close.parquet`, which now runs to 2026-11-02 (pulled at the start of 6.0b, see D3). They cover the expiries 2026-10-30 and 2026-11-02, from the latest earlier day with an accepted slice whose density is `ok`.

### E5. Section 6: EVENTS table


```
   ticker         group  event_date   timing pre_snap_date          E1          E2   n1    n2    theta1    theta2           S           F  straddle_move   ts_move  realised_move     ratio  log_ratio           status
0   GOOGL       singles  2026-10-28      AMC           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN  no_pre_snapshot
1    MSFT  xlk_holdings  2026-10-28      AMC           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN  no_pre_snapshot
2    ^SPX         index  2026-10-28     FOMC           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN  no_pre_snapshot
3    AMZN       singles  2026-10-29      AMC    2026-10-29  2026-11-04  2026-11-06  4.0   6.0  0.011354  0.011667  245.289993  245.455716       0.085919  0.083241       0.014211  0.170720  -1.767732               ok
4    INTC  xlk_holdings  2026-10-29      AMC    2026-10-29  2026-11-06  2026-11-13  6.0  11.0  0.016732  0.022077   91.849998   91.932557       0.104790  0.085143       0.336537  3.952634   1.374382               ok
5     CVX       singles  2026-10-30      BMO    2026-10-29  2026-10-30  2026-11-06  1.0   6.0  0.000862  0.002457  230.625000  230.631498       0.024304  0.023420       0.017389  0.742469  -0.297774               ok
6     XOM       singles  2026-10-30      BMO    2026-10-29  2026-10-30  2026-11-06  1.0   6.0  0.000917  0.002529  182.470001  182.479205       0.023867  0.024158       0.021375  0.884801  -0.122393               ok
7    AAPL  xlk_holdings  2026-11-02      AMC           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN  no_pre_snapshot
8    PLTR  xlk_holdings  2026-11-02      AMC           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN  no_pre_snapshot
9     AMD  xlk_holdings  2026-11-03      AMC           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
10   SHOP       singles  2026-11-03      BMO           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN  no_pre_snapshot
11   UBER       singles  2026-11-04      BMO           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
12   ABNB       singles  2026-11-05      AMC           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
13   ^SPX         index  2026-11-06      NFP           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
14   ^SPX         index  2026-11-10      CPI           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
15   AMAT  xlk_holdings  2026-11-12      AMC           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
16   CSCO  xlk_holdings  2026-11-12  unknown           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          unknown
17    DIS       singles  2026-11-17      BMO           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
18     HD       singles  2026-11-17      BMO           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
19   NVDA  xlk_holdings  2026-11-17      AMC           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
20   PANW  xlk_holdings  2026-11-19  unknown           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          unknown
21    WMT       singles  2026-11-19      BMO           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
22    CRM  xlk_holdings  2026-12-02  unknown           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          unknown
23   ^SPX         index  2026-12-04      NFP           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
24   AVGO  xlk_holdings  2026-12-09  unknown           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          unknown
25   ^SPX         index  2026-12-09     FOMC           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
26   ^SPX         index  2026-12-10      CPI           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
27   ORCL  xlk_holdings  2026-12-14  unknown           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          unknown
28     MU  xlk_holdings  2026-12-23  unknown           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          unknown
29    UNH       singles  2027-01-12      BMO           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
30    JPM       singles  2027-01-14      BMO           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
31    BAC       singles  2027-01-15      BMO           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          pending
32   NFLX       singles  2027-01-19  unknown           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          unknown
33    IBM  xlk_holdings  2027-01-27  unknown           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          unknown
34   LRCX  xlk_holdings  2027-01-27  unknown           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          unknown
35   META       singles  2027-01-27  unknown           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          unknown
36   MSFT  xlk_holdings  2027-01-27  unknown           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          unknown
37   TSLA       singles  2027-01-27  unknown           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          unknown
38   INTC  xlk_holdings  2027-01-28  unknown           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          unknown
39  GOOGL       singles  2027-02-03  unknown           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          unknown
40   AMZN       singles  2027-02-04  unknown           NaN         NaN         NaN  NaN   NaN       NaN       NaN         NaN         NaN            NaN       NaN            NaN       NaN        NaN          unknown
```

#### Summary (event_summary.csv)

```
  scope  n  mean_log_ratio  median_log_ratio  mean_lo  mean_hi  share_above  share_lo  share_hi       status
0   all  4       -0.203379         -0.210083      NaN      NaN         0.25       NaN       NaN  below_min_n
```

#### Status counts

```
                 count
status                
pending             16
unknown             15
no_pre_snapshot      6
ok                   4
```

#### unknown rows

```
   ticker         group  event_date   timing   status
16   CSCO  xlk_holdings  2026-11-12  unknown  unknown
20   PANW  xlk_holdings  2026-11-19  unknown  unknown
22    CRM  xlk_holdings  2026-12-02  unknown  unknown
24   AVGO  xlk_holdings  2026-12-09  unknown  unknown
27   ORCL  xlk_holdings  2026-12-14  unknown  unknown
28     MU  xlk_holdings  2026-12-23  unknown  unknown
32   NFLX       singles  2027-01-19  unknown  unknown
33    IBM  xlk_holdings  2027-01-27  unknown  unknown
34   LRCX  xlk_holdings  2027-01-27  unknown  unknown
35   META       singles  2027-01-27  unknown  unknown
36   MSFT  xlk_holdings  2027-01-27  unknown  unknown
37   TSLA       singles  2027-01-27  unknown  unknown
38   INTC  xlk_holdings  2027-01-28  unknown  unknown
39  GOOGL       singles  2027-02-03  unknown  unknown
40   AMZN       singles  2027-02-04  unknown  unknown
```

#### no_pre_snapshot rows

```
   ticker         group  event_date timing           status
0   GOOGL       singles  2026-10-28    AMC  no_pre_snapshot
1    MSFT  xlk_holdings  2026-10-28    AMC  no_pre_snapshot
2    ^SPX         index  2026-10-28   FOMC  no_pre_snapshot
7    AAPL  xlk_holdings  2026-11-02    AMC  no_pre_snapshot
8    PLTR  xlk_holdings  2026-11-02    AMC  no_pre_snapshot
10   SHOP       singles  2026-11-03    BMO  no_pre_snapshot
```

#### pending rows

```
   ticker         group  event_date timing   status
9     AMD  xlk_holdings  2026-11-03    AMC  pending
11   UBER       singles  2026-11-04    BMO  pending
12   ABNB       singles  2026-11-05    AMC  pending
13   ^SPX         index  2026-11-06    NFP  pending
14   ^SPX         index  2026-11-10    CPI  pending
15   AMAT  xlk_holdings  2026-11-12    AMC  pending
17    DIS       singles  2026-11-17    BMO  pending
18     HD       singles  2026-11-17    BMO  pending
19   NVDA  xlk_holdings  2026-11-17    AMC  pending
21    WMT       singles  2026-11-19    BMO  pending
23   ^SPX         index  2026-12-04    NFP  pending
25   ^SPX         index  2026-12-09   FOMC  pending
26   ^SPX         index  2026-12-10    CPI  pending
29    UNH       singles  2027-01-12    BMO  pending
30    JPM       singles  2027-01-14    BMO  pending
31    BAC       singles  2027-01-15    BMO  pending
```

### E6. Section 6: hand check of θ1, θ2, n1 and n2 (AMZN and CVX)

θ_i = SVI w(0) = a + b(−ρm + √(m² + s²)), computed from the `svi_fits.csv` parameters for the pre-snapshot day. n_i is the count of XNYS sessions after the pre-snapshot day, up to and including E_i, from `exchange_calendars`.

```
AMZN: pre-snapshot 2026-10-29
  2026-11-04: a=0.00933408 b=0.0183229 rho=0.43364 m=0.194621 s=0.0001 status=ok_refit -> theta=w(0)=0.011354; XNYS sessions after 2026-10-29 to 2026-11-04: 4 ['2026-10-30', '2026-11-02', '2026-11-03', '2026-11-04']
  2026-11-06: a=0.00801346 b=0.0656657 rho=-0.999 m=-0.40811 s=0.219377 status=ok_refit -> theta=w(0)=0.011667; XNYS sessions after 2026-10-29 to 2026-11-06: 6 ['2026-10-30', '2026-11-02', '2026-11-03', '2026-11-04', '2026-11-05', '2026-11-06']
CVX: pre-snapshot 2026-10-29
  2026-10-30: a=-0.0730906 b=0.0429887 rho=-0.298286 m=-0.53532 s=1.80212 status=ok -> theta=w(0)=0.000862; XNYS sessions after 2026-10-29 to 2026-10-30: 1 ['2026-10-30']
  2026-11-06: a=-0.00866257 b=0.0169159 rho=-0.443173 m=-0.356039 s=0.733265 status=ok -> theta=w(0)=0.002457; XNYS sessions after 2026-10-29 to 2026-11-06: 6 ['2026-10-30', '2026-11-02', '2026-11-03', '2026-11-04', '2026-11-05', '2026-11-06']
```

Each matches `events.csv`:

| event | θ1 | θ2 | n1 | n2 |
|---|---|---|---|---|
| AMZN | 0.011354 | 0.011667 | 4 | 6 |
| CVX | 0.000862 | 0.002457 | 1 | 6 |

Term-structure move for AMZN, by hand:

- v_d = (0.011667 − 0.011354) / 2 = 1.565e-4
- v_e = 0.011354 − 3 × 1.565e-4 = 0.010885
- M_t = √(2/π) √v_e = 0.0832, the same as `ts_move` 0.083241

**AMZN's E1 slice (2026-11-04) has s = 1e-4 and is a `kink` slice.** O-38 removes kink slices from `tail_probs`, `pit` and the density figure only, so it is used here for θ1 = w(0).

## Tests run

Command, on Windows at `5dae296` (the working tree equals HEAD):

```
.venv\Scripts\python -m pytest -p socket --disable-socket -q
.venv\Scripts\ruff check .
```

Result: `4539 passed` in 19 min 25 s; ruff: `All checks passed!` The output with the progress dots dropped (the 6 warnings are the urllib3 IPv6 probe at import time and pytest's config warning):

```
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:894
  C:\Utkarsh\10. Quant Projects\7) Volatility Surface and Event Pricing\Volatility-Surface-and-Event-Pricing\.venv\Lib\site-packages\_pytest\config\__init__.py:894: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
  C:\Utkarsh\10. Quant Projects\7) Volatility Surface and Event Pricing\Volatility-Surface-and-Event-Pricing\.venv\Lib\site-packages\pandas\core\series.py:848: Pandas4Warning: Series.values returning an ndarray that drops timezone information for DatetimeTZDtype is deprecated. In a future version, this will return the underlying DatetimeArray instead. Use 'Series.dt.tz_convert(None).to_numpy()' to get a NumPy array of UTC values, or 'Series.array' to get the ExtensionArray.
  See https://pandas.pydata.org/docs/dev/whatsnew/v3.1.0.html#whatsnew-310-deprecations-values for more details.
    warnings.warn(

tests/test_snapshots.py::test_wait_chains_when_above_max_wait
  C:\Utkarsh\10. Quant Projects\7) Volatility Surface and Event Pricing\Volatility-Surface-and-Event-Pricing\.venv\Lib\site-packages\pytest_socket\__init__.py:138: UserWarning: A test tried to use socket.socket.
    raise SocketBlockedError()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
4539 passed, 6 warnings in 1165.56s (0:19:25)
All checks passed!
```

## Fresh-clone check

```
git clone https://github.com/uty101/Volatility-Surface-and-Event-Pricing.git C:\vs6   (at 5dae296)
uv venv --python 3.12
uv pip install -r requirements-lock.txt
uv pip install -e . --no-deps
.venv\Scripts\python -m pytest -p socket --disable-socket -q
```

Result on Windows: `4539 passed` in 21 min 38 s, the same as the working copy. Output, with the progress dots dropped:

```
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:894
  C:\vs6\.venv\Lib\site-packages\_pytest\config\__init__.py:894: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)
tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
  C:\vs6\.venv\Lib\site-packages\pandas\core\series.py:848: Pandas4Warning: Series.values returning an ndarray that drops timezone information for DatetimeTZDtype is deprecated. In a future version, this will return the underlying DatetimeArray instead. Use 'Series.dt.tz_convert(None).to_numpy()' to get a NumPy array of UTC values, or 'Series.array' to get the ExtensionArray.
  See https://pandas.pydata.org/docs/dev/whatsnew/v3.1.0.html#whatsnew-310-deprecations-values for more details.
    warnings.warn(
tests/test_snapshots.py::test_wait_chains_when_above_max_wait
  C:\vs6\.venv\Lib\site-packages\pytest_socket\__init__.py:138: UserWarning: A test tried to use socket.socket.
    raise SocketBlockedError()
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
4539 passed, 6 warnings in 1298.21s (0:21:38)
```

### CI

Run 41661762643 (`ci`, push of `5dae296`, Linux): success in 15 min 5 s. Ruff: `All checks passed!` Pytest: `4539 passed, 6 warnings in 885.60s (0:14:45)`.

## Runtime per step

- Step 6.0: the test file runs in 3 s.
- Step 6.0b:
  - The surface stage reran sequentially in 155 min 18 s over 3 days. A first attempt across processes ran out of memory and wrote nothing.
  - The density stage takes 1 min 27 s; the tails stage takes 19 s.
- Step 6.2: the events stage takes 9 s.
- `pull_snapshots.py`: 8 assets, all already present, nothing downloaded.

## Deviations from PLAN.md

None in method. How I read the instruction where it leaves room:

1. **Pre-event snapshot.** This is the snapshot on the window's start session itself: the close before BMO, or the close of D for AMC. An earlier snapshot is not used. This is the reading under which "This covers 2026-11-02" holds:
   - AAPL and PLTR (AMC on 11-02) need the 11-02 snapshot.
   - SHOP is BMO on 11-03, so its start session is also 11-02.
   - GOOGL, MSFT and FOMC on 10-28 have no snapshot on their start session: the fixture day has only `^SPX`, SPY and AAPL, and FOMC's start is 10-27.
2. **`no_pre_snapshot` against `pending`.**
   - A window whose start session is after the ticker's last close is `pending`. It is in the future, not missed.
   - A window that starts on or before the last close with no snapshot that day is `no_pre_snapshot`.
   - A row with a pre-snapshot whose end is after the last close would be `pending` and keep its implied values. No row is in that state now.
3. **Prices.** `pull_data.py --stage prices` ran once, at the start of 6.0b. The tail, PIT and event tables all use the same `close.parquet`, which ends on 2026-11-02. The diff against the earlier files: no change to existing `close` and `index` rows, `sectors` moved by at most 6.1e-5, dividends identical.
4. **Macro events.** Ticker `^SPX`, group `index`, timing = the event kind. The windows follow the BMO rule, as kickoff 5.7 says for macro releases.
5. **Straddle.**
   - The straddle comes from the clean chain with both sides (`iv_inputs`), because the IV parquet files hold OTM quotes only.
   - The strike is the one nearest F among strikes where both the call and the put have clean mids. A tie goes to the lower strike.
6. **`too_few_expiries`.** This is the status when fewer than 2 accepted expiries end on or after the window's end session. No row has it now.
7. **Earnings rows.** The rows come from the fixture's earnings file and every snapshot's earnings CSV, limited to event dates on or after the capture start (2026-10-28). The latest snapshot defines each event.
8. **Summary.** Scope `all`, plus each group with at least `min_group_n` events. The status is `ok` or `below_min_n`. Below `min_n`, the interval columns are blank. The intervals are a percentile bootstrap for the mean and Clopper–Pearson for the share.
9. **PIT status when no accepted slice has an `ok` density.** The row carries the status of the slice it would have used, `kink` for example, instead of `no_accepted_slice`.
10. **Failed chain dispatch (6.0).** If `gh workflow run` fails, the script raises, so the run fails visibly instead of exiting 0 after dropping the day.
11. **`run_all.py` across commits.** The 6.0b commit has the density and full-precision changes only. The events stage arrives in 6.1.

## Not verified

- **Run 41622958662**, armed in step 6.0: its log and outcome (see E3).
- **2026-11-03 data.** It was not in the `snapshots` release when `pull_snapshots.py` ran, so it is not in this section's tables.
- **INTC.** The realised move is |log return| 0.337 (close 92.07 to 65.76 on 2026-10-30, −28.6%), the largest in the sample, with ratio 3.95. This is the unadjusted close as served. I did not check it against a second source.

## Open questions

None new. O-38 and O-39 are decided, in `decisions/OPEN.md`.

## Files changed

- **6.0:**
  - `config.toml`
  - `scripts/snapshot.py`
  - `.github/workflows/snapshot.yml`
  - `tests/test_snapshots.py`
- **6.0b:**
  - `volsurf/density.py`
  - `tests/test_density.py`
  - `scripts/run_all.py`
  - `outputs/tables/svi_fits.csv`, `density_checks.csv`, `tail_probs.csv` and `pit.csv`
  - `data/raw/prices/close.parquet`, `index.parquet` and `sectors.parquet`
  - `data/raw/MANIFEST.json`
  - `decisions/section_5_review.md`, `decisions/capture.md` and `decisions/OPEN.md`
- **6.1:**
  - `volsurf/events.py` (new)
  - `tests/test_events.py` (new)
  - `scripts/run_all.py`
  - `data/manual/earnings_overrides.csv` and `data/manual/macro_events.csv`
- **6.2:**
  - `outputs/tables/events.csv` and `outputs/tables/event_summary.csv`
  - `outputs/figures/event_scatter.png` and `outputs/figures/event_term_structures.png`

### Figures, by path

- `outputs/figures/event_scatter.png`
- `outputs/figures/event_term_structures.png`
- `outputs/figures/spx_density_last.png`
- `outputs/figures/spx_metrics.png`
- `outputs/figures/spx_smile_fits_2026-10-28.png`
- `outputs/figures/spx_smiles_2026-10-28.png`
- `outputs/figures/spx_smiles_2026-10-29.png`
- `outputs/figures/spx_smiles_2026-10-30.png`
- `outputs/figures/spx_surface_last.png`

## Reviewer reads

1. E4 (density status and PIT), then `volsurf/density.py`: `is_kink`, `fd_step` and `fd_gap`.
2. `volsurf/events.py`: `event_windows`, `event_table` and `term_structure_move`.
3. E5 and E6.
4. Deviations 1 and 2 (pre-snapshot and pending).
5. `tests/test_events.py`.
