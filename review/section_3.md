# Review: Section 3

## Section

Section 3: Forwards and implied volatility (`PLAN.md` steps 3.1 to 3.3, with instruction 03, which adds step 3.0 and replaces the parity forward of kickoff Section 5.2).

**Stopped at step 3.2 under rules 4 and 5.** PLAN 3.2 fixes 2 round-trip tests, `test_european_roundtrip_grid` and `test_american_roundtrip_grid`, which recover σ to `iv_roundtrip` = 1e-8 on the 2.1 grid. No solver can pass them. On 8 of 252 European and 27 of 252 American grid cases, the price at the true σ equals the price at `iv_lo`, or the intrinsic floor, to float64 rounding, so the price holds no vol information (evidence S1). Rule 5 forbids skipping or narrowing those cases and says to stop. Steps 3.0 and 3.1 are complete. `volsurf/iv.py`, steps 3.2 and 3.3, and review items D4 and D5 are not built.

## Steps completed

- A, B  e53507e  section 3: section 2 decisions recorded, parity forward amendment (`decisions/section_2_review.md`; O-29 and O-30 marked decided in `decisions/OPEN.md`; the part B correction under `CLAUDE.md` Amendments)
- 3.0  2f7a4ad  step 3.0: EEP on matched trees (adds `[eep] min_vega_pt = 0.01`)
- 3.1  b3b330d  step 3.1: forwards (removes `[forwards] parity_r2_min`; adds `parity_min_pairs = 5`, `parity_mad_max_bp = 2.0`)
- 3.2  not built (stopped, see S1)
- 3.3  not built

## Evidence

### S1. Why the section stopped: grid cases where σ cannot be recovered

For every 2.1 grid case (S 100, r 0.045, q 0.015, T = days / 365), the European price is Black-76 on F = S e^((r − q)T) and D = e^(−rT). The American price is CRR American at `n_prod` = 200 (the PLAN 3.2 inputs). Each price is inverted with plain `scipy.optimize.brentq` on [`iv_lo`, `iv_hi`], on the same pricing function. `brentq_iv` is blank when the bracket holds no sign change. The table lists every case where |brentq_iv − σ| is not ≤ `iv_roundtrip` = 1e-8.

```
          cases  fail
model                
american    252    27
european    252     8
        model kind    K  days  sigma   price  price_minus_lower  price_at_iv_lo  brentq_iv     abs_err
0    european    C   70     7   0.15 30.0316                  0         30.0316      0.005       0.145
1    american    C   70     7   0.15 30.0316          0.0316219         30.0316      0.005       0.145
2    european    C   70     7    0.3 30.0316                  0         30.0316      0.005       0.295
3    american    C   70     7    0.3 30.0316          0.0316219         30.0316   0.329336   0.0293359
6    european    C   70    30   0.15 30.1352                  0         30.1352      0.005       0.145
7    american    C   70    30   0.15 30.1352           0.135214         30.1352        NaN         NaN
36   european    C   80     7   0.15 20.0402                  0         20.0402      0.005       0.145
37   american    C   80     7   0.15 20.0402          0.0402483         20.0402      0.005       0.145
39   american    C   80     7    0.3 20.0402          0.0402483         20.0402        0.3 1.70971e-07
43   american    C   80    30   0.15 20.1721           0.172132         20.1721       0.15 3.50104e-08
73   american    C   90     7   0.15 10.0489          0.0488748         10.0489       0.15 3.54741e-08
253  american    P   70     7   0.15       0                  0               0      0.005       0.145
397  american    P  110     7   0.15      10        6.82121e-13              10  0.0883686   0.0616314
403  american    P  110    30   0.15      10       -1.60583e-12              10        NaN         NaN
432  european    P  120     7   0.15 19.9252                  0         19.9252      0.005       0.145
433  american    P  120     7   0.15      20        6.82121e-13              20   0.408048    0.258048
435  american    P  120     7    0.3      20        1.77636e-12              20      0.005       0.295
439  american    P  120    30   0.15      20       -1.60583e-12              20        NaN         NaN
441  american    P  120    30    0.3      20        1.42109e-14              20        NaN         NaN
445  american    P  120    91   0.15      20       -1.36424e-12              20        NaN         NaN
451  american    P  120   182   0.15      20       -2.55795e-13              20      0.005       0.145
457  american    P  120   365   0.15      20        1.69109e-12              20      0.005       0.145
468  european    P  130     7   0.15 29.9166                  0         29.9166      0.005       0.145
469  american    P  130     7   0.15      30        6.82121e-13              30   0.629375    0.479375
470  european    P  130     7    0.3 29.9166        1.05878e-10         29.9166   0.299999 1.21714e-06
471  american    P  130     7    0.3      30        1.77636e-12              30      0.005       0.295
473  american    P  130     7    0.6      30       -5.68434e-13              30      0.005       0.595
474  european    P  130    30   0.15 29.6433        5.80016e-10         29.6433       0.15  1.9319e-07
475  american    P  130    30   0.15      30       -1.60583e-12              30        NaN         NaN
477  american    P  130    30    0.3      30        1.42109e-14              30        NaN         NaN
481  american    P  130    91   0.15      30       -1.36424e-12              30        NaN         NaN
483  american    P  130    91    0.3      30        8.81073e-13              30        NaN         NaN
487  american    P  130   182   0.15      30       -2.55795e-13              30      0.005       0.145
493  american    P  130   365   0.15      30        1.69109e-12              30      0.005       0.145
499  american    P  130   730   0.15      30        9.66338e-13              30        NaN         NaN
```

Why no solver can pass these:

- **European, 8 cases.** In 6, `price_minus_lower` is exactly 0. The time value (for example the 7-day K 70 call at σ 0.15) is below float64 resolution for a price near 30. So the price equals the lower bound D(F − K) and also the price at `iv_lo` (`price_at_iv_lo`), and every σ from `iv_lo` up to about the true σ reproduces it exactly. The strict Section 5.3 bound (price > lower bound) sends these to `bounds` with no vol. In the other 2 (P 130 at 7 days σ 0.30, and at 30 days σ 0.15), the time value is 1.1e-10 and 5.8e-10. A σ error of 1.2e-6 and 1.9e-7 moves the price by less than its own rounding.
- **American, 27 cases.** These are deep ITM puts and calls whose tree value is immediate exercise. The price equals intrinsic to about 1e-12 (`price_minus_lower` between −1.6e-12 and 1.8e-12) and does not depend on σ near the true value. Where it sits a few e-12 *below* intrinsic, the Section 5.3 American bound (put ≥ max(K − S, 0)) rejects it as `bounds`. The 4 calls with errors from 3.5e-8 to 1.7e-7 are short-dated deep ITM calls, whose American price moves by about 1e-14 per vol point.

The 2 tests are wrong as written for these cases; the solver is not. Options for the reviewer:

- **(a)** Keep the full grid. Each case where the price does not identify σ must return no vol (method `bounds`, or a new no-root method), and the test states the rule that marks such a case: for example, the price at σ equals the price at `iv_lo` within `iv_tol`, or the time value is below a stated bound. Every other case recovers σ to `iv_roundtrip`.
- **(b)** Run both round trips on the OTM half of the 2.1 grid only (calls with K ≥ F, puts with K < F; Convention 4.5), which is what feeds the surface; the ITM cases get no round-trip test. Every failing case in the probe above is ITM.

Probe source (run from the repo root with the venv Python):

