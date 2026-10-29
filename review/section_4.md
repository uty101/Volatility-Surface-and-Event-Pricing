# Review: Section 4

## Section

Section 4: Volatility surface (`PLAN.md` steps 4.1 to 4.3, with instruction 04, which adds step 4.0 and replaces the penalty refit of kickoff Section 5.4).

**Stopped at step 4.1 under rule 4, as instruction 04 step 4.1 directs.** The fixture gate needs at least 23 accepted SPY slices. As built, SPY has 20 (`^SPX` 30 against 28, AAPL 14 against 13). The bounds are not lowered. Every rejected SPY slice is a short expiry, and each has a constrained refit with RMSE 0.2 to 0.5 vol points and min g ≥ 0. SLSQP ends those refits with "Iteration limit reached", so they do not count as converged (evidence S1). Step 4.0 is complete. Step 4.1 is built and committed, and its 5 PLAN tests pass. `test_fixture_accepted_slices` fails. Steps 4.2 and 4.3 are not built.

## Steps completed

- 4.0  5027fae  step 4.0: remove local task, one-sided flat rule, measurement script (with the part A decisions in `decisions/section_3_review.md` and the `CLAUDE.md` amendment)
- 4.1  de9b908  step 4.1: SVI per expiry (fixture gate fails for SPY, section stopped) (removes `[svi] penalty`, adds `[svi] max_rmse_volpts = 2.0`; the part B correction under `CLAUDE.md` Amendments; O-31 and O-32 in `decisions/OPEN.md`)
- 4.2  not built (stopped, see S1)
- 4.3  not built

## Evidence

### S1. Why the section stopped: SPY accepted slices on the fixture day

`test_fixture_accepted_slices` fits every fixture expiry with `fit_svi` on the OTM rows with an IV, from an IV table the test builds from the fixture (rule 7). Status counts:

```
status  ok  ok_refit  poor_fit
ticker
AAPL     8         6         0
SPY      8        12         4
^SPX     4        26         6
```

```
E           AssertionError: ('SPY', 20, 23)
```

The 4 rejected SPY slices are the 2026-10-29, 10-30, 11-03 and 11-04 expiries (1 to 7 days). On each, the first fit has a small RMSE but fails the butterfly check. Each constrained refit (from the first fit, then from the 5 starts) is printed below with its SLSQP outcome. Each slice has at least 1 refit with min g ≥ 0 and RMSE under 0.5 vol points, and SLSQP ends every one of those at its 1,000-iteration limit. The only refits that report `success` sit in poor local minima (RMSE 5.8 to 1,028 vol points). The best of those is kept, so the slice becomes `poor_fit`.

```
SPY 2026-10-29 43 k [-0.036,0.019] first rmse=0.474 min_g=-0.00674
   refit rmse=1.739 min_g=-8.83e-05 success=False nit=1000 msg=Iteration limit reached
   refit rmse=21.007 min_g=1 success=True nit=2 msg=Optimization terminated successfully
   refit rmse=0.385 min_g=0.00503 success=False nit=1000 msg=Iteration limit reached
   refit rmse=0.382 min_g=0.00279 success=False nit=1000 msg=Iteration limit reached
   refit rmse=19.562 min_g=0.339 success=True nit=11 msg=Optimization terminated successfully
   refit rmse=143.743 min_g=0.151 success=True nit=13 msg=Optimization terminated successfully
SPY 2026-10-30 75 k [-0.073,0.025] first rmse=0.895 min_g=-0.0034
   refit rmse=1.114 min_g=-1.69e-05 success=False nit=1000 msg=Iteration limit reached
   refit rmse=24.319 min_g=2.69e-05 success=False nit=3 msg=Inequality constraints incompatible
   refit rmse=985304.183 min_g=0.762 success=False nit=7 msg=Inequality constraints incompatible
   refit rmse=0.456 min_g=1.79e-06 success=False nit=1000 msg=Iteration limit reached
   refit rmse=6.226 min_g=0.00254 success=True nit=39 msg=Optimization terminated successfully
   refit rmse=12.580 min_g=0.0134 success=False nit=20 msg=Inequality constraints incompatible
SPY 2026-11-03 86 k [-0.140,0.036] first rmse=0.260 min_g=-0.00858
   refit rmse=1028.392 min_g=0.933 success=True nit=76 msg=Optimization terminated successfully
   refit rmse=5.819 min_g=0.295 success=True nit=55 msg=Optimization terminated successfully
   refit rmse=18.831 min_g=4.79e-06 success=False nit=3 msg=Inequality constraints incompatible
   refit rmse=0.242 min_g=0.023 success=False nit=1000 msg=Iteration limit reached
   refit rmse=18.560 min_g=0.423 success=True nit=11 msg=Optimization terminated successfully
   refit rmse=7.058 min_g=1 success=True nit=49 msg=Optimization terminated successfully
SPY 2026-11-04 96 k [-0.186,0.042] first rmse=0.271 min_g=-0.0114
   refit rmse=0.446 min_g=-1.29e-05 success=False nit=1000 msg=Iteration limit reached
   refit rmse=21.696 min_g=7.17e-06 success=False nit=3 msg=Inequality constraints incompatible
   refit rmse=21.696 min_g=5.07e-08 success=True nit=2 msg=Optimization terminated successfully
   refit rmse=0.225 min_g=0.0298 success=False nit=1000 msg=Iteration limit reached
   refit rmse=7.371 min_g=0.009 success=True nit=61 msg=Optimization terminated successfully
   refit rmse=6.452 min_g=0.00281 success=True nit=81 msg=Optimization terminated successfully
^SPX 2026-11-04 176 k [-0.288,0.106] first rmse=0.397 min_g=-0.0494
   refit rmse=0.454 min_g=-7.82e-11 success=False nit=1000 msg=Iteration limit reached
   refit rmse=4.004 min_g=0.0811 success=True nit=40 msg=Optimization terminated successfully
   refit rmse=22.603 min_g=1 success=True nit=7 msg=Optimization terminated successfully
   refit rmse=0.454 min_g=1.48e-05 success=False nit=1000 msg=Iteration limit reached
   refit rmse=22.596 min_g=1 success=False nit=7 msg=Inequality constraints incompatible
   refit rmse=22.603 min_g=0.999 success=False nit=54 msg=Singular matrix E in LSQ subproblem
```

