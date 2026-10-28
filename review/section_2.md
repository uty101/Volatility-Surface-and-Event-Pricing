# Review: Section 2

## Section

Section 2: Pricing and Greeks (`PLAN.md` steps 2.1 to 2.3, with instruction 02). Instruction 02 part A also allowed the PLAN 1.1 and 8.2 updates, committed first.

## Steps completed

- A    809a596  section 2: PLAN 1.1 and 8.2 updated for the section 1 review
- 2.1  7590674  step 2.1: pricing
- 2.2  91dec32  step 2.2: greeks (adds `[tolerances.greeks_fd_abs] theta = 3e-5` and `rho = 1e-6`)
- 2.3  eb54907  step 2.3: early exercise premium table (also appends O-29 and O-30 to `decisions/OPEN.md`)

## Evidence

### D1. Test output grouped by test file, with the counts per parametrised test

Each test file run on its own on Windows at eb54907 (the last line of each run):

```
$ .venv/Scripts/pytest -p socket --disable-socket -q tests/test_capture_health.py
3 passed, 5 warnings in 3.06s
$ .venv/Scripts/pytest -p socket --disable-socket -q tests/test_data.py
21 passed, 5 warnings in 2.71s
$ .venv/Scripts/pytest -p socket --disable-socket -q tests/test_eep.py
3 passed, 1 warning in 5.29s
$ .venv/Scripts/pytest -p socket --disable-socket -q tests/test_fixture.py
4 passed, 5 warnings in 2.37s
$ .venv/Scripts/pytest -p socket --disable-socket -q tests/test_greeks.py
3026 passed, 1 warning in 25.53s
$ .venv/Scripts/pytest -p socket --disable-socket -q tests/test_placeholder.py
1 passed, 1 warning in 0.04s
$ .venv/Scripts/pytest -p socket --disable-socket -q tests/test_pricing.py
1264 passed, 1 warning in 31.39s
$ .venv/Scripts/pytest -p socket --disable-socket -q tests/test_pull_data.py
7 passed, 1 warning in 2.68s
$ .venv/Scripts/pytest -p socket --disable-socket -q tests/test_pull_snapshots.py
3 passed, 1 warning in 1.02s
$ .venv/Scripts/pytest -p socket --disable-socket -q tests/test_snapshots.py
10 passed, 5 warnings in 1.68s
```

Items per test function in the 3 Section 2 files (`pytest --collect-only -q`, counted by function):

```
tests/test_eep.py::test_eep_failed_solve_keeps_row_with_status                1
tests/test_eep.py::test_eep_nonnegative_on_synthetic                          1
tests/test_eep.py::test_eep_summary_columns                                   1
tests/test_greeks.py::test_book_greeks_long_short_same_contract_nets_to_zero  1
tests/test_greeks.py::test_book_greeks_sums                                   1
tests/test_greeks.py::test_greeks_vs_fd                                       1260
tests/test_greeks.py::test_greeks_vs_quantlib                                 1260
tests/test_greeks.py::test_theta_rho_vs_fd                                    504
tests/test_pricing.py::test_american_call_no_dividend_premium_zero            126
tests/test_pricing.py::test_american_put_no_dividend_premium_positive         1
tests/test_pricing.py::test_black76_equals_bsm                                252
tests/test_pricing.py::test_bsm_vs_quantlib                                   252
tests/test_pricing.py::test_crr_american_vs_quantlib                          252
tests/test_pricing.py::test_crr_european_vs_analytic                          252
tests/test_pricing.py::test_crr_n2000_under_one_second                        1
tests/test_pricing.py::test_crr_raises_on_bad_probability                     1
tests/test_pricing.py::test_european_parity                                   126
tests/test_pricing.py::test_kind_must_be_c_or_p                               1
```

Grid sizes: 252 cases are 2 kinds x 7 strikes x 6 tenors x 3 vols; 126 are the same without the kind (parity, and the q = 0 call premium, which is calls only). The Greek tests multiply by the Greeks covered: `test_greeks_vs_fd` 5 x 252 (delta, gamma, vega, vanna, volga), `test_theta_rho_vs_fd` 2 x 252, `test_greeks_vs_quantlib` 5 x 252 (delta, gamma, vega, theta, rho). Every parametrised id names the grid point, for example `test_greeks_vs_fd[vanna-P-K100-d7-s0.15]`.

