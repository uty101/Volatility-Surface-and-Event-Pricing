"""BSM Greeks, their finite-difference check and book aggregation (PLAN 2.2).

Units follow Convention 4.10: vega per 1.00 of vol, theta = -dV/dT per year, rho per 1.00 of rate.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm

from volsurf.pricing import _is_call, bsm

GREEKS = ("delta", "gamma", "vega", "theta", "rho", "vanna", "volga")
BOOK_COLUMNS = ["underlying", "expiry", *GREEKS]
BOOK_TOTAL = "total"


def greeks(S, K, T, r, q, sigma, kind) -> dict[str, np.ndarray]:
    """Analytic BSM Greeks with continuous dividend yield q; broadcasts over every argument."""
    S, K, T, r, q, sigma = (np.asarray(x, dtype=float) for x in (S, K, T, r, q, sigma))
    call = _is_call(kind)
    sqrt_t = np.sqrt(T)
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * sqrt_t)
    d2 = d1 - sigma * sqrt_t
    eq, er = np.exp(-q * T), np.exp(-r * T)
    pdf = norm.pdf(d1)
    vega = S * eq * pdf * sqrt_t
    decay = -S * eq * pdf * sigma / (2.0 * sqrt_t)
    return {
        "delta": np.where(call, eq * norm.cdf(d1), -eq * norm.cdf(-d1)),
        "gamma": eq * pdf / (S * sigma * sqrt_t),
        "vega": vega,
        "theta": np.where(
            call,
            decay - r * K * er * norm.cdf(d2) + q * S * eq * norm.cdf(d1),
            decay + r * K * er * norm.cdf(-d2) - q * S * eq * norm.cdf(-d1),
        ),
        "rho": np.where(call, K * T * er * norm.cdf(d2), -K * T * er * norm.cdf(-d2)),
        "vanna": -eq * pdf * d2 / sigma,
        "volga": vega * d1 * d2 / sigma,
    }


def fd_greeks(S, K, T, r, q, sigma, kind, h: dict) -> dict[str, np.ndarray]:
    """Central differences of bsm. h holds the `[tolerances]` bumps fd_h_spot_rel (h_S = it x S), fd_h_vol,
    fd_h_t and fd_h_rate. Gamma and volga by second differences, vanna by the 4-point cross difference,
    theta = -dV/dT."""
    hs, hv, ht, hr = h["fd_h_spot_rel"] * np.asarray(S, dtype=float), h["fd_h_vol"], h["fd_h_t"], h["fd_h_rate"]

    def v(dS=0.0, dsig=0.0, dT=0.0, dr=0.0):
        return bsm(S + dS, K, T + dT, r + dr, q, sigma + dsig, kind)

    v0 = v()
    return {
        "delta": (v(dS=hs) - v(dS=-hs)) / (2 * hs),
        "gamma": (v(dS=hs) - 2 * v0 + v(dS=-hs)) / hs**2,
        "vega": (v(dsig=hv) - v(dsig=-hv)) / (2 * hv),
        "theta": -(v(dT=ht) - v(dT=-ht)) / (2 * ht),
        "rho": (v(dr=hr) - v(dr=-hr)) / (2 * hr),
        "vanna": (v(dS=hs, dsig=hv) - v(dS=hs, dsig=-hv) - v(dS=-hs, dsig=hv) + v(dS=-hs, dsig=-hv)) / (4 * hs * hv),
        "volga": (v(dsig=hv) - 2 * v0 + v(dsig=-hv)) / hv**2,
    }


def book_greeks(positions: pd.DataFrame) -> pd.DataFrame:
    """Instruction 02 step 2.2: positions (underlying, expiry, kind, strike, quantity, S, T, r, q, sigma) to
    1 row per (underlying, expiry) and 1 `total` row per underlying, each Greek x quantity x 100."""
    g = greeks(*(positions[c].to_numpy() for c in ["S", "strike", "T", "r", "q", "sigma", "kind"]))
    scale = positions["quantity"].to_numpy(dtype=float) * 100  # contract multiplier 100 (instruction 02, step 2.2)
    frame = pd.DataFrame({"underlying": positions["underlying"].to_numpy(),
                          "expiry": positions["expiry"].astype(str).to_numpy(),
                          **{name: g[name] * scale for name in GREEKS}})
    rows = []
    for underlying, block in frame.groupby("underlying", sort=True):
        rows.append(block.groupby("expiry", sort=True)[list(GREEKS)].sum().reset_index()
                    .assign(underlying=underlying))
        rows.append(block[list(GREEKS)].sum().to_frame().T.assign(underlying=underlying, expiry=BOOK_TOTAL))
    if not rows:
        return pd.DataFrame(columns=BOOK_COLUMNS)
    return pd.concat(rows, ignore_index=True)[BOOK_COLUMNS]