The `^SPX` 2026-11-04 row shows that this build reads "converges" as the reviewer did. The only refit with `success` and min g ≥ −1e-10 there has RMSE 22.603, which matches the reviewer's 22.6 for that expiry.

**The same rejection set on `^SPX`.** The 6 rejected `^SPX` slices are the 6 expiries within 12 days (10-29, 10-30, 11-02, 11-03, 11-04, 11-05), the same 6 that part B names. Part B splits them 3 `butterfly_fail` and 3 `poor_fit`; here all 6 are `poor_fit`. In each case the kept refit converges with min g ≥ 0 and is then rejected by the RMSE gate. The `ok` counts differ too (`^SPX` 4 here against 2, SPY 8 against 11, AAPL 8 against 9): optimiser paths on these ill-conditioned slices differ between machines.

**The same test on Linux (CI run 40926086033 on `de9b908`) fails too, with a different rejection set.** There SPY has 22 accepted slices. `^SPX` has 29: it accepts 10-29 and 10-30 but rejects 11-02 to 11-10, and 3 of those are `butterfly_fail`, as in part B. Same code, same lock, same inputs: on these short expiries the SLSQP path, and so the status, depends on the platform. Counts and every row that is not `ok`, from the CI log:

```
status  butterfly_fail  ok  ok_refit  poor_fit
ticker                                        
AAPL                 0   8         6         0
SPY                  0   8        14         2
^SPX                 3   3        26         4
```

