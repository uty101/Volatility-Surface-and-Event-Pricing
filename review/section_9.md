# Review: Section 9

## Section

Section 9: P&L attribution (`PLAN.md` steps 9.1 and 9.2), with instruction 09.

The section is complete. The identity holds, and the MEASURE value is 0.944138, the median over 21 daily steps. All 9 of the reviewer's GBM checks pass. The live median explained share is 0.936652 over N = 6 moves, which is a method demonstration only (kickoff Section 2 item 1). 2 new open items, O-45 and O-46, are implemented as (a) for the reviewer to confirm or switch.

## Steps completed

- 9.1  4ff57b6  step 9.1: attribution identity, straddle Greeks, explained share MEASURE. It also commits `decisions/section_8_review.md`, marks O-43 and O-44 decided, and adds O-45.
- 9.2  c01ff14  step 9.2: hedging frequency simulation, live attribution. It adds O-46 and the `attribution` stage.
- The wrap-up commit holds this file and the status file.

## Evidence

### E1. Step 9.1: tests and the MEASURE value

`.venv\Scripts\python -m pytest tests/test_attribution.py -p socket --disable-socket -v -s -W ignore`, the whole file at `c01ff14`. The `-s` output includes the 21 rows of the synthetic path:

```
============================= test session starts =============================
collecting ... collected 40 items

tests/test_attribution.py::test_identity_exact[0] PASSED
tests/test_attribution.py::test_identity_exact[1] PASSED
tests/test_attribution.py::test_identity_exact[2] PASSED
tests/test_attribution.py::test_identity_exact[3] PASSED
tests/test_attribution.py::test_identity_exact[4] PASSED
tests/test_attribution.py::test_identity_exact[5] PASSED
tests/test_attribution.py::test_identity_exact[6] PASSED
tests/test_attribution.py::test_identity_exact[7] PASSED
tests/test_attribution.py::test_identity_exact[8] PASSED
tests/test_attribution.py::test_identity_exact[9] PASSED
tests/test_attribution.py::test_identity_exact[10] PASSED
tests/test_attribution.py::test_identity_exact[11] PASSED
tests/test_attribution.py::test_identity_exact[12] PASSED
tests/test_attribution.py::test_identity_exact[13] PASSED
tests/test_attribution.py::test_identity_exact[14] PASSED
tests/test_attribution.py::test_identity_exact[15] PASSED
tests/test_attribution.py::test_identity_exact[16] PASSED
tests/test_attribution.py::test_identity_exact[17] PASSED
tests/test_attribution.py::test_identity_exact[18] PASSED
tests/test_attribution.py::test_identity_exact[19] PASSED
tests/test_attribution.py::test_bs_path_explained_share_measure     day           S        dS  dsigma     delta     gamma     theta  vega  vanna  volga     hedge  residual    option     total  explained_share
0     1   99.736604 -0.263396     0.0  0.018178 -0.004776  0.110599  -0.0   -0.0   -0.0 -0.018178 -0.000192  0.123809  0.105631         0.998179
1     2   98.943886 -0.792718     0.0  0.023843 -0.044580  0.113451  -0.0    0.0    0.0 -0.023843 -0.003644  0.089070  0.065227         0.944138
2     3   98.629482 -0.314405     0.0 -0.027778 -0.007213  0.114895  -0.0    0.0   -0.0  0.027778 -0.004189  0.075715  0.103492         0.959523
3     4   98.864209  0.234727     0.0  0.033161 -0.004104  0.116582  -0.0   -0.0   -0.0 -0.033161 -0.001305  0.144335  0.111174         0.988266
4     5   97.593026 -1.271182     0.0 -0.143521 -0.124267  0.121067  -0.0    0.0   -0.0  0.143521 -0.013512 -0.160233 -0.016712         0.191481
5     6   98.961093  1.368067     0.0  0.433170 -0.139699  0.114313  -0.0   -0.0   -0.0 -0.433170  0.004752  0.412537 -0.020633         0.769670
6     7   99.781341  0.820248     0.0  0.091867 -0.055037  0.129293  -0.0   -0.0   -0.0 -0.091867  0.001959  0.168081  0.076215         0.974300
7     8   99.921995  0.140654     0.0 -0.002724 -0.001677  0.136481  -0.0   -0.0    0.0  0.002724  0.000123  0.132203  0.134927         0.999087
8     9  100.734642  0.812648     0.0 -0.033028 -0.057968  0.141895  -0.0    0.0   -0.0  0.033028  0.000392  0.051291  0.084319         0.995346
9    10   99.694786 -1.039856     0.0  0.191725 -0.095488  0.145191  -0.0   -0.0   -0.0 -0.191725  0.000307  0.241734  0.050009         0.993864
10   11   99.051391 -0.643395     0.0 -0.005378 -0.039641  0.154672  -0.0    0.0   -0.0  0.005378 -0.005914  0.103739  0.109117         0.945800
11   12   99.704484  0.653092     0.0  0.093023 -0.042430  0.158830  -0.0   -0.0   -0.0 -0.093023  0.002840  0.212263  0.119240         0.976179
12   13   98.645843 -1.058641     0.0 -0.018250 -0.118615  0.171915  -0.0    0.0   -0.0  0.018250 -0.013861  0.021190  0.039439         0.648553
13   14   99.517674  0.871831     0.0  0.224898 -0.081714  0.170885  -0.0   -0.0   -0.0 -0.224898  0.008012  0.322082  0.097184         0.917554
14   15  100.551217  1.033543     0.0  0.078263 -0.127887  0.195358  -0.0   -0.0   -0.0 -0.078263  0.000862  0.146596  0.068333         0.987383
15   16  101.343029  0.791811     0.0 -0.140599 -0.078600  0.209923  -0.0    0.0   -0.0  0.140599 -0.009949 -0.019226  0.121373         0.918026
16   17  101.802840  0.459811     0.0 -0.181172 -0.025863  0.207442  -0.0    0.0   -0.0  0.181172 -0.010937 -0.010531  0.170641         0.935906
17   18  104.579026  2.776186     0.0 -1.512683 -0.906878  0.199058  -0.0    0.0   -0.0  1.512683  0.114122 -2.106381 -0.593698         0.807778
18   19  104.697534  0.118508     0.0 -0.114110 -0.000280  0.024583  -0.0    0.0   -0.0  0.114110  0.012767 -0.077039  0.037070         0.655609
19   20  104.597431 -0.100103     0.0  0.099179 -0.000072  0.005359  -0.0   -0.0   -0.0 -0.099179  0.016833  0.121299  0.022120         0.239004
20   21  104.689811  0.092380     0.0 -0.092349 -0.000004  0.000109  -0.0    0.0   -0.0  0.092349  0.015845 -0.076399  0.015950         0.006584
MEASURE median explained share, 21 daily steps: 0.944138
PASSED
tests/test_attribution.py::test_total_is_the_change_in_value_plus_hedge PASSED
tests/test_attribution.py::test_theta_reprices_with_only_t_shortened PASSED
tests/test_attribution.py::test_dsigma_is_the_contract_vol_change PASSED
tests/test_attribution.py::test_greeks_match_bsm_call_plus_put[100.0-100.0-0.2] PASSED
tests/test_attribution.py::test_greeks_match_bsm_call_plus_put[90.0-100.0-0.35] PASSED
tests/test_attribution.py::test_greeks_match_bsm_call_plus_put[112.0-100.0-0.15] PASSED
tests/test_attribution.py::test_value_and_delta_match_the_live_mark PASSED
tests/test_attribution.py::test_value_at_expiry_is_intrinsic PASSED
tests/test_attribution.py::test_attribute_live_matches_live_straddles PASSED
tests/test_attribution.py::test_attribute_live_skips_rows_with_no_value PASSED
tests/test_attribution.py::test_simulation_deterministic PASSED
tests/test_attribution.py::test_more_frequent_hedging_lower_error_gbm PASSED
tests/test_attribution.py::test_unknown_model_raises PASSED
tests/test_attribution.py::test_hedge_run_by_hand PASSED
tests/test_attribution.py::test_cash_accrues_at_r PASSED
tests/test_attribution.py::test_straddle_delta_is_call_plus_put_delta PASSED
tests/test_attribution.py::test_straddle_delta_at_zero_vol_is_the_limit PASSED
tests/test_attribution.py::test_heston_price_with_tiny_vol_of_vol_is_bsm PASSED
tests/test_attribution.py::test_heston_paths_truncate_and_stay_finite PASSED

============================= 40 passed in 3.30s ==============================
```

