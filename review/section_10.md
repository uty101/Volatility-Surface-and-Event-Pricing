# Review: Section 10

## Section

Section 10: Risk report (`PLAN.md` steps 10.1 and 10.2), with instruction 10 and its step 10.0, on the last captured day, 2026-11-03.

The section is complete. The MEASURE bound is met: the median explained share is 0.951878 against the bound of 0.90. The live median rises from 0.936652 to 0.976712 over N = 6 moves. The sample book breaches 1 of 9 limits: `^SPX` dollar gamma, −1,008,798 against 250,000. 3 new open items, O-47, O-48 and O-49, are implemented as (a) for the reviewer to confirm or switch. Everything built on captured chains is a method demonstration, N = 4 capture days.

## Steps completed

- 10.0  3a46e37  step 10.0: theta includes the carry of F and D
- 10.1  9fc5157  step 10.1: shock grid and limits. It adds O-47, O-48 and the `risk` stage.
- 10.2  30a29e9  step 10.2: PDF risk report. It adds O-49 and the `report` stage.
- The wrap-up commit holds this file, the status file, `decisions/section_9_review.md`, and marks O-45 and O-46 decided.

## Evidence

### E1. Step 10.0: the new MEASURE and the last 5 days

`bs_path_attribution` on the synthetic path. Median over 21 daily steps: **0.951878**, against session 9's 0.944138. It is above 0.90, so `test_bs_path_explained_share_measure` now asserts median share ≥ 0.90.

```
    day           S     theta  residual     total  explained_share
0     1   99.736604  0.110973 -0.000566  0.105631         0.994644
1     2   98.943886  0.113209 -0.003402  0.065227         0.947840
2     3   98.629482  0.112753 -0.002047  0.103492         0.980217
3     4   98.864209  0.113603  0.001675  0.111174         0.984932
4     5   97.593026  0.118559 -0.011003 -0.016712         0.341573
5     6   98.961093  0.108549  0.010516 -0.020633         0.490341
6     7   99.781341  0.126828  0.004423  0.076215         0.941966
7     8   99.921995  0.136181  0.000423  0.134927         0.996864
8     9  100.734642  0.141967  0.000320  0.084319         0.996209
9    10   99.694786  0.147677 -0.002179  0.050009         0.956418
10   11   99.051391  0.153979 -0.005221  0.109117         0.952148
11   12   99.704484  0.155932  0.005738  0.119240         0.951878
12   13   98.645843  0.171119 -0.013064  0.039439         0.668746
13   14   99.517674  0.166074  0.012823  0.097184         0.868052
14   15  100.551217  0.193609  0.002611  0.068333         0.961791
15   16  101.343029  0.212586 -0.012612  0.121373         0.896086
16   17  101.802840  0.214015 -0.017510  0.170641         0.897387
17   18  104.579026  0.208503  0.104677 -0.593698         0.823686
18   19  104.697534  0.040267 -0.002917  0.037070         0.921310
19   20  104.597431  0.021224  0.000968  0.022120         0.956241
20   21  104.689811  0.015981 -0.000027  0.015950         0.998320
median 0.951878
```

The last 5 days:

```
    day     theta  residual     total  explained_share
16   17  0.214015 -0.017510  0.170641         0.897387
17   18  0.208503  0.104677 -0.593698         0.823686
18   19  0.040267 -0.002917  0.037070         0.921310
19   20  0.021224  0.000968  0.022120         0.956241
20   21  0.015981 -0.000027  0.015950         0.998320
```

Day 21 was 0.006584 in session 9 and is 0.998320 now. Days 5 and 6 stay low (0.34 and 0.49) because their totals are near 0, so a small residual is a large share. Day 18 (0.82) is the largest move on the path, 2.78.

### E2. Step 10.0: the live median against session 9's

```
     open_day      expiry  strike        day0        day1   theta_s9  theta_s10  residual_s9  residual_s10      total  share_s9  share_s10
0  2026-10-28  2026-11-27    7750  2026-10-28  2026-10-29   4.728704   4.715295    -0.526931     -0.513521  18.612096  0.971689   0.972409
1  2026-10-28  2026-11-27    7750  2026-10-29  2026-10-30   3.828796   3.747817     3.048997      3.129977 -45.097602  0.932391   0.930595
2  2026-10-28  2026-11-27    7750  2026-10-30  2026-11-03  14.697972  13.233272    -1.693747     -0.229047  15.642263  0.891720   0.985357
3  2026-10-29  2026-11-27    7720  2026-10-29  2026-10-30   3.996499   3.980637     2.618482      2.634343 -44.315916  0.940913   0.940555
4  2026-10-29  2026-11-27    7720  2026-10-30  2026-11-03  16.091217  14.877562    -1.537395     -0.323740  18.491742  0.916860   0.982493
5  2026-10-30  2026-11-30    7580  2026-10-30  2026-11-03  19.292062  19.202101    -0.597762     -0.507801  26.745823  0.977650   0.981014
median s9 0.936652 s10 0.976712 N 6 total unchanged 0.0
```

Live median 0.976712 against session 9's 0.936652, N = 6. `total` is unchanged to 0.0, as it should be: only the split between theta and the residual moves. 4 of the 6 shares rise. 2 fall slightly: row 1 from 0.932391 to 0.930595 and row 3 from 0.940913 to 0.940555. Both are the 1-day move of 2026-10-30, when spot fell 141 points; the change in theta there is 0.02 to 0.08 and their residuals are 2.6 to 3.1, so the fix barely touches them. `hedging_frequency.csv` is byte-identical, since the simulation does not use theta.