```
   ticker      expiry         T  n_quotes             a             b       rho          m         s  rmse_volpts         min_g  refit          status
0    ^SPX  2026-10-29  0.003309       153 -1.465822e-02  4.632049e-02 -0.230840  -0.066063  0.327658     1.718737  4.129870e-04   True        ok_refit
1    ^SPX  2026-10-30  0.006048       259 -4.283503e-03  3.049438e-02 -0.043769   0.006006  0.145275     0.678748  2.062036e-06   True        ok_refit
2    ^SPX  2026-11-02  0.014382       177  9.871340e-04  0.000000e+00 -0.955986  32.786209  5.827446    11.518427  1.000000e+00   True        poor_fit
3    ^SPX  2026-11-03  0.017121       181 -3.922570e-02  1.493371e-01  0.574336   0.244999  0.322665     0.443583 -8.117240e-02   True  butterfly_fail
4    ^SPX  2026-11-04  0.019861       176  1.964158e-13  0.000000e+00  0.999000  -0.174033  0.239822    22.603089  1.000000e+00   True        poor_fit
5    ^SPX  2026-11-05  0.022601       170  9.282640e-04  2.992597e-14  0.280966  -0.875787  0.342039     9.744741  1.000000e+00   True        poor_fit
6    ^SPX  2026-11-06  0.025340       251 -3.170804e-02  1.216267e-01  0.442469   0.172619  0.294134     0.357578 -6.532005e-02   True  butterfly_fail
7    ^SPX  2026-11-09  0.033560       162  1.224479e-03  0.000000e+00  0.696669   0.241290  0.394740    10.079543  1.000000e+00   True        poor_fit
8    ^SPX  2026-11-10  0.036299       158 -2.407407e-02  9.797222e-02  0.304479   0.115735  0.263120     0.231712 -5.103986e-02   True  butterfly_fail
9    ^SPX  2026-11-11  0.039039       153 -8.946373e-03  5.297340e-02 -0.150759   0.005211  0.181208     0.262019  2.815680e-06   True        ok_refit
10   ^SPX  2026-11-12  0.041779       137 -9.508922e-03  5.494242e-02 -0.165589   0.003857  0.186250     0.243970  4.120738e-09   True        ok_refit
11   ^SPX  2026-11-13  0.044518       219 -9.641320e-03  5.639931e-02 -0.163523   0.005449  0.184520     0.250025  3.253599e-09   True        ok_refit
12   ^SPX  2026-11-16  0.052738       126 -1.025721e-02  5.847490e-02 -0.174098   0.005208  0.189961     0.208945  2.830914e-10   True        ok_refit
13   ^SPX  2026-11-17  0.055477       121 -1.035039e-02  5.934391e-02 -0.175833   0.006601  0.189522     0.189049  1.193964e-08   True        ok_refit
14   ^SPX  2026-11-18  0.058217       120 -1.095442e-02  6.141079e-02 -0.181723   0.007240  0.194432     0.187329 -5.898060e-16   True        ok_refit
15   ^SPX  2026-11-19  0.060957       116 -1.135524e-02  6.345151e-02 -0.175171   0.008826  0.195273     0.202418  4.126506e-11   True        ok_refit
16   ^SPX  2026-11-20  0.063696       201 -1.276817e-02  6.737371e-02 -0.174967   0.007380  0.206222     0.272306  8.269233e-12   True        ok_refit
17   ^SPX  2026-11-23  0.071916       111 -1.242496e-02  6.722362e-02 -0.178803   0.009678  0.202262     0.172358 -8.743006e-15   True        ok_refit
18   ^SPX  2026-11-24  0.074655       106 -1.276809e-02  6.859923e-02 -0.180832   0.010138  0.204025     0.171534  1.804000e-09   True        ok_refit
19   ^SPX  2026-11-25  0.077395        99 -1.285876e-02  6.909699e-02 -0.182353   0.011526  0.204557     0.169319  8.666414e-08   True        ok_refit
20   ^SPX  2026-11-27  0.082874       168 -1.328152e-02  7.090077e-02 -0.181835   0.011444  0.205964     0.200756  1.073169e-13   True        ok_refit
21   ^SPX  2026-11-30  0.091094       461 -1.317006e-02  7.191848e-02 -0.165495   0.015660  0.201905     0.260829  9.074068e-11   True        ok_refit
22   ^SPX  2026-12-01  0.093833        36 -1.285996e-02  7.188453e-02 -0.170892   0.017192  0.198319     0.131541  8.209939e-08   True        ok_refit
23   ^SPX  2026-12-03  0.099313        59 -1.419975e-02  7.484522e-02 -0.174041   0.017687  0.210211     0.160011  1.600916e-07   True        ok_refit
24   ^SPX  2026-12-04  0.102052       130 -1.534422e-02  7.797212e-02 -0.170893   0.017226  0.217535     0.156956  1.011136e-13   True        ok_refit
25   ^SPX  2026-12-11  0.121230        95 -1.709230e-02  8.354757e-02 -0.172092   0.023090  0.228076     0.136201 -8.083811e-15   True        ok_refit
26   ^SPX  2026-12-18  0.140409       192 -1.989752e-02  9.069853e-02 -0.190333   0.022353  0.245365     0.183438 -3.406997e-15   True        ok_refit
27   ^SPX  2026-12-31  0.176025       602 -2.356892e-02  1.003227e-01 -0.197137   0.025030  0.264011     0.583713  8.458512e-15   True        ok_refit
28   ^SPX  2027-01-15  0.217121       148 -2.798970e-02  1.112014e-01 -0.204651   0.028550  0.284479     0.174563  1.755834e-09   True        ok_refit
29   ^SPX  2027-01-29  0.255477       297 -3.293394e-02  1.207970e-01 -0.211645   0.031083  0.308952     0.183241  3.915533e-09   True        ok_refit
30   ^SPX  2027-02-19  0.313011        64 -4.106172e-02  1.344500e-01 -0.213788   0.036189  0.346686     0.194527  1.369167e-10   True        ok_refit
31   ^SPX  2027-02-26  0.332189       161 -4.095641e-02  1.361914e-01 -0.208849   0.042455  0.343281     0.189652 -1.804112e-16   True        ok_refit
32   ^SPX  2027-03-19  0.389609        52 -4.853056e-02  1.489121e-01 -0.208255   0.048838  0.372994     0.188595  6.305600e-10   True        ok_refit
36    SPY  2026-10-29  0.003308        43 -8.385961e-05  5.171828e-04 -0.555951   0.199765  0.243154     2.591253  1.279632e-04   True        poor_fit
37    SPY  2026-10-30  0.006047        75 -3.670668e-03  3.051667e-02 -0.520567  -0.068455  0.146216     0.454928  1.304645e-09   True        ok_refit
38    SPY  2026-11-02  0.014381        77 -3.841723e-03  3.325943e-02 -0.561668  -0.073796  0.146325     0.232117  4.189615e-11   True        ok_refit
39    SPY  2026-11-03  0.017120        86 -6.487982e-02  1.596542e+00 -0.968512  -0.610249  0.163794     0.288202  1.285752e-08   True        ok_refit
40    SPY  2026-11-04  0.019860        96 -4.153076e-03  1.517652e-02  0.749353   0.938416  0.413800     7.728789  1.403513e-01   True        poor_fit
42    SPY  2026-11-06  0.025340       120 -1.031250e-02  5.081154e-02 -0.217043  -0.016668  0.215743     0.267948  9.160366e-08   True        ok_refit
45    SPY  2026-11-27  0.082874       135 -1.456315e-02  7.340492e-02 -0.165389   0.011728  0.216688     0.169847  1.359175e-10   True        ok_refit
46    SPY  2026-11-30  0.091093       270 -1.477239e-02  7.431536e-02 -0.166408   0.013397  0.217750     0.118357 -2.151057e-16   True        ok_refit
48    SPY  2026-12-18  0.140408       215 -2.206822e-02  9.372798e-02 -0.181351   0.021284  0.261398     0.243477  2.431478e-10   True        ok_refit
49    SPY  2026-12-31  0.176024       315 -2.118372e-02  9.682859e-02 -0.173267   0.032392  0.247207     0.155207  1.435692e-11   True        ok_refit
50    SPY  2027-01-15  0.217120       140 -1.753030e-01  4.791942e-01  0.639287   0.494730  0.483603     0.272477  2.861822e-12   True        ok_refit
52    SPY  2027-02-19  0.313011       107 -4.471525e-02  1.376466e-01 -0.200727   0.036767  0.366136     0.125345  7.010607e-10   True        ok_refit
54    SPY  2027-03-19  0.389609       154 -6.318415e-02  1.602736e-01 -0.217177   0.033302  0.442825     0.440545  6.820035e-10   True        ok_refit
55    SPY  2027-03-31  0.422485       189 -2.185277e-01  4.622262e-01  0.525197   0.484451  0.571218     0.713816  6.163793e-07   True        ok_refit
56    SPY  2027-06-17  0.636184       194 -9.940184e-02  1.999723e-01 -0.215624   0.060702  0.563604     0.187413  1.024997e-09   True        ok_refit
58    SPY  2027-09-17  0.888239       206 -4.114931e-01  4.661724e-01  0.317933   0.552297  0.965935     0.483452  1.057737e-12   True        ok_refit
60   AAPL  2026-10-30  0.006045        16 -2.687245e-02  5.869489e-02 -0.170252  -0.050345  0.471105     1.077081  3.125139e-11   True        ok_refit
61   AAPL  2026-11-04  0.019858        29  1.909368e-03  9.846348e-03 -0.528611   0.049808  0.031036     0.569930  3.655473e-01   True        ok_refit
63   AAPL  2026-11-13  0.044515        21 -1.438340e-03  4.581179e-02  0.400942   0.138080  0.110022     0.432040  8.719579e-07   True        ok_refit
64   AAPL  2026-11-20  0.063693        39 -7.329848e-03  6.258478e-02  0.318963   0.156818  0.191104     0.594277  1.019772e-09   True        ok_refit
66   AAPL  2026-12-04  0.102050        21 -3.031999e-03  6.455638e-02  0.408900   0.165258  0.143405     0.521015  2.540832e-10   True        ok_refit
67   AAPL  2026-12-18  0.140406        33 -8.938806e-03  8.009995e-02  0.349896   0.200011  0.214411     0.300646  6.179115e-09   True        ok_refit
```