### D2. Largest gap per grid test, with the grid point where it occurs

S 100, r 0.045, q 0.015 throughout (q = 0 for `amer_call_q0_premium`); T = days / 365; QuantLib dates `today + days` with `Actual365Fixed` (instruction 02 Section B). `crr_*` at N = `n_validate` = 2000. For the finite-difference rows, `bound` is the pass rule and `min_slack` is the smallest (bound − gap) over the 252 cases, so a positive value means every case passes. Theta and rho are compared with QuantLib with no conversion.

```
               check  n_cases  largest_gap                        bound kind   K  days  sigma    min_slack
     bsm_vs_quantlib      252 3.907985e-14                        1e-10    C  70    91   0.30          NaN
      black76_vs_bsm      252 4.973799e-14                        1e-12    C  70   365   0.30          NaN
              parity      126 1.776357e-14                        1e-10  C-P 120    91   0.60          NaN
crr_amer_vs_quantlib      252 6.825657e-03                         0.01    C  90   182   0.60          NaN
crr_euro_vs_analytic      252 3.868824e-03                        0.005    C 100   730   0.60          NaN
amer_call_q0_premium      126 0.000000e+00                        1e-12    C  70     7   0.15          NaN
            fd_delta      252 9.059858e-08   1e-05 x |analytic| + 1e-06    P 100     7   0.15 9.998040e-07
            fd_gamma      252 3.687893e-07   1e-05 x |analytic| + 4e-06    C 100     7   0.15 3.999576e-06
             fd_vega      252 5.474050e-06   1e-05 x |analytic| + 6e-05    P 130   730   0.15 5.998255e-05
            fd_theta      252 2.940024e-06   1e-05 x |analytic| + 3e-05    P 100     7   0.60 3.000000e-05
              fd_rho      252 8.747374e-08   1e-05 x |analytic| + 1e-06    P  90   730   0.15 1.000000e-06
            fd_vanna      252 1.140639e-06 1e-05 x |analytic| + 1.2e-05    P 100     7   0.15 1.131929e-05
            fd_volga      252 4.833923e-05  1e-05 x |analytic| + 0.0005    P  70   730   0.15 4.955999e-04
            ql_delta      252 2.553513e-15                        1e-08    C 100    30   0.15          NaN
            ql_gamma      252 1.552578e-16                        1e-08    C 110     7   0.30          NaN
             ql_vega      252 7.815970e-14                        1e-08    C 130   365   0.15          NaN
            ql_theta      252 4.405365e-13                        1e-08    C  90     7   0.60          NaN
              ql_rho      252 8.526513e-14                        1e-08    P 110   730   0.15          NaN
```

These agree with the reviewer's measurements in instruction 02 Section B and kickoff Correction 16: theta against fd 2.94e-6, rho against fd 8.75e-8, theta against QuantLib 4.4e-13, CRR American against QuantLib 6.8e-5 x S, CRR European against analytic 3.9e-5 x S; and kickoff step 2.2 for delta 9.1e-8, gamma 3.7e-7, vega 5.5e-6, vanna 1.1e-6, volga 4.8e-5.

### D3. CRR timing

`crr(100, 100, 730/365, 0.045, 0.015, 0.30, "P", 2000, american)`, 20 timed calls each, on Windows (seconds):

```
          count       min       50%       max
american                                     
False      20.0  0.007835  0.008291  0.016141
True       20.0  0.020341  0.021842  0.028580
```

The American tree at N = 2000 takes about 0.02 s, under the 1 s bound. Backward induction is vectorised over the nodes of each step (1 numpy operation per step for the continuation, 1 for the early exercise check), with the step loop in Python. `test_crr_n2000_under_one_second` asserts the bound on 1 call.

### D4. Early exercise premium table

#### `outputs/tables/eep_summary.csv` in full