**MEASURE: 0.944138**, the median of 1 − |residual| / |total| over the 21 daily steps of 1 path (`[sim] gbm`, seed `[run] seed`, dt = 1/252, σ fixed, dσ = 0 on every row). Under O-45 (b), with the option alone as `total`, the same path gives 0.959092.

**Why the last days score low.** The path ends deep in the money (S = 104.69, K = 100), so gamma and theta are close to 0, and the small total is mostly the carry. Instruction 09 fixes Θ as a reprice with only T changed, so the roll of F and D falls into the residual. On day 21 the residual is 0.015845 against r × dt × K = 0.04 / 252 × 100 = 0.015873, and the total is 0.015950, so the share is 0.006584. A bound on the share should sit on the median, not on the worst day.

`test_identity_exact` runs 20 random moves and asserts components + residual = total to 1e-12 absolute. The residual is defined as the difference, so only floating point separates the 2 sides.

### E2. Step 9.2: `hedging_frequency.csv` in full

```
    model  hedge_every_steps  error_mean  error_sd  cost_mean   cost_sd
0     gbm                  1    0.002295  0.241395   0.105833  0.039590
1     gbm                 13    0.002311  0.862063   0.029056  0.009896
2     gbm                 65    0.011767  1.762867   0.014300  0.004887
3  heston                  1    0.000818  0.812829   0.104074  0.040147
4  heston                 13   -0.009613  1.166031   0.028771  0.010185
5  heston                 65   -0.007520  1.947346   0.014249  0.004956
```