```python
"""Instruction 03 step 3.2 stop evidence: which 2.1 grid cases can round-trip sigma at all in float64."""
import itertools
import numpy as np
import pandas as pd
from scipy.optimize import brentq
from volsurf.config import load_config
from volsurf.pricing import black76, crr

cfg = load_config()
lo, hi, n, tol = cfg.iv.iv_lo, cfg.iv.iv_hi, cfg.pricing.n_prod, cfg.tolerances.iv_roundtrip
S, R, Q = 100.0, 0.045, 0.015
rows = []
for kind, K, days, sigma in itertools.product("CP", [70, 80, 90, 100, 110, 120, 130], [7, 30, 91, 182, 365, 730],
                                              [0.15, 0.30, 0.60]):
    T = days / 365
    D, F = np.exp(-R * T), S * np.exp((R - Q) * T)
    for model in ("european", "american"):
        if model == "european":
            f = lambda s: float(black76(F, K, T, D, s, kind))  # noqa: E731
            lower = max(D * (F - K), 0.0) if kind == "C" else max(D * (K - F), 0.0)
        else:
            f = lambda s: crr(S, K, T, R, Q, s, kind, n, True)  # noqa: E731
            lower = max(S - K, 0.0) if kind == "C" else max(K - S, 0.0)
        price = f(sigma)
        try:
            iv = brentq(lambda s: f(s) - price, lo, hi)
        except ValueError:
            iv = np.nan
        rows.append({"model": model, "kind": kind, "K": K, "days": days, "sigma": sigma, "price": price,
                     "price_minus_lower": price - lower, "price_at_iv_lo": f(lo), "brentq_iv": iv,
                     "abs_err": abs(iv - sigma)})
df = pd.DataFrame(rows)
bad = df[~(df["abs_err"] <= tol)]
pd.set_option("display.width", 250)
print(df.groupby("model").apply(lambda g: pd.Series({"cases": len(g), "fail": int((~(g.abs_err <= tol)).sum())}),
                                include_groups=False).to_string())
print(bad.to_string(float_format=lambda x: f"{x:.6g}"))
```

### D1. Step 3.0: `eep_summary.csv` before and after, and the change in OTM median vol points per bin

Before (`eb54907`, closed-form BSM European IV):

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

After (`2f7a4ad`, both IVs on CRR at `n_prod`, `low_vega` rows blank):

```
   ticker kind           k_bin     n  median_vol_pts   max_vol_pts  median_pct_mid  max_pct_mid
0     SPY    C   (-inf, -0.10]   893    7.685519e-12  4.296084e+01        0.000000     0.553725
1     SPY    C  (-0.10, -0.02]   763   -2.220446e-14  1.619149e-10        0.000000     0.000000
2     SPY    C   (-0.02, 0.02]   525    0.000000e+00  2.289557e-11        0.000000     0.000000
3     SPY    C    (0.02, 0.10]   493    0.000000e+00  4.802270e-11        0.000000     0.000000
4     SPY    C     (0.10, inf)   297   -5.551115e-15  4.704570e-11        0.000000     0.000000
5     SPY    P   (-inf, -0.10]  1363    3.432353e-02  4.613645e-01        0.525886     4.260132
6     SPY    P  (-0.10, -0.02]   835    5.991000e-02  9.953888e-01        0.798134     6.496440
7     SPY    P   (-0.02, 0.02]   496    2.168924e-01  1.904757e+00        1.340696     8.335898
8     SPY    P    (0.02, 0.10]   208    1.626201e+00  5.216219e+00        4.027170    13.763772
9     SPY    P     (0.10, inf)    44    1.394652e+00  8.039938e+00        0.817656     7.680414
10   AAPL    C   (-inf, -0.10]   165    2.720046e-12  4.181521e-01        0.000000     0.007749
11   AAPL    C  (-0.10, -0.02]    75   -1.276756e-13  2.786660e-11        0.000000     0.000000
12   AAPL    C   (-0.02, 0.02]    48    0.000000e+00  7.049916e-12        0.000000     0.000000
13   AAPL    C    (0.02, 0.10]    84   -5.551115e-15  3.308465e-12        0.000000     0.000000
14   AAPL    C     (0.10, inf)    90    4.024558e-14  4.379830e-12        0.000000     0.000000
15   AAPL    P   (-inf, -0.10]   159    6.198093e-02  6.339169e-01        0.897608     3.556377
16   AAPL    P  (-0.10, -0.02]    81    6.192725e-02  1.097097e+00        0.430128     4.422871
17   AAPL    P   (-0.02, 0.02]    47    1.551960e-01  1.490318e+00        0.552391     4.968263
18   AAPL    P    (0.02, 0.10]    85    8.535098e-01  2.900993e+00        0.958386     6.363887
19   AAPL    P     (0.10, inf)   109    4.792174e+00  1.434790e+01        1.873821     7.610278
```

Row status counts before and after (`eep_rows.csv`, 7,108 rows):

```
ticker  status       
SPY     ok               5944
        both_fail          37
        american_fail       1
AAPL    ok                946
        both_fail         180
```

```
ticker  status       
SPY     low_vega           27
        ok               5917
        both_fail          37
        american_fail       1
AAPL    ok                943
        both_fail         180
        low_vega            3
```

`low_vega` rows (BSM vega per vol point at the American IV below `[eep] min_vega_pt` = 0.01), by bin:

```
ticker  kind  k_bin        
SPY     C     (-inf, -0.10]    11
        P     (-inf, -0.10]    16
AAPL    C     (-inf, -0.10]     3
```

OTM median vol premium per bin (Convention 4.5: calls with K ≥ F, puts with K < F, F = S e^((r − q)T) from each row; status `ok` rows). OTM calls now sit at 0 to within 1e-14. Before, the mismatch between the tree and BSM put them between −0.027 and +0.016:

```
   ticker kind           k_bin  n_before  median_before  n_after  median_after    change
0     SPY    C   (-0.02, 0.02]       263       0.005393      263  2.775558e-15 -0.005393
1     SPY    C    (0.02, 0.10]       493      -0.004775      493  0.000000e+00  0.004775
2     SPY    C     (0.10, inf)       297      -0.027192      297 -5.551115e-15  0.027192
3     SPY    P   (-inf, -0.10]      1379       0.009446     1363  3.432353e-02  0.024878
4     SPY    P  (-0.10, -0.02]       835       0.064045      835  5.991000e-02 -0.004135
5     SPY    P   (-0.02, 0.02]       264       0.122587      264  1.166038e-01 -0.005983
6    AAPL    C   (-0.02, 0.02]        23       0.015653       23  0.000000e+00 -0.015653
7    AAPL    C    (0.02, 0.10]        84       0.005688       84 -5.551115e-15 -0.005688
8    AAPL    C     (0.10, inf)        90      -0.022484       90  4.024558e-14  0.022484
9    AAPL    P   (-inf, -0.10]       159       0.045773      159  6.198093e-02  0.016208
10   AAPL    P  (-0.10, -0.02]        81       0.071617       81  6.192725e-02 -0.009689
11   AAPL    P   (-0.02, 0.02]        24       0.145113       24  1.296517e-01 -0.015462
```

The 5 largest vol premiums after the change, with every input:

```
     ticker      expiry kind  strike     bid     ask      mid        S         T         r         q           F         k          k_bin  iv_american  iv_european  premium_vol_pts  premium_price  premium_pct_mid status
5426    SPY  2027-09-17    C    50.0  718.23  723.00  720.615  770.375  0.888239  0.043945  0.009843  794.067298 -2.765145  (-inf, -0.10]     1.342547     1.772156        42.960839       3.990228         0.553725     ok
5427    SPY  2027-09-17    C    55.0  713.50  718.32  715.910  770.375  0.888239  0.043945  0.009843  794.067298 -2.669835  (-inf, -0.10]     1.351185     1.707528        35.634357       3.720621         0.519705     ok
4846    SPY  2027-06-17    C    80.0  689.03  692.59  690.810  770.375  0.636184  0.043353  0.009843  786.974679 -2.286169  (-inf, -0.10]     1.264310     1.534180        26.987018       2.188023         0.316733     ok
3337    SPY  2027-01-15    C    70.0  699.19  702.65  700.920  770.375  0.217120  0.041548  0.009843  775.696419 -2.405266  (-inf, -0.10]     2.255419     2.475163        21.974387       0.754980         0.107713     ok
5428    SPY  2027-09-17    C   120.0  648.70  653.50  651.100  770.375  0.888239  0.043945  0.009843  794.067298 -1.889676  (-inf, -0.10]     0.869308     1.047987        17.867853       2.039887         0.313299     ok
```