### E3. Step 10.1: the selected contracts

```
   position                contract  side  contracts  target_days  days  target_delta  select_delta     delta       vol      price         T            S            F         D         r         q status
0         1  ^SPX 2026-12-03 P 7275    -1         10           30    30         -0.25     -0.244107 -0.244107  0.216530  70.048120  0.082248  7561.450195  7580.025029  0.996659  0.040683  0.010853     ok
1         2  ^SPX 2026-12-03 C 7780    -1         10           30    30          0.25      0.257847  0.257847  0.135771  44.874809  0.082248  7561.450195  7580.025029  0.996659  0.040683  0.010853     ok
2         3   AAPL 2027-01-15 C 335     1         20           60    73          0.50      0.505311  0.505205  0.245292  13.779636  0.200053   330.964996   333.506287  0.991744  0.041438  0.003203     ok
3         4   NVDA 2026-12-18 P 193    -1         15           45    45         -0.30     -0.300039 -0.301502  0.475454   7.223777  0.123342   206.750000   207.732246  0.994963  0.040942  0.002515     ok
                 contract     gamma        vega  dollar_delta   dollar_gamma      vega_pt
0  ^SPX 2026-12-03 P 7275  0.000668  680.094444  1.845800e+06 -381876.472300 -6800.944443
1  ^SPX 2026-12-03 C 7780  0.001096  700.080541 -1.949694e+06 -626921.096500 -7000.805408
2   AAPL 2027-01-15 C 335  0.011001   59.299523  3.344103e+05   24100.969510  1185.990451
3   NVDA 2026-12-18 P 193  0.010176   25.874702  9.350329e+04   -6524.756143  -388.120533
```

AAPL's 60-day target lands on 73 days: 2027-01-15 is 13 days away and 2026-12-18 is 15. `select_delta` is the BSM delta of O-21 (a); `delta` is the pricer's delta used for the limits.

### E4. Step 10.1: `risk_grid.csv` for the last day

The book rows as a table, in dollars:

```
vol_shock_pts          -5.0           -2.5           0.0           2.5           5.0
spot_shock                                                                          
-0.100        -386275.83290 -395004.813700 -405357.04230 -417181.72730 -430445.55030
-0.075        -220001.62670 -234817.893400 -250733.69340 -267980.79970 -286959.00880
-0.050         -84723.67997 -104062.240800 -124909.14200 -147786.86750 -172941.70010
-0.025          10722.56851  -11498.327030  -37338.39366  -66235.75707  -97502.57609
 0.000          58660.13058   31156.060320       0.00000  -33523.38205  -68641.15783
 0.025          37267.84070    7801.773119  -23632.58805  -56708.27932  -91059.55980
 0.050         -66590.84437  -85433.133040 -108312.52480 -134304.56090 -162654.79630
 0.075        -222328.35160 -228464.149700 -239672.41700 -255303.43520 -274670.07570
 0.100        -393495.77540 -394049.966700 -397381.02950 -404496.35650 -415291.67000
```

The file in full, 225 rows (4 positions and the book, 45 cells each):

