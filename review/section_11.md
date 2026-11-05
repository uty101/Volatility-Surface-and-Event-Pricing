# Review: Section 11

## Section

Section 11: Write-up and reproducibility (`PLAN.md` steps 11.1 to 11.4), with instruction 11 and its step 11.0.

The section is complete, and this is the last section of the project. The risk book now takes each contract's vol from its own expiry's SVI slice, and the `^SPX` small-shock bound of 0.5% is met at 0.113% and 0.156%. `scripts/run_all.py` covers all 20 stages. `outputs/tables/answers.csv` answers the 6 questions in 51 rows, and `README.md` is 12,957 bytes. Fresh clone: `4729 passed, 35 warnings in 2963.43s (0:49:23)`.

3 things the reviewer should know first:

- **The first cold run failed.** It stopped at the `answers` stage with exit 1, after 9,644 s: U+2212 could not be printed to a piped Windows stdout. The fix is `6de2e14`, with a test that fails without it. The cold run was then repeated in full from an empty cache, and the figures below come from that repeat.
- **The slice vol is not closer to the quote everywhere.** NVDA's gap went from +0.19 to −1.05 vol points. See E1.
- **The tables cover 4 capture days, 2026-10-28 to 2026-11-03.** Those were all the days in the release when both runs ran. `chains_2026-11-04.parquet` reached the release afterwards and is in no table here.

Everything built on captured chains is a method demonstration, N = 4 capture days.

## Steps completed

- 11.0  153c1e0  step 11.0: risk vols from the expiry's SVI slice
- 11.1  c37e01b  step 11.1: run_all covers every stage
- 11.2  9adb654  step 11.2: answers to the 6 questions
- 11.3  79f5c7f  step 11.3: README and methods
- 11.4  813a2ac  step 11.4: licence, outline folder renamed, unused files removed
- 11.1  6de2e14  step 11.1: run_all prints on a piped Windows stdout. It fixes the failure the first cold run found, as a new commit because history is not rewritten.
- The wrap-up commit holds this file and the status file. Part A's `decisions/section_10_review.md` is in `153c1e0`, which also marks O-47, O-48 and O-49 decided.

## Evidence

### E1. Step 11.0: each position's vol against its quote mid IV

`gap_pts` is `vol` minus `iv`, in vol points, on 2026-11-03.

Now, on the slice vol:

```
                 contract  days  select_delta vol_source       vol        iv   gap_pts     mid      price
0  ^SPX 2026-12-03 P 7300    30     -0.244073        svi  0.197602  0.200918 -0.331607  66.000  63.736713
1  ^SPX 2026-12-03 C 7800    30      0.248204        svi  0.142523  0.138990  0.353213  42.350  44.758703
2   AAPL 2027-01-15 C 335    73      0.505352        svi  0.245555  0.245214  0.034115  13.775  13.795230
3   NVDA 2026-12-18 P 193    45     -0.296716        svi  0.463103  0.473569 -1.046634   7.175   6.904258
```

Session 10, on the SSVI vol:

```
                 contract  days  select_delta       vol        iv   gap_pts     mid      price
0  ^SPX 2026-12-03 P 7275    30     -0.244107  0.216530  0.204091  1.243895  61.700  70.048120
1  ^SPX 2026-12-03 C 7780    30      0.257847  0.135771  0.140696 -0.492527  48.350  44.874809
2   AAPL 2027-01-15 C 335    73      0.505311  0.245292  0.245214  0.007818  13.775  13.779636
3   NVDA 2026-12-18 P 193    45     -0.300039  0.475454  0.473569  0.188517   7.175   7.223777
```

- **`^SPX`.** The largest gap falls from 1.24 to 0.35 vol points. Both strikes moved, because the O-21 selection now runs on the slice vol: P 7275 to P 7300 and C 7780 to C 7800.
- **AAPL.** The contract is unchanged, and the gap is 0.03 against 0.01 vol points.
- **NVDA.** The contract is unchanged, and the gap widens from +0.19 to −1.05 vol points. The price is 6.90 against a mid of 7.175; session 10's was 7.22. The slice fits this strike worse than SSVI did. Instruction 11 fixes the slice as the source, so this is reported and not changed.

### E2. Step 11.0: grid corners and limits, session 10 against now

The book's contracts changed as well as the vols, so the change in each corner has both causes.

```
                           session_10   session_11      change
spot_shock vol_shock_pts                                      
-0.1       -5.0          -386275.8329 -410731.0504 -24455.2175
            5.0          -430445.5503 -447394.4664 -16948.9161
 0.1       -5.0          -393495.7754 -380292.3478  13203.4276
            5.0          -415291.6700 -404692.2628  10599.4072
largest loss and gain
       session_10    session_11
min -430445.55030 -447394.46640
max   58660.13058   57679.28805
```

Limits. The session 10 row, then all 9 rows now. 1 of 9 is still breached:

```
          day underlying       measure        value   limit  breach status  left_out
1  2026-11-03       ^SPX  dollar_gamma -1008797.569  250000    True     ok         0
          day underlying       measure         value    limit  breach status  left_out
0  2026-11-03       ^SPX  dollar_delta -3.123956e+04  2000000   False     ok         0
1  2026-11-03       ^SPX  dollar_gamma -1.003799e+06   250000    True     ok         0
2  2026-11-03       ^SPX       vega_pt -1.366234e+04    50000   False     ok         0
3  2026-11-03       AAPL  dollar_delta  3.344375e+05  2000000   False     ok         0
4  2026-11-03       AAPL  dollar_gamma  2.407501e+04   250000   False     ok         0
5  2026-11-03       AAPL       vega_pt  1.185973e+03    50000   False     ok         0
6  2026-11-03       NVDA  dollar_delta  9.245464e+04  2000000   False     ok         0
7  2026-11-03       NVDA  dollar_gamma -6.669952e+03   250000   False     ok         0
8  2026-11-03       NVDA       vega_pt -3.879399e+02    50000   False     ok         0
```

### E3. Step 11.0: the bound test