```
   ticker kind           k_bin     n  median_vol_pts  max_vol_pts
0     SPY    C   (-inf, -0.10]   904       -0.015539    42.931249
1     SPY    C  (-0.10, -0.02]   763        0.004117     0.024866
2     SPY    C   (-0.02, 0.02]   525        0.006837     0.023746
3     SPY    C    (0.02, 0.10]   493       -0.004775     0.017733
4     SPY    C     (0.10, inf)   297       -0.027192     0.007192
5     SPY    P   (-inf, -0.10]  1379        0.009446     0.478022
6     SPY    P  (-0.10, -0.02]   835        0.064045     1.016281
7     SPY    P   (-0.02, 0.02]   496        0.219926     1.897363
8     SPY    P    (0.02, 0.10]   208        1.628884     5.215862
9     SPY    P     (0.10, inf)    44        1.447464     8.003193
10   AAPL    C   (-inf, -0.10]   168       -0.012931     0.207379
11   AAPL    C  (-0.10, -0.02]    75        0.012147     0.033718
12   AAPL    C   (-0.02, 0.02]    48        0.011201     0.035474
13   AAPL    C    (0.02, 0.10]    84        0.005688     0.034384
14   AAPL    C     (0.10, inf)    90       -0.022484     0.020342
15   AAPL    P   (-inf, -0.10]   159        0.045773     0.602976
16   AAPL    P  (-0.10, -0.02]    81        0.071617     1.124697
17   AAPL    P   (-0.02, 0.02]    47        0.177503     1.522301
18   AAPL    P    (0.02, 0.10]    85        0.844626     2.922865
19   AAPL    P     (0.10, inf)   109        4.800528    14.232209
```

#### Row status counts (`outputs/tables/eep_rows.csv`, 7,108 rows: SPY 5,982, AAPL 1,126, the clean rows of `clean_log_fixture.csv`)

```
ticker        status kind          k_bin  rows
   SPY            ok    C  (-inf, -0.10]   904
   SPY            ok    C (-0.10, -0.02]   763
   SPY     both_fail    C (-0.10, -0.02]     2
   SPY            ok    C  (-0.02, 0.02]   525
   SPY            ok    P (-0.10, -0.02]   835
   SPY            ok    P  (-0.02, 0.02]   496
   SPY            ok    C   (0.02, 0.10]   493
   SPY            ok    P   (0.02, 0.10]   208
   SPY            ok    P    (0.10, inf)    44
   SPY            ok    P  (-inf, -0.10]  1379
   SPY american_fail    P   (0.02, 0.10]     1
   SPY            ok    C    (0.10, inf)   297
   SPY     both_fail    C  (-inf, -0.10]    35
  AAPL            ok    C  (-inf, -0.10]   168
  AAPL            ok    C (-0.10, -0.02]    75
  AAPL            ok    C  (-0.02, 0.02]    48
  AAPL            ok    C   (0.02, 0.10]    84
  AAPL            ok    P (-0.10, -0.02]    81
  AAPL            ok    P  (-0.02, 0.02]    47
  AAPL            ok    P   (0.02, 0.10]    85
  AAPL            ok    P    (0.10, inf)   109
  AAPL     both_fail    C  (-inf, -0.10]   180
  AAPL            ok    P  (-inf, -0.10]   159
  AAPL            ok    C    (0.10, inf)    90
```

#### The 5 contracts with the largest premium, with every input

```
                                             5426                              5427                              4846                              3337                              5428
ticker                                        SPY                               SPY                               SPY                               SPY                               SPY
expiry                                 2027-09-17                        2027-09-17                        2027-06-17                        2027-01-15                        2027-09-17
kind                                            C                                 C                                 C                                 C                                 C
strike                                       50.0                              55.0                              80.0                              70.0                             120.0
contract_symbol                SPY270917C00050000                SPY270917C00055000                SPY270617C00080000                SPY270115C00070000                SPY270917C00120000
snap_utc         2026-10-28 15:01:42.593311+00:00  2026-10-28 15:01:42.593311+00:00  2026-10-28 15:01:41.350084+00:00  2026-10-28 15:01:37.567566+00:00  2026-10-28 15:01:42.593311+00:00
bid                                        718.23                             713.5                            689.03                            699.19                             648.7
ask                                         723.0                            718.32                            692.59                            702.65                             653.5
mid                                       720.615                            715.91                            690.81                            700.92                             651.1
S                                         770.375                           770.375                           770.375                           770.375                           770.375
T                                        0.888239                          0.888239                          0.636184                           0.21712                          0.888239
r                                        0.043945                          0.043945                          0.043353                          0.041548                          0.043945
q                                        0.009843                          0.009843                          0.009843                          0.009843                          0.009843
F                                      794.067298                        794.067298                        786.974679                        775.696419                        794.067298
k                                       -2.765145                         -2.669835                         -2.286169                         -2.405266                         -1.889676
k_bin                               (-inf, -0.10]                     (-inf, -0.10]                     (-inf, -0.10]                     (-inf, -0.10]                     (-inf, -0.10]
iv_american                              1.342547                          1.351185                           1.26431                          2.255419                          0.869308
iv_european                               1.77186                          1.707227                          1.530997                          2.472636                          1.047239
premium_vol_pts                         42.931249                         35.604251                         26.668769                         21.721677                         17.793108
status                                         ok                                ok                                ok                                ok                                ok
```