```
            day  position                contract  spot_shock  vol_shock_pts            pnl status  left_out
0    2026-11-03         1  ^SPX 2026-12-03 P 7275      -0.100           -5.0 -395244.422300     ok       NaN
1    2026-11-03         1  ^SPX 2026-12-03 P 7275      -0.100           -2.5 -404395.380300     ok       NaN
2    2026-11-03         1  ^SPX 2026-12-03 P 7275      -0.100            0.0 -415358.706800     ok       NaN
3    2026-11-03         1  ^SPX 2026-12-03 P 7275      -0.100            2.5 -427779.806000     ok       NaN
4    2026-11-03         1  ^SPX 2026-12-03 P 7275      -0.100            5.0 -441367.739300     ok       NaN
5    2026-11-03         1  ^SPX 2026-12-03 P 7275      -0.075           -5.0 -235433.162300     ok       NaN
6    2026-11-03         1  ^SPX 2026-12-03 P 7275      -0.075           -2.5 -251140.288600     ok       NaN
7    2026-11-03         1  ^SPX 2026-12-03 P 7275      -0.075            0.0 -267813.217600     ok       NaN
8    2026-11-03         1  ^SPX 2026-12-03 P 7275      -0.075            2.5 -285186.228800     ok       NaN
9    2026-11-03         1  ^SPX 2026-12-03 P 7275      -0.075            5.0 -303079.844700     ok       NaN
10   2026-11-03         1  ^SPX 2026-12-03 P 7275      -0.050           -5.0 -107384.220500     ok       NaN
11   2026-11-03         1  ^SPX 2026-12-03 P 7275      -0.050           -2.5 -127604.387500     ok       NaN
12   2026-11-03         1  ^SPX 2026-12-03 P 7275      -0.050            0.0 -147915.715400     ok       NaN
13   2026-11-03         1  ^SPX 2026-12-03 P 7275      -0.050            2.5 -168289.255300     ok       NaN
14   2026-11-03         1  ^SPX 2026-12-03 P 7275      -0.050            5.0 -188706.718500     ok       NaN
15   2026-11-03         1  ^SPX 2026-12-03 P 7275      -0.025           -5.0  -19121.252290     ok       NaN
16   2026-11-03         1  ^SPX 2026-12-03 P 7275      -0.025           -2.5  -39052.228270     ok       NaN
17   2026-11-03         1  ^SPX 2026-12-03 P 7275      -0.025            0.0  -59200.065790     ok       NaN
18   2026-11-03         1  ^SPX 2026-12-03 P 7275      -0.025            2.5  -79497.938250     ok       NaN
19   2026-11-03         1  ^SPX 2026-12-03 P 7275      -0.025            5.0  -99903.423560     ok       NaN
20   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.000           -5.0   31876.128860     ok       NaN
21   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.000           -2.5   16527.211400     ok       NaN
22   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.000            0.0      -0.000000     ok       NaN
23   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.000            2.5  -17392.006540     ok       NaN
24   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.000            5.0  -35432.827640     ok       NaN
25   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.025           -5.0   56250.204430     ok       NaN
26   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.025           -2.5   46833.794060     ok       NaN
27   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.025            0.0   35457.819990     ok       NaN
28   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.025            2.5   22494.401890     ok       NaN
29   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.025            5.0    8253.948187     ok       NaN
30   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.050           -5.0   65849.484510     ok       NaN
31   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.050           -2.5   61160.629780     ok       NaN
32   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.050            0.0   54499.286220     ok       NaN
33   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.050            2.5   46004.091400     ok       NaN
34   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.050            5.0   35882.648280     ok       NaN
35   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.075           -5.0   68971.291990     ok       NaN
36   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.075           -2.5   67042.170960     ok       NaN
37   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.075            0.0   63680.735880     ok       NaN
38   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.075            2.5   58737.573180     ok       NaN
39   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.075            5.0   52208.837780     ok       NaN
40   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.100           -5.0   69814.409720     ok       NaN
41   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.100           -2.5   69147.482420     ok       NaN
42   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.100            0.0   67667.933130     ok       NaN
43   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.100            2.5   65090.373070     ok       NaN
44   2026-11-03         1  ^SPX 2026-12-03 P 7275       0.100            5.0   61240.494630     ok       NaN
45   2026-11-03         2  ^SPX 2026-12-03 C 7780      -0.100           -5.0   44874.807250     ok       NaN
46   2026-11-03         2  ^SPX 2026-12-03 C 7780      -0.100           -2.5   44873.915420     ok       NaN
47   2026-11-03         2  ^SPX 2026-12-03 C 7780      -0.100            0.0   44847.779410     ok       NaN
48   2026-11-03         2  ^SPX 2026-12-03 C 7780      -0.100            2.5   44659.568550     ok       NaN
49   2026-11-03         2  ^SPX 2026-12-03 C 7780      -0.100            5.0   44014.988300     ok       NaN
50   2026-11-03         2  ^SPX 2026-12-03 C 7780      -0.075           -5.0   44874.348880     ok       NaN
51   2026-11-03         2  ^SPX 2026-12-03 C 7780      -0.075           -2.5   44841.943110     ok       NaN
52   2026-11-03         2  ^SPX 2026-12-03 C 7780      -0.075            0.0   44540.860800     ok       NaN
53   2026-11-03         2  ^SPX 2026-12-03 C 7780      -0.075            2.5   43461.057390     ok       NaN
54   2026-11-03         2  ^SPX 2026-12-03 C 7780      -0.075            5.0   41093.297630     ok       NaN
55   2026-11-03         2  ^SPX 2026-12-03 C 7780      -0.050           -5.0   44833.004160     ok       NaN
56   2026-11-03         2  ^SPX 2026-12-03 C 7780      -0.050           -2.5   44293.765720     ok       NaN
57   2026-11-03         2  ^SPX 2026-12-03 C 7780      -0.050            0.0   42315.272930     ok       NaN
58   2026-11-03         2  ^SPX 2026-12-03 C 7780      -0.050            2.5   38228.426120     ok       NaN
59   2026-11-03         2  ^SPX 2026-12-03 C 7780      -0.050            5.0   31881.126490     ok       NaN
60   2026-11-03         2  ^SPX 2026-12-03 C 7780      -0.025           -5.0   43631.474480     ok       NaN
61   2026-11-03         2  ^SPX 2026-12-03 C 7780      -0.025           -2.5   39510.589120     ok       NaN
62   2026-11-03         2  ^SPX 2026-12-03 C 7780      -0.025            0.0   32010.268240     ok       NaN
63   2026-11-03         2  ^SPX 2026-12-03 C 7780      -0.025            2.5   21616.341290     ok       NaN
64   2026-11-03         2  ^SPX 2026-12-03 C 7780      -0.025            5.0    8970.995807     ok       NaN
65   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.000           -5.0   30863.585960     ok       NaN
66   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.000           -2.5   16649.814740     ok       NaN
67   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.000            0.0      -0.000000     ok       NaN
68   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.000            2.5  -18123.708590     ok       NaN
69   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.000            5.0  -37188.854440     ok       NaN
70   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.025           -5.0  -26058.856890     ok       NaN
71   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.025           -2.5  -48194.897030     ok       NaN
72   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.025            0.0  -70339.145080     ok       NaN
73   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.025            2.5  -92486.900380     ok       NaN
74   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.025            5.0 -114635.838500     ok       NaN
75   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.050           -5.0 -152060.026900     ok       NaN
76   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.050           -2.5 -168186.214700     ok       NaN
77   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.050            0.0 -186386.767000     ok       NaN
78   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.050            2.5 -205805.600500     ok       NaN
79   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.050            5.0 -225989.738300     ok       NaN
80   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.075           -5.0 -324684.830700     ok       NaN
81   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.075           -2.5 -330566.468900     ok       NaN
82   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.075            0.0 -340163.825700     ok       NaN
83   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.075            2.5 -352682.493400     ok       NaN
84   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.075            5.0 -367365.080300     ok       NaN
85   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.100           -5.0 -511430.972000     ok       NaN
86   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.100           -2.5 -512605.581400     ok       NaN
87   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.100            0.0 -515991.318200     ok       NaN
88   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.100            2.5 -522075.167500     ok       NaN
89   2026-11-03         2  ^SPX 2026-12-03 C 7780       0.100            5.0 -530747.178900     ok       NaN
90   2026-11-03         3   AAPL 2027-01-15 C 335      -0.100           -5.0  -24820.428170     ok       NaN
91   2026-11-03         3   AAPL 2027-01-15 C 335      -0.100           -2.5  -23425.213410     ok       NaN
92   2026-11-03         3   AAPL 2027-01-15 C 335      -0.100            0.0  -21816.024010     ok       NaN
93   2026-11-03         3   AAPL 2027-01-15 C 335      -0.100            2.5  -20059.857550     ok       NaN
94   2026-11-03         3   AAPL 2027-01-15 C 335      -0.100            5.0  -18120.078870     ok       NaN
95   2026-11-03         3   AAPL 2027-01-15 C 335      -0.075           -5.0  -22398.952800     ok       NaN
96   2026-11-03         3   AAPL 2027-01-15 C 335      -0.075           -2.5  -20472.746720     ok       NaN
97   2026-11-03         3   AAPL 2027-01-15 C 335      -0.075            0.0  -18411.930380     ok       NaN
98   2026-11-03         3   AAPL 2027-01-15 C 335      -0.075            2.5  -16203.999030     ok       NaN
99   2026-11-03         3   AAPL 2027-01-15 C 335      -0.075            5.0  -13919.024960     ok       NaN
100  2026-11-03         3   AAPL 2027-01-15 C 335      -0.050           -5.0  -18631.068030     ok       NaN
101  2026-11-03         3   AAPL 2027-01-15 C 335      -0.050           -2.5  -16198.024840     ok       NaN
102  2026-11-03         3   AAPL 2027-01-15 C 335      -0.050            0.0  -13742.837830     ok       NaN
103  2026-11-03         3   AAPL 2027-01-15 C 335      -0.050            2.5  -11147.924080     ok       NaN
104  2026-11-03         3   AAPL 2027-01-15 C 335      -0.050            5.0   -8525.828224     ok       NaN
105  2026-11-03         3   AAPL 2027-01-15 C 335      -0.025           -5.0  -13212.297200     ok       NaN
106  2026-11-03         3   AAPL 2027-01-15 C 335      -0.025           -2.5  -10398.368400     ok       NaN
107  2026-11-03         3   AAPL 2027-01-15 C 335      -0.025            0.0   -7589.252840     ok       NaN
108  2026-11-03         3   AAPL 2027-01-15 C 335      -0.025            2.5   -4793.339640     ok       NaN
109  2026-11-03         3   AAPL 2027-01-15 C 335      -0.025            5.0   -2007.537097     ok       NaN
110  2026-11-03         3   AAPL 2027-01-15 C 335       0.000           -5.0   -5939.661557     ok       NaN
111  2026-11-03         3   AAPL 2027-01-15 C 335       0.000           -2.5   -2967.191750     ok       NaN
112  2026-11-03         3   AAPL 2027-01-15 C 335       0.000            0.0       0.000000     ok       NaN
113  2026-11-03         3   AAPL 2027-01-15 C 335       0.000            2.5    2963.058120     ok       NaN
114  2026-11-03         3   AAPL 2027-01-15 C 335       0.000            5.0    5922.708940     ok       NaN
115  2026-11-03         3   AAPL 2027-01-15 C 335       0.025           -5.0    3211.060708     ok       NaN
116  2026-11-03         3   AAPL 2027-01-15 C 335       0.025           -2.5    6146.969285     ok       NaN
117  2026-11-03         3   AAPL 2027-01-15 C 335       0.025            0.0    9098.988356     ok       NaN
118  2026-11-03         3   AAPL 2027-01-15 C 335       0.025            2.5   12056.439410     ok       NaN
119  2026-11-03         3   AAPL 2027-01-15 C 335       0.025            5.0   15017.621520     ok       NaN
120  2026-11-03         3   AAPL 2027-01-15 C 335       0.050           -5.0   14129.461530     ok       NaN
121  2026-11-03         3   AAPL 2027-01-15 C 335       0.050           -2.5   16876.232180     ok       NaN
122  2026-11-03         3   AAPL 2027-01-15 C 335       0.050            0.0   19642.462060     ok       NaN
123  2026-11-03         3   AAPL 2027-01-15 C 335       0.050            2.5   22422.527120     ok       NaN
124  2026-11-03         3   AAPL 2027-01-15 C 335       0.050            5.0   25237.337600     ok       NaN
125  2026-11-03         3   AAPL 2027-01-15 C 335       0.075           -5.0   26599.539370     ok       NaN
126  2026-11-03         3   AAPL 2027-01-15 C 335       0.075           -2.5   28965.596900     ok       NaN
127  2026-11-03         3   AAPL 2027-01-15 C 335       0.075            0.0   31417.408800     ok       NaN
128  2026-11-03         3   AAPL 2027-01-15 C 335       0.075            2.5   34030.810130     ok       NaN
129  2026-11-03         3   AAPL 2027-01-15 C 335       0.075            5.0   36659.704290     ok       NaN
130  2026-11-03         3   AAPL 2027-01-15 C 335       0.100           -5.0   40318.419730     ok       NaN
131  2026-11-03         3   AAPL 2027-01-15 C 335       0.100           -2.5   42210.478800     ok       NaN
132  2026-11-03         3   AAPL 2027-01-15 C 335       0.100            0.0   44365.256700     ok       NaN
133  2026-11-03         3   AAPL 2027-01-15 C 335       0.100            2.5   46610.766970     ok       NaN
134  2026-11-03         3   AAPL 2027-01-15 C 335       0.100            5.0   49038.609280     ok       NaN
135  2026-11-03         4   NVDA 2026-12-18 P 193      -0.100           -5.0  -11085.789710     ok       NaN
136  2026-11-03         4   NVDA 2026-12-18 P 193      -0.100           -2.5  -12058.135450     ok       NaN
137  2026-11-03         4   NVDA 2026-12-18 P 193      -0.100            0.0  -13030.090890     ok       NaN
138  2026-11-03         4   NVDA 2026-12-18 P 193      -0.100            2.5  -14001.632320     ok       NaN
139  2026-11-03         4   NVDA 2026-12-18 P 193      -0.100            5.0  -14972.720430     ok       NaN
140  2026-11-03         4   NVDA 2026-12-18 P 193      -0.075           -5.0   -7043.860466     ok       NaN
141  2026-11-03         4   NVDA 2026-12-18 P 193      -0.075           -2.5   -8046.801178     ok       NaN
142  2026-11-03         4   NVDA 2026-12-18 P 193      -0.075            0.0   -9049.406200     ok       NaN
143  2026-11-03         4   NVDA 2026-12-18 P 193      -0.075            2.5  -10051.629260     ok       NaN
144  2026-11-03         4   NVDA 2026-12-18 P 193      -0.075            5.0  -11053.436810     ok       NaN
145  2026-11-03         4   NVDA 2026-12-18 P 193      -0.050           -5.0   -3541.395547     ok       NaN
146  2026-11-03         4   NVDA 2026-12-18 P 193      -0.050           -2.5   -4553.594171     ok       NaN
147  2026-11-03         4   NVDA 2026-12-18 P 193      -0.050            0.0   -5565.861705     ok       NaN
148  2026-11-03         4   NVDA 2026-12-18 P 193      -0.050            2.5   -6578.114240     ok       NaN
149  2026-11-03         4   NVDA 2026-12-18 P 193      -0.050            5.0   -7590.279784     ok       NaN
150  2026-11-03         4   NVDA 2026-12-18 P 193      -0.025           -5.0    -575.356477     ok       NaN
151  2026-11-03         4   NVDA 2026-12-18 P 193      -0.025           -2.5   -1558.319469     ok       NaN
152  2026-11-03         4   NVDA 2026-12-18 P 193      -0.025            0.0   -2559.343267     ok       NaN
153  2026-11-03         4   NVDA 2026-12-18 P 193      -0.025            2.5   -3560.820467     ok       NaN
154  2026-11-03         4   NVDA 2026-12-18 P 193      -0.025            5.0   -4562.611238     ok       NaN
155  2026-11-03         4   NVDA 2026-12-18 P 193       0.000           -5.0    1860.077316     ok       NaN
156  2026-11-03         4   NVDA 2026-12-18 P 193       0.000           -2.5     946.225926     ok       NaN
157  2026-11-03         4   NVDA 2026-12-18 P 193       0.000            0.0      -0.000000     ok       NaN
158  2026-11-03         4   NVDA 2026-12-18 P 193       0.000            2.5    -970.725042     ok       NaN
159  2026-11-03         4   NVDA 2026-12-18 P 193       0.000            5.0   -1942.184689     ok       NaN
160  2026-11-03         4   NVDA 2026-12-18 P 193       0.025           -5.0    3865.432455     ok       NaN
161  2026-11-03         4   NVDA 2026-12-18 P 193       0.025           -2.5    3015.906803     ok       NaN
162  2026-11-03         4   NVDA 2026-12-18 P 193       0.025            0.0    2149.748684     ok       NaN
163  2026-11-03         4   NVDA 2026-12-18 P 193       0.025            2.5    1227.779761     ok       NaN
164  2026-11-03         4   NVDA 2026-12-18 P 193       0.025            5.0     304.708990     ok       NaN
165  2026-11-03         4   NVDA 2026-12-18 P 193       0.050           -5.0    5490.236538     ok       NaN
166  2026-11-03         4   NVDA 2026-12-18 P 193       0.050           -2.5    4716.219677     ok       NaN
167  2026-11-03         4   NVDA 2026-12-18 P 193       0.050            0.0    3932.493972     ok       NaN
168  2026-11-03         4   NVDA 2026-12-18 P 193       0.050            2.5    3074.421130     ok       NaN
169  2026-11-03         4   NVDA 2026-12-18 P 193       0.050            5.0    2214.956157     ok       NaN
170  2026-11-03         4   NVDA 2026-12-18 P 193       0.075           -5.0    6785.647705     ok       NaN
171  2026-11-03         4   NVDA 2026-12-18 P 193       0.075           -2.5    6094.551350     ok       NaN
172  2026-11-03         4   NVDA 2026-12-18 P 193       0.075            0.0    5393.264008     ok       NaN
173  2026-11-03         4   NVDA 2026-12-18 P 193       0.075            2.5    4610.674884     ok       NaN
174  2026-11-03         4   NVDA 2026-12-18 P 193       0.075            5.0    3826.462598     ok       NaN
175  2026-11-03         4   NVDA 2026-12-18 P 193       0.100           -5.0    7802.367093     ok       NaN
176  2026-11-03         4   NVDA 2026-12-18 P 193       0.100           -2.5    7197.653420     ok       NaN
177  2026-11-03         4   NVDA 2026-12-18 P 193       0.100            0.0    6577.098910     ok       NaN
178  2026-11-03         4   NVDA 2026-12-18 P 193       0.100            2.5    5877.670931     ok       NaN
179  2026-11-03         4   NVDA 2026-12-18 P 193       0.100            5.0    5176.404965     ok       NaN
180  2026-11-03         0                    book      -0.100           -5.0 -386275.832900     ok       0.0
181  2026-11-03         0                    book      -0.100           -2.5 -395004.813700     ok       0.0
182  2026-11-03         0                    book      -0.100            0.0 -405357.042300     ok       0.0
183  2026-11-03         0                    book      -0.100            2.5 -417181.727300     ok       0.0
184  2026-11-03         0                    book      -0.100            5.0 -430445.550300     ok       0.0
185  2026-11-03         0                    book      -0.075           -5.0 -220001.626700     ok       0.0
186  2026-11-03         0                    book      -0.075           -2.5 -234817.893400     ok       0.0
187  2026-11-03         0                    book      -0.075            0.0 -250733.693400     ok       0.0
188  2026-11-03         0                    book      -0.075            2.5 -267980.799700     ok       0.0
189  2026-11-03         0                    book      -0.075            5.0 -286959.008800     ok       0.0
190  2026-11-03         0                    book      -0.050           -5.0  -84723.679970     ok       0.0
191  2026-11-03         0                    book      -0.050           -2.5 -104062.240800     ok       0.0
192  2026-11-03         0                    book      -0.050            0.0 -124909.142000     ok       0.0
193  2026-11-03         0                    book      -0.050            2.5 -147786.867500     ok       0.0
194  2026-11-03         0                    book      -0.050            5.0 -172941.700100     ok       0.0
195  2026-11-03         0                    book      -0.025           -5.0   10722.568510     ok       0.0
196  2026-11-03         0                    book      -0.025           -2.5  -11498.327030     ok       0.0
197  2026-11-03         0                    book      -0.025            0.0  -37338.393660     ok       0.0
198  2026-11-03         0                    book      -0.025            2.5  -66235.757070     ok       0.0
199  2026-11-03         0                    book      -0.025            5.0  -97502.576090     ok       0.0
200  2026-11-03         0                    book       0.000           -5.0   58660.130580     ok       0.0
201  2026-11-03         0                    book       0.000           -2.5   31156.060320     ok       0.0
202  2026-11-03         0                    book       0.000            0.0       0.000000     ok       0.0
203  2026-11-03         0                    book       0.000            2.5  -33523.382050     ok       0.0
204  2026-11-03         0                    book       0.000            5.0  -68641.157830     ok       0.0
205  2026-11-03         0                    book       0.025           -5.0   37267.840700     ok       0.0
206  2026-11-03         0                    book       0.025           -2.5    7801.773119     ok       0.0
207  2026-11-03         0                    book       0.025            0.0  -23632.588050     ok       0.0
208  2026-11-03         0                    book       0.025            2.5  -56708.279320     ok       0.0
209  2026-11-03         0                    book       0.025            5.0  -91059.559800     ok       0.0
210  2026-11-03         0                    book       0.050           -5.0  -66590.844370     ok       0.0
211  2026-11-03         0                    book       0.050           -2.5  -85433.133040     ok       0.0
212  2026-11-03         0                    book       0.050            0.0 -108312.524800     ok       0.0
213  2026-11-03         0                    book       0.050            2.5 -134304.560900     ok       0.0
214  2026-11-03         0                    book       0.050            5.0 -162654.796300     ok       0.0
215  2026-11-03         0                    book       0.075           -5.0 -222328.351600     ok       0.0
216  2026-11-03         0                    book       0.075           -2.5 -228464.149700     ok       0.0
217  2026-11-03         0                    book       0.075            0.0 -239672.417000     ok       0.0
218  2026-11-03         0                    book       0.075            2.5 -255303.435200     ok       0.0
219  2026-11-03         0                    book       0.075            5.0 -274670.075700     ok       0.0
220  2026-11-03         0                    book       0.100           -5.0 -393495.775400     ok       0.0
221  2026-11-03         0                    book       0.100           -2.5 -394049.966700     ok       0.0
222  2026-11-03         0                    book       0.100            0.0 -397381.029500     ok       0.0
223  2026-11-03         0                    book       0.100            2.5 -404496.356500     ok       0.0
224  2026-11-03         0                    book       0.100            5.0 -415291.670000     ok       0.0
```