Status 4 binds `^SPX` at 0.5% of delta × dS. The tree positions are report-only, because the tree's value is piecewise linear in S. Real positions, at a shock of `fd_h_spot_rel` = 1e-4:

```
                 contract         pnl    delta_dS   gap_pct        bound
0  ^SPX 2026-12-03 P 7300  184.345483  184.554603  0.113311         0.5%
1  ^SPX 2026-12-03 C 7800 -187.971399 -187.678559  0.156032         0.5%
2   AAPL 2027-01-15 C 335   34.500576   33.443752  3.160004  report-only
3   NVDA 2026-12-18 P 193    9.990075    9.245464  8.053804  report-only
```

NVDA's report-only gap was 6.7% in session 10.

```
============================= test session starts =============================
platform win32 -- Python 3.12.13, pytest-9.2.0, pluggy-1.7.0 -- C:\Utkarsh\10. Quant Projects\7) Volatility Surface and Event Pricing\Volatility-Surface-and-Event-Pricing\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Utkarsh\10. Quant Projects\7) Volatility Surface and Event Pricing\Volatility-Surface-and-Event-Pricing
configfile: pyproject.toml
plugins: platformdirs-4.13.6, socket-0.8.1
collecting ... collected 28 items / 26 deselected / 2 selected

tests/test_risk.py::test_small_shock_matches_delta_measure[^SPX] PASSED  [ 50%]
tests/test_risk.py::test_small_shock_matches_delta_measure[AAPL] PASSED  [100%]

====================== 2 passed, 26 deselected in 3.91s =======================
```

### E4. Step 11.1: 2 runs and both runtimes

Capture days, printed by both runs: `capture days: 4, 2026-10-28 to 2026-11-03 (the fixture day and 3 in the release)`.

- **Cold:** 15,587.6 s, exit 0, from an empty `data/processed/surface`.
- **Warm:** 3,385.2 s, exit 0, with the surface cache in place.
- **`git status --short`** printed nothing after the cold run and nothing after the warm run. So every committed table, the PDF and the README rebuilt byte for byte.
- **The surface cache.** `diff -rq data/processed/surface data/processed/surface_s10_backup` printed nothing after the cold run: the 4 refitted days match session 10's files exactly.

The per-stage runtimes are under "Runtime per step".

### E5. Step 11.1: the failed cold run

The end of the first cold run's log:

```
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'charmap' codec can't encode character '\u2212' in position 1247: character maps to <undefined>
wall clock 9644.0 s, exit 1
```

`tests/test_run_all.py::test_main_prints_the_minus_sign_on_a_cp1252_stdout` fails without `6de2e14` (`1 failed, 5 passed`) and passes with it (`6 passed`).

### E6. Step 11.2: `answers.csv` in full