**Measured, not built: refits that stop at the iteration limit.** In a scratch run (not committed), a refit also counted as converged when SLSQP stopped at the iteration limit (status 9) with the Section 5.4 bounds and constraints met to 1e-12. With that, every bound passes on Windows (not run on Linux):

```
status  ok  ok_refit  poor_fit
ticker
AAPL     8         6         0
SPY      8        16         0
^SPX     4        30         2
  ticker      expiry  rmse_volpts         min_g    status
0   ^SPX  2026-10-29     3.352176  3.611035e-12  poor_fit
1   ^SPX  2026-10-30     4.915271  2.099075e-01  poor_fit
```

That is option (a) of O-32. Option (b) keeps `success` only, as built, with new bounds.

**First fits.** The first fit keeps the lowest objective over the 5 starts, as Section 5.4 writes it, whether or not SLSQP reported success. An early build kept the lowest objective among starts that reported success. It is not used, because on short expiries the starts that report success are often degenerate. On `^SPX` 2026-11-10, for example, the converged start has b = 0 and RMSE 21.96 vol points, while 3 iteration-limited starts reach 0.23 to 0.25.

```
^SPX 2026-11-10 158
   fun=0.000990897 rmse=0.250 success=False nit=1000 msg=Iteration limit reached x=[-0.01239  0.06182  0.00666  0.03276  0.20834]
   fun=7.62135 rmse=21.963 success=True nit=6 msg=Optimization terminated successfully x=[ 0.       0.      -0.57639 -0.46449  0.57449]
   fun=0.000860492 rmse=0.233 success=False nit=1000 msg=Iteration limit reached x=[-0.0289   0.11639  0.39705  0.15067  0.27503]
   fun=0.0174209 rmse=1.050 success=False nit=1000 msg=Iteration limit reached x=[-1.69279  0.58282  0.17567  0.57683  2.95118]
   fun=0.000861794 rmse=0.234 success=False nit=1000 msg=Iteration limit reached x=[-0.02904  0.11709  0.4006   0.15203  0.27517]
```

On every rejected or refitted slice, the kept first fit meets the Section 5.4 bounds and constraints exactly (largest violation 0.0).

### D1. Step 4.0

**Unregister, on the owner's machine:**

```
PS> powershell -ExecutionPolicy Bypass -File scripts\windows\unregister_snapshot_task.ps1
Unregistered volsurf-snapshot
PS> Get-ScheduledTask volsurf-snapshot
Get-ScheduledTask volsurf-snapshot: No MSFT_ScheduledTask objects found with property 'TaskName' equal to 'volsurf-snapshot'.  Verify the value of the property and retry.
```

Before the unregister, `Get-ScheduledTask volsurf-snapshot` showed the task in state `Ready`. `scripts/windows/` and `[snapshot] local_task_times_utc` are deleted. Nothing in `volsurf/`, `scripts/` or `tests/` read the key. `decisions/capture.md` item 2 now says that GitHub Actions with `--wait` is the only scheduled capture. `scripts/snapshot.py` is not changed, so `--runner local` still works by hand.

**The flat-rule test** (`tests/test_iv.py::test_flat_rule_one_sided_at_immediate_exercise`): the P 130, 365-day, σ 0.15 American grid put, priced on CRR at `n_prod`, returns no vol with status `flat` from both `iv_american` and `iv_american_batch`. It passes.

**Round-trip status counts** (`-s` output of the 2 round-trip tests), unchanged from session 3b:

```
european: {'bounds': 6, 'flat': 28, 'brent': 102, 'newton': 116}
american: {'flat': 33, 'no_root': 5, 'brent': 206, 'bounds': 8}
```

That makes 424 within 1e-8, 80 flagged and 0 wrong, the reviewer's totals. The P 130 put was already `flat` in the scalar round trip. The one-sided rule changes the batch solver only, which now agrees.

**Other test output in `tests/test_iv.py`:**

```
sens = 0.00161734                                                     (Brent fallback, 7-day 30% OTM put)
statuses {'batch': 194, 'no_root': 6}; largest gap 2.89e-10, median 1.51e-10   (batch against scalar)
batch on 3992 fixture American OTM rows: 14.2 s; {'batch': 3992}
3992 rows, largest gap 0.00335205, median 0.000151423                 (reads iv_tree_convergence.csv)
9 passed
```

**Measurement script.** `scripts/measure_iv_tree.py` wrote `outputs/tables/iv_tree_convergence.csv` (3,992 rows) in 299 s:

```
N = 200 against N = 2000: 3992 rows, 6 Newton iterations, largest gap 0.00335205, median 0.000151423, unconverged 0
     ticker      expiry kind  strike    iv_200   iv_2000       gap
1435    SPY  2026-12-18    P   330.0  0.762681  0.759329  0.003352
1436    SPY  2026-12-18    P   335.0  0.749732  0.746564  0.003167
1437    SPY  2026-12-18    P   340.0  0.736979  0.733995  0.002985
1933    SPY  2027-01-15    P   255.0  0.802669  0.799764  0.002905
1942    SPY  2027-01-15    P   300.0  0.714073  0.711204  0.002869
```

The values match session 3b (largest 0.00335, median 0.00015). `test_american_n200_vs_n2000_measure` now reads the committed CSV, checks its columns and asserts that every gap is finite.

**Suite runtime after step 4.0:** `4489 passed, 5 warnings in 85.01s (0:01:25)` on Windows, against about 6 minutes in session 3b.

**`iv_summary.csv` after rerunning the IV stage:** unchanged. `diff` of the file before and after reports no difference, and `git diff --stat outputs/` is empty, so `parity_forwards_fixture.csv` is unchanged too.