All 5 are deep ITM SPY calls (K 50 to 120 against S 770.375), where vega is close to 0: both implied vols are far above any sensible level (0.87 to 2.47), so a small price difference becomes many vol points. With q > 0, early exercise of a deep ITM call is optimal, so the premium itself is real; its size in vol points is not informative.

#### Sanity checks (printed by the stage, not tested)

Deep ITM puts (k > 0.10), then the bin with the largest median and the bin with the largest max per ticker:

```
   ticker kind        k_bin    n  median_vol_pts  max_vol_pts
9     SPY    P  (0.10, inf)   44        1.447464     8.003193
19   AAPL    P  (0.10, inf)  109        4.800528    14.232209
```

```
   ticker kind         k_bin    n  median_vol_pts  max_vol_pts
8     SPY    P  (0.02, 0.10]  208        1.628884     5.215862
19   AAPL    P   (0.10, inf)  109        4.800528    14.232209
```

```
   ticker kind          k_bin    n  median_vol_pts  max_vol_pts
0     SPY    C  (-inf, -0.10]  904       -0.015539    42.931249
19   AAPL    P    (0.10, inf)  109        4.800528    14.232209
```

AAPL OTM calls (k > 0.02):

```
   ticker kind         k_bin   n  median_vol_pts  max_vol_pts
13   AAPL    C  (0.02, 0.10]  84        0.005688     0.034384
14   AAPL    C   (0.10, inf)  90       -0.022484     0.020342
```

- AAPL OTM calls are close to 0, as expected: medians 0.0057 and −0.0225 vol points, max 0.034.
- AAPL: deep ITM puts carry the largest premium (median 4.80, max 14.23 vol points), as expected.
- SPY: **not as expected on the median.** Among puts the largest median is the (0.02, 0.10] bin (1.63) rather than deep ITM (1.45, n = 44), though deep ITM puts have the largest put max (8.00). Over all SPY rows the largest max is in deep ITM calls (42.93, the rows above). Reported, not changed.

#### Failed solves

Every `both_fail` row has a mid below both model values at σ = `iv_lo` = 0.005, so no vol in [`iv_lo`, `iv_hi`] reproduces it. These are deep ITM calls priced below the near-zero-vol carry value S e^(−qT) − K e^(−rT). The 1 `american_fail` is the SPY 2026-11-06 792 put, whose mid 21.625 is exactly intrinsic (792 − 770.375): the tree at `iv_lo` returns the same value to rounding, so brentq sees no sign change.

```
                      size  sum
ticker status                  
AAPL   both_fail       180  180
SPY    american_fail     1    0
       both_fail        37   37
```

```
     ticker      expiry kind  strike     bid     ask      mid           S         T         r         q  value_at_iv_lo_american  value_at_iv_lo_european  value_at_iv_hi_american         status
45      SPY  2026-10-29    C   750.0   19.89   20.96   20.425  770.375000  0.003308  0.040683  0.009843                20.450837                20.450837                97.590328      both_fail
1019    SPY  2026-11-06    P   792.0   20.41   22.84   21.625  770.375000  0.025340  0.040683  0.009843                21.625000                21.001075               252.302380  american_fail
1822    SPY  2026-11-30    C   595.0  174.22  177.37  175.795  770.375000  0.091093  0.040734  0.009843               176.888231               176.888231               467.434364      both_fail
2854    SPY  2026-12-31    C   624.0  144.94  148.40  146.670  770.375000  0.176024  0.041283  0.009843               149.559383               149.559383               566.807998      both_fail
6022   AAPL  2026-11-04    C   280.0   64.45   66.55   65.500  345.480011  0.019858  0.040683  0.003068                65.685079                65.685079               122.557044      both_fail
6023   AAPL  2026-11-04    C   300.0   44.45   46.70   45.575  345.480011  0.019858  0.040683  0.003068                45.701230                45.701230               113.502664      both_fail
6024   AAPL  2026-11-04    C   305.0   39.05   42.05   40.550  345.480011  0.019858  0.040683  0.003068                40.705268                40.705268               111.282001      both_fail
```