### E3. Step 9.2: GBM against the reviewer's table

The opening premium is 4.605945 against the reviewer's 4.606. `se` is the reviewer's error sd / √20,000.

```
   hedge_every_steps  error_mean  rev_error_mean        se  mean_gap_in_se  error_sd  rev_error_sd  sd_gap_pct  cost_mean  rev_cost_mean  cost_gap_pct   cost_sd  rev_cost_sd
0                  1    0.002295         -0.0008  0.001718        1.801293  0.241395         0.243   -0.660630   0.105833          0.105      0.793579  0.039590        0.039
1                 13    0.002311         -0.0080  0.006081        1.695589  0.862063         0.860    0.239914   0.029056          0.029      0.192741  0.009896        0.010
2                 65    0.011767         -0.0250  0.012558        2.927697  1.762867         1.776   -0.739477   0.014300          0.014      2.143503  0.004887        0.005
```

| check | limit | k = 1 | k = 13 | k = 65 | result |
|---|---|---|---|---|---|
| error sd gap | 3% | −0.66% | +0.24% | −0.74% | pass |
| cost mean gap | 3% | +0.79% | +0.19% | +2.14% | pass |
| error mean gap | 3 se | 1.80 | 1.70 | 2.93 | pass |

The k = 65 mean is close to the limit, so it was checked on 10 other seeds (`[run] seed` + 1 to + 10, 20,000 paths each). These runs are a session check and are not in any output table.