```
          day ticker  n_in  n_solved  n_newton  n_brent  n_batch  n_bounds  n_no_root  n_flat  n_parity_fail
0  2026-10-28   ^SPX  6841      6841      2473     4368        0         0          0       0              0
1  2026-10-28    SPY  3531      3531         0        0     3531         0          0       0              0
2  2026-10-28   AAPL   461       461         0        0      461         0          0       0              0
```

### D2. Fixture fit status counts and every slice row that is not `ok`

Status counts are under S1. The full per-slice table, as `test_fixture_accepted_slices` prints it (parameters of rejected rows are those of the fit that was judged, shown for diagnosis only):

```
     ticker      expiry         T  n_quotes             a         b       rho         m         s  rmse_volpts         min_g  refit    status
0    ^SPX  2026-10-29  0.003309       153 -3.329347e-03  0.009329  0.837457  1.491683  0.653212     8.635073  3.348798e-01   True  poor_fit
1    ^SPX  2026-10-30  0.006048       259 -7.847009e-05  0.006281 -0.968443 -0.022073  0.082407     4.915271  2.099075e-01   True  poor_fit
2    ^SPX  2026-11-02  0.014382       177 -3.774571e-04  0.003174  0.466883  0.609265  0.134667     8.657657  4.709387e-01   True  poor_fit
3    ^SPX  2026-11-03  0.017121       181  2.394092e-13  0.000000  0.999000 -0.173131  0.231177    21.616740  1.000000e+00   True  poor_fit
4    ^SPX  2026-11-04  0.019861       176 -7.135712e-04  0.012813 -0.873862 -0.066120  0.143499     4.004472  8.109837e-02   True  poor_fit
5    ^SPX  2026-11-05  0.022601       170 -4.313414e-02  0.028100 -0.286817 -0.755729  1.625467    11.478629  4.304398e-03   True  poor_fit
6    ^SPX  2026-11-06  0.025340       251 -3.375002e-01  0.353238  0.472692  0.615403  1.085509     0.915600  1.278854e-02  False        ok
7    ^SPX  2026-11-09  0.033560       162 -8.030041e-03  0.049201 -0.133919  0.004600  0.173855     0.306958  1.413606e-07   True  ok_refit
8    ^SPX  2026-11-10  0.036299       158 -8.520776e-03  0.051089 -0.141014  0.005614  0.178411     0.287277  6.781631e-07   True  ok_refit
9    ^SPX  2026-11-11  0.039039       153 -8.981273e-03  0.053040 -0.151095  0.005096  0.181662     0.262042  9.464278e-08   True  ok_refit
10   ^SPX  2026-11-12  0.041779       137 -9.505796e-03  0.054944 -0.165490  0.003873  0.186186     0.243968  1.333522e-07   True  ok_refit
11   ^SPX  2026-11-13  0.044518       219 -9.640920e-03  0.056398 -0.163581  0.005447  0.184520     0.250026  3.162055e-07   True  ok_refit
12   ^SPX  2026-11-16  0.052738       126 -1.025721e-02  0.058475 -0.174098  0.005207  0.189962     0.208945 -7.979728e-16   True  ok_refit
13   ^SPX  2026-11-17  0.055477       121 -1.035065e-02  0.059343 -0.175844  0.006601  0.189528     0.189049 -7.228940e-14   True  ok_refit
14   ^SPX  2026-11-18  0.058217       120 -1.095282e-02  0.061407 -0.181747  0.007240  0.194417     0.187328 -2.567391e-16   True  ok_refit
15   ^SPX  2026-11-19  0.060957       116 -1.134281e-02  0.063429 -0.175153  0.008850  0.195139     0.202413  9.674494e-08   True  ok_refit
16   ^SPX  2026-11-20  0.063696       201 -1.276463e-02  0.067371 -0.174878  0.007398  0.206173     0.272305  1.444947e-07   True  ok_refit
17   ^SPX  2026-11-23  0.071916       111 -1.242466e-02  0.067223 -0.178814  0.009678  0.202261     0.172357  4.752795e-13   True  ok_refit
18   ^SPX  2026-11-24  0.074655       106 -1.276777e-02  0.068600 -0.180809  0.010141  0.204018     0.171534  3.028737e-09   True  ok_refit
19   ^SPX  2026-11-25  0.077395        99 -1.285876e-02  0.069097 -0.182352  0.011526  0.204557     0.169319  8.623398e-08   True  ok_refit
20   ^SPX  2026-11-27  0.082874       168 -1.327659e-02  0.070898 -0.181714  0.011469  0.205898     0.200755  1.340692e-07   True  ok_refit
21   ^SPX  2026-11-30  0.091094       461 -1.317055e-02  0.071919 -0.165501  0.015657  0.201909     0.260829  3.997263e-10   True  ok_refit
22   ^SPX  2026-12-01  0.093833        36 -1.286021e-02  0.071887 -0.170835  0.017198  0.198315     0.131541  1.070188e-08   True  ok_refit
23   ^SPX  2026-12-03  0.099313        59 -1.419975e-02  0.074845 -0.174042  0.017687  0.210211     0.160011  1.599856e-07   True  ok_refit
24   ^SPX  2026-12-04  0.102052       130 -1.534021e-02  0.077967 -0.170879  0.017234  0.217495     0.156955  6.932077e-08   True  ok_refit
25   ^SPX  2026-12-11  0.121230        95 -1.709026e-02  0.083543 -0.172108  0.023093  0.228065     0.136200  3.786360e-09   True  ok_refit
26   ^SPX  2026-12-18  0.140409       192 -1.989605e-02  0.090698 -0.190324  0.022355  0.245350     0.183438  1.401303e-12   True  ok_refit
27   ^SPX  2026-12-31  0.176025       602 -2.356853e-02  0.100323 -0.197131  0.025031  0.264007     0.583713 -3.816392e-16   True  ok_refit
28   ^SPX  2027-01-15  0.217121       148 -2.799081e-02  0.111202 -0.204673  0.028544  0.284488     0.174563  9.714451e-15   True  ok_refit
29   ^SPX  2027-01-29  0.255477       297 -3.293983e-02  0.120800 -0.211669  0.031074  0.308996     0.183241 -2.380041e-15   True  ok_refit
30   ^SPX  2027-02-19  0.313011        64 -4.106149e-02  0.134450 -0.213787  0.036189  0.346685     0.194527  7.189110e-13   True  ok_refit
31   ^SPX  2027-02-26  0.332189       161 -4.094965e-02  0.136185 -0.208836  0.042465  0.343245     0.189652  4.986857e-10   True  ok_refit
32   ^SPX  2027-03-19  0.389609        52 -4.853177e-02  0.148914 -0.208245  0.048839  0.372997     0.188595  4.588526e-10   True  ok_refit
33   ^SPX  2027-03-31  0.422486       497 -2.017555e-01  0.597680  0.650301  0.514929  0.457486     0.809052  1.602702e-02  False        ok
34   ^SPX  2027-06-30  0.671801       378 -2.827429e-01  1.100888  0.776893  0.672751  0.424101     0.378289  1.422465e-01  False        ok
35   ^SPX  2027-09-30  0.923856       305 -2.783382e-01  1.552556  0.835408  0.696986  0.345158     0.110923  1.663523e-01  False        ok
36    SPY  2026-10-29  0.003308        43 -1.833728e-05  0.000009  0.588216  1.133100  2.574563    19.561560  3.393504e-01   True  poor_fit
37    SPY  2026-10-30  0.006047        75 -2.495909e-03  0.025357  0.932235  1.120057  0.281348     6.226483  2.541539e-03   True  poor_fit
38    SPY  2026-11-02  0.014381        77 -3.837402e-03  0.033247 -0.561830 -0.073782  0.146244     0.232074  5.920876e-10   True  ok_refit
39    SPY  2026-11-03  0.017120        86 -4.549994e-03  0.004637  0.142393  0.637163  0.991556     5.819064  2.946615e-01   True  poor_fit
40    SPY  2026-11-04  0.019860        96 -6.753840e-02  0.040275 -0.275899 -0.342279  1.754819     6.451873  2.809149e-03   True  poor_fit
41    SPY  2026-11-05  0.022600        22 -2.828937e-01  0.273974  0.288712  0.354747  1.079728     0.178613  7.535430e-04  False        ok
42    SPY  2026-11-06  0.025340       120 -1.031718e-02  0.050821 -0.217076 -0.016687  0.215801     0.267963  7.899408e-10   True  ok_refit
43    SPY  2026-11-13  0.044518       142 -1.021660e-02  0.055945 -0.242116 -0.009904  0.199731     0.185253  5.755857e-03  False        ok
44    SPY  2026-11-20  0.063696       172 -1.099126e-02  0.062971 -0.217720  0.001210  0.193702     0.178919  8.985020e-03  False        ok
45    SPY  2026-11-27  0.082874       135 -1.456324e-02  0.073405 -0.165388  0.011728  0.216688     0.169848  1.179612e-16   True  ok_refit
46    SPY  2026-11-30  0.091093       270 -1.477129e-02  0.074316 -0.166361  0.013404  0.217732     0.118356  3.133258e-13   True  ok_refit
47    SPY  2026-12-04  0.102052       130 -1.609262e-02  0.078715 -0.180146  0.012784  0.226319     0.189217  4.371181e-03  False        ok
48    SPY  2026-12-18  0.140408       215 -2.206751e-02  0.093727 -0.181368  0.021282  0.261394     0.243477  3.217669e-12   True  ok_refit
49    SPY  2026-12-31  0.176024       315 -2.118115e-02  0.096827 -0.173211  0.032405  0.247184     0.155207  2.810230e-08   True  ok_refit
50    SPY  2027-01-15  0.217120       140 -1.753027e-01  0.479194  0.639287  0.494730  0.483602     0.272477  6.349615e-11   True  ok_refit
51    SPY  2027-01-29  0.255476       180 -2.613599e-02  0.111103 -0.212649  0.035074  0.274122     0.186453  9.454013e-03  False        ok
52    SPY  2027-02-19  0.313011       107 -4.471844e-02  0.137650 -0.200730  0.036762  0.366152     0.125345  7.624079e-10   True  ok_refit
53    SPY  2027-02-26  0.332189       146 -2.266146e-03  0.070084 -0.704347 -0.017238  0.148626     0.232590  1.827273e-01  False        ok
54    SPY  2027-03-19  0.389609       154 -6.318414e-02  0.160274 -0.217177  0.033302  0.442825     0.440545  6.818097e-10   True  ok_refit
55    SPY  2027-03-31  0.422485       189 -2.185919e-01  0.461841  0.524689  0.484283  0.571646     0.713817  1.520146e-09   True  ok_refit
56    SPY  2027-06-17  0.636184       194 -9.940184e-02  0.199972 -0.215624  0.060702  0.563604     0.187413  1.026082e-09   True  ok_refit
57    SPY  2027-06-30  0.671800       163 -9.461423e-04  0.090177 -0.690659  0.022407  0.184888     0.535809  2.308578e-01  False        ok
58    SPY  2027-09-17  0.888239       206 -4.114819e-01  0.466178  0.317953  0.552309  0.965905     0.483452  2.053682e-08   True  ok_refit
59    SPY  2027-09-30  0.923855       154  1.093462e-02  0.087652 -0.999000 -0.018544  0.179570     0.255200  2.387138e-01  False        ok
60   AAPL  2026-10-30  0.006045        16 -3.018245e-02  0.062757 -0.194630 -0.067729  0.496427     1.077565  4.328314e-09   True  ok_refit
61   AAPL  2026-11-04  0.019858        29  1.908839e-03  0.009852 -0.527885  0.049830  0.031061     0.569930  3.655350e-01   True  ok_refit
62   AAPL  2026-11-06  0.025337        35 -1.197021e+00  2.075568 -0.927171 -3.662874  1.542418     0.560237  9.217397e-03  False        ok
63   AAPL  2026-11-13  0.044515        21 -1.464677e-03  0.045841  0.400451  0.138313  0.110557     0.432042  8.656948e-07   True  ok_refit
64   AAPL  2026-11-20  0.063693        39 -5.612788e-02  1.002480  0.937609  0.562000  0.172660     0.577939  1.350160e-06   True  ok_refit
65   AAPL  2026-11-27  0.082871        24 -5.986820e-02  0.143781  0.531742  0.473526  0.526339     0.437561  4.843005e-02  False        ok
66   AAPL  2026-12-04  0.102050        21 -3.032924e-03  0.064558  0.408893  0.165264  0.143418     0.521015  7.996154e-09   True  ok_refit
67   AAPL  2026-12-18  0.140406        33 -8.948649e-03  0.080107  0.349842  0.200050  0.214522     0.300646  3.188371e-08   True  ok_refit
68   AAPL  2027-01-15  0.217118        40 -1.478920e-01  0.908820  0.887704  0.878955  0.378930     0.353721  1.853223e-01  False        ok
69   AAPL  2027-02-19  0.313008        23  5.305294e-03  0.053014 -0.228937  0.127668  0.217506     0.182109  3.124106e-01  False        ok
70   AAPL  2027-03-19  0.389607        28 -5.056243e-03  0.078262 -0.044363  0.191646  0.329686     0.164477  1.847334e-01  False        ok
71   AAPL  2027-04-16  0.466319        48  2.075895e-02  0.040354 -0.660886  0.106338  0.142435     0.137148  4.118161e-01  False        ok
72   AAPL  2027-06-17  0.636182        39 -1.219678e-01  0.224125  0.382672  0.591898  0.762502     0.151753  4.622989e-02  False        ok
73   AAPL  2027-09-17  0.888237        65 -1.759180e-01  0.255190  0.332621  0.649806  0.944979     0.126444  8.257292e-02  False        ok
```

