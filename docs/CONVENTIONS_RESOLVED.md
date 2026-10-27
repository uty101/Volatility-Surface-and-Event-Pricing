# Conventions resolved

Items 1 to 15 are Section 4 of `instructions/00_kickoff.md`, numbered as there. Items 16 to 19 are added by session 0.

1. **Time to expiry.** T = (expiry at 16:00 New York − snapshot timestamp) / (365 × 86400 s), ACT/365 with intraday precision, using the snapshot time of that underlying's chain.
2. **Trading-day counts** (event method only): n(t, E) = number of XNYS sessions s with t < s ≤ E.
3. **Quote mid** = (bid + ask) / 2. Prices are per share (Yahoo's convention), contract multiplier 100 recorded but unused.
4. **Cleaning rules, applied in this order, each logged with rows dropped:** (a) bid ≤ 0; (b) ask ≤ bid; (c) mid < `min_mid`; (d) (ask − bid) / mid > `max_rel_spread`; (e) mid outside the no-arbitrage bounds of Section 5.3. Flags (kept, counted): `stale` if `lastTradeDate` is more than `stale_sessions` sessions before the snapshot or missing; `after_close` if captured after 16:00 New York.
5. **OTM selection for the surface:** calls with K ≥ F, puts with K < F.
6. **Rates.** CMT yields y (percent, bond-equivalent) from DGS1MO, DGS3MO, DGS6MO, DGS1 at tenors 1/12, 0.25, 0.5, 1 year, converted to continuous r = 2 ln(1 + y/200). Linear in T between tenors, flat beyond. Observation date ≤ t − 1 (Correction 15).
7. **Dividend yield (American underlyings).** q = (sum of cash dividends with ex-date in (t − 365 days, t]) / S_t, continuous. 0 if none.
8. **Forward.** `^SPX`: from parity regression (Section 5.2). Others: F = S exp((r − q)T).
9. **Log-moneyness** k = ln(K / F). Total implied variance w = σ² T.
10. **Units.** Vega per 1.00 of vol in code; tables report vega per vol point (÷ 100) and theta per calendar day (÷ 365). Rates and vols are decimals in code, percent only in tables.
11. **Earnings timing.** From the yfinance timestamp in New York time: before 09:30 → BMO; at or after 16:00 → AMC; 00:00 exactly or anything else → `unknown` (excluded until an override sets it). Event window: BMO on date D runs close(prev session of D) to close(D); AMC on D runs close(D) to close(next session). The **pre-event snapshot** is the last snapshot on a session strictly before the window's end close and no later than the window's start session. Realised move = ln(close_end / close_start), using unadjusted close.
12. **Constant-maturity vol.** σ_cm(τ) = √(w(τ)/τ), with w linear in T between the 2 bracketing accepted expiries' ATM total variance θ; no extrapolation (blank if τ is outside the accepted range).
13. **Calendar months** for any monthly aggregation use calendar-month periods, never `DateOffset`.
14. **Annualisation.** 252 trading days. Daily variance × 252; monthly return series × 12 for means, √12 for vol.
15. **Failed fits and failed gates** keep their rows with a `status` column and blank results, never a fallback number.
16. **SPXW only.** For `^SPX` keep only contracts whose `contractSymbol` starts with `SPXW` (PM-settled); AM-settled `SPX` contracts are dropped and counted in the log (Section 3.1).
17. **Parity forward on `^SPX` only.** The forward and discount factor are backed out by put-call parity only for `^SPX` (Section 5.2, Correction 4).
18. **American IV on the CRR tree.** Every underlying other than `^SPX` uses Brent on the CRR American price at `n_prod` steps, on S, r and q (Section 5.3, Correction 4).
19. **Tail probabilities only inside the quoted range.** Beyond the last quoted strike the density is the SVI wing; probabilities there are labelled `extrapolated` (Section 5.6, Correction 11).