One cell recomputed by hand, from a Black-76 put written separately from the project's pricer: `^SPX` put, spot −5%, vol +2.5 points.

```
hand -168289.2554406676 grid -168289.2553
```

### E5. Step 10.1: `limit_breaches.csv`

```
          day underlying       measure         value    limit  breach status  left_out
0  2026-11-03       ^SPX  dollar_delta -1.038943e+05  2000000   False     ok         0
1  2026-11-03       ^SPX  dollar_gamma -1.008798e+06   250000    True     ok         0
2  2026-11-03       ^SPX       vega_pt -1.380175e+04    50000   False     ok         0
3  2026-11-03       AAPL  dollar_delta  3.344103e+05  2000000   False     ok         0
4  2026-11-03       AAPL  dollar_gamma  2.410097e+04   250000   False     ok         0
5  2026-11-03       AAPL       vega_pt  1.185990e+03    50000   False     ok         0
6  2026-11-03       NVDA  dollar_delta  9.350329e+04  2000000   False     ok         0
7  2026-11-03       NVDA  dollar_gamma -6.524756e+03   250000   False     ok         0
8  2026-11-03       NVDA       vega_pt -3.881205e+02    50000   False     ok         0
```

### E6. Step 10.1: the small-shock MEASURE

`test_small_shock_matches_delta_measure` on its synthetic 1-position books, shock `fd_h_spot_rel` = 1e-4, P&L against delta × dS:

```
MEASURE ^SPX shock 0.0001: P&L 193.636600, delta x dS 193.823123, relative gap 0.000962337
MEASURE AAPL shock 0.0001: P&L 24.987615, delta x dS 25.016764, relative gap 0.00116517
```

The same on the 4 real positions, at 3 shock sizes:

```
     shock                contract           pnl      delta_dS   rel_gap
0   0.0001  ^SPX 2026-12-03 P 7275    184.389100    184.579961  0.001034
1   0.0001  ^SPX 2026-12-03 C 7780   -195.283016   -194.969393  0.001609
2   0.0001   AAPL 2027-01-15 C 335     34.500994     33.441029  0.031697
3   0.0001   NVDA 2026-12-18 P 193      9.974368      9.350329  0.066740
4   0.0010  ^SPX 2026-12-03 P 7275   1826.783281   1845.799611  0.010302
5   0.0010  ^SPX 2026-12-03 C 7780  -1981.202623  -1949.693925  0.016161
6   0.0010   AAPL 2027-01-15 C 335    345.009944    334.410294  0.031697
7   0.0010   NVDA 2026-12-18 P 193     99.743642     93.503295  0.066739
8   0.0100  ^SPX 2026-12-03 P 7275  16627.283050  18457.996110  0.099183
9   0.0100  ^SPX 2026-12-03 C 7780 -22782.811283 -19496.939250  0.168533
10  0.0100   AAPL 2027-01-15 C 335   3450.099441   3344.102936  0.031697
11  0.0100   NVDA 2026-12-18 P 193    880.528123    935.032948  0.058292
```

