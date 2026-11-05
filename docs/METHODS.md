# Methods

The conventions and methods behind every result, as built. This is kickoff Sections 4 and 5 with the Section 2 corrections and every later change applied, so where the two differ this file describes the code. Parameters in backticks are `config.toml` keys. Decisions and their reasons are in `decisions/`.

## Data

**History is the binding constraint.** Free sources only give today's option chains, so capture started on 2026-10-28 and the live window is weeks. Every result built only on captured chains is a method demonstration with its N stated. Results that need years use published Cboe and FRED series.

**Capture.** A GitHub Actions job starts well before the window, waits until 15:30 New York and hands over to a fresh run of itself when the wait is longer than a job may last. Quotes after the close often show a zero bid, so the snapshot runs inside the session, with a window of 15:25 to 16:30; rows captured after 16:00 are flagged. Files are uploaded as assets of the `snapshots` release, never committed. A day is a snapshot day if a chains asset exists, and each ticker is used only if its log status is `ok`. 2026-11-02 was lost when GitHub started every scheduled run hours late.

**Universe.** `^SPX` (European, cash settled, SPXW PM-settled contracts only), 5 ETFs, the 15 largest XLK holdings and 16 other single names. Expiries run out to 400 calendar days.

**Sources.** Chains, spot and earnings dates from yfinance. Daily prices from yfinance, ending at the last completed session. VIX family, PUT, BXM and COR3M from Cboe. Treasury yields from FRED `fredgraph.csv`. XLK holdings from SSGA.

## Conventions

1. **Time to expiry.** T = (expiry at 16:00 New York − snapshot time) / (365 × 86,400 s), ACT/365 with intraday precision.
2. **Trading-day counts** (event method only). n(t, E) is the number of XNYS sessions s with t < s ≤ E.
3. **Quote mid.** (bid + ask) / 2, per share. The multiplier of 100 is applied only in dollar risk.
4. **Cleaning**, in this order, each logged with rows dropped: (a) bid ≤ 0; (b) ask ≤ bid; (c) mid < `min_mid`; (d) (ask − bid) / mid > `max_rel_spread`; (e) mid outside the no-arbitrage bounds. Staleness is a flag, not a drop, because far OTM options often have no recent trade but a live quote, and they are the wings SVI needs. `after_close` is also a flag.
5. **OTM selection.** Calls with K ≥ F, puts with K < F.
6. **Rates.** CMT yields y at 1/12, 0.25, 0.5 and 1 year become r = 2 ln(1 + y/200), linear in T between tenors and flat beyond. Each tenor uses its latest valid observation dated t − 1 or earlier, so nothing is used before it was published.
7. **Dividend yield.** q = (cash dividends with ex-date in (t − 365 days, t]) / S, continuous.
8. **Forward.** `^SPX` from parity. Others F = S exp((r − q)T).
9. **Log-moneyness.** k = ln(K / F). Total variance w = σ² T.
10. **Units.** Vega per 1.00 of vol in code; tables give vega per vol point and theta per calendar day. Rates and vols are decimals in code.
11. **Earnings timing.** From the New York timestamp: before 09:30 is BMO, at or after 16:00 is AMC, anything else, and Yahoo's 15:00 placeholder, is `unknown` until `data/manual/earnings_overrides.csv` sets it. BMO on D runs close(previous session) to close(D); AMC on D runs close(D) to close(next session). The pre-event snapshot is the last snapshot on a session strictly before the window's end close and no later than its start session; `pre_snap_age` counts the sessions between them. Realised move = ln(close_end / close_start) on unadjusted closes.
12. **Constant-maturity vol.** σ(τ) = √(w(τ)/τ), w linear in T between the 2 bracketing accepted expiries, blank outside their range.
13. **Calendar months** are calendar periods.
14. **Annualisation.** 252 trading days.
15. **Failed fits and gates** keep their rows with a `status` and blank results, never a fallback number.

## Pricing