**The deep ITM SPY calls are still the largest values.** The `low_vega` rule blanks 30 rows. But the 2027-09-17 K 50 call has an American IV of 1.34, where BSM vega is 0.054 per vol point, above the 0.01 cut, so it keeps its 42.96 vol point premium. Its price premium is 3.99, 0.55% of the mid. These calls are 2.8 log units ITM on a dividend payer. A vol number says little there, and `premium_pct_mid` is the readable measure for them. Implemented as specified and reported, not changed.

Item 5 test (`test_american_call_no_dividend_premium_zero_on_matched_trees`): the 126 calls of the 2.1 grid with q = 0, mid = CRR American at `n_prod` at the grid σ. Shown: status counts, the largest absolute premiums, the row with the largest vol premium, and the 1 case with no IV.

```
status
ok           96
low_vega     29
both_fail     1
   max_abs_premium_price  max_abs_premium_vol_pts
0                    0.0             1.106615e-11
     K  days  sigma        mid  iv_american  iv_european  premium_vol_pts  premium_price  premium_pct_mid status
15  70   730   0.15  36.131651         0.15         0.15     1.106615e-11            0.0              0.0     ok
    K  days  sigma        mid  iv_american  iv_european  premium_vol_pts  premium_price  premium_pct_mid     status
3  70    30   0.15  30.258426          NaN          NaN              NaN            NaN              NaN  both_fail
```

The K 70, 30-day, σ 0.15 call has no IV in [`iv_lo`, `iv_hi`]. Its tree price at `iv_lo` is 4.0e-13 above the mid (the time value is below rounding), so both solves fail alike, and the premiums are blank by O-29 (a). For that case the test asserts that the tree price at `iv_lo` is at or above the mid. On every case it asserts that CRR American − CRR European at the grid σ is within 1e-12. This is the S1 identification problem showing up in the step 3.0 test, and the reviewer may want the S1 decision to cover this case too.

### D2. `parity_forwards_fixture.csv` in full

The CSV is a step 3.3 output and is **not written**, because the section stopped at 3.2. The table below is the same content, from `spx_forwards` on the fixture day: rules a to d applied, T by Convention 4.1 from each expiry's `snap_utc`, r = `rate_curve(fred, 2026-10-28)(T)`, D = e^(−rT), and the instruction 03 part B estimator.

```
        expiry         T         r         D            F    mad_bp  n_pairs    q_impl     r_reg status
0   2026-10-29  0.003309  0.040683  0.999865  7731.925259  0.390665       10 -0.017766       NaN     ok
1   2026-10-30  0.006048  0.040683  0.999754  7733.927196  0.520511       10 -0.034093       NaN     ok
2   2026-11-02  0.014382  0.040683  0.999415  7735.347279  0.595326       10 -0.003531       NaN     ok
3   2026-11-03  0.017121  0.040683  0.999304  7735.897143  0.332401       10 -0.000607       NaN     ok
4   2026-11-04  0.019861  0.040683  0.999192  7736.489087  0.208099       10  0.001236       NaN     ok
5   2026-11-05  0.022601  0.040683  0.999081  7737.518124  0.690671       10  0.000133       NaN     ok
6   2026-11-06  0.025340  0.040683  0.998970  7740.443489  0.274324       10 -0.010400       NaN     ok
7   2026-11-09  0.033560  0.040683  0.998636  7740.696416  0.405742       10  0.001137       NaN     ok
8   2026-11-10  0.036299  0.040683  0.998524  7741.868339  0.279379       10 -0.000048       NaN     ok
9   2026-11-11  0.039039  0.040683  0.998413  7741.638307  0.835817       10  0.003571       NaN     ok
10  2026-11-12  0.041779  0.040683  0.998302  7742.500475  0.722559       10  0.003339       NaN     ok
11  2026-11-13  0.044518  0.040683  0.998190  7743.963839  0.620345       10  0.001392       NaN     ok
12  2026-11-16  0.052738  0.040683  0.997857  7743.779533  0.242659       10  0.007967       NaN     ok
13  2026-11-17  0.055477  0.040683  0.997746  7744.104342  0.499922       10  0.008827       NaN     ok
14  2026-11-18  0.058217  0.040683  0.997634  7744.932639  0.415408       10  0.008489       NaN     ok
15  2026-11-19  0.060957  0.040683  0.997523  7744.811454  0.663526       10  0.010193       NaN     ok
16  2026-11-20  0.063696  0.040683  0.997412  7746.197509  0.357073       10  0.008695       NaN     ok
17  2026-11-23  0.071916  0.040683  0.997079  7747.197153  0.404366       10  0.010556       NaN     ok
18  2026-11-24  0.074655  0.040683  0.996967  7747.898955  0.608039       10  0.010449       NaN     ok
19  2026-11-25  0.077395  0.040683  0.996856  7749.960579  0.497413       10  0.008081       NaN     ok
20  2026-11-27  0.082874  0.040683  0.996634  7752.375314  0.280639       10  0.006478  0.077889     ok
21  2026-11-30  0.091094  0.040734  0.996296  7753.189591  0.449509       10  0.008461 -0.071620     ok
22  2026-12-01  0.093833  0.040751  0.996183  7753.367210  0.838293        8  0.009177  0.055533     ok
23  2026-12-03  0.099313  0.040787  0.995958  7753.590043  0.489732       10  0.010665  0.057250     ok
24  2026-12-04  0.102052  0.040804  0.995844  7755.259188  0.458225       10  0.009382 -0.028878     ok
25  2026-12-11  0.121230  0.040928  0.995051  7760.539793  0.633429       10  0.008862  0.119817     ok
26  2026-12-18  0.140409  0.041052  0.994252  7765.248271  0.334998       10  0.009046  0.045813     ok
27  2026-12-31  0.176025  0.041283  0.992760  7777.177790  0.561604       10  0.007032  0.034189     ok
28  2027-01-15  0.217121  0.041548  0.991020  7794.520202  0.319080       10  0.003521  0.051545     ok
29  2027-01-29  0.255477  0.041789  0.989381  7805.394443  0.321724       10  0.004014 -0.010088     ok
30  2027-02-19  0.313011  0.042082  0.986914  7821.388424  0.595902        9  0.004711  0.047002     ok
31  2027-02-26  0.332189  0.042179  0.986086  7827.646701  0.360462       10  0.004558  0.079248     ok
32  2027-03-19  0.389609  0.042472  0.983589  7841.745373  0.810618        9  0.005776  0.045047     ok
33  2027-03-31  0.422486  0.042639  0.982147  7851.321332  0.599872       10  0.005910  0.053388     ok
34  2027-06-30  0.671801  0.043437  0.971241  7932.897822  0.178584       10  0.004953  0.048835     ok
35  2027-09-30  0.923856  0.044029  0.960140  8019.957064  0.294012       10  0.004230  0.045065     ok
          mad_bp  n_pairs
median  0.453867     10.0
max     0.838293     10.0
min     0.178584      8.0
status
ok    36
```

All 36 expiries pass. The median mad_bp is 0.454 and the largest 0.838, against the reviewer's 0.46 and 0.84. Every expiry has at least 8 pairs (2026-12-01 has 8; 2027-02-19 and 2027-03-19 have 9). `r_reg` is blank for T < 30/365, as specified. Where it is reported, it swings from −0.072 (2026-11-30) to 0.120 (2026-12-11), which is the regression problem part B describes. q_impl is negative on the first 4 expiries (down to −0.034 on 2026-10-30). A candidate cause, not checked: the fixture's `^SPX` UNDERLYING price is the 14:46 UTC bar, 15 minutes before the 15:00:58 snapshot, so S and the option mids are not simultaneous.