On `^SPX` the gap grows with the shock, as gamma says it should. On AAPL and NVDA it does not shrink below 3.2% and 6.7%, however small the shock: the tree's value is piecewise linear in S, so the revaluation follows the local segment while the delta comes from the nodes either side. A bound set from these numbers has to allow for that on the tree contracts.

### E7. Step 10.1: tree Greeks at `n_prod` against `n_validate` (O-48)

```
                                0                      1
contract    AAPL 2027-01-15 C 335  NVDA 2026-12-18 P 193
delta_200                0.505205              -0.301502
gamma_200                0.011001               0.010176
vega_200                59.299523              25.874702
delta_2000               0.505305              -0.301622
gamma_2000                0.01098               0.010152
vega_2000               59.010976              25.161611
```

### E8. Step 10.1: SSVI vol against the market on the selected contracts

Instruction 10 fixes the SSVI vol, so the book uses it. For the reviewer, the same contracts against their own quotes:

```
                 contract  ssvi_vol  market_iv   gap_pts  model_price  market_mid
0  ^SPX 2026-12-03 P 7275  0.216530   0.204091  1.243895    70.048120      61.700
1  ^SPX 2026-12-03 C 7780  0.135771   0.140696 -0.492527    44.874809      48.350
2   AAPL 2027-01-15 C 335  0.245292   0.245214  0.007818    13.779636      13.775
3   NVDA 2026-12-18 P 193  0.475454   0.473569  0.188517     7.223777       7.175
```