- **BSM.** d1 = [ln(S/K) + (r − q + σ²/2)T] / (σ√T), d2 = d1 − σ√T.
- **Black-76.** C = D[F N(d1) − K N(d2)], d1 = [ln(F/K) + σ²T/2] / (σ√T).
- **CRR.** Δt = T/N, u = e^(σ√Δt), d = 1/u, p = (e^((r−q)Δt) − d)/(u − d), early exercise at every node for American. `n_validate` = 2000, `n_prod` = 200.
- **Early exercise premium.** American IV and European IV, both on the CRR tree at `n_prod` so discretisation error cancels, on the same mid. Rows with less than `min_vega_pt` of vega per vol point are blank, because a vol number there means nothing.
- QuantLib's `"crr"` engine uses a drift-approximated up probability, so it does not match the textbook tree exactly. At 2000 steps the bound is 1e-4 × S.

## Forward from parity, `^SPX` only

Put-call parity is an inequality for American options, so only `^SPX` backs out a forward. D comes from the Treasury curve, D = exp(−r(T) T). An OLS slope over the strikes nearest spot is badly identified, so only F is backed out, as Cboe does for VIX. For each of the `parity_n_strikes` strikes nearest S with clean call and put mids, F_i = K_i + (C_i − P_i) / D. F is the median, and mad_bp = 10,000 × median(|F_i − F|) / F. The gate needs at least `parity_min_pairs` pairs and mad_bp ≤ `parity_mad_max_bp`, else the expiry gets `parity_fail` for the day.

## Implied volatility

- **Bounds first.** European: max(0, D(F − K)) < C < D F and max(0, D(K − F)) < P < D K. American: at least intrinsic, below S (call) or K (put). Outside gives `bounds` and no vol.
- **European.** Brenner-Subrahmanyam start, Newton on vega, Brent on [`iv_lo`, `iv_hi`] if vega falls below `min_vega` × F × D or Newton leaves the range.
- **American.** Bisection on the CRR tree at `n_prod`, batched across options, to `am_vol_tol`; this is what "de-Americanising" means here. A row with no root gets `no_root`.
- **Flat prices.** After any solve, sens = min(|P(σ̂ + 0.01) − P(σ̂)|, |P(σ̂) − P(σ̂ − 0.01)|). Below `flat_tol` the row gets `flat` and no vol, because the price holds no vol information.
- `^SPX` uses European on the parity forward. Everything else uses American on S, r, q. Only OTM quotes are solved.

## SVI per expiry

- **Raw SVI.** w(k) = a + b[ρ(k − m) + √((k − m)² + s²)].
- **Fit.** Minimise Σ (√(w(k_i)/T) − σ_i)² over OTM quotes, with b ≥ 0, |ρ| ≤ 0.999, s ≥ `s_min`, a + b s √(1 − ρ²) ≥ 0 and b(1 + |ρ|) ≤ `wing_max` = 1.98. Roger Lee's moment bound caps the wing slope at 2, and at 1.98 g stays above 0 in the limit and the mean equals F. SLSQP from each of the `starts`, lowest objective kept. Fewer than `min_quotes` quotes gives `too_few`.
- **Butterfly.** g(k) = (1 − k w′/(2w))² − (w′²/4)(1/w + 1/4) + w″/2. Checked on a sinh grid k = m + s·sinh(u) over [−`k_check`, `k_check`], dense where the curvature is. Acceptance needs min g ≥ −1e-10, w ≥ 1e-12 and every bound met, on the 200,001-point grid the density integrates on.
- **Refit.** A first fit that fails is refitted with g ≥ 0 as a hard SLSQP constraint on 801 sinh points. A refit that meets it but fails acceptance adds the 10 lowest points to the constraint, at most 3 more times. Slices still failing are retried from their 3 nearest accepted neighbours, with a and b scaled by T / T_neighbour. A refit may stop at the iteration limit if the result passes every check. None passing gives `butterfly_fail`.
- **Quality.** RMSE above `max_rmse_volpts` gives `poor_fit`. The short `^SPX` expiries can be too sharp for 5 parameters, and that is reported, not worked around.
- **Calendar.** Between consecutive accepted expiries, w_{i+1}(k) ≥ w_i(k) − 1e-10 on the overlap of their quoted k ranges. Violations are recorded per pair, with no refit.

## SSVI across expiries

θ_i is the accepted slice's w_i(0), made non-decreasing by cumulative maximum. w(k, θ) = (θ/2)[1 + ρ φ k + √((φ k + ρ)² + 1 − ρ²)], φ(θ) = η / (θ^γ (1 + θ)^(1 − γ)). ρ, η, γ are fitted on implied vol with |ρ| ≤ 0.999, η > 0, 0 < γ ≤ 0.5 and η(1 + |ρ|) ≤ 2 (the Gatheral-Jacquier condition). With θ non-decreasing it is free of calendar arbitrage.

