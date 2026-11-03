"""P&L attribution and hedging frequency (PLAN 9.1 and 9.2, kickoff Section 5.10, instruction 09).

Each move of a straddle between 2 marks splits into Taylor terms with the Greeks at the first mark, a hedge leg, and a
residual defined as the difference, so the identity holds by construction. The Greeks come from the pricer and inputs
of the live marks (`volsurf.vrp.straddle_mark`): Black-76 on the day's F and D at the contract's SSVI vol.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm

from volsurf.pricing import black76

COMPONENTS = ("delta", "gamma", "theta", "vega", "vanna", "volga", "hedge")
TRADING_DAYS = 252  # Convention 4.14


def straddle_value(F: float, K: float, T: float, D: float, sigma: float) -> float:
    """Black-76 call + put; D |F - K| once T has run out."""
    if T <= 0:
        return float(D * abs(F - K))
    return float(black76(F, K, T, D, sigma, "C") + black76(F, K, T, D, sigma, "P"))


def straddle_greeks(S: float, F: float, K: float, T: float, D: float, sigma: float) -> dict:
    """Greeks of the long straddle (instruction 09 step 9.1), vega per 1.00 of vol (Convention 4.10). With V =
    D (F (2 N(d1) - 1) - K (2 N(d2) - 1)), the S derivatives are the F derivatives by the chain rule with F / S held
    fixed: dF / dS = F / S. Delta is the spot delta of O-44 (a). Theta is not here: `attribute_day` reprices."""
    sd = sigma * np.sqrt(T)
    d1 = (np.log(F / K) + sd**2 / 2) / sd
    d2 = d1 - sd
    pdf = norm.pdf(d1)
    vega = 2 * D * F * pdf * np.sqrt(T)
    fs = F / S
    return {"delta": float(D * fs * (2 * norm.cdf(d1) - 1)), "gamma": float(fs**2 * 2 * D * pdf / (F * sd)),
            "vega": float(vega), "vanna": float(-fs * 2 * D * pdf * d2 / sigma),
            "volga": float(vega * d1 * d2 / sigma)}


def attribute_day(pos: pd.Series, t0: dict, t1: dict) -> dict:
    """Kickoff 5.10 for 1 straddle between 2 marks. `pos`: strike and side (-1 short). `t0`, `t1`: T, S, F, D, vol.

    total = side (V1 - V0) + hedge, and
    total = delta dS + 1/2 gamma dS^2 + theta dt + vega dsigma + vanna dS dsigma + 1/2 volga dsigma^2 + hedge + residual

    with every Greek at t0 and times the side, hedge = -side delta dS, and the residual the difference. dt = T0 - T1,
    which is t1 - t0 in years (Convention 4.1), as both T run to the same expiry. The theta term is V(T0 - dt) - V(T0)
    with F, D and vol held at t0.

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
             "theta": side * (straddle_value(F0, K, T0 - dt, D0, vol0) - v0), "vega": side * g["vega"] * dsigma,
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
    pos = pd.Series({"strike": g.s0, "side": -1})
    return pd.DataFrame([{"day": i + 1, "S": S[i + 1], **attribute_day(pos, marks[i], marks[i + 1])}
                         for i in range(n)])