```
         1         13        65
0  0.001280  0.003690  0.000262
1 -0.000743  0.007333 -0.005058
2  0.000898  0.002969  0.039704
3  0.000620  0.012121  0.019028
4 -0.003212 -0.001073  0.002227
5 -0.001191 -0.003503  0.009349
6  0.001802  0.001256 -0.000392
7  0.001400  0.006112  0.012029
8 -0.000448  0.007799  0.034332
9 -0.000654 -0.000706  0.005471
        mean  se_of_mean
1  -0.000025    0.000482
13  0.003600    0.001517
65  0.011695    0.004764
```

The 10-seed mean at k = 65 is +0.0117 (standard error 0.0048), against +0.0118 here. So this table sits on the expected value, and the reviewer's −0.025 was the low draw. The gap is Monte Carlo error, not a sign or timing difference. The reviewer's limit also treats the reviewer's number as exact: the difference of 2 independent runs has a standard error √2 larger, which makes the gap 2.07.

The error sd grows ×3.571 from k = 1 to k = 13, against the reviewer's ×3.54 and √13 = 3.606.

### E4. Step 9.2: Heston rows and the side-by-side at k = 1

**Error sd at k = 1: GBM 0.241395, Heston 0.812829, ×3.367.**

```
model                   gbm    heston  heston_over_gbm
hedge_every_steps                                     
1                  0.241395  0.812829         3.367219
13                 0.862063  1.166031         1.352605
65                 1.762867  1.947346         1.104647
model                   gbm    heston    sqrt_k
hedge_every_steps                              
1                  1.000000  1.000000  1.000000
13                 3.571178  1.434535  3.605551
65                 7.302841  2.395764  8.062258
```

The premium and the paths agree. The analytic premium is inside the Monte Carlo interval of the same paths, and the Heston error means in E2 are within 1 standard error of 0 at k = 1 and k = 65 and 1.2 at k = 13:

```
gbm premium 4.6059446777016575
heston premium (AnalyticHestonEngine) 4.541880710442829
   analytic   mc_mean     mc_se  gap_in_se
0  4.541881  4.567226  0.024516   1.033829
share of path-steps with v+ = 0: 9.726277372262773e-05  paths touching 0: 0.0056
```

**Why the error sd stops falling in proportion to √k under Heston (for the write-up).** Discrete hedging error comes from gamma on the moves between hedges, and it shrinks as hedges get closer together. That is the only source under GBM, so the sd falls close to √k: ×7.30 from k = 65 to k = 1, against √65 = 8.06. Under Heston there is a second source. The hedge uses the delta at √v_t, so it follows the current vol, but it holds only the underlying, so it is blind to vol moves. The straddle's vega is left open, and even continuous hedging leaves an unhedged vega P&L. More frequent hedging cannot remove that part. Here the sd falls only ×2.40 over the same range.

The variance shows this directly. Heston's error variance is GBM's plus a part that barely depends on k:

```
    k   var_gbm  var_heston   var_gap
0   1  0.058271    0.660690  0.602419
1  13  0.743153    1.359628  0.616475
2  65  3.107700    3.792156  0.684456
```

The gap is 0.60 to 0.68 at every frequency, which means an sd floor near √0.60 = 0.78. At k = 1 that floor is almost the whole of Heston's 0.81. So going from daily hedging to every step cuts GBM's error sd by 72% and Heston's by 30%, for the same 3.6-fold rise in cost. This is 1 parameter set, with the Heston spot drifting at r and GBM at μ = 0 (O-46).

### E5. Step 9.2: live attribution

`attribution_live.csv` in full. This is a **method demonstration: N = 6 moves, 3 positions, 4 snapshot days** (2026-10-28, 10-29, 10-30 and 11-03). No statistic here supports a claim about the book.

