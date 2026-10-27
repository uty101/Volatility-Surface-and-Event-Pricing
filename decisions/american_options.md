# American options

1. Put-call parity is an equality only for European options, so the forward is backed out by parity only for `^SPX` (SPXW, PM-settled) (Correction 4).
2. For SPY, QQQ, sector ETFs and single stocks, F = S exp((r − q)T) with r from Treasury yields and q from trailing dividends, and implied vols are American vols solved on the CRR tree (Correction 4).
3. QuantLib's `"crr"` engine uses a drift-approximated up probability, so tolerances against it are set from the reviewer's measurements: 6.8e-5 × S at 2000 steps against QuantLib, 3.9e-5 × S for the European tree against analytic (Correction 16).
