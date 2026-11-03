"""P&L attribution and hedging frequency (PLAN 9.1 and 9.2, kickoff Section 5.10, instruction 09).

Each move of a straddle between 2 marks splits into Taylor terms with the Greeks at the first mark, a hedge leg, and a
residual defined as the difference, so the identity holds by construction. The Greeks come from the pricer and inputs
of the live marks (`volsurf.vrp.straddle_mark`): Black-76 on the day's F and D at the contract's SSVI vol.
"""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
import QuantLib as ql
from scipy.stats import norm

from volsurf.pricing import black76, bsm

COMPONENTS = ("delta", "gamma", "theta", "vega", "vanna", "volga", "hedge")
ATTRIBUTION_COLUMNS = ["open_day", "expiry", "strike", "day0", "day1", "dt", "dS", "dsigma", *COMPONENTS, "residual",
                       "option", "total", "explained_share"]
HEDGING_COLUMNS = ["model", "hedge_every_steps", "error_mean", "error_sd", "cost_mean", "cost_sd"]
MARKED = ("open", "closed")  # O-44 (a): the live_straddles.csv statuses that carry a value
SHORT = -1  # kickoff 5.9 and 5.10: the live and simulated straddles are short
TRADING_DAYS = 252  # Convention 4.14


def straddle_value(F: float, K: float, T: float, D: float, sigma: float) -> float:
    """Black-76 call + put; D |F - K| once T has run out."""
    if T <= 0:
        return float(D * abs(F - K))
    return float(black76(F, K, T, D, sigma, "C") + black76(F, K, T, D, sigma, "P"))


def straddle_greeks(S: float, F: float, K: float, T: float, D: float, sigma: float) -> dict:
    """Greeks of the long straddle (instruction 09 step 9.1), vega per 1.00 of vol (Convention 4.10). With V =
    D (F (2 N(d1) - 1) - K (2 N(d2) - 1)), the S derivatives are the F derivatives by the chain rule with F / S held
    fixed: dF / dS = F / S. Delta is the spot delta of O-44 (a). Theta is not here: `attribute_day` uses `theta_value`."""
    sd = sigma * np.sqrt(T)
    d1 = (np.log(F / K) + sd**2 / 2) / sd
    d2 = d1 - sd
    pdf = norm.pdf(d1)
    vega = 2 * D * F * pdf * np.sqrt(T)
    fs = F / S
    return {"delta": float(D * fs * (2 * norm.cdf(d1) - 1)), "gamma": float(fs**2 * 2 * D * pdf / (F * sd)),
            "vega": float(vega), "vanna": float(-fs * 2 * D * pdf * d2 / sigma),
            "volga": float(vega * d1 * d2 / sigma)}


def theta_value(S: float, F: float, K: float, T: float, D: float, sigma: float, dt: float) -> float:
    """Instruction 10 step 10.0: the straddle's value with S and sigma fixed and the clock moved on by dt. r and q are
    implied by the day's D and F / S, and T - dt takes both with it: D rolls to e^(-r (T - dt)) and F to
    S e^((r - q)(T - dt)). This is the time decay a desk reports. Shortening T alone would leave F and D where they
    were, so the roll of the carry would land in the residual, and near expiry that roll dominates the day's move."""
    r, carry = -np.log(D) / T, np.log(F / S) / T
    T1 = T - dt
    return straddle_value(S * np.exp(carry * T1), K, T1, np.exp(-r * T1), sigma)


def attribute_day(pos: pd.Series, t0: dict, t1: dict) -> dict:
    """Kickoff 5.10 for 1 straddle between 2 marks. `pos`: strike and side (-1 short). `t0`, `t1`: T, S, F, D, vol.

    total = side (V1 - V0) + hedge, and
    total = delta dS + 1/2 gamma dS^2 + theta dt + vega dsigma + vanna dS dsigma + 1/2 volga dsigma^2 + hedge + residual

    with every Greek at t0 and times the side, hedge = -side delta dS, and the residual the difference. dt = T0 - T1,
    which is t1 - t0 in years (Convention 4.1), as both T run to the same expiry. The theta term is `theta_value` - V0:
    S and vol stay at t0, while T, F and D all roll on by dt.

    dsigma is the change in the contract's SSVI vol: at the same strike, at T1 on t1 minus at T0 on t0. It is not a
    change at constant maturity, so the part of the move that comes from T shortening along the surface's term
    structure falls into dsigma, not into theta.

    explained_share = 1 - |residual| / |total|, blank if total is 0."""
    K, side = float(pos["strike"]), float(pos["side"])
    T0, S0, F0, D0, vol0 = (t0[c] for c in ("T", "S", "F", "D", "vol"))
    dt, dS, dsigma = T0 - t1["T"], t1["S"] - S0, t1["vol"] - vol0
    g = straddle_greeks(S0, F0, K, T0, D0, vol0)
    v0 = straddle_value(F0, K, T0, D0, vol0)
    v1 = straddle_value(t1["F"], K, t1["T"], t1["D"], t1["vol"])
    parts = {"delta": side * g["delta"] * dS, "gamma": side * g["gamma"] * dS**2 / 2,
             "theta": side * (theta_value(S0, F0, K, T0, D0, vol0, dt) - v0), "vega": side * g["vega"] * dsigma,
             "vanna": side * g["vanna"] * dS * dsigma, "volga": side * g["volga"] * dsigma**2 / 2,
             "hedge": -side * g["delta"] * dS}
    option = side * (v1 - v0)
    total = option + parts["hedge"]
    residual = total - sum(parts[c] for c in COMPONENTS)
    share = 1 - abs(residual) / abs(total) if total != 0 else np.nan
    return {"dt": dt, "dS": dS, "dsigma": dsigma, **parts, "residual": residual, "option": option, "total": total,
            "explained_share": share}


