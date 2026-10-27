# Data and history

1. Capture starts 2026-10-28, so every result built only on captured chains is a method demonstration with its N stated (Correction 1).
2. The volatility risk premium uses VIX against forward realised S&P 500 variance from 1990 and the Cboe PUT and BXM indices; captured chains give only a descriptive live delta-hedged straddle (Correction 2).
3. Long correlation history is Cboe COR3M from 2006-01-03 against forward realised correlation of the 9 original sector SPDRs, labelled a sector-level proxy; XLK implied correlation from captured chains is the live part (Correction 3). The VIX term structure uses VIX9D, VIX, VIX3M and VIX6M, not futures settlements (Correction 13).
4. FRED series are read from `fredgraph.csv`, and snapshot day t uses the latest observation dated t − 1 or earlier (Correction 15).