```
     open_day      expiry  strike        day0        day1        dt          dS    dsigma      delta      gamma      theta       vega     vanna     volga      hedge  residual     option      total  explained_share
0  2026-10-28  2026-11-27    7750  2026-10-28  2026-10-29  0.003252  -31.760254 -0.008891   0.690762  -1.342943   4.728704  15.772264 -0.019160  0.000163  -0.690762 -0.526931  19.302858  18.612096         0.971689
1  2026-10-28  2026-11-27    7750  2026-10-29  2026-10-30  0.002789 -141.109863  0.014274 -10.402106 -28.966301   3.828796 -24.622230  1.629711 -0.016575  10.402106  3.048997 -55.499708 -45.097602         0.932391
2  2026-10-28  2026-11-27    7750  2026-10-30  2026-11-03  0.011024    3.890136 -0.001848   1.648780  -0.017609  14.697972   2.640520  0.020959 -0.005832  -1.648780 -1.693747  17.291043  15.642263         0.891720
3  2026-10-29  2026-11-27    7720  2026-10-29  2026-10-30  0.002789 -141.109863  0.013376   1.976590 -27.984056   3.996499 -23.169474  0.222232  0.000402  -1.976590  2.618482 -42.339326 -44.315916         0.940913
4  2026-10-29  2026-11-27    7720  2026-10-30  2026-11-03  0.011024    3.890136 -0.002603   1.337024  -0.018122  16.091217   3.939086  0.024650 -0.007693  -1.337024 -1.537395  19.828766  18.491742         0.916860
5  2026-10-30  2026-11-30    7580  2026-10-30  2026-11-03  0.011024    3.890136 -0.004591  -0.061958  -0.016714  19.292062   8.065759  0.002415  0.000063   0.061958 -0.597762  26.683865  26.745823         0.977650
```

**1 live position end to end, the 2026-10-28 straddle (K = 7750, expiry 2026-11-27).** Its marks in `live_straddles.csv`:

```
     open_day      expiry  strike    mark_day         T            S            F         D       vol       value     delta  option_pnl  hedge_pnl  total_pnl status
0  2026-10-28  2026-11-27    7750  2026-10-28  0.082874  7730.430176  7752.375314  0.996634  0.134528  238.700000  0.021749    0.000000   0.000000   0.000000   open
1  2026-10-28  2026-11-27    7750  2026-10-29  0.079623  7698.669922  7719.755807  0.996766  0.125637  219.397142 -0.073716   19.302858  -0.690762  18.612096   open
2  2026-10-28  2026-11-27    7750  2026-10-30  0.076834  7557.560059  7578.018656  0.996879  0.139911  274.896850 -0.423836  -36.196850   9.711344 -26.485506   open
3  2026-10-28  2026-11-27    7750  2026-11-03  0.065810  7561.450195  7578.755094  0.997326  0.138063  257.605807 -0.460047  -18.905807   8.062564 -10.843243   open
```

Its moves are rows 0 to 2 above. They add up to the position's last total_pnl: 18.612096 − 45.097602 + 15.642263 = −10.843243.

Row 1 is the 10-30 sell-off: dS = −141.1, with gamma −28.97 and vega −24.62 together outweighing theta +3.83. The residual of +3.05 on a total of −45.10 is mostly the terms past second order on a 1.8% move.

Row 2 spans 4 calendar days, since there is no 11-02 snapshot, so dt = 0.011024 and theta is 14.70.

Every move matches the increments of `live_straddles.csv`, to the %.10g rounding of that file:

```
     open_day        day1      total  live_d_total           gap    option_gap     hedge_gap
0  2026-10-28  2026-10-29  18.612096     18.612096  0.000000e+00  1.000000e-08 -1.290000e-08
1  2026-10-28  2026-10-30 -45.097602    -45.097602 -2.000000e-08  9.000000e-08 -1.043000e-07
2  2026-10-28  2026-11-03  15.642263     15.642263  1.000000e-07  9.000000e-08  9.999996e-10
3  2026-10-29  2026-10-30 -44.315916    -44.315916  7.000000e-08  1.700000e-07 -9.800000e-08
4  2026-10-29  2026-11-03  18.491742     18.491742 -4.000000e-08 -5.000000e-08  1.000000e-09
5  2026-10-30  2026-11-03  26.745823     26.745823  4.000000e-08  3.000000e-08  4.140000e-09
max |components + residual - total| as written to the csv: 7.250015698900825e-09
moves per position:
open_day
2026-10-28    3
2026-10-29    2
2026-10-30    1
median explained share (a) hedged total: 0.93665221365  N = 6
median explained share (b) option total: 0.9416088361037288
```