### D3. The `^SPX` rule e row of the regenerated clean log

`outputs/tables/clean_log_fixture.csv` in full (`b3b330d`):

```
day,ticker,rule,rows_before,rows_dropped,note
2026-10-28,^SPX,a,11557,634,
2026-10-28,^SPX,b,10923,0,
2026-10-28,^SPX,c,10923,0,
2026-10-28,^SPX,d,10923,256,
2026-10-28,^SPX,e,10667,335,
2026-10-28,SPY,a,7466,640,
2026-10-28,SPY,b,6826,1,
2026-10-28,SPY,c,6825,476,
2026-10-28,SPY,d,6349,6,
2026-10-28,SPY,e,6343,361,
2026-10-28,AAPL,a,1856,275,
2026-10-28,AAPL,b,1581,2,
2026-10-28,AAPL,c,1579,96,
2026-10-28,AAPL,d,1483,195,
2026-10-28,AAPL,e,1288,162,
```

The `^SPX` rule e row was `2026-10-28,^SPX,e,10667,0,deferred to section 3` and is now `2026-10-28,^SPX,e,10667,335,` (no note). All 335 dropped rows are ITM and below the European lower bound: 236 calls with mid ≤ max(D(F − K), 0) and 99 puts with mid ≤ max(D(K − F), 0). None is OTM, so none could reach the surface. Their shortfall below the bound, in bp of F, has median 6.4, quartiles 0.80 and 73.7, and a largest value of 1,042.

### D4, D5. Not reached

The batch-against-scalar IV gaps, the batch timing, the N = 200 against N = 2000 MEASURE, `iv_summary.csv` and the 10 random solved rows all need `volsurf/iv.py` (step 3.2), which is not built.

### D6. Fresh-clone check and CI

Both are in the sections below.

## Tests run

`.venv/Scripts/pytest -p socket --disable-socket -q` on Windows at `b3b330d`: `4475 passed, 5 warnings in 136.08s (0:02:16)`. The 5 warnings are the same as in the fresh clone below. `.venv/Scripts/ruff check .`: `All checks passed!`

New and changed tests in this section:

- `tests/test_eep.py`: `test_american_call_no_dividend_premium_zero_on_matched_trees` (126 cases, step 3.0 item 5).
- `tests/test_forwards.py`: `test_synthetic_recovers_f` (F = 100, D = e^(−0.02); F to 1e-10 absolute, mad_bp < 1e-6, r_reg and q_impl checked), `test_gate_rejects_noisy_chain`, `test_gate_rejects_too_few_pairs`, `test_nearest_strikes_used`, `test_fixture_every_spx_expiry_with_min_pairs_passes_gate`.
- `tests/test_data.py`: `test_rule_e_spx_european_bounds`, `test_rule_e_spx_parity_fail_expiry_kept_unchecked`.
- `tests/test_fixture.py`: `test_clean_log_fixture_reproduced` now runs `clean_with_forwards`, so rule e for `^SPX` uses the parity forward, and compares bytes with the regenerated file.

## Fresh-clone check

Cloned into `C:\Users\astha\AppData\Local\Temp\vs3` from GitHub after the push of `b3b330d`. The pytest progress lines (only `.` characters) are left out; everything else is as printed:

```
$ git clone https://github.com/uty101/Volatility-Surface-and-Event-Pricing vs3
$ git log --oneline -1
b3b330d step 3.1: forwards
$ uv venv --python 3.12
$ uv pip install -r requirements-lock.txt
$ uv pip install -e . --no-deps
$ .venv/Scripts/pytest -p socket --disable-socket -q
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:894
  C:\Users\astha\AppData\Local\Temp\vs3\.venv\Lib\site-packages\_pytest\config\__init__.py:894: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
  C:\Users\astha\AppData\Local\Temp\vs3\.venv\Lib\site-packages\pandas\core\series.py:848: Pandas4Warning: Series.values returning an ndarray that drops timezone information for DatetimeTZDtype is deprecated. In a future version, this will return the underlying DatetimeArray instead. Use 'Series.dt.tz_convert(None).to_numpy()' to get a NumPy array of UTC values, or 'Series.array' to get the ExtensionArray.
  See https://pandas.pydata.org/docs/dev/whatsnew/v3.1.0.html#whatsnew-310-deprecations-values for more details.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
4475 passed, 5 warnings in 147.72s (0:02:27)
exit=0
```

CI (`ci` workflow) on `b3b330d`: success, run 40730251845.

## Runtime per step

- 3.0: the `eep` stage took 218 s for 7,108 rows (2 brentq solves per row, both on 200-step trees, plus the premium at the American IV), against 169 s in step 2.3. `tests/test_eep.py` takes 7 s.
- 3.1: the `clean_log` stage, parity forwards included, takes a few seconds. `tests/test_forwards.py`, `tests/test_data.py` and `tests/test_fixture.py` together take 13 s.
- Full suite: 136 s on Windows and 148 s in the fresh clone, against 41 s on Windows after step 3.0. The `eep` stage was running on the same machine during the 136 s run.

## Deviations from PLAN.md

1. **The parity forward** follows instruction 03 part B, not PLAN 3.1 and kickoff 5.2. The signature is `parity_forward(calls, puts, spot, T, D, n, min_pairs, mad_max_bp)` with keys F, mad_bp, n_pairs, q_impl, r_reg, status. PLAN's `test_synthetic_recovers_d_and_f`, `test_fixture_spx_expiry_passes_gate` and `test_r2_gate_rejects_noisy_chain` become `test_synthetic_recovers_f`, `test_fixture_every_spx_expiry_with_min_pairs_passes_gate` and `test_gate_rejects_noisy_chain` (instruction 03 step 3.1). The forwards table has instruction 03's columns (expiry, T, r, D, F, mad_bp, n_pairs, q_impl, r_reg, status).
2. **`clean_chain` gains an optional `forwards` argument**, a frame with columns expiry, D, F and status. With it, rule e for `^SPX` uses the Section 5.3 European bounds. Without it, behaviour is that of Section 1 (rule e deferred, O-23 (b)), so the Section 6.1 call `clean_chain(chains, underlying, cfg)` is unchanged. `volsurf/forwards.py` adds 2 O-1 (a) helpers: `spx_forwards`, and `clean_with_forwards` (rules a to d, the forward on the rows they keep, then rule e).
3. **`run_all.py` gains a `clean_log` stage**, which writes `outputs/tables/clean_log_fixture.csv`. That file had no stage before.
4. **`eep_solve`** in `volsurf/pricing.py` holds the per-quote step 3.0 logic, so the item 5 grid test can call it with exact T and r. `eep_rows` calls it.
5. **Steps 3.0 and 3.1 were pushed before the fresh-clone check**, as in Section 2.

## Not verified

Interpretations made while building, for the reviewer to confirm:

- **`low_vega` rows** keep both IVs, `premium_price` and `premium_pct_mid`. Only `premium_vol_pts` is blank, the one column instruction 03 step 3.0 item 3 names.
- **`eep_summary.csv`**: `n`, the vol point statistics and the new `median_pct_mid` and `max_pct_mid` are all over status `ok` rows (the rows with a vol premium), so `n` counts every row behind every column. The other reading takes the percent statistics over `ok` and `low_vega` rows together. Groups with no `ok` row are left out, as before.
- **Strike selection in `parity_forward`**: strikes with both a clean call and a clean put mid, sorted by |K − S| with a tie going to the lower strike; the first `parity_n_strikes` are used.
- **On `parity_fail`**, F and q_impl are blank (Convention 4.15), and mad_bp, n_pairs and r_reg are kept as diagnostics. r_reg is reported when T ≥ 30/365 and there are at least 2 pairs, and is blank if the fitted slope is not negative.
- **`^SPX` rule e on a `parity_fail` expiry**: its rows cannot be checked, so they are kept and counted in the CLEAN_LOG note (`N rows on parity_fail expiries not checked`). No fixture expiry fails, so the note is blank on the fixture.
- **European bounds in rule e** are strict at both ends, as Section 5.3 writes them. The American bounds keep Section 1's ≥ at the lower end and < at the upper.
- **S from UNDERLYING** is used in the forward only to pick the strikes nearest spot and for q_impl. The D2 note on the 14:46 UTC `^SPX` bar affects q_impl only.
- **Determinism of the 3.0 and 3.1 outputs**: after the commits, a second run of the `clean_log` and `eep` stages left `git status --short outputs/` empty, so `clean_log_fixture.csv`, `eep_rows.csv` and `eep_summary.csv` are byte-identical across 2 runs.