```
   question                                                                                                                                                                                                                                                                                                                 answer             value               source_table                                                                                    source_row            source_column
0         1                                                                                                                                                                                           Yes. BSM matches QuantLib's analytic engine: the largest price gap is 3.9e-14 over 252 grid cases, against a bound of 1e-10.   3.907985047e-14           pricer_check.csv                                                                         check=bsm_vs_quantlib              largest_gap
1         1                                                                                                                                                                                                                                   Black-76 equals BSM once S e^(−qT) = D F: the largest gap is 5.0e-14 over 252 cases.    4.97379915e-14           pricer_check.csv                                                                          check=black76_vs_bsm              largest_gap
2         1                                                                                                                                                                         The American CRR tree at 2000 steps matches QuantLib's CRR engine: the largest gap is 6.8e-05 x S over 252 cases, against a bound of 1e-4 x S.   6.825657499e-05           pricer_check.csv                                                       check=crr_american_vs_quantlib_rel_spot              largest_gap
3         1                                                                                                                                                                                             Delta, gamma, vega, theta and rho match QuantLib: the largest gap is 4.4e-13 over 252 cases each, against a bound of 1e-8.   4.405364962e-13           pricer_check.csv  check=delta_vs_quantlib|gamma_vs_quantlib|vega_vs_quantlib|theta_vs_quantlib|rho_vs_quantlib         max(largest_gap)
4         1                                                                                                                                                                                                            Early exercise premium on SPY near the money puts: median 0.22 vol points (N = 496 contracts, fixture day).      0.2168923554            eep_summary.csv                                                         ticker=SPY;kind=P;k_bin=(-0.02, 0.02]           median_vol_pts
5         1                                                                                                                                                                                                                                     It grows on SPY deep in the money puts: median 1.39 vol points (N = 44 contracts).       1.394651874            eep_summary.csv                                                           ticker=SPY;kind=P;k_bin=(0.10, inf)           median_vol_pts
6         1                                                                                                                                                                                                            Early exercise premium on AAPL near the money puts: median 0.16 vol points (N = 47 contracts, fixture day).      0.1551960481            eep_summary.csv                                                        ticker=AAPL;kind=P;k_bin=(-0.02, 0.02]           median_vol_pts
7         1                                                                                                                                                                                                                                   It grows on AAPL deep in the money puts: median 4.79 vol points (N = 109 contracts).       4.792174384            eep_summary.csv                                                          ticker=AAPL;kind=P;k_bin=(0.10, inf)           median_vol_pts
8         1                                                                                    On calls it is 0 to rounding: the largest median in any SPY or AAPL call bin is 7.7e-12 vol points. The single names captured later have no premium table, because the step runs on the fixture day, which holds SPY and AAPL only.   7.685518888e-12            eep_summary.csv                                                                                        kind=C      max(median_vol_pts)
9         2                                                                                                                                                                                                                                                     ^SPX 30-day ATM vol was 13.44% on 2026-10-28 (N = 4 capture days).      0.1344428167          surface_daily.csv                                                                    ticker=^SPX;day=2026-10-28                   atm_30
10        2                                                                                                                                                                                                                                                            It was 16.28% on 2026-11-03, after the 2026-10-30 sell-off.      0.1628414893          surface_daily.csv                                                                    ticker=^SPX;day=2026-11-03                   atm_30
11        2                                                                                                                                                                                                                 The 30-day 25-delta risk reversal went from -4.16 to -5.37 vol points, so skew steepened (N = 4 days).     -0.0537239881          surface_daily.csv                                                                    ticker=^SPX;day=2026-11-03                  rr25_30
12        2                                                                                                                                                                                 The term slope, ATM 90 days minus 30 days, went from 1.02 to -0.40 vol points, so the short end moved above the long end (N = 4 days).   -0.004027883285          surface_daily.csv                                                                    ticker=^SPX;day=2026-11-03               term_slope
13        2                                                                                                                                                                     Butterfly: 1550 of 1683 SVI slices across every underlying and day are accepted; the rest are rejected or have too few quotes to fit (N = 4 days).              1550               svi_fits.csv                                                                            status=ok|ok_refit                 count(*)
14        2                                                                                                                                                                    Every accepted slice is free of butterfly arbitrage up to the check's tolerance: the smallest g on the acceptance grid is -9.5e-11, against -1e-10.  -9.462312184e-11               svi_fits.csv                                                                            status=ok|ok_refit               min(min_g)
15        2                                                                                                                                                                       Calendar: the per-expiry slices are not fully clean. 13 of 134 consecutive ^SPX pairs cross somewhere on their shared quoted range (N = 4 days).                13    calendar_violations.csv                                                                     ticker=^SPX;violated=True                 count(*)
16        2                                                                                                                                   Across every underlying it is 41 of 1436 pairs. Slices are not refitted for this; SSVI is the calendar-consistent surface, because its theta is non-decreasing in T by construction.                41    calendar_violations.csv                                                                                 violated=True                 count(*)
17        2                                                                                                                                                             SSVI pays for that in fit: its ^SPX RMSE was 3.16 vol points on 2026-11-03, because 1 rho cannot hold the skew, so the daily metrics come from the slices.     0.03164805278          surface_daily.csv                                                                    ticker=^SPX;day=2026-11-03                ssvi_rmse
18        3                                                                                                                                                                    With N = 4 completed events, fewer than the 20 the summary needs, the gap between implied and realised moves cannot be told apart from 0 at this N.                 4          event_summary.csv                                                                                     scope=all                        n
19        3                                                                                                                                                                                                   AMZN AMC 2026-10-29: realised 1.42% against a term structure move of 8.32% and a straddle move of 8.59%, ratio 0.17.      0.1707197799                 events.csv                                                             ticker=AMZN;event_date=2026-10-29                    ratio
20        3                                                                                                                                                                                                 INTC AMC 2026-10-29: realised 33.65% against a term structure move of 8.51% and a straddle move of 10.48%, ratio 3.95.       3.952633585                 events.csv                                                             ticker=INTC;event_date=2026-10-29                    ratio
21        3                                                                                                                                                                                                    CVX BMO 2026-10-30: realised 1.74% against a term structure move of 2.34% and a straddle move of 2.43%, ratio 0.74.      0.7424694232                 events.csv                                                              ticker=CVX;event_date=2026-10-30                    ratio
22        3                                                                                                                                                                                                    XOM BMO 2026-10-30: realised 2.14% against a term structure move of 2.42% and a straddle move of 2.39%, ratio 0.88.      0.8848005615                 events.csv                                                              ticker=XOM;event_date=2026-10-30                    ratio
23        3                                                                                                                                                                                                                              38 more events have a window that ends after the last close in the data and stay pending.                38                 events.csv                                                                                status=pending                 count(*)
24        3                                                                                                                                                                                                                              3 events have no pre-event snapshot, because they fall before the capture could see them.                 3                 events.csv                                                                        status=no_pre_snapshot                 count(*)
25        4                                                                                                                                                                                              VIX squared sat above the variance that followed by 0.01037 of annualised variance on average, over 441 months from 1990.     0.01037227478            vrp_monthly.csv                                                                              iv!=;rv_fwd_21!=                mean(vrp)
26        4                                                                                                                                                                                                                                           Over the 394 months that also have a GARCH forecast the mean gap is 0.00970.    0.009699409516            vrp_monthly.csv                                                                   iv!=;rv_fwd_21!=;garch_fc!=                mean(vrp)
27        4                                                                                                                                                                                                                                                 Implied variance is above the GARCH forecast in 362 of 395 month ends.               362            vrp_monthly.csv                                                                                      signal>0                 count(*)
28        4                                                                                                                                                                                          The forecast says little about the size of the gap: the correlation of the signal with the later gap is 0.15 over 394 months.      0.1474838223            vrp_monthly.csv                                                                   iv!=;rv_fwd_21!=;garch_fc!=         corr(signal,vrp)
29        4  Selling puts paid, but less per unit of risk than holding the index: Cboe PUT has a Sharpe of 0.56 over 237 months from 2007, against 0.65 for the S&P 500 total return index and 0.44 for BXM. The index carries no trading costs of its own, so the only cost deducted here is the timed strategy's switching cost.      0.5553589463         strategy_stats.csv                                                                                  strategy=put                   sharpe
30        4                                                                                                                                                                                                                                                                                         PUT's worst month was -17.65%.     -0.1765015969         strategy_stats.csv                                                                                  strategy=put              worst_month
31        4                                                                                                                                                                                                           Timing on implied minus GARCH variance gives a raw Sharpe of 0.80 over 237 months, after the switching cost.      0.8025587878         strategy_stats.csv                                                                            strategy=timed_put                   sharpe
32        4                                                                                                                                                                              The deflated Sharpe beside it is blank, with status too_few_trials, because 1 specification was tried and the deflation needs at least 2.                           strategy_stats.csv                                                                            strategy=timed_put          deflated_sharpe
33        4                                                                                                                                                                  So the number of specifications tried is 1, and the raw figure is 1 specification of a family, not evidence that timing improves the deflated Sharpe.                 1               spec_log.csv                                                                                           all                 count(*)
34        4                                                                                                                                                                                                                                                                The raw gain over PUT comes from sitting out 27 months.                27            vrp_monthly.csv                                         month_end>=2007-01-31;month_end<=2026-09-30;signal<=0                 count(*)
35        5                                                                                                                                                                       Yes, in part. Regressing the next 63 sessions' realised sector correlation on COR3M gives a slope of 0.711 (Newey-West se 0.074), N = 5163 days.        0.71145938            cor3m_study.csv                                                                                           all                    slope
36        5                                                                                                                                                                                           R² is 0.437, so COR3M accounts for a bit under half of the variation in next quarter's realised correlation (N = 5163 days).         0.4373451            cor3m_study.csv                                                                                           all                       r2
37        5                                                                               The mean gap, implied minus realised, is -0.167. COR3M covers single stocks and this proxy uses sector ETFs, which correlate with each other more, so implied sits below realised; the gap is the proxy, not a correlation risk premium.     -0.1671848312            cor3m_study.csv                                                                                           all                 mean_gap
38        5                                                                                                                                                                              The XLK chain priced an implied correlation of 0.496 on 2026-11-03, with 15 names covering 72.0% of the weight (N = 3 days with a value).      0.4959847449      implied_corr_live.csv                                                                                day=2026-11-03             implied_corr
39        5                                                                                                                                                    It rose from 0.331 on 2026-10-29 to 0.565 on 2026-10-30, when the S&P 500 fell 1.8% and XLK 4.9%. Implied correlation rising in a sell-off is the textbook pattern.      0.5648914496      implied_corr_live.csv                                                                                day=2026-10-30             implied_corr
40        6                                                                                                                                                                                            On the live delta-hedged ^SPX straddles the median explained share is 0.977 (N = 6 position moves, a method demonstration).      0.9767115369       attribution_live.csv                                                                                           all  median(explained_share)
41        6                                                                                                                                                                                                                                                    On a synthetic Black-Scholes path it is 0.952 (N = 21 daily steps).      0.9518780944  attribution_synthetic.csv                                                                                           all  median(explained_share)
42        6                                                                                                                                                                                                                                           Gamma summed to -58.35 index points per straddle unit over the 6 live moves.      -58.34574531       attribution_live.csv                                                                                           all               sum(gamma)
43        6                                                                                                                                                                                                                                            Theta summed to 59.76 index points per straddle unit over the 6 live moves.       59.75668348       attribution_live.csv                                                                                           all               sum(theta)
44        6                                                                                                                                                                                                                                            Vega summed to -17.37 index points per straddle unit over the 6 live moves.      -17.37407626       attribution_live.csv                                                                                           all                sum(vega)
45        6                                                                                                                                                                                                                                      The residual summed to 4.19 index points per straddle unit over the 6 live moves.       4.190210809       attribution_live.csv                                                                                           all            sum(residual)
46        6                                                                                                                                                                                               Delta and the hedge cancel and vanna and volga are small, so the delta-hedged P&L summed to -9.92 over the same 6 moves.       -9.92159334       attribution_live.csv                                                                                           all               sum(total)
47        6                                                                                                                                                                                                                                                      Hedging every step (k = 1) leaves an error sd of 0.241 under GBM.      0.2413946689      hedging_frequency.csv                                                                 model=gbm;hedge_every_steps=1                 error_sd
48        6                  The same hedge leaves 0.813 under Heston: the hedge uses delta at the current vol but is blind to vol moves, so even continuous hedging leaves an unhedged vega P&L, and the error sd stops falling in proportion to the square root of k. The means are not comparable, because the 2 drifts differ.      0.8128286265      hedging_frequency.csv                                                              model=heston;hedge_every_steps=1                 error_sd
49        6                                                                                                                                                                                                                                  Hedging less often raises the GBM error sd to 1.763 at k = 65, 5 days between hedges.       1.762866892      hedging_frequency.csv                                                                model=gbm;hedge_every_steps=65                 error_sd
50        6                                                                                                                                                                                                                                          It cuts cost: the GBM mean cost falls from 0.106 at k = 1 to 0.014 at k = 65.      0.1058332577      hedging_frequency.csv                                                                 model=gbm;hedge_every_steps=1                cost_mean
```