def bs_path_attribution(cfg) -> pd.DataFrame:
    """Instruction 09 step 9.1 MEASURE: 1 synthetic Black-Scholes path from `[sim] gbm` at daily steps, 1 / 252 years
    (O-18), over `[sim] days` days, seed `[run] seed`. A short straddle at K = s0 is attributed each day with F =
    S e^(r T), D = e^(-r T) and sigma fixed, so dsigma = 0. 1 row per day."""
    g, n = cfg.sim.gbm, cfg.sim.days
    dt = 1 / TRADING_DAYS
    z = np.random.default_rng(cfg.run.seed).standard_normal(n)
    logs = np.cumsum((g.mu - g.sigma**2 / 2) * dt + g.sigma * np.sqrt(dt) * z)
    S = g.s0 * np.exp(np.concatenate([[0.0], logs]))
    T = (n - np.arange(n + 1)) * dt
    marks = [{"T": T[i], "S": S[i], "F": S[i] * np.exp(g.r * T[i]), "D": np.exp(-g.r * T[i]), "vol": g.sigma}
             for i in range(n + 1)]
    pos = pd.Series({"strike": g.s0, "side": SHORT})
    return pd.DataFrame([{"day": i + 1, "S": S[i + 1], **attribute_day(pos, marks[i], marks[i + 1])}
                         for i in range(n)])


def attribute_live(straddles: pd.DataFrame) -> pd.DataFrame:
    """`attribute_day` on every mark-to-mark move of live_straddles.csv (O-44 (a)): for each position, each pair of
    consecutive marked rows, 1 row per move (ATTRIBUTION_COLUMNS). A position with 1 mark has no move."""
    rows = []
    marked = straddles[straddles["status"].isin(MARKED)]
    for (open_day, expiry, strike), block in marked.groupby(["open_day", "expiry", "strike"], sort=True):
        marks = block.sort_values("mark_day").to_dict("records")
        pos = pd.Series({"strike": strike, "side": SHORT})
        for m0, m1 in itertools.pairwise(marks):
            rows.append({"open_day": open_day, "expiry": expiry, "strike": strike, "day0": m0["mark_day"],
                         "day1": m1["mark_day"], **attribute_day(pos, m0, m1)})
    return pd.DataFrame(rows, columns=ATTRIBUTION_COLUMNS)


def straddle_delta(S, K, tau, r, sigma):
    """BSM delta of a call + put with no dividends, 2 N(d1) - 1. With sigma = 0, the path's variance truncated at 0
    under Heston, d1 is +-inf and this is the limit, the sign of the forward's moneyness."""
    with np.errstate(divide="ignore"):
        d1 = (np.log(S / K) + (r + sigma**2 / 2) * tau) / (sigma * np.sqrt(tau))
    return 2 * norm.cdf(d1) - 1


def heston_straddle_price(h, K: float, days: int) -> float:
    """O-18: QuantLib `AnalyticHestonEngine`, call + put at t = 0 under `[sim] heston`. Business252 on a null calendar
    makes `days` calendar days exactly T = days / 252, which Actual/365 dates cannot."""
    today = ql.Date(28, 10, 2026)  # any date: only the year fraction to maturity enters
    ql.Settings.instance().evaluationDate = today
    dc = ql.Business252(ql.NullCalendar())
    rate, carry = (ql.YieldTermStructureHandle(ql.FlatForward(today, x, dc)) for x in (h.r, 0.0))
    process = ql.HestonProcess(rate, carry, ql.QuoteHandle(ql.SimpleQuote(h.s0)), h.v0, h.kappa, h.theta, h.xi, h.rho)
    engine = ql.AnalyticHestonEngine(ql.HestonModel(process))
    value = 0.0
    for kind in (ql.Option.Call, ql.Option.Put):
        option = ql.VanillaOption(ql.PlainVanillaPayoff(kind, K), ql.EuropeanExercise(today + days))
        option.setPricingEngine(engine)
        value += option.NPV()
    return value