## Open questions

- **S1, the stop.** The PLAN 3.2 round-trip tests on the full 2.1 grid: (a) keep the full grid and state the rule for the cases that must return no vol; (b) round trip on the OTM half of the grid only (Convention 4.5). This is not entered in `decisions/OPEN.md`: it is a stop on a fixed test under rule 5, not an unspecified design choice.
- **Choices step 3.2 will need.** Instruction 03 leaves the following unspecified. They are listed now so the instruction that resumes step 3.2 can settle them together. Nothing is built on them yet, so they are not in `decisions/OPEN.md`.
  1. The IV `method` for rows solved by `iv_american_batch` (`bisection`, or `brent` as for the scalar solver), and for rows inside the bounds with no root in [`iv_lo`, `iv_hi`] (a new `no_root`, or `bounds`).
  2. In `iv_european`, the scale for the switch at vega < `min_vega` × S, since the signature has no S (F, or D F).
  3. In step 3.3, the rows of a `^SPX` expiry rejected by the parity gate. They have no F, so Convention 4.5's OTM selection cannot apply: keep every clean row of that expiry with blank F and iv and flag `parity_fail`, or drop them from IV and count them in `iv_summary.csv`. Also the q column for `^SPX` rows (q_impl, or blank).
  4. The names of the by-method columns in `iv_summary.csv`.

## Files changed

- `decisions/section_2_review.md` (new), `decisions/OPEN.md` (O-29 and O-30 decided), `CLAUDE.md` (Amendments: instruction 03 part B) (A, B)
- `config.toml` (`[eep] min_vega_pt`), `volsurf/config.py` (`eep` table), `volsurf/pricing.py` (`eep_solve`, matched trees, new columns), `tests/test_eep.py`, `outputs/tables/eep_rows.csv`, `outputs/tables/eep_summary.csv` (3.0)
- `config.toml` (`[forwards]`), `volsurf/forwards.py` (new), `volsurf/data.py` (European rule e for `^SPX`), `scripts/run_all.py` (`clean_log` stage), `tests/test_forwards.py` (new), `tests/test_data.py`, `tests/test_fixture.py`, `outputs/tables/clean_log_fixture.csv` (3.1)
- `review/section_3.md`, `instructions/03_section_3.status.md`

## Reviewer reads

1. `instructions/03_section_3.status.md`
2. This file: S1 (the stop and the 2 options), D1, D2, Not verified, Open questions
3. `volsurf/forwards.py`
4. `volsurf/pricing.py` (`eep_solve`)
5. `volsurf/data.py` (`clean_chain`, rule e for `^SPX`)
6. `outputs/tables/eep_summary.csv`, `outputs/tables/clean_log_fixture.csv`

## Session 3c

Instruction 03c: the capture waits for 15:30 New York. Step 3c.1 is commit `a96f353` (`step 3c.1: capture waits for 15:30 New York`). It touches only the files the instruction names: `config.toml` (`[snapshot] target_ny`, `cron_utc`), `volsurf/snapshots.py` (`seconds_until_target`, `already_captured`), `scripts/snapshot.py` (`--wait`), `.github/workflows/snapshot.yml` and `tests/test_snapshots.py`. No 03b work had started, so nothing else was in the working tree. The local task is unchanged.

### 3c.1 test output

`.venv/Scripts/pytest -p socket --disable-socket tests/test_snapshots.py -rA`:

```
PASSED tests/test_snapshots.py::test_in_window_across_clock_change
PASSED tests/test_snapshots.py::test_is_session
PASSED tests/test_snapshots.py::test_filter_expiries
PASSED tests/test_snapshots.py::test_keep_spxw
PASSED tests/test_snapshots.py::test_classify_timing
PASSED tests/test_snapshots.py::test_chain_frame_column_order
PASSED tests/test_snapshots.py::test_should_upload_no_existing_asset
PASSED tests/test_snapshots.py::test_should_upload_more_tickers_ok
PASSED tests/test_snapshots.py::test_should_upload_tie_keeps_existing
PASSED tests/test_snapshots.py::test_should_upload_fewer_tickers_ok
PASSED tests/test_snapshots.py::test_seconds_until_target
PASSED tests/test_snapshots.py::test_already_captured
======================= 12 passed, 5 warnings in 0.97s ========================
```

Full suite before the push: `4477 passed, 5 warnings in 106.37s (0:01:46)`. `ruff check .`: `All checks passed!`

Smoke test of the real `--wait` path before the push. `scripts/snapshot.py`'s `wait_for_target` ran against GitHub at 15:05 UTC with `time.sleep` stubbed. Check (a) found no `snapshots` release, so `existing_n_ok` is None:

```
2026-10-29T15:05:38.859635+00:00 waiting 15861 seconds until 15:30 New York
(stub sleep 15861)
proceed to capture: True
```

### Diff of `snapshot.yml`

```diff
diff --git a/.github/workflows/snapshot.yml b/.github/workflows/snapshot.yml
index 670b629..a5f1f5d 100644
--- a/.github/workflows/snapshot.yml
+++ b/.github/workflows/snapshot.yml
@@ -2,8 +2,9 @@ name: snapshot
 
 on:
   schedule:
-    - cron: "30 19 * * 1-5"
-    - cron: "30 20 * * 1-5"
+    - cron: "17 15 * * 1-5"
+    - cron: "17 17 * * 1-5"
+    - cron: "47 18 * * 1-5"
   workflow_dispatch:
     inputs:
       force:
@@ -19,10 +20,14 @@ on:
 permissions:
   contents: write
 
+concurrency:
+  group: snapshot
+  cancel-in-progress: false
+
 jobs:
   snapshot:
     runs-on: ubuntu-latest
-    timeout-minutes: 45
+    timeout-minutes: 355
     steps:
       - uses: actions/checkout@v4
       - uses: astral-sh/setup-uv@v6
@@ -38,9 +43,12 @@ jobs:
           FORCE_INPUT: ${{ inputs.force }}
         run: |
           FORCE=""
+          WAIT=""
           if [ "$EVENT" = "push" ]; then FORCE="--force"; fi
           if [ "$EVENT" = "workflow_dispatch" ] && [ "$FORCE_INPUT" = "true" ]; then FORCE="--force"; fi
-          .venv/bin/python scripts/snapshot.py $FORCE --runner actions --out snap --upload better
+          if [ "$EVENT" = "schedule" ]; then WAIT="--wait"; fi
+          if [ "$EVENT" = "workflow_dispatch" ] && [ "$FORCE_INPUT" != "true" ]; then WAIT="--wait"; fi
+          .venv/bin/python scripts/snapshot.py $FORCE $WAIT --runner actions --out snap --upload better
       - uses: actions/upload-artifact@v4
         if: always()
         with:
```

### 3c.2 output

Pushed `a96f353` at 15:07 UTC. The push matched the workflow's `push` paths, so it started a forced run to `snapshots-test` (40898385139: success, 7m23s, `uploaded 4 files to release snapshots-test`). Then `gh workflow run snapshot.yml` with no force input started run 40898405093. The concurrency group held it as `pending` until the push run ended, and its Capture step started at 15:15:17 UTC.