### D3 to D5. Not reached

The SSVI parameters and `SURFACE_DAILY` rows, the 25-delta strike test and the figures all need steps 4.2 and 4.3, which are not built.

### D6. Fresh-clone check, CI and tonight's capture

The fresh-clone check and CI are in the sections below. Tonight's 2026-10-29 capture is not reported. Run 40898405093 is still sleeping in its Capture step until 19:30 UTC, and the section stopped before then (status file, item 3).

## Tests run

`.venv/Scripts/pytest -p socket --disable-socket -q` on Windows at `de9b908`:

```
FAILED tests/test_svi.py::test_fixture_accepted_slices - AssertionError: ('SP...
1 failed, 4494 passed, 5 warnings in 352.52s (0:05:52)
```

The failure is the S1 gate (`AssertionError: ('SPY', 20, 23)`). The 5 warnings are the same as in the fresh clone below. `.venv/Scripts/ruff check .`: `All checks passed!`

New and changed tests in this section:

- `tests/test_iv.py`: `test_flat_rule_one_sided_at_immediate_exercise` (new); `test_american_n200_vs_n2000_measure` reads `outputs/tables/iv_tree_convergence.csv`.
- `tests/test_svi.py` (new): `test_recovers_known_params`, `test_g_analytic_vs_fd`, `test_arbitrageable_params_fail_butterfly`, `test_calendar_flags_crossing_pair`, `test_too_few_status` (pass) and `test_fixture_accepted_slices` (fails, S1).