def gbm_paths(g, n: int, dt: float, paths: int, rng) -> np.ndarray:
    """(n + 1, paths) spot under `[sim] gbm` at drift mu, exact log steps."""
    z = rng.standard_normal((n, paths))
    logs = np.cumsum((g.mu - g.sigma**2 / 2) * dt + g.sigma * np.sqrt(dt) * z, axis=0)
    return g.s0 * np.exp(np.vstack([np.zeros(paths), logs]))


def heston_paths(h, n: int, dt: float, paths: int, rng) -> tuple[np.ndarray, np.ndarray]:
    """(n + 1, paths) spot and sqrt(v+) under `[sim] heston` by full-truncation Euler (O-18), with v+ = max(v, 0) in
    the drift and the diffusion of both equations, ln S stepped at drift r (O-46 (a)). Each step draws 2 rows of
    normals: the variance shock, then the independent part of the spot shock."""
    S, vol = np.empty((n + 1, paths)), np.empty((n + 1, paths))
    S[0] = h.s0
    v = np.full(paths, float(h.v0))
    vol[0] = np.sqrt(v)
    for i in range(n):
        zv, ze = rng.standard_normal((2, paths))
        zs = h.rho * zv + np.sqrt(1 - h.rho**2) * ze
        vp = np.maximum(v, 0.0)
        S[i + 1] = S[i] * np.exp((h.r - vp / 2) * dt + np.sqrt(vp * dt) * zs)
        v = v + h.kappa * (h.theta - vp) * dt + h.xi * np.sqrt(vp * dt) * zv
        vol[i + 1] = np.sqrt(np.maximum(v, 0.0))
    return S, vol


def hedge_run(S: np.ndarray, vol: np.ndarray, K: float, T: float, r: float, premium: float, every: int,
              cost_bp: float) -> tuple[np.ndarray, np.ndarray]:
    """Instruction 09 step 9.2: a straddle sold for `premium` and hedged at steps 0, `every`, 2 `every`, ... before
    expiry, at the BSM delta at `vol`, which has 1 row per step. Cash accrues at r. Returns per path the hedging error
    (cash + hedge - payoff at expiry, before costs, O-18) and the cost (`cost_bp` x |shares traded| x S, summed)."""
    n = S.shape[0] - 1
    dt = T / n
    grow = np.exp(r * dt)
    cash, shares, cost = np.full(S.shape[1], premium), np.zeros(S.shape[1]), np.zeros(S.shape[1])
    for i in range(n):
        if i % every == 0:
            target = straddle_delta(S[i], K, T - i * dt, r, vol[i])
            traded = target - shares
            cash -= traded * S[i]
            cost += cost_bp / 10_000 * np.abs(traded) * S[i]
            shares = target
        cash *= grow
    return cash + shares * S[n] - np.abs(S[n] - K), cost


def simulate_hedging(model: str, cfg) -> pd.DataFrame:
    """Kickoff 5.10 and O-18, instruction 09 step 9.2: a short ATM straddle (K = s0) over T = `[sim] days` / 252 at
    `steps_per_day` steps a day, sold at its model price (BSM at sigma for `gbm`, `heston_straddle_price` for
    `heston`) and hedged at BSM delta at sigma or at sqrt(v_t). Every frequency in `hedge_every_steps` runs on the
    same paths, drawn from `default_rng([run] seed)`. 1 row per frequency (HEDGING_COLUMNS)."""
    s = cfg.sim
    n, dt, T = s.days * s.steps_per_day, 1 / (TRADING_DAYS * s.steps_per_day), s.days / TRADING_DAYS
    rng = np.random.default_rng(cfg.run.seed)
    if model == "gbm":
        p = s.gbm
        S = gbm_paths(p, n, dt, s.paths, rng)
        vol = np.full(n + 1, float(p.sigma))
        premium = float(bsm(p.s0, p.s0, T, p.r, 0.0, p.sigma, "C") + bsm(p.s0, p.s0, T, p.r, 0.0, p.sigma, "P"))
    elif model == "heston":
        p = s.heston
        S, vol = heston_paths(p, n, dt, s.paths, rng)
        premium = heston_straddle_price(p, p.s0, s.days)
    else:
        raise ValueError(f"unknown model {model}")
    rows = []
    for every in s.hedge_every_steps:
        error, cost = hedge_run(S, vol, p.s0, T, p.r, premium, every, s.hedge_cost_bp)
        rows.append({"model": model, "hedge_every_steps": every, "error_mean": error.mean(),
                     "error_sd": error.std(ddof=1), "cost_mean": cost.mean(), "cost_sd": cost.std(ddof=1)})
    return pd.DataFrame(rows, columns=HEDGING_COLUMNS)