`gh run list --workflow snapshot.yml -L 3`, at 15:16:02 UTC:

```
in_progress		snapshot	snapshot	main	workflow_dispatch	40898405093	8m14s	2026-10-29T15:07:49Z
completed	success	step 3c.1: capture waits for 15:30 New York	snapshot	main	push	40898385139	7m23s	2026-10-29T15:07:42Z
completed	success	snapshot	snapshot	main	schedule	40792431105	19s	2026-10-29T00:11:42Z
```

**The first 20 log lines cannot be printed yet.** GitHub serves a job's log only once the job has finished. Run while the step was in progress:

```
$ gh run view 40898405093 --log
run 40898405093 is still in progress; logs will be available when it is complete
$ gh api repos/uty101/Volatility-Surface-and-Event-Pricing/actions/jobs/123538072209/logs
<Error><Code>BlobNotFound</Code><Message>The specified blob does not exist. ...</Message></Error>gh: HTTP 404
```

The `waiting ... seconds` line will be in the log when the run completes, after about 19:37 UTC. From a start at 15:15:17 UTC it should read about 15,280 seconds. The evidence that the run is sleeping and not capturing is the step's state well past the length of a capture (the forced push run captured and uploaded in under 7 minutes in total), with no `snapshots` release yet:

```
Thu Oct 29 15:26:00 UTC 2026
run in_progress, Capture step in_progress, started 2026-10-29T15:15:17Z
in_progress		snapshot	snapshot	main	workflow_dispatch	40898405093	18m13s	2026-10-29T15:07:49Z
completed	success	step 3c.1: capture waits for 15:30 New York	snapshot	main	push	40898385139	7m23s	2026-10-29T15:07:42Z
completed	success	snapshot	snapshot	main	schedule	40792431105	19s	2026-10-29T00:11:42Z
$ gh release view snapshots
release not found
```

Steps and job of run 40898405093 at 15:15 UTC:

```
123538072209 1 Set up job completed success 2026-10-29T15:15:08Z
123538072209 2 Run actions/checkout@v4 completed success 2026-10-29T15:15:10Z
123538072209 3 Run astral-sh/setup-uv@v6 completed success 2026-10-29T15:15:12Z
123538072209 4 Install from the lock completed success 2026-10-29T15:15:14Z
123538072209 5 Capture in_progress  2026-10-29T15:15:17Z
123538072209 6 Run actions/upload-artifact@v4 pending  0001-01-01T00:00:00Z
```

### Notes for the reviewer

- **Concurrency keeps at most 1 pending run.** GitHub allows 1 running and 1 pending run per group. A newer pending run replaces the older one even with `cancel-in-progress: false`. With a sleeping run in progress, the 17:17 run waits as pending until the 18:47 run replaces it, and the 18:47 run then exits at check (a) once the sleeper has uploaded. Nothing is lost, but the Actions history will show the 17:17 runs as cancelled.
- **Check (a) treats an unreadable release as "not captured".** If `gh release view snapshots` fails (no release yet, or a gh error), `existing_n_ok` is None and the run goes on to wait and capture. The `better` upload rule still protects a good existing asset.
- **The skip line for `None`** reads `skip runner=actions ny=<date time> wait: not a session or after the window`. The instruction gives the text only for the already-captured skip.
- **Timeout margin.** The worst case is the 15:17 UTC cron starting on time after the 2026-11-01 clock change: it waits until 20:30 UTC (5 h 13 min), and the capture takes about 7 min, inside `timeout-minutes: 355`.

## Session 3b

Instruction 03b: steps 3.2 and 3.3, with the flat-price rule and the decisions of part B. Section 3 is now complete.

### Steps completed

- B    4c1fcf9  section 3b: section 3 review decisions recorded (`decisions/section_3_review.md`)
- 3.2  b02f724  step 3.2: implied volatility (`volsurf/iv.py`, `tests/test_iv.py`; `[iv] flat_tol = 1e-4`, `am_vol_tol = 1e-9`)
- 3.3  75ec927  step 3.3: IV on every captured day (`iv` stage in `scripts/run_all.py`, `tests/test_iv_chain.py`, `outputs/tables/iv_summary.csv`, `outputs/tables/parity_forwards_fixture.csv`)

Session 3c (`a96f353`, `a149d82`) ran between 3b's decisions and step 3.2 and is recorded above.

### 3b-D1. Round trips: status counts for both models, and every returned vol's largest error

The full 2.1 grid, 252 cases per model. European: Black-76 on F = S e^((r − q)T), D = e^(−rT), solved by `iv_european`. American: CRR at `n_prod`, solved by the scalar `iv_american`. Brent runs at `xtol = rtol = 1e-14`.

```
COUNTS
method    bounds  brent  flat  newton  no_root
model                                         
american       8    206    33       0        5
european       6    102    28     116        0
LARGEST
        model kind    K  days  sigma   iv  method       abs_err
399  american    P  110     7    0.3  0.3   brent  2.514938e-11
448  european    P  120    91    0.6  0.6  newton  4.626077e-12
WRONG 0
BATCH_DISAGREE
    kind    K  days  sigma  iv method  iv_batch status_batch
493    P  130   365   0.15 NaN   flat  0.209932        batch
```

Every case returns either a vol within `iv_roundtrip` = 1e-8 or no vol with status `flat`, `no_root` or `bounds`. No returned vol is wrong. 424 cases are solved (218 European, 206 American) and 80 are flagged (34 European, 46 American), which matches the reviewer's 424 and 80. The split of the flagged cases differs. Here, prices outside the Section 5.3 bounds are caught as `bounds` before any solve (6 European, 8 American), where the reviewer's run counted them as `flat` or `no_root`.

`BATCH_DISAGREE` is the one grid case where `iv_american_batch` and the scalar solver disagree. It is not a fixture row, and no test covers the batch solver on the grid. The P 130, 365-day, σ 0.15 put is at immediate exercise: its tree price equals intrinsic, to ±3e-12, for every σ up to about 0.21, and then rises. Brent lands inside that flat stretch, where sens < 1e-4 gives `flat`. Bisection lands at the edge, 0.2099, where σ + 0.01 is already on the rising part, so sens = 0.024 passes the rule and a vol comes back. The flat rule measures sensitivity on both sides of σ̂, so a solve that ends at the edge of a flat region gets through. On real data this is an ITM-only case, and `iv_chain` solves OTM quotes only.

### 3b-D2. Batch against scalar: gaps, status agreement and timing

The test `test_batch_matches_scalar_on_200_fixture_rows` draws 200 clean American fixture rows (SPY and AAPL, ITM and OTM) with `default_rng([run] seed)`. Statuses match on every row (the scalar `brent` is compared with `batch`):

```
statuses {'batch': 194, 'no_root': 6}; largest gap 2.89e-10, median 1.51e-10
```

The same comparison on every clean American fixture row (7,108), run once with a script while building. Status crosstab (scalar rows, batch columns) and gap by OTM:

```
st_b           batch  no_root
otm   st_s                   
False brent     2898        0
      no_root      0      218
True  brent     3992        0
                max        median  count
otm                                     
False  2.919979e-10  1.459112e-10   2898
True   2.906541e-10  1.419969e-10   3992
disagree 0
Empty DataFrame
Columns: [ticker, expiry, kind, strike, S, T, mid, otm, iv_s, st_s, iv_b, st_b, gap]
Index: []
```

Timing, on Windows on the owner's machine (the Python process runs single-threaded):

```
batch on 3992 fixture American OTM rows: 38.8 s; {'batch': 3992}
```

That is under the 300 s bound of instruction 03. `crr_batch` holds the nodes × options array and updates it in place. At N = 200 and N = 2000 its prices are bit-identical to `crr` on 300 sampled fixture rows (largest difference 0.0). The step 2.3 scalar route took 169 s for 7,108 rows.