**Daily metrics come from the slices, not SSVI**, because 1 ρ cannot fit the S&P skew. For a target τ, take the 2 accepted slices that bracket it (else `no_bracket`). Find each slice's 25-delta strikes from the Black forward delta inside its quoted range (else `delta_outside_quotes`). Interpolate total variance linearly in T at matched delta, then σ = √(w/τ). RR = σ_25c − σ_25p, BF = (σ_25c + σ_25p)/2 − σ_ATM, term slope = σ_ATM(90d) − σ_ATM(30d). `ssvi_rr25_30` sits beside `rr25_30` as a check.

## Risk-neutral density

- d− = −k/√w − √w/2, p_k(k) = g(k) / √(2π w) × exp(−d−²/2), q(K) = p_k(ln(K/F)) / K, computed analytically from the slice (Gatheral).
- The integral and mean are trapezoid sums on the sinh grid, with the closed-form mass beyond ±`k_check` added and reported as `tail_mass`. A slice that misses `int_tol` gets `density_fail`. q ≥ 0 holds up to the butterfly tolerance.
- **Cross-check.** e^(rT) ∂²C/∂K² by central differences of Black prices, step F × min(`bl_dk`, s/10), bounded by 5e-3 × the slice's peak density on the quoted range. A slice that misses gets `fd_gap`.
- **Kinks.** A slice with s at `s_min` has a corner, not information, and gets `kink`. `kink`, `fd_gap` and `density_fail` slices stay out of the tail table, the PIT and the figure.
- **Tails.** P(S_T > x), P(S_T < x) for moves in `moves`, and P(|ln(S_T/F)| > m), flagged `extrapolated` outside the quoted strikes, because the density there is the SVI wing, not market information.
- **PIT.** u = P_Q(S_T ≤ S_realised) for every captured expiry that has expired. It is descriptive: uniform only if risk-neutral equals physical, which is not expected.

## Event pricing

With E1 < E2 the first 2 accepted expiries ending at or after the window's end, and θ1, θ2 their SVI w(0):

- **Straddle move.** M_s = (C_K + P_K) / S at the strike K nearest F on E1, on mids.
- **Term structure move.** v_d = (θ2 − θ1)/(n2 − n1), v_e = θ1 − v_d(n1 − 1). If v_e ≤ 0 the status is `no_event_premium`. Else M_t = √(2/π) × √v_e, the expected absolute log move under a normal jump.
- **Realised.** R = |ln(close_end / close_start)|, with R/M_t and ln(R/M_t) per event.
- **Summary**, only with N ≥ `min_n`: mean of ln(R/M_t) with an iid bootstrap 90% interval, and the share with R > M_t with a binomial 90% interval, by group only at `min_group_n` events. Below `min_n` the table is descriptive.
- **Macro events.** `^SPX`, dates in `data/manual/macro_events.csv`, window close(previous session) to close(event date).

## Correlation

- **Live.** ρ = (σ_I² − Σ w_i² σ_i²) / (Σ_{i≠j} w_i w_j σ_i σ_j), σ the 30-day ATM vol, I = XLK. Weights are the SSGA holdings renormalised over names with a vol that day, and the covered weight is reported beside every value. The realised side is `pending` until 21 sessions exist: √(252/21 × Σ r²) on adjusted closes, and demeaned Pearson for the average pairwise correlation.
- **Long history.** COR3M / 100 on day t against the realised average pairwise correlation of the 9 sector SPDRs' daily log returns over sessions t+1 to t+63. OLS with Newey-West errors (`nw_maxlags`). COR3M covers the 50 largest S&P 500 stocks and sector ETFs correlate with each other more than single stocks do, so the mean gap is the proxy, not a correlation risk premium. The slope and R² are the usable result.
- **RV screens.** A z-score of 30-day ATM vol against the name's own history once it has `rv_min_days` prior days, and the name's vol minus its group median.

## Volatility risk premium