#### Negative premiums are tree error at `n_prod`

Several medians are slightly negative (OTM calls, deep OTM puts). The American IV comes from the CRR tree at `n_prod` = 200 and the European IV from closed-form BSM, so where the true premium is near 0 the tree's discretisation error decides the sign. On synthetic puts the n = 200 European tree misses BSM by up to 0.015, more than the American premium on short-dated OTM strikes:

```
   T   K  crr_american_n200          bsm  crr_european_n200  american_minus_bsm  tree_european_error
0.05  70       3.256891e-08 4.598741e-08       3.253390e-08       -1.341849e-08        -1.345351e-08
0.05  85       1.434991e-02 1.465147e-02       1.432806e-02       -3.015602e-04        -3.234134e-04
0.05 100       2.604184e+00 2.598104e+00       2.594765e+00        6.079983e-03        -3.339160e-03
0.05 115       1.500135e+01 1.487191e+01       1.487155e+01        1.294406e-01        -3.607828e-04
0.05 130       3.000000e+01 2.979034e+01       2.979033e+01        2.096638e-01        -8.267808e-06
0.25  70       3.076847e-02 3.111643e-02       3.062419e-02       -3.479664e-04        -4.922436e-04
0.25  85       8.882732e-01 8.806797e-01       8.823474e-01        7.593525e-03         1.667724e-03
0.25 100       5.628872e+00 5.576068e+00       5.568637e+00        5.280406e-02        -7.431139e-03
0.25 115       1.602741e+01 1.576244e+01       1.576582e+01        2.649721e-01         3.382479e-03
0.25 130       3.000124e+01 2.926702e+01       2.926649e+01        7.342226e-01        -5.260061e-04
0.50  70       2.814375e-01 2.808255e-01       2.788898e-01        6.120146e-04        -1.935654e-03
0.50  85       2.199250e+00 2.167495e+00       2.172658e+00        3.175491e-02         5.163040e-03
0.50 100       7.749682e+00 7.622385e+00       7.611938e+00        1.272971e-01        -1.044671e-02
0.50 115       1.750286e+01 1.707304e+01       1.707895e+01        4.298162e-01         5.907642e-03
0.50 130       3.035210e+01 2.935520e+01       2.935509e+01        9.969040e-01        -1.080325e-04
1.00  70       1.154235e+00 1.132239e+00       1.134867e+00        2.199675e-02         2.628356e-03
1.00  85       4.323604e+00 4.222922e+00       4.223669e+00        1.006828e-01         7.476181e-04
1.00 100       1.053095e+01 1.022510e+01       1.021050e+01        3.058536e-01        -1.459782e-02
1.00 115       1.981946e+01 1.905210e+01       1.905975e+01        7.673670e-01         7.654863e-03
1.00 130       3.157822e+01 3.006345e+01       3.006153e+01        1.514768e+00        -1.917437e-03
```

This is why `test_eep_nonnegative_on_synthetic` uses an expiry about 1 year out with strikes 85 to 130, where the premium is well above the tree error.

#### Determinism

The `eep` stage was run twice; both CSVs are byte-identical (sha256):

```
cb024cb633aef2b7ddc8963f91422bbe552e0b6a7cdf5a13c00e92a569b5d308 *outputs/tables/eep_rows.csv
38c815de0167c3fdd85a0d08c4cfde7d5e02a9e47d417940e04259e7202136f9 *outputs/tables/eep_summary.csv
cb024cb633aef2b7ddc8963f91422bbe552e0b6a7cdf5a13c00e92a569b5d308 *outputs/tables/eep_rows.csv
38c815de0167c3fdd85a0d08c4cfde7d5e02a9e47d417940e04259e7202136f9 *outputs/tables/eep_summary.csv
```

### D5. Fresh-clone check and CI status of the final commit

The fresh clone is under Fresh-clone check below: 4342 passed at eb54907. CI (`gh run list`): workflow, head, event, conclusion, created, updated:

```
ci	eb54907	push	success	2026-10-28T16:16:37Z	2026-10-28T16:17:28Z	(run 40724360340)
```

eb54907 holds every step of this section. The commit that adds this review and the status file changes no code, so its CI result cannot be printed inside it.

## Tests run

`.venv/Scripts/pytest -p socket --disable-socket -q` on Windows, at eb54907. The 62 progress lines (only `.` characters, 4342 in all) are left out; everything else is as printed:

```
============================== warnings summary ===============================
  C:\Utkarsh\10. Quant Projects\7) Volatility Surface and Event Pricing\Volatility-Surface-and-Event-Pricing\.venv\Lib\site-packages\_pytest\config\__init__.py:894: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
  C:\Utkarsh\10. Quant Projects\7) Volatility Surface and Event Pricing\Volatility-Surface-and-Event-Pricing\.venv\Lib\site-packages\pandas\core\series.py:848: Pandas4Warning: Series.values returning an ndarray that drops timezone information for DatetimeTZDtype is deprecated. In a future version, this will return the underlying DatetimeArray instead. Use 'Series.dt.tz_convert(None).to_numpy()' to get a NumPy array of UTC values, or 'Series.array' to get the ExtensionArray.
  See https://pandas.pydata.org/docs/dev/whatsnew/v3.1.0.html#whatsnew-310-deprecations-values for more details.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
4342 passed, 5 warnings in 31.56s
```

`.venv/Scripts/ruff check .`:

```
All checks passed!
```

## Fresh-clone check

Cloned into `C:\Users\astha\AppData\Local\Temp\vs2` from GitHub after the push of eb54907. The pytest progress lines (only `.` characters) are left out; everything else is as printed:

```
$ git clone https://github.com/uty101/Volatility-Surface-and-Event-Pricing vs2
$ git log --oneline -1
eb54907 step 2.3: early exercise premium table
$ uv venv --python 3.12
$ uv pip install -r requirements-lock.txt
$ uv pip install -e . --no-deps
$ .venv/Scripts/pytest -p socket --disable-socket -q
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:894
  C:\Users\astha\AppData\Local\Temp\vs2\.venv\Lib\site-packages\_pytest\config\__init__.py:894: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
  C:\Users\astha\AppData\Local\Temp\vs2\.venv\Lib\site-packages\pandas\core\series.py:848: Pandas4Warning: Series.values returning an ndarray that drops timezone information for DatetimeTZDtype is deprecated. In a future version, this will return the underlying DatetimeArray instead. Use 'Series.dt.tz_convert(None).to_numpy()' to get a NumPy array of UTC values, or 'Series.array' to get the ExtensionArray.
  See https://pandas.pydata.org/docs/dev/whatsnew/v3.1.0.html#whatsnew-310-deprecations-values for more details.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
4342 passed, 5 warnings in 72.03s (0:01:12)
exit=0
```

## Runtime per step

- A: edit only.
- 2.1: `tests/test_pricing.py` 31 s (1,264 items; the 252 QuantLib binomial engines at N = 2000 and the trees dominate).
- 2.2: `tests/test_greeks.py` 26 s (3,026 items).
- 2.3: the `eep` stage 169 s for 7,108 rows (2 brentq solves per row, the American one on a 200-step tree); `tests/test_eep.py` 5 s.
- Full suite: 32 s on Windows, 72 s in the fresh clone.

## Deviations from PLAN.md

1. **Premium sign.** PLAN 2.3 defines premium = (American IV − European IV) × 100; instruction 02 step 2.3 defines it as (European IV − American IV) × 100, positive when early exercise matters. Instruction 02 is followed (rule 13).
2. **`test_theta_rho_vs_fd_measure` is `test_theta_rho_vs_fd`** and asserts the bounds of instruction 02 Section B with the same pass rule as the other Greeks, since theta and rho are no longer MEASURE.
3. **`eep_summary.csv` columns** are those of instruction 02 (ticker, kind, k_bin, n, median_vol_pts, max_vol_pts), and **`outputs/tables/eep_rows.csv`** is added (instruction 02).
4. **Tests beyond the PLAN names:** `test_american_put_no_dividend_premium_positive`, `test_crr_n2000_under_one_second` and `test_book_greeks_long_short_same_contract_nets_to_zero` (instruction 02); `test_kind_must_be_c_or_p` and `test_eep_failed_solve_keeps_row_with_status` (added).
5. **`tests/conftest.py`** holds the QuantLib option builder shared by `test_pricing.py` and `test_greeks.py` (a fixture, `ql_option`).
6. **Where the 2.3 code lives (O-1 (a)).** `time_to_expiry`, `eep_rows` and `eep_summary` are in `volsurf/pricing.py`, the section's module; the driver is the `eep` stage of `scripts/run_all.py`.
7. **Pushes.** Steps 2.1 to 2.3 were pushed before the fresh-clone check, which clones the pushed repo (rule 12). This review and the status file are the last push.