### 3b-D3. N = 200 against N = 2000

`test_american_n200_vs_n2000_measure`: the 3,992 fixture American OTM rows are solved at N = 200 by `iv_american_batch`, then at N = `n_validate` = 2000 by `iv_american_refine`. That is Newton on `crr_batch` at 2000 steps, from the N = 200 vol, with BSM vega as the slope, until every step is below `am_vol_tol`, for at most `newton_max_iter` iterations.

```
N = 200 against N = 2000: 3992 rows, 6 Newton iterations, largest gap 0.00335205, median 0.000151423, unconverged 0
```

The largest gap is 0.34 vol points, and the median is 0.015 vol points. The test asserts only that the gap is finite (MEASURE).

### 3b-D4. `parity_forwards_fixture.csv` in full

```
        expiry         T         r         D            F    mad_bp  n_pairs    q_impl     r_reg status
0   2026-10-29  0.003309  0.040683  0.999865  7731.925259  0.390665       10 -0.017766       NaN     ok
1   2026-10-30  0.006048  0.040683  0.999754  7733.927196  0.520511       10 -0.034093       NaN     ok
2   2026-11-02  0.014382  0.040683  0.999415  7735.347279  0.595326       10 -0.003531       NaN     ok
3   2026-11-03  0.017121  0.040683  0.999304  7735.897143  0.332401       10 -0.000607       NaN     ok
4   2026-11-04  0.019861  0.040683  0.999192  7736.489087  0.208099       10  0.001236       NaN     ok
5   2026-11-05  0.022601  0.040683  0.999081  7737.518124  0.690671       10  0.000133       NaN     ok
6   2026-11-06  0.025340  0.040683  0.998970  7740.443489  0.274324       10 -0.010400       NaN     ok
7   2026-11-09  0.033560  0.040683  0.998636  7740.696416  0.405742       10  0.001137       NaN     ok
8   2026-11-10  0.036299  0.040683  0.998524  7741.868339  0.279379       10 -0.000048       NaN     ok
9   2026-11-11  0.039039  0.040683  0.998413  7741.638307  0.835817       10  0.003571       NaN     ok
10  2026-11-12  0.041779  0.040683  0.998302  7742.500475  0.722559       10  0.003339       NaN     ok
11  2026-11-13  0.044518  0.040683  0.998190  7743.963839  0.620345       10  0.001392       NaN     ok
12  2026-11-16  0.052738  0.040683  0.997857  7743.779533  0.242659       10  0.007967       NaN     ok
13  2026-11-17  0.055477  0.040683  0.997746  7744.104342  0.499922       10  0.008827       NaN     ok
14  2026-11-18  0.058217  0.040683  0.997634  7744.932639  0.415408       10  0.008489       NaN     ok
15  2026-11-19  0.060957  0.040683  0.997523  7744.811454  0.663526       10  0.010193       NaN     ok
16  2026-11-20  0.063696  0.040683  0.997412  7746.197509  0.357073       10  0.008695       NaN     ok
17  2026-11-23  0.071916  0.040683  0.997079  7747.197153  0.404366       10  0.010556       NaN     ok
18  2026-11-24  0.074655  0.040683  0.996967  7747.898955  0.608039       10  0.010449       NaN     ok
19  2026-11-25  0.077395  0.040683  0.996856  7749.960579  0.497413       10  0.008081       NaN     ok
20  2026-11-27  0.082874  0.040683  0.996634  7752.375314  0.280639       10  0.006478  0.077889     ok
21  2026-11-30  0.091094  0.040734  0.996296  7753.189591  0.449509       10  0.008461 -0.071620     ok
22  2026-12-01  0.093833  0.040751  0.996183  7753.367210  0.838293        8  0.009177  0.055533     ok
23  2026-12-03  0.099313  0.040787  0.995958  7753.590043  0.489732       10  0.010665  0.057250     ok
24  2026-12-04  0.102052  0.040804  0.995844  7755.259188  0.458225       10  0.009382 -0.028878     ok
25  2026-12-11  0.121230  0.040928  0.995051  7760.539793  0.633429       10  0.008862  0.119817     ok
26  2026-12-18  0.140409  0.041052  0.994252  7765.248271  0.334998       10  0.009046  0.045813     ok
27  2026-12-31  0.176025  0.041283  0.992760  7777.177790  0.561604       10  0.007032  0.034189     ok
28  2027-01-15  0.217121  0.041548  0.991020  7794.520202  0.319080       10  0.003521  0.051545     ok
29  2027-01-29  0.255477  0.041789  0.989381  7805.394443  0.321724       10  0.004014 -0.010088     ok
30  2027-02-19  0.313011  0.042082  0.986914  7821.388424  0.595902        9  0.004711  0.047002     ok
31  2027-02-26  0.332189  0.042179  0.986086  7827.646701  0.360462       10  0.004558  0.079248     ok
32  2027-03-19  0.389609  0.042472  0.983589  7841.745373  0.810618        9  0.005776  0.045047     ok
33  2027-03-31  0.422486  0.042639  0.982147  7851.321332  0.599872       10  0.005910  0.053388     ok
34  2027-06-30  0.671801  0.043437  0.971241  7932.897822  0.178584       10  0.004953  0.048835     ok
35  2027-09-30  0.923856  0.044029  0.960140  8019.957064  0.294012       10  0.004230  0.045065     ok
```

These are the same values as the session 3 D2 table.

### 3b-D5. `iv_summary.csv` in full, and 10 random solved rows with all inputs

`scripts/pull_snapshots.py` ran first. The `snapshots` release still does not exist (`release snapshots does not exist; wrote header-only snapshot_manifest.csv`), so the run covers the fixture day alone, which instruction 03b allows.

```
          day ticker  n_in  n_solved  n_newton  n_brent  n_batch  n_bounds  n_no_root  n_flat  n_parity_fail
0  2026-10-28   ^SPX  6841      6841      2473     4368        0         0          0       0              0
1  2026-10-28    SPY  3531      3531         0        0     3531         0          0       0              0
2  2026-10-28   AAPL   461       461         0        0      461         0          0       0              0
```

10 solved rows drawn with `default_rng([run] seed)` from `data/processed/iv/2026-10-28.parquet`:

```
             day ticker      expiry kind  strike         T            S            F         r         q      mid        iv  method   flag
173   2026-10-28   ^SPX  2026-10-30    C  7835.0  0.006048  7730.430176  7733.927196  0.040683 -0.034093    5.600  0.146320   brent       
234   2026-10-28   ^SPX  2026-10-30    P  6830.0  0.006048  7730.430176  7733.927196  0.040683 -0.034093    0.175  0.552958   brent       
712   2026-10-28   ^SPX  2026-11-03    P  7450.0  0.017121  7730.430176  7735.897143  0.040683 -0.000607    4.600  0.183850   brent       
1180  2026-10-28   ^SPX  2026-11-06    C  8125.0  0.025340  7730.430176  7740.443489  0.040683 -0.010400    0.550  0.130646   brent       
1789  2026-10-28   ^SPX  2026-11-11    P  7425.0  0.039039  7730.430176  7741.638307  0.040683  0.003571   18.100  0.187098   brent       
1831  2026-10-28   ^SPX  2026-11-11    P  7695.0  0.039039  7730.430176  7741.638307  0.040683  0.003571   63.950  0.140294  newton       
5859  2026-10-28   ^SPX  2027-03-31    P  6275.0  0.422486  7730.430176  7851.321332  0.042639  0.005910   54.950  0.266500   brent  stale
6070  2026-10-28   ^SPX  2027-03-31    P  7415.0  0.422486  7730.430176  7851.321332  0.042639  0.005910  176.050  0.179829  newton       
7087  2026-10-28    SPY  2026-11-03    P   736.0  0.017120   770.375000   770.781862  0.040683  0.009843    0.295  0.198458   batch       
7903  2026-10-28    SPY  2026-11-30    P   597.0  0.091093   770.375000   772.545801  0.040734  0.009843    0.465  0.399306   batch  stale
```