The `^SPX` put is marked 1.24 vol points above its quote, 70.05 against a mid of 61.70, and the call 0.49 below, 44.87 against 48.35. This is the SSVI skew limit of instruction 05 correction 4. It feeds the grid's base value and the vols of both `^SPX` rows.

### E9. Step 10.2: the page and the 2-build byte check

Page render: `review/section_10_page.png`. PDF: `outputs/reports/risk_2026-11-03.pdf`, 1 page.

The report stage run twice on the committed tables:

```
13dac125f0a9aeeb90457e37b66c5edd19cd396b2f92754c6dd6e75e99a7d440  first build
13dac125f0a9aeeb90457e37b66c5edd19cd396b2f92754c6dd6e75e99a7d440  second build
```

`test_two_builds_byte_identical` and `test_one_page` pass in `tests/test_report.py`. Heat colour strength is the square root of each cell's share of the largest size, because on a linear scale the largest gain, +58.7, was almost the neutral beside −430.4. Every cell prints its number.

### E10. CI

Run 41822349686 at `30a29e9` on Linux: success. `ruff check .`: `All checks passed!`. Pytest: `4632 passed, 35 warnings in 707.19s (0:11:47)`.

## Tests run

`.venv\Scripts\python -m pytest -p socket --disable-socket -q` on Windows at `30a29e9`:

```
4632 passed, 35 warnings in 43297.28s (12:01:37)
```

The time is not a runtime: the machine slept from about 00:21 to 11:30 with the run open. `ruff check .`: `All checks passed!`

## Fresh-clone check

`git clone` into `C:\vs10`, `uv venv --python 3.12`, install from `requirements-lock.txt`, `pip install -e . --no-deps`, then `pytest -p socket --disable-socket -q`:

```
HEAD 30a29e9
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:894
  C:\vs10\.venv\Lib\site-packages\_pytest\config\__init__.py:894: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

tests/test_capture_health.py: 4 warnings
tests/test_correlation.py: 4 warnings
tests/test_vrp.py: 24 warnings
  C:\vs10\.venv\Lib\site-packages\pandas\core\series.py:848: Pandas4Warning: Series.values returning an ndarray that drops timezone information for DatetimeTZDtype is deprecated. In a future version, this will return the underlying DatetimeArray instead. Use 'Series.dt.tz_convert(None).to_numpy()' to get a NumPy array of UTC values, or 'Series.array' to get the ExtensionArray.
  See https://pandas.pydata.org/docs/dev/whatsnew/v3.1.0.html#whatsnew-310-deprecations-values for more details.
    warnings.warn(

tests/test_correlation.py::test_rv_screen_blank_below_min_days
  C:\vs10\volsurf\correlation.py:205: RuntimeWarning: invalid value encountered in scalar divide
    z = (r.atm_30 - prior.mean()) / prior.std(ddof=1)  # O-15 (a): ddof 1, today excluded

tests/test_snapshots.py::test_wait_chains_when_above_max_wait
  C:\vs10\.venv\Lib\site-packages\pytest_socket\__init__.py:138: UserWarning: A test tried to use socket.socket.
    raise SocketBlockedError()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
4632 passed, 35 warnings in 1476.96s (0:24:36)
```

## Runtime per step

- `run_all.py --stage attribution`: 9 s.
- `run_all.py --stage risk`: 4 s.
- `run_all.py --stage report`: under 3 s.

## Deviations from PLAN.md

- `build_risk_report` takes a 6th argument, `n_days` (O-49), because instruction 10 puts N on the page.
- `test_theta_reprices_with_only_t_shortened` is replaced by `test_theta_rolls_t_f_and_d`. Instruction 10 changed the definition of Θ, so the old assertion no longer describes the spec. Rule 5 is not engaged: the reviewer changed the spec, as in O-37.
- `risk_book.csv` is an extra table, holding the selected book (O-47).
- `decisions/section_9_review.md` is written and O-45 and O-46 are marked decided. Instruction 10 does not ask for this by name; it follows every earlier section and `WORKFLOW.md` Part 5.

## Not verified

- The PDF's bytes on Linux. The 2-build check ran on Windows here; `test_two_builds_byte_identical` also runs in CI, but no Windows and Linux PDFs were compared.
- Limits are not market limits: `[limits]` and `[book]` are config values, so the breach describes the sample book only.
- The sample book's Greeks are not checked against a second source beyond E4's hand cell and E7's finer tree.

## Open questions

- **O-47** The book, grid and limit tables. (a) IV table candidates, `risk_book.csv`, long grid, every measure in `limit_breaches.csv`. (b) Every listed strike, breached rows only, wide grid. Implemented as (a).
- **O-48** Greeks on the CRR tree. (a) Node delta and gamma, vega at width `fd_h_vol`. (b) As (a), with a wider bump from a new `[risk] vega_bump` key. Implemented as (a).
- **O-49** The report's N. (a) A 6th argument. (b) A column of `grid`. Implemented as (a).

## Files changed

- New: `volsurf/risk.py`, `volsurf/report.py`, `tests/test_risk.py`, `tests/test_report.py`, `outputs/tables/risk_book.csv`, `outputs/tables/risk_grid.csv`, `outputs/tables/limit_breaches.csv`, `outputs/reports/risk_2026-11-03.pdf`, `review/section_10_page.png`, `review/section_10.md`, `decisions/section_9_review.md`, `instructions/10_section_10.status.md`.
- Changed: `volsurf/attribution.py`, `tests/test_attribution.py`, `scripts/run_all.py`, `outputs/tables/attribution_live.csv`, `decisions/OPEN.md`.

## Reviewer reads

1. `instructions/10_section_10.status.md`
2. `review/section_10_page.png`
3. E1, E2, E6, E7 and E8 above
4. `volsurf/risk.py`
5. `volsurf/attribution.py`, `theta_value`