- RV_t,21 = (252/21) Σ r²_{t+j}, r the daily log return of `^GSPC`. IV_t = (VIX_t/100)². VRP_t = IV_t − RV_t,21 (ex post).
- **GARCH.** `arch` GARCH(1,1), constant mean, normal errors, on returns × 100 up to each month's last session, expanding from `garch_min_obs` observations; variance summed over horizons 1 to 21, × 252/21 / 10,000. Signal s_m = IV − forecast (ex ante).
- **Strategies.** Monthly, month end to month end, on a common window from `strategy_start`, because Cboe PUT is daily only from 2007: PUT, BXM, `^SP500TR`, and the timed PUT, which holds PUT in month m+1 if s_m > 0, else T-bills, paying `switch_cost_bp` per change, the first included. The T-bill return for month m+1 is DTB3 on the last session of month m / 1200. BXM is also shown alone from `bxm_start`. Cboe indices carry no trading costs of their own.
- **Specification family.** 5 timed PUTs, a closed family: `timed_put_main` (the signal above), `iv_minus_rv21` and `iv_minus_rv63` (IV minus (252/n) Σ r² over the n sessions ending at m), `iv_minus_ewma` (IV minus 252 × the EWMA of r², α = 0.06, from 1990-01-02) and `garch_above_median` (the main signal minus its expanding median over month ends strictly before m). Each holds PUT in month m+1 if its signal is above 0, with the same switch cost, T-bills and 237 month window. All 5 are in `spec_log.csv`.
- **Deflated Sharpe.** Bailey and López de Prado, with N the rows in `spec_log.csv`, the variance of the family's monthly Sharpe ratios, and the skew and non-excess kurtosis of the series tested. It is reported twice in `spec_family.csv`: on the timed PUT's excess returns over T-bills, and on the monthly series timed minus PUT, whose family is the same 5 specifications' Sharpes of that series. The second answers whether timing improves on selling puts; its probabilistic Sharpe against 0 sits beside it. Fewer than 2 rows gives `too_few_trials` and a blank.
- **Live straddles.** Each snapshot day, a short ATM `^SPX` straddle nearest 30 days, marked off SSVI, delta hedged at each snapshot. Descriptive, no statistics.

## P&L attribution

- Per position between snapshots: ΔV = Δ dS + ½ Γ dS² + Θ dt + ν dσ + vanna dS dσ + ½ volga dσ² + residual, Greeks at t. The hedge leg adds −Δ_t dS. The residual is the difference, so the identity is exact.
- Θ is the value change over dt with S and σ fixed and the clock moved on: T − dt, D and F both rolled. This is the time decay a desk reports.
- dσ is the change in the contract's SSVI vol at the same strike, so the move from the shorter T falls into dσ.
- Explained share = 1 − |residual| / |total|, on the delta-hedged position.
- **Hedging study.** T = 21/252, 13 steps a day, a short ATM straddle, hedges every 1, 13 and 65 steps, cost `hedge_cost_bp` of traded notional. GBM hedges at BSM delta at σ. Heston uses full-truncation Euler, sells at QuantLib's analytic Heston price, and hedges at BSM delta at √v_t. Spot drifts at μ = 0 under GBM and at r under Heston, so the 2 means are not comparable. Error = cash + hedge − payoff at expiry.

## Risk report

- **Book.** `[book]`, on the last captured day. Each position takes the expiry nearest its target days, then the strike nearest its target delta, among the IV table's solved contracts.
- **Vol.** Each contract's own expiry's accepted SVI slice at its strike. SSVI is the fallback only when that expiry has no accepted slice, shown in `vol_source`.
- **Revaluation.** Black-76 on the day's parity F and D for `^SPX`, CRR American at `n_prod` for the others. Spot shocks of −10% to +10% in steps of 2.5%, parallel vol shocks of −5 to +5 points in steps of 2.5, full revaluation, sticky strike: a spot shock moves S and F but not the vol, and a vol shock adds its points, floored at `iv_lo`.
- **Limits**, per underlying on the net: dollar delta Δ S × 100 × contracts × side, dollar gamma Γ S² × 0.01 × 100 × contracts × side, vega per vol point. Tree delta and gamma come from the nodes of steps 1 and 2, because the tree's value is piecewise linear in S.
- **PDF.** reportlab, A4, Helvetica, `invariant=1`, 1 page, byte-identical between builds.