Flags, IV ranges and the `^SPX` method split by |k| and by T:

```
FLAGS
ticker  flag 
^SPX             5888
        stale     953
SPY              3104
        stale     427
AAPL              455
        stale       6
IV RANGE
         count      mean       std       min       25%       50%       75%       max
ticker                                                                              
^SPX    6841.0  0.216246  0.112944  0.104983  0.137752  0.178634  0.251992  0.905826
SPY     3531.0  0.241129  0.136861  0.109512  0.139749  0.191820  0.293476  0.868181
AAPL     461.0  0.303129  0.063255  0.220411  0.246328  0.293180  0.341111  0.520279
SPX METHOD BY |k|
method          brent  newton
absk_bin                     
(-0.001, 0.02]    120    1345
(0.02, 0.05]      888     752
(0.05, 0.1]      1235     308
(0.1, 0.25]      1538      68
(0.25, inf]       587       0
SPX METHOD BY T
method            brent  newton
T_bin                          
(-0.001, 0.0192]    621     149
(0.0192, 0.0822]   1563     863
(0.0822, 1.0]      2184    1461
```

64% of `^SPX` rows fall back to Brent. The share rises with distance from the money: 8% within |k| ≤ 0.02, and all rows beyond 0.25. The Brenner-Subrahmanyam start is an ATM approximation, so far from the money Newton from it leaves [`iv_lo`, `iv_hi`] or meets vega below `min_vega` × F × D, and the Section 5.3 switch to Brent applies. No OTM row on the fixture is `bounds`, `no_root` or `flat`.

A second run of the `iv` stage leaves `git status` clean, so `iv_summary.csv` and `parity_forwards_fixture.csv` are byte-identical across 2 runs.

### 3b-D6. Tests, fresh-clone check and CI

`.venv/Scripts/pytest -p socket --disable-socket -q` on Windows at `75ec927`: `4488 passed, 5 warnings in 338.37s (0:05:38)`. `ruff check .`: `All checks passed!`

New tests: `tests/test_iv.py` (`test_european_roundtrip_grid`, `test_american_roundtrip_grid`, `test_flat_rule`, `test_bounds_flagged`, `test_brent_fallback_7d_30pct_otm_put`, `test_batch_matches_scalar_on_200_fixture_rows`, `test_batch_timing_fixture_american_otm`, `test_american_n200_vs_n2000_measure`) and `tests/test_iv_chain.py` (`test_iv_chain_schema`, `test_iv_chain_spx_uses_european_and_others_american`, `test_iv_chain_parity_fail_expiry_flagged_without_vol`). What they print:

```
test_european_roundtrip_grid: {'bounds': 6, 'flat': 28, 'brent': 102, 'newton': 116}
test_american_roundtrip_grid: {'flat': 33, 'no_root': 5, 'brent': 206, 'bounds': 8}
test_brent_fallback_7d_30pct_otm_put: sens = 0.00167275
test_batch_matches_scalar_on_200_fixture_rows: statuses {'batch': 194, 'no_root': 6}; largest gap 2.89e-10, median 1.51e-10
test_batch_timing_fixture_american_otm: batch on 3992 fixture American OTM rows: 38.8 s; {'batch': 3992}
test_american_n200_vs_n2000_measure: N = 200 against N = 2000: 3992 rows, 6 Newton iterations, largest gap 0.00335205, median 0.000151423, unconverged 0
```

The Brent fallback test uses σ = 1.0 on the 7-day put with K = 0.7 F: sens = 0.00167, at least 1e-3.

Fresh clone into `C:\Users\astha\AppData\Local\Temp\vs3b` from GitHub after the push of `75ec927`, with the same commands as above (`git clone`, `uv venv --python 3.12`, `uv pip install -r requirements-lock.txt`, `uv pip install -e . --no-deps`). The progress lines are left out:

```
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:894
  C:\Users\astha\AppData\Local\Temp\vs3b\.venv\Lib\site-packages\_pytest\config\__init__.py:894: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
  C:\Users\astha\AppData\Local\Temp\vs3b\.venv\Lib\site-packages\pandas\core\series.py:848: Pandas4Warning: Series.values returning an ndarray that drops timezone information for DatetimeTZDtype is deprecated. In a future version, this will return the underlying DatetimeArray instead. Use 'Series.dt.tz_convert(None).to_numpy()' to get a NumPy array of UTC values, or 'Series.array' to get the ExtensionArray.
  See https://pandas.pydata.org/docs/dev/whatsnew/v3.1.0.html#whatsnew-310-deprecations-values for more details.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
4488 passed, 5 warnings in 443.20s (0:07:23)
exit=0
```

CI (`ci` workflow) on `75ec927`: success, run 40910469696.

### 3b runtime per step

- 3.2: `tests/test_iv.py` takes about 3 to 4 minutes, mostly the N = 2000 measurement (6 passes of a 2000-step tree over 3,992 rows, about 40 s each) and the 38.8 s batch timing test.
- 3.3: the `iv` stage takes 135 s on the fixture day (the batch solve on 3,992 OTM rows and the 6,841 `^SPX` European solves).
- Full suite: 338 s on Windows and 443 s in the fresh clone, against 106 s before Section 3b.

### 3b deviations from PLAN.md

1. **The round-trip tests** follow instruction 03b part B (a vol within `iv_roundtrip`, or no vol with status `flat`, `no_root` or `bounds`), not PLAN 3.2. Each runs as 1 test over the 252 cases and prints the status counts, so a failure lists every case that failed.
2. **Methods** add `batch`, `no_root` and `flat` to PLAN's `newton`, `brent` and `bounds` (instruction 03b). The scalar American solver reports `brent`.
3. **Helpers beyond Section 6.1** (O-1 (a)), all in `volsurf/iv.py`: `crr_batch`, `iv_american_batch`, `iv_american_refine` (for the MEASURE only), `iv_inputs` (adds T, S, r, q, F, D, mid and parity_fail to a clean chain, since `iv_chain(clean, cfg)` has no other inputs) and `iv_summary`.
4. **`test_iv_chain.py`** runs on each fixture ticker's first 2 expiries, to keep it quick. The full fixture day runs in the `iv` stage and in the batch timing and MEASURE tests.

### 3b not verified

- **The Brent tolerance `1e-14` and the bump `0.01`** are literals in `volsurf/iv.py` (`BRENT_TOL`, `FLAT_BUMP`), each with a comment citing instruction 03b part B, under the rule 6 exception for constants written in an instruction file. Neither is in `config.toml`.
- **The bisection midpoint** is returned as the batch vol, and a row whose price at `iv_lo` equals the mid exactly takes `iv_lo` as its root, as `brentq` does. The batch flat rule is evaluated on the same 200-step batch tree.
- **Newton in `iv_european`** starts only when the Brenner-Subrahmanyam start lies in [`iv_lo`, `iv_hi`]. A start outside the range is treated as Newton leaving the range, so Brent runs. Newton that does not converge within `newton_max_iter` also hands over to Brent.
- **`price_bounds`** broadcasts, and returns a bool for scalar input.
- **`iv_chain` row order** follows the clean chain (ticker, then expiry, kind and strike as captured). `flag` joins `stale`, `after_close` and `parity_fail` in that order, and `method` is blank on `parity_fail` rows.
- **`n_in`** counts the rows of the IV table, which are the OTM rows plus every row of a `parity_fail` expiry. `n_solved` counts the rows with a vol.

### 3b open questions

None new. The batch edge case in 3b-D1 is reported, not decided: the flat rule could be made to require low sensitivity on either side of σ̂, if the reviewer wants batch and scalar to agree on synthetic ITM cases too.