## Not verified

Interpretations made while building, each small, for the reviewer to confirm:

- `fd_greeks` takes `h` as a dict keyed by the config names `fd_h_spot_rel`, `fd_h_vol`, `fd_h_t`, `fd_h_rate`, so `{k: getattr(cfg.tolerances, k) ...}` passes straight in.
- The extra put premium test (K 120, 365 days) uses N = `n_validate`; instruction 02 names no N. At N = 2000 the premium is 1.426, far above 1e-4.
- `bsm`, `black76` and `crr` take kind `C` or `P` (the CHAINS convention) and raise on anything else.
- `crr` steps the node prices down the tree by multiplying by u (node j of step i is node j of step i + 1 times u) instead of recomputing `exp` each step; rounding drift over 2000 steps is about 1e-13 relative.
- EEP solves use `scipy.optimize.brentq` with its default tolerances (xtol 2e-12, rtol about 8.9e-16); `[iv] iv_tol` is the Newton price tolerance of Section 3 and is not used here.
- EEP inputs per row: T from that row's own `snap_utc` (Convention 4.1, expiry at `[snapshot] close_ny`), r = `rate_curve(fred, 2026-10-28)` at that T, q per ticker from `dividends.csv` (SPY 0.009843, AAPL 0.003068), F = S e^((r − q)T), k = ln(K/F).
- `eep_summary.csv` holds only (ticker, kind, k_bin) groups with at least 1 `ok` row, and `n` counts `ok` rows; tickers are in fixture order, kinds C then P, bins in k order. Bin labels are the O-8 (a) intervals written as text, for example `(-0.10, -0.02]`.
- The CRR timing test runs on CI as well; at about 0.02 s it has a wide margin, but it is a wall-clock test.

## Open questions

- **O-29** EEP row status vocabulary: (a) `ok`, `american_fail`, `european_fail`, `both_fail`, with both vols and the premium blank on any failure (implemented); (b) `ok` and a single `solve_fail`, keeping the vol that solved and blanking only the premium.
- **O-30** `book_greeks` total row: (a) `expiry = total` on a row after each underlying's expiry rows (implemented); (b) blank `expiry` plus a `level` column (`expiry` or `underlying`).
- **SPY sanity check (D4).** Not an OPEN item, because no step in this section depends on it. Deep ITM SPY puts do not carry the largest median premium, and deep ITM SPY calls with vega near 0 give the largest values (up to 42.9 vol points). If the summary should exclude low-vega rows, Section 3 or a later instruction would need a rule.

## Files changed

- `PLAN.md` (part A: PLAN 1.1 and 8.2)
- `volsurf/pricing.py`, `tests/conftest.py`, `tests/test_pricing.py` (2.1)
- `volsurf/greeks.py`, `tests/test_greeks.py`, `config.toml` (2 keys under `[tolerances.greeks_fd_abs]`) (2.2)
- `volsurf/pricing.py` (EEP helpers), `scripts/run_all.py` (`eep` stage), `tests/test_eep.py`, `outputs/tables/eep_rows.csv`, `outputs/tables/eep_summary.csv`, `decisions/OPEN.md` (O-29, O-30) (2.3)
- `review/section_2.md`, `instructions/02_section_2.status.md`

## Reviewer reads

1. `instructions/02_section_2.status.md`
2. This file: D2, D4 (sanity checks, failed solves, negative premiums), Not verified, Open questions
3. `volsurf/pricing.py`
4. `volsurf/greeks.py`
5. `outputs/tables/eep_summary.csv`
6. `decisions/OPEN.md` O-29 and O-30