**Median explained share: 0.936652 over the 6 moves** (range 0.891720 to 0.977650). Under O-45 (b) it is 0.941609.

### E6. Part A: mean VRP, labelled as decided

```
                                 label       first        last    n  mean_vrp
0   headline: every row with IV and RV  1990-01-31  2026-09-30  441  0.010372
1  GARCH era: rows with a forecast too  1993-12-31  2026-09-30  394  0.009699
```

The headline is 0.01037 over 441 months. The GARCH-era mean of 0.00970 over 394 months sits beside it.

## Tests run

`.venv\Scripts\python -m pytest -p socket --disable-socket -q` at `c01ff14`, the last 45 lines of output (the progress dots are cut):

```
........................................................................ [ 65%]
........................................................................ [ 67%]
........................................................................ [ 68%]
........................................................................ [ 70%]
........................................................................ [ 72%]
........................................................................ [ 73%]
........................................................................ [ 75%]
........................................................................ [ 76%]
........................................................................ [ 78%]
........................................................................ [ 79%]
........................................................................ [ 81%]
........................................................................ [ 82%]
........................................................................ [ 84%]
........................................................................ [ 86%]
........................................................................ [ 87%]
........................................................................ [ 89%]
........................................................................ [ 90%]
........................................................................ [ 92%]
........................................................................ [ 93%]
........................................................................ [ 95%]
........................................................................ [ 97%]
........................................................................ [ 98%]
..............................................................           [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:894
  C:\Utkarsh\10. Quant Projects\7) Volatility Surface and Event Pricing\Volatility-Surface-and-Event-Pricing\.venv\Lib\site-packages\_pytest\config\__init__.py:894: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

tests/test_capture_health.py: 4 warnings
tests/test_correlation.py: 4 warnings
tests/test_vrp.py: 24 warnings
  C:\Utkarsh\10. Quant Projects\7) Volatility Surface and Event Pricing\Volatility-Surface-and-Event-Pricing\.venv\Lib\site-packages\pandas\core\series.py:848: Pandas4Warning: Series.values returning an ndarray that drops timezone information for DatetimeTZDtype is deprecated. In a future version, this will return the underlying DatetimeArray instead. Use 'Series.dt.tz_convert(None).to_numpy()' to get a NumPy array of UTC values, or 'Series.array' to get the ExtensionArray.
  See https://pandas.pydata.org/docs/dev/whatsnew/v3.1.0.html#whatsnew-310-deprecations-values for more details.
    warnings.warn(

tests/test_correlation.py::test_rv_screen_blank_below_min_days
  C:\Utkarsh\10. Quant Projects\7) Volatility Surface and Event Pricing\Volatility-Surface-and-Event-Pricing\volsurf\correlation.py:205: RuntimeWarning: invalid value encountered in scalar divide
    z = (r.atm_30 - prior.mean()) / prior.std(ddof=1)  # O-15 (a): ddof 1, today excluded

tests/test_snapshots.py::test_wait_chains_when_above_max_wait
  C:\Utkarsh\10. Quant Projects\7) Volatility Surface and Event Pricing\Volatility-Surface-and-Event-Pricing\.venv\Lib\site-packages\pytest_socket\__init__.py:138: UserWarning: A test tried to use socket.socket.
    raise SocketBlockedError()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
4598 passed, 35 warnings in 1157.32s (0:19:17)
```