`-s` output of the passing `tests/test_svi.py` tests:

```
{'n_quotes': 161, 'params': (0.019999982133194996, 0.1500000068348449, -0.3999999574890161, 0.049999991360144456, 0.20000026716639133), 'rmse_vol': 2.134240434969172e-08, 'rmse_volpts': 2.134240434969172e-06, 'min_g': 0.25806671881878407, 'refit': False, 'status': 'ok', 'first_success': True, 'first_violation': 0.0}
(0.02, 0.15, -0.4, 0.05, 0.2): largest |g - g_fd| 2.57e-08
(-0.041, 0.1331, 0.306, 0.3586, 0.4153): largest |g - g_fd| 1.99e-08
  day ticker expiry_1 expiry_2   T_1  T_2  n_grid  n_violations  min_diff  k_at_min  violated
0                near    cross  0.25  0.5     401           200 -0.039501       1.0      True
```

## Fresh-clone check

Cloned into `C:\vs4` from GitHub after the push of `de9b908`. Pytest progress lines and the traceback of the failing test are left out; its assertion and everything from the warnings summary on are as printed:

```
$ git clone https://github.com/uty101/Volatility-Surface-and-Event-Pricing vs4
$ git log --oneline -1
de9b908 step 4.1: SVI per expiry (fixture gate fails for SPY, section stopped)
$ uv venv --python 3.12
$ uv pip install -r requirements-lock.txt
$ uv pip install -e . --no-deps
$ .venv/Scripts/pytest -p socket --disable-socket -q
E           AssertionError: ('SPY', 20, 23)
...
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:894
  C:\vs4\.venv\Lib\site-packages\_pytest\config\__init__.py:894: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
  C:\vs4\.venv\Lib\site-packages\pandas\core\series.py:848: Pandas4Warning: Series.values returning an ndarray that drops timezone information for DatetimeTZDtype is deprecated. In a future version, this will return the underlying DatetimeArray instead. Use 'Series.dt.tz_convert(None).to_numpy()' to get a NumPy array of UTC values, or 'Series.array' to get the ExtensionArray.
  See https://pandas.pydata.org/docs/dev/whatsnew/v3.1.0.html#whatsnew-310-deprecations-values for more details.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ===========================
FAILED tests/test_svi.py::test_fixture_accepted_slices - AssertionError: ('SP...
1 failed, 4494 passed, 5 warnings in 344.43s (0:05:44)
exit=1
```