`test_sources_resolve` reads every row's value back from its source table. The deflated Sharpe row is blank, with status `too_few_trials`, because 1 specification was tried and the deflation needs at least 2.

### E7. Step 11.3: the README diff

From `7118cf5`, the last commit of session 10:

~~~diff
diff --git a/README.md b/README.md
index bb647c4..478e2ec 100644
--- a/README.md
+++ b/README.md
@@ -6,4 +6,138 @@ Tests the volatility risk premium on S&P 500 history from 1990 and implied again
 Splits delta-hedged option P&L into Greeks and builds a 1-page daily risk report.
 Option chains are captured daily from 2026-10-28, so every live result is a method demonstration with its N stated.
 
-Results pending.
+Results are in [`outputs/`](outputs/). [![ci](https://github.com/uty101/Volatility-Surface-and-Event-Pricing/actions/workflows/ci.yml/badge.svg)](https://github.com/uty101/Volatility-Surface-and-Event-Pricing/actions/workflows/ci.yml) 4,729 tests.
+
+**Capture window:** 2026-10-28 to 2026-11-03, 4 days, 2026-11-02 missed. The first day holds `^SPX`, SPY and AAPL only, from an in-session test capture. The others hold all 37 underlyings.
+
+## Run it
+
+```bash
+uv venv --python 3.12
+uv pip install -r requirements-lock.txt
+uv pip install -e . --no-deps
+python scripts/run_all.py                  # every stage, in section order
+pytest -p socket --disable-socket -q
+```
+
+`run_all.py` needs an authenticated `gh` to download the chains from the `snapshots` release. Long history is committed in `data/raw/`. Fitted surfaces are cached in `data/processed/surface/`, so only new days are fitted. Methods are in [`docs/METHODS.md`](docs/METHODS.md).
+
+## 1. Does the pricer match QuantLib?
+
+Yes. BSM matches QuantLib's analytic engine: the largest price gap is 3.9e-14 over 252 grid cases, against a bound of 1e-10. Black-76 equals BSM once S e^(−qT) = D F: the largest gap is 5.0e-14 over 252 cases. The American CRR tree at 2000 steps matches QuantLib's CRR engine: the largest gap is 6.8e-05 x S over 252 cases, against a bound of 1e-4 x S. Delta, gamma, vega, theta and rho match QuantLib: the largest gap is 4.4e-13 over 252 cases each, against a bound of 1e-8. Early exercise premium on SPY near the money puts: median 0.22 vol points (N = 496 contracts, fixture day). It grows on SPY deep in the money puts: median 1.39 vol points (N = 44 contracts). Early exercise premium on AAPL near the money puts: median 0.16 vol points (N = 47 contracts, fixture day). It grows on AAPL deep in the money puts: median 4.79 vol points (N = 109 contracts). On calls it is 0 to rounding: the largest median in any SPY or AAPL call bin is 7.7e-12 vol points. The single names captured later have no premium table, because the step runs on the fixture day, which holds SPY and AAPL only.
+
+## 2. The S&P 500 surface
+
+^SPX 30-day ATM vol was 13.44% on 2026-10-28 (N = 4 capture days). It was 16.28% on 2026-11-03, after the 2026-10-30 sell-off. The 30-day 25-delta risk reversal went from −4.16 to −5.37 vol points, so skew steepened (N = 4 days). The term slope, ATM 90 days minus 30 days, went from 1.02 to −0.40 vol points, so the short end moved above the long end (N = 4 days). Butterfly: 1550 of 1683 SVI slices across every underlying and day are accepted; the rest are rejected or have too few quotes to fit (N = 4 days). Every accepted slice is free of butterfly arbitrage up to the check's tolerance: the smallest g on the acceptance grid is −9.5e-11, against −1e-10. Calendar: the per-expiry slices are not fully clean. 13 of 134 consecutive ^SPX pairs cross somewhere on their shared quoted range (N = 4 days). Across every underlying it is 41 of 1436 pairs. Slices are not refitted for this; SSVI is the calendar-consistent surface, because its theta is non-decreasing in T by construction. SSVI pays for that in fit: its ^SPX RMSE was 3.16 vol points on 2026-11-03, because 1 rho cannot hold the skew, so the daily metrics come from the slices.
+
+| day | ATM 30d % | RR 25d, pts | BF 25d, pts | ATM 90d % | term slope, pts | expiries |
+| --- | --- | --- | --- | --- | --- | --- |
+| 2026-10-28 | 13.44 | −4.16 | 0.63 | 14.46 | 1.02 | 36 |
+| 2026-10-29 | 12.98 | −4.11 | 0.60 | 14.25 | 1.26 | 34 |
+| 2026-10-30 | 16.54 | −6.36 | 0.82 | 16.26 | −0.28 | 34 |
+| 2026-11-03 | 16.28 | −5.37 | 0.66 | 15.88 | −0.40 | 34 |
+
+The smile on the last day shows the skew the slices hold: the 30-day 25-delta risk reversal is −5.37 vol points.
+
+![^SPX smiles](outputs/figures/spx_smiles_2026-11-03.png)
+
+ATM vol jumped on 2026-10-30 and stayed up, ending at 16.28%, with the term slope turning negative.
+
+![^SPX metrics](outputs/figures/spx_metrics.png)
+
+The density comes straight from each slice, and the shaded band marks where quotes exist. Tail probabilities outside it are labelled extrapolated.
+
+![^SPX density](outputs/figures/spx_density_last.png)
+
+## 3. Earnings events
+
+With N = 4 completed events, fewer than the 20 the summary needs, the gap between implied and realised moves cannot be told apart from 0 at this N. AMZN AMC 2026-10-29: realised 1.42% against a term structure move of 8.32% and a straddle move of 8.59%, ratio 0.17. INTC AMC 2026-10-29: realised 33.65% against a term structure move of 8.51% and a straddle move of 10.48%, ratio 3.95. CVX BMO 2026-10-30: realised 1.74% against a term structure move of 2.34% and a straddle move of 2.43%, ratio 0.74. XOM BMO 2026-10-30: realised 2.14% against a term structure move of 2.42% and a straddle move of 2.39%, ratio 0.88. 38 more events have a window that ends after the last close in the data and stay pending. 3 events have no pre-event snapshot, because they fall before the capture could see them.
+
+| ticker | date | timing | straddle % | term structure % | realised % | ratio |
+| --- | --- | --- | --- | --- | --- | --- |
+| AMZN | 2026-10-29 | AMC | 8.59 | 8.32 | 1.42 | 0.17 |
+| INTC | 2026-10-29 | AMC | 10.48 | 8.51 | 33.65 | 3.95 |
+| CVX | 2026-10-30 | BMO | 2.43 | 2.34 | 1.74 | 0.74 |
+| XOM | 2026-10-30 | BMO | 2.39 | 2.42 | 2.14 | 0.88 |
+
+Points above the line moved more than the options priced. 4 points say nothing about the average.
+
+![Implied against realised](outputs/figures/event_scatter.png)
+
+## 4. The volatility risk premium
+
+VIX squared sat above the variance that followed by 0.01037 of annualised variance on average, over 441 months from 1990. Over the 394 months that also have a GARCH forecast the mean gap is 0.00970. Implied variance is above the GARCH forecast in 362 of 395 month ends. The forecast says little about the size of the gap: the correlation of the signal with the later gap is 0.15 over 394 months. Selling puts paid, but less per unit of risk than holding the index: Cboe PUT has a Sharpe of 0.56 over 237 months from 2007, against 0.65 for the S&P 500 total return index and 0.44 for BXM. The index carries no trading costs of its own, so the only cost deducted here is the timed strategy's switching cost. PUT's worst month was −17.65%. Timing on implied minus GARCH variance gives a raw Sharpe of 0.80 over 237 months, after the switching cost. The deflated Sharpe beside it is blank, with status too_few_trials, because 1 specification was tried and the deflation needs at least 2. So the number of specifications tried is 1, and the raw figure is 1 specification of a family, not evidence that timing improves the deflated Sharpe. The raw gain over PUT comes from sitting out 27 months.
+
+| strategy | months | mean % | vol % | Sharpe | worst month % | worst drawdown % | skew | excess kurtosis |
+| --- | --- | --- | --- | --- | --- | --- | --- | --- |
+| put | 237 | 7.52 | 10.72 | 0.555 | −17.65 | −32.66 | −1.69 | 7.41 |
+| bxm | 237 | 6.39 | 10.95 | 0.441 | −15.01 | −35.81 | −1.36 | 5.24 |
+| sp500tr | 237 | 11.55 | 15.40 | 0.648 | −16.80 | −50.95 | −0.55 | 1.05 |
+| timed_put | 237 | 8.85 | 9.06 | 0.803 | −13.42 | −20.75 | −1.03 | 5.48 |
+| bxm_long | 295 | 6.57 | 10.64 | 0.455 | −15.01 | −35.81 | −1.26 | 5.11 |
+
+`bxm_long` is BXM alone over its longer window. VIX squared sat above the variance that followed in 372 of 441 months.
+
+![VIX squared against realised](outputs/figures/vrp_vix2_vs_rv.png)
+
+The timed line ends highest of the option strategies, with a Sharpe of 0.80 against PUT's 0.56. That is 1 specification, so read it with the deflated Sharpe note above.
+
+![Cumulative excess return](outputs/figures/vrp_cumulative.png)
+
+Its worst drawdown is −20.8% against PUT's −32.7%, because it was out of the market for part of the falls.
+
+![Drawdowns](outputs/figures/vrp_drawdowns.png)
+
+## 5. Correlation
+
+Yes, in part. Regressing the next 63 sessions' realised sector correlation on COR3M gives a slope of 0.711 (Newey-West se 0.074), N = 5163 days. R² is 0.437, so COR3M accounts for a bit under half of the variation in next quarter's realised correlation (N = 5163 days). The mean gap, implied minus realised, is −0.167. COR3M covers single stocks and this proxy uses sector ETFs, which correlate with each other more, so implied sits below realised; the gap is the proxy, not a correlation risk premium. The XLK chain priced an implied correlation of 0.496 on 2026-11-03, with 15 names covering 72.0% of the weight (N = 3 days with a value). It rose from 0.331 on 2026-10-29 to 0.565 on 2026-10-30, when the S&P 500 fell 1.8% and XLK 4.9%. Implied correlation rising in a sell-off is the textbook pattern.
+
+| days | first | last | intercept | slope | slope se | R² |
+| --- | --- | --- | --- | --- | --- | --- |
+| 5163 | 2006-01-03 | 2026-08-04 | 0.2862 | 0.7115 | 0.0740 | 0.4373 |
+
+| day | XLK vol % | names | covered weight % | implied correlation |
+| --- | --- | --- | --- | --- |
+| 2026-10-29 | 25.24 | 15 | 72.0 | 0.331 |
+| 2026-10-30 | 33.72 | 13 | 66.1 | 0.565 |
+| 2026-11-03 | 32.18 | 15 | 72.0 | 0.496 |
+
+Implied and realised move together, with a slope of 0.711 and an R² of 0.437. The shaded gap is the sector proxy, not a premium.
+
+![COR3M against realised](outputs/figures/cor3m_vs_realised.png)
+
+## 6. P&L attribution and hedging
+
+On the live delta-hedged ^SPX straddles the median explained share is 0.977 (N = 6 position moves, a method demonstration). On a synthetic Black-Scholes path it is 0.952 (N = 21 daily steps). Gamma summed to −58.35 index points per straddle unit over the 6 live moves. Theta summed to 59.76 index points per straddle unit over the 6 live moves. Vega summed to −17.37 index points per straddle unit over the 6 live moves. The residual summed to 4.19 index points per straddle unit over the 6 live moves. Delta and the hedge cancel and vanna and volga are small, so the delta-hedged P&L summed to −9.92 over the same 6 moves. Hedging every step (k = 1) leaves an error sd of 0.241 under GBM. The same hedge leaves 0.813 under Heston: the hedge uses delta at the current vol but is blind to vol moves, so even continuous hedging leaves an unhedged vega P&L, and the error sd stops falling in proportion to the square root of k. The means are not comparable, because the 2 drifts differ. Hedging less often raises the GBM error sd to 1.763 at k = 65, 5 days between hedges. It cuts cost: the GBM mean cost falls from 0.106 at k = 1 to 0.014 at k = 65.
+
+| model | k | error mean | error sd | cost mean |
+| --- | --- | --- | --- | --- |
+| gbm | 1 | 0.002 | 0.241 | 0.106 |
+| gbm | 13 | 0.002 | 0.862 | 0.029 |
+| gbm | 65 | 0.012 | 1.763 | 0.014 |
+| heston | 1 | 0.001 | 0.813 | 0.104 |
+| heston | 13 | −0.010 | 1.166 | 0.029 |
+| heston | 65 | −0.008 | 1.947 | 0.014 |
+
+## Risk report
+
+[`outputs/reports/risk_2026-11-03.pdf`](outputs/reports/risk_2026-11-03.pdf) is the 1-page report for 2026-11-03 (N = 4 capture days). Each vol is the contract's own SVI slice at its strike.
+
+| contract | side | contracts | vol % | vol source | dollar delta | dollar gamma 1% | vega per pt |
+| --- | --- | --- | --- | --- | --- | --- | --- |
+| ^SPX 2026-12-03 P 7300 | −1 | 10 | 19.76 | svi | 1845546 | −418425 | −6800 |
+| ^SPX 2026-12-03 C 7800 | −1 | 10 | 14.25 | svi | −1876786 | −585374 | −6862 |
+| AAPL 2027-01-15 C 335 | 1 | 20 | 24.56 | svi | 334438 | 24075 | 1186 |
+| NVDA 2026-12-18 P 193 | −1 | 15 | 46.31 | svi | 92455 | −6670 | −388 |
+
+The worst cell of the grid loses 447.4 thousand dollars, at spot −10% and vol +5 points. 1 of 9 limits is breached: ^SPX dollar gamma of 1,003,799 against 250,000, which the short wings produce and the report is meant to show.
+
+## What this does not do
+
+- The live window is a few weeks, so nothing built on captured chains is a statistical result.
+- Option prices are Yahoo's delayed quotes at 15:30 New York, not exchange data.
+- The COR3M comparison is a sector proxy, because COR3M covers single stocks and the realised side uses sector ETFs.
+- The timed PUT result is 1 specification of a family.
+- The risk book is a sample, not a real portfolio.
+
+`instructions/`, `review/`, `decisions/` and `PLAN.md` are the record of how this was built. The source outline is in [`project_outline/`](project_outline/). MIT licence, see [`LICENSE`](LICENSE).
~~~

`test_readme_tables_match_csvs` and `test_no_banned_words`:

```
============================= test session starts =============================
platform win32 -- Python 3.12.13, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Utkarsh\10. Quant Projects\7) Volatility Surface and Event Pricing\Volatility-Surface-and-Event-Pricing
configfile: pyproject.toml
plugins: platformdirs-4.13.6, socket-0.8.1
collected 26 items / 14 deselected / 12 selected

tests\test_readme.py ............                                        [100%]

====================== 12 passed, 14 deselected in 6.52s ======================
```

### E8. Step 11.4: deleted files

- `data/raw/.gitkeep`
- `outputs/figures/.gitkeep`
- `outputs/reports/.gitkeep`
- `outputs/tables/.gitkeep`
- `tests/fixtures/.gitkeep`

`Project Outline/` is now `project_outline/`. The old name remains only in `instructions/00_kickoff.md` and `instructions/11_section_11.md`, which are historical and were not edited.

Kept: `tests/test_placeholder.py`, `review/.gitkeep` and `docs/CONVENTIONS_RESOLVED.md`.

## Tests run

`ruff check .`:

```
All checks passed!
```

Pre-push suite at `813a2ac`, in clone `C:\vs11pre`, before the fix: `pytest -p socket --disable-socket -q`. It predates `6de2e14`, so it holds 1 test fewer than the fresh-clone run.

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
........................................................................ [ 35%]
........................................................................ [ 36%]
........................................................................ [ 38%]
........................................................................ [ 39%]
........................................................................ [ 41%]
........................................................................ [ 42%]
........................................................................ [ 44%]
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
........................................................................ [ 67%]
........................................................................ [ 68%]
........................................................................ [ 70%]
........................................................................ [ 71%]
........................................................................ [ 73%]
........................................................................ [ 74%]
........................................................................ [ 76%]
........................................................................ [ 77%]
........................................................................ [ 79%]
........................................................................ [ 80%]
........................................................................ [ 82%]
........................................................................ [ 83%]
........................................................................ [ 85%]
........................................................................ [ 86%]
........................................................................ [ 88%]
........................................................................ [ 89%]
........................................................................ [ 91%]
........................................................................ [ 92%]
........................................................................ [ 94%]
........................................................................ [ 95%]
........................................................................ [ 97%]
........................................................................ [ 98%]
................................................                         [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:894
  C:\vs11pre\.venv\Lib\site-packages\_pytest\config\__init__.py:894: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

tests/test_capture_health.py: 4 warnings
tests/test_correlation.py: 4 warnings
tests/test_vrp.py: 24 warnings
  C:\vs11pre\.venv\Lib\site-packages\pandas\core\series.py:848: Pandas4Warning: Series.values returning an ndarray that drops timezone information for DatetimeTZDtype is deprecated. In a future version, this will return the underlying DatetimeArray instead. Use 'Series.dt.tz_convert(None).to_numpy()' to get a NumPy array of UTC values, or 'Series.array' to get the ExtensionArray.
  See https://pandas.pydata.org/docs/dev/whatsnew/v3.1.0.html#whatsnew-310-deprecations-values for more details.
    warnings.warn(

tests/test_correlation.py::test_rv_screen_blank_below_min_days
  C:\vs11pre\volsurf\correlation.py:205: RuntimeWarning: invalid value encountered in scalar divide
    z = (r.atm_30 - prior.mean()) / prior.std(ddof=1)  # O-15 (a): ddof 1, today excluded

tests/test_snapshots.py::test_wait_chains_when_above_max_wait
  C:\vs11pre\.venv\Lib\site-packages\pytest_socket\__init__.py:138: UserWarning: A test tried to use socket.socket.
    raise SocketBlockedError()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
4728 passed, 35 warnings in 3967.93s (1:06:07)
wall clock 4004.9 s, exit 0
```

CI: run 42068655262, `6de2e14`: success, `4729 passed, 35 warnings in 391.76s (0:06:31)`.

## Fresh-clone check

`git clone` into `C:\vs11`, `uv venv --python 3.12`, install from `requirements-lock.txt`, `pip install -e . --no-deps`, then `pytest -p socket --disable-socket -q`:

```
HEAD 6de2e14
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
........................................................................ [ 35%]
........................................................................ [ 36%]
........................................................................ [ 38%]
........................................................................ [ 39%]
........................................................................ [ 41%]
........................................................................ [ 42%]
........................................................................ [ 44%]
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
........................................................................ [ 70%]
........................................................................ [ 71%]
........................................................................ [ 73%]
........................................................................ [ 74%]
........................................................................ [ 76%]
........................................................................ [ 77%]
........................................................................ [ 79%]
........................................................................ [ 80%]
........................................................................ [ 82%]
........................................................................ [ 83%]
........................................................................ [ 85%]
........................................................................ [ 86%]
........................................................................ [ 88%]
........................................................................ [ 89%]
........................................................................ [ 91%]
........................................................................ [ 92%]
........................................................................ [ 94%]
........................................................................ [ 95%]
........................................................................ [ 97%]
........................................................................ [ 98%]
.................................................                        [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:894
  C:\vs11\.venv\Lib\site-packages\_pytest\config\__init__.py:894: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

tests/test_capture_health.py: 4 warnings
tests/test_correlation.py: 4 warnings
tests/test_vrp.py: 24 warnings
  C:\vs11\.venv\Lib\site-packages\pandas\core\series.py:848: Pandas4Warning: Series.values returning an ndarray that drops timezone information for DatetimeTZDtype is deprecated. In a future version, this will return the underlying DatetimeArray instead. Use 'Series.dt.tz_convert(None).to_numpy()' to get a NumPy array of UTC values, or 'Series.array' to get the ExtensionArray.
  See https://pandas.pydata.org/docs/dev/whatsnew/v3.1.0.html#whatsnew-310-deprecations-values for more details.
    warnings.warn(

tests/test_correlation.py::test_rv_screen_blank_below_min_days
  C:\vs11\volsurf\correlation.py:205: RuntimeWarning: invalid value encountered in scalar divide
    z = (r.atm_30 - prior.mean()) / prior.std(ddof=1)  # O-15 (a): ddof 1, today excluded

tests/test_snapshots.py::test_wait_chains_when_above_max_wait
  C:\vs11\.venv\Lib\site-packages\pytest_socket\__init__.py:138: UserWarning: A test tried to use socket.socket.
    raise SocketBlockedError()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
4729 passed, 35 warnings in 2963.43s (0:49:23)
wall clock 2992.6 s, exit 0
```

## Runtime per step

Seconds, from each run's `runtime` lines. Cold 1 stopped in `answers`, so it has no later rows.

```
                cold 1 (failed)   cold 2    warm
stage                                           
snapshots                   1.5      0.6     0.6
capture_health              1.6      0.5     0.5
pricer_check               61.8     17.6    26.3
eep                      1063.3    323.6   881.9
clean_log                   5.9      1.0     3.6
iv_tree                   694.6    333.3   634.0
iv                       1915.5    706.1  1583.0
surface                  5701.9  13807.1     4.5
density                   134.3    251.7   170.3
tails                       8.7     31.4    16.7
events                      5.0     19.3    10.1
cor3m                       4.9     19.6     9.6
live_corr                   0.1      0.4     0.2
vrp                        17.0     54.1    25.3
strategies                  1.5      2.1     2.2
attribution                 1.7      2.5     1.7
risk                        0.7      0.8     0.9
report                      0.1      0.1     0.1
answers                              0.6     0.8
readme                              15.3    12.8
total                            15587.6  3385.2
```

These are measured times on a shared machine, not benchmarks. Only the surface stage has a cache, which is why the warm run still takes 3,385 s, mostly `iv`, `eep` and `iv_tree`. The surface stage took 13,807 s in cold 2 against 5,702 s in cold 1. I did not establish the cause of that difference. Cold 1 shared the machine with my pytest run and with a `run_all.py` from another project.

## Deviations from PLAN.md

- **O-50 to O-55** are implemented as (a), listed below.
- **`answers.csv` has a 6th column,** `source_column` (O-52).
- **Step 11.1 has 2 commits,** and the second follows 11.4, because the first cold run failed after the later steps were committed.
- **2 pushes:** the step commits first, because rule 12 clones the pushed repo, then the wrap-up commit.

## Not verified

- **2026-11-04 is not in the tables.** It reached the release after both runs.
- **Prices were not refreshed.** They end on 2026-11-02, and instruction 11 does not name a refresh. So 38 events stay pending and question 3 has N = 4.
- **Why the surface stage's time differs** between the cold runs (above).
- **Cold 1's rebuilt tables** were clean up to `report`, but that run never reached `answers` or `readme`. Cold 2 and the warm run cover them.

## Open questions

- **O-50, a source table for question 1.** (a) A `pricer_check` stage writes `outputs/tables/pricer_check.csv`. (b) Question 1 cites `review/section_2.md` by line.
- **O-51, a source table for the synthetic explained share.** (a) The attribution stage writes `outputs/tables/attribution_synthetic.csv`. (b) The median becomes a row of `hedging_frequency.csv`.
- **O-52, the layout of `answers.csv`.** (a) A 6th column, `source_column`, with a selector in `source_row`. (b) 5 columns, a row number in `source_row`, and a new table of aggregates.
- **O-53, how the README is built.** (a) A template rendered by a `readme` stage. (b) A hand-written README where a script replaces only the marked table blocks.
- **O-54, tests that read `outputs/tables/`.** (a) They read the committed tables. (b) They rebuild a small table set from the fixture.
- **O-55, where `run_all.py` gets the days.** (a) A first stage pulls the release, so a plain run needs an authenticated `gh`. (b) `run_all.py` stays offline and the user pulls first.

## Files changed

From `c2d116c`, before this review:

```
 LICENSE                                            |  21 +
 README.md                                          | 136 ++++++-
 data/raw/.gitkeep                                  |   0
 decisions/OPEN.md                                  |  17 +
 decisions/section_10_review.md                     |  13 +
 docs/METHODS.md                                    | 115 ++++++
 docs/README.template.md                            | 109 +++++
 outputs/figures/.gitkeep                           |   0
 outputs/reports/.gitkeep                           |   0
 outputs/reports/risk_2026-11-03.pdf                | Bin 4731 -> 4766 bytes
 outputs/tables/.gitkeep                            |   0
 outputs/tables/answers.csv                         |  52 +++
 outputs/tables/attribution_synthetic.csv           |  22 +
 outputs/tables/limit_breaches.csv                  |  18 +-
 outputs/tables/pricer_check.csv                    |  10 +
 outputs/tables/risk_book.csv                       |  10 +-
 outputs/tables/risk_grid.csv                       | 444 ++++++++++-----------
 .../07_Volatility_Surface_and_Event_Pricing.md     |   0
 scripts/run_all.py                                 | 196 ++++++++-
 tests/fixtures/.gitkeep                            |   0
 tests/test_answers.py                              | 112 ++++++
 tests/test_readme.py                               | 112 ++++++
 tests/test_risk.py                                 |  54 ++-
 tests/test_run_all.py                              |  65 +++
 volsurf/answers.py                                 | 269 +++++++++++++
 volsurf/readme.py                                  | 140 +++++++
 volsurf/risk.py                                    |  45 ++-
 27 files changed, 1691 insertions(+), 269 deletions(-)
```

## Reviewer reads

1. `instructions/11_section_11.status.md`
2. E1 and E4 in this file
3. `outputs/tables/answers.csv` (E6)
4. `README.md`
5. `decisions/OPEN.md`, O-50 to O-55
6. `volsurf/risk.py`, `vol_source` and `contract_vol`