`.venv\Scripts\ruff check .`: `All checks passed!`

**Determinism.** `scripts/run_all.py --stage attribution` run twice gives the same SHA-256 for `hedging_frequency.csv` and `attribution_live.csv`.

## Fresh-clone check

At `c01ff14` (Windows, `C:\vs9`): `git clone`, `uv venv --python 3.12`, `uv pip install -r requirements-lock.txt`, `uv pip install -e . --no-deps`, then `.venv\Scripts\python -m pytest -p socket --disable-socket -q`. The first launch died before pytest finished, because its output file was on `C:\`, which is not writable here, even though the shell reported exit code 0. That run is not counted. The run below is a full rerun in the same clone, with the last 45 lines of output kept (the progress dots are cut):

```
........................................................................ [ 65%]
........................................................................ [ 67%]
........................................................................ [ 68%]
........................................................................ [ 70%]
........................................................................ [ 72%]
........................................................................ [ 73%]
........................................................................ [ 75%]
........................................................................ [ 76%]
........................................................................ [ 78%]
........................................................................ [ 79%]
........................................................................ [ 81%]
........................................................................ [ 82%]
........................................................................ [ 84%]
........................................................................ [ 86%]
........................................................................ [ 87%]
........................................................................ [ 89%]
........................................................................ [ 90%]
........................................................................ [ 92%]
........................................................................ [ 93%]
........................................................................ [ 95%]
........................................................................ [ 97%]
........................................................................ [ 98%]
..............................................................           [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:894
  C:\vs9\.venv\Lib\site-packages\_pytest\config\__init__.py:894: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

tests/test_capture_health.py: 4 warnings
tests/test_correlation.py: 4 warnings
tests/test_vrp.py: 24 warnings
  C:\vs9\.venv\Lib\site-packages\pandas\core\series.py:848: Pandas4Warning: Series.values returning an ndarray that drops timezone information for DatetimeTZDtype is deprecated. In a future version, this will return the underlying DatetimeArray instead. Use 'Series.dt.tz_convert(None).to_numpy()' to get a NumPy array of UTC values, or 'Series.array' to get the ExtensionArray.
  See https://pandas.pydata.org/docs/dev/whatsnew/v3.1.0.html#whatsnew-310-deprecations-values for more details.
    warnings.warn(

tests/test_correlation.py::test_rv_screen_blank_below_min_days
  C:\vs9\volsurf\correlation.py:205: RuntimeWarning: invalid value encountered in scalar divide
    z = (r.atm_30 - prior.mean()) / prior.std(ddof=1)  # O-15 (a): ddof 1, today excluded

tests/test_snapshots.py::test_wait_chains_when_above_max_wait
  C:\vs9\.venv\Lib\site-packages\pytest_socket\__init__.py:138: UserWarning: A test tried to use socket.socket.
    raise SocketBlockedError()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
4598 passed, 35 warnings in 1144.36s (0:19:04)
```

### CI

On `c01ff14` (run 41731723151, Linux): success. Ruff `All checks passed!`; pytest `4598 passed, 35 warnings in 398.13s (0:06:38)`.

## Runtime per step

- 9.1: `tests/test_attribution.py` in full, 3.11 s for 40 tests.
- 9.2: `scripts/run_all.py --stage attribution`, 4.4 s, both models at 20,000 paths and 273 steps.

## Deviations from PLAN.md

1. **Moves per position.** Instruction 09 says 3 day-to-day moves per position. Only the 2026-10-28 position has 3. The 10-29 position has 2, the 10-30 position has 1, and the 11-03 position has its opening mark only, so no move. N is 6, not 12.
2. **Helpers beyond the fixed signatures.** `volsurf/attribution.py` also has `straddle_value`, `straddle_greeks`, `bs_path_attribution`, `attribute_live`, `straddle_delta`, `heston_straddle_price`, `gbm_paths`, `heston_paths` and `hedge_run`. `attribute_day` and `simulate_hedging` keep their signatures.
3. **`attribute_day` takes straddles only.** Kickoff 5.10 says "per option position", and the only positions it attributes are straddles. `pos` holds strike and side.
4. **Tests beyond PLAN.** `tests/test_attribution.py` has the 4 PLAN tests and 15 others. In my first draft of `test_more_frequent_hedging_lower_error_gbm` the assertion ran the wrong way: it required the error sd to fall down rows ordered k = 1, 13, 65. It failed on first run, I corrected the direction, and that draft was never committed. The test asserts what PLAN says, that more frequent hedging has lower error.
5. **No figures.** PLAN 9 and kickoff 9.1 and 9.2 name none, so Section 9 adds none.

## Not verified

- **The reviewer's GBM run is compared, not reproduced.** The draw order differs, as instruction 09 expects.
- **Heston has no reviewer check.** The session's own checks are the analytic premium against the same paths' discounted payoff (1.03 standard errors) and the small vol-of-vol limit against BSM (`test_heston_price_with_tiny_vol_of_vol_is_bsm`).
- **Full-truncation bias.** The Feller condition fails here (2κθ = 0.16 < ξ² = 0.25), and 0.56% of paths touch v = 0. No finer-step run was done.
- **The MEASURE value is 1 path.** It depends on the seed. The instruction asks for 1 path, so no spread over paths was measured.
- **New capture days.** Instruction 09 says 4 snapshot days, so no new day was pulled and `live_straddles.csv` is unchanged.

## Open questions

- **O-45 (`decisions/OPEN.md`): the `total` of the explained share.** (a) side × ΔV + hedge, the delta-hedged position. (b) side × ΔV, the option alone. Implemented as (a). `attribution_live.csv` holds `option` and `total`, so (b) needs no rerun. Measured: MEASURE 0.944138 against 0.959092, live median 0.936652 against 0.941609.
- **O-46 (`decisions/OPEN.md`): the simulation details and the table columns.** (a) Heston spot drifts at r; ln S is stepped; the frequencies share 1 set of paths per model; columns as listed in the item. (b) Add `mu = 0.0` to `[sim] heston`; step S directly; each frequency on its own paths. Implemented as (a).
- **MEASURE bound.** `test_bs_path_explained_share_measure` asserts only that the value is finite, until the reviewer sets a bound (rule 5).

## Files changed

- New: `volsurf/attribution.py`, `tests/test_attribution.py`, `decisions/section_8_review.md`, `outputs/tables/hedging_frequency.csv`, `outputs/tables/attribution_live.csv`, `review/section_9.md`, `instructions/09_section_9.status.md`.
- Changed: `scripts/run_all.py` (the `attribution` stage), `decisions/OPEN.md` (O-43 and O-44 decided, O-45 and O-46 added).

### Figures, by path

Section 9 adds and changes no figure. The figures in the repo, all from earlier sections:

```
outputs/figures/cor3m_vs_realised.png
outputs/figures/event_scatter.png
outputs/figures/event_term_structures.png
outputs/figures/spx_density_last.png
outputs/figures/spx_metrics.png
outputs/figures/spx_smile_fits_2026-10-28.png
outputs/figures/spx_smiles_2026-10-28.png
outputs/figures/spx_smiles_2026-10-29.png
outputs/figures/spx_smiles_2026-10-30.png
outputs/figures/spx_smiles_2026-11-03.png
outputs/figures/spx_surface_last.png
outputs/figures/vrp_cumulative.png
outputs/figures/vrp_drawdowns.png
outputs/figures/vrp_vix2_vs_rv.png
```

## Reviewer reads

1. `volsurf/attribution.py`: `attribute_day`, then `hedge_run` and `simulate_hedging`.
2. E3 and E4 of this file.
3. E5, for the live position end to end.
4. O-45 and O-46 in `decisions/OPEN.md`.