CI (`ci` workflow) on `de9b908`: failure, run 40926086033, at the same test only: `1 failed, 4494 passed, 5 warnings in 440.31s`, `AssertionError: ('SPY', 22, 23)` (S1).

## Runtime per step

- 4.0: `scripts/measure_iv_tree.py` 299 s. The IV stage reran in about 1 minute. Full suite 85 s, against about 6 minutes in session 3b.
- 4.1: fitting the 74 fixture slices takes 190 to 230 s. `tests/test_svi.py` takes 303 s, almost all of it in `test_fixture_accepted_slices`, which also solves the full fixture IV table. Full suite 353 s on Windows, against 85 s after step 4.0.

## Deviations from PLAN.md

1. **The penalty refit is replaced** by instruction 04 part B's constrained refit and RMSE gate. `fit_svi` returns params, rmse_vol, rmse_volpts, min_g, refit, n_quotes and status, plus first_success and first_violation as review diagnostics.
2. **`test_american_n200_vs_n2000_measure` reads `outputs/tables/iv_tree_convergence.csv`**, as instruction 04 step 4.0 says. That departs from rule 7 (tests do not depend on `outputs/`). The instruction prevails under rule 13. The CSV is committed.
3. **Step 4.1 is committed with a failing test**, so CI on `de9b908` fails at that test. Rule 5 forbids skipping or xfailing it, and leaving it out of the commit would hide the stop.
4. **Steps 4.0 and 4.1 were pushed before the fresh-clone check**, as in Sections 2 and 3.

## Not verified

Interpretations made while building, for the reviewer to confirm:

- **"Converges" for the refit** is SLSQP `success` (S1, O-32). The first fit uses the lowest objective over all starts, converged or not (Section 5.4: "keep the lowest objective").
- **The RMSE gate** applies to `ok` and `ok_refit` fits only, so a `butterfly_fail` stays `butterfly_fail` whatever its RMSE. RMSE is √(mean((√(max(w, 1e-12)/T) − σ)²)), the objective's residuals, × 100 for `rmse_volpts`.
- **Rejected rows** (`butterfly_fail`, `poor_fit`) carry the RMSE and min g of the fit that was judged: for `poor_fit`, the kept fit; for `butterfly_fail`, the first fit. Instruction 04 review item 2 asks for both. Whether `svi_fits.csv` should also blank a to s on rejected rows (Convention 4.15) is for step 4.3. The plan here was to blank them.
- **Bounds and constraints in SLSQP.** b ≥ 0, |ρ| ≤ 0.999 and s ≥ `s_min` are SLSQP bounds. a + b s √(1 − ρ²) ≥ 0 is an inequality constraint. b(1 + |ρ|) ≤ 4 is split into 4 − b(1 + ρ) ≥ 0 and 4 − b(1 − ρ) ≥ 0, which is equivalent and smooth. a and m are unbounded.
- **Literals** cited in `volsurf/svi.py`: `RHO_MAX` 0.999, `WING_MAX` 4, `G_TOL` 1e-10 (kickoff 5.4), `W_FLOOR` 1e-12 and `SLSQP` maxiter 1000 / ftol 1e-14 (instruction 04 part B).
- **`test_recovers_known_params`** uses (a, b, ρ, m, s) = (0.02, 0.15, −0.4, 0.05, 0.2), T = 0.5, and 161 quotes over k ∈ [−2, 2]. At ftol 1e-14, narrower grids stop with a, b, ρ and s traded off against each other. The largest parameter error is 9.6e-6 at k ∈ [−0.6, 0.6] (41 quotes), 2.8e-6 at [−1, 1], 1.3e-6 at [−1.5, 1.5] and 2.7e-7 at [−2, 2]. Only the synthetic design was chosen; the 1e-6 tolerance is the PLAN's.
- **`test_arbitrageable_params_fail_butterfly`** uses Axel Vogt's slice (a, b, ρ, m, s) = (−0.0410, 0.1331, 0.3060, 0.3586, 0.4153) from Gatheral and Jacquier (2014).
- **`calendar_violations`** follows O-31 (a). It is built and tested but has not run on fixture data, since step 4.3 is not built.
- **Quotes fitted**: every OTM row with an IV, stale and after_close flags included, with equal weights.

## Open questions

- **S1, the stop (O-32).** (a) A refit counts as converged when SLSQP reports success, or stops at the iteration limit with the Section 5.4 bounds and constraints met. Measured on Windows: `^SPX` 34, SPY 24, AAPL 14 accepted. (b) `success` only, as built, with new bounds. Measured: `^SPX` 30, SPY 20, AAPL 14 on Windows, and 29, 22, 14 on Linux.
- **O-31.** Columns of `calendar_violations.csv`. (a) One row per consecutive accepted pair, violating or not (day, ticker, expiry_1, expiry_2, T_1, T_2, n_grid, n_violations, min_diff, k_at_min, violated). (b) Only violating pairs, one row per violating grid point. Implemented as (a).

## Files changed

- `CLAUDE.md` (Amendments: instruction 04 step 4.0), `config.toml` (`[snapshot] local_task_times_utc` removed), `decisions/section_3_review.md` (`## Session 3b and 3c`), `decisions/capture.md` (item 2), `scripts/windows/` (deleted), `volsurf/iv.py` (one-sided flat rule), `tests/test_iv.py`, `scripts/measure_iv_tree.py` (new), `outputs/tables/iv_tree_convergence.csv` (new) (4.0)
- `CLAUDE.md` (Amendments: instruction 04 part B), `config.toml` (`[svi]`), `decisions/OPEN.md` (O-31, O-32), `volsurf/svi.py` (new), `tests/test_svi.py` (new) (4.1)
- `review/section_4.md`, `instructions/04_section_4.status.md`

## Reviewer reads

1. S1 above, then O-32 in `decisions/OPEN.md`.
2. `volsurf/svi.py` (`fit_svi`).
3. `tests/test_svi.py`.
4. D1 for step 4.0, and `volsurf/iv.py` `_sens` and the end of `iv_american_batch`.
