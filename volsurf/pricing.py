"""BSM, Black-76, the CRR tree and the early exercise premium (PLAN 2.1, kickoff Section 5.1)."""

from __future__ import annotations

import numpy as np
from scipy.stats import norm


def _is_call(kind) -> np.ndarray:
    """True where kind is 'C', False where 'P' (CHAINS convention); anything else raises."""
    k = np.asarray(kind)
    bad = ~np.isin(k, ["C", "P"])
    if bad.any():
        raise ValueError(f"kind must be 'C' or 'P', got {sorted(set(np.atleast_1d(k[bad]).tolist()))}")
    return k == "C"


def bsm(S, K, T, r, q, sigma, kind) -> np.ndarray:
    """Section 5.1 Black-Scholes-Merton with continuous dividend yield q; broadcasts over every argument."""
    S, K, T, r, q, sigma = (np.asarray(x, dtype=float) for x in (S, K, T, r, q, sigma))
    sd = sigma * np.sqrt(T)
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / sd
    d2 = d1 - sd
    fs, dk = S * np.exp(-q * T), K * np.exp(-r * T)
    call = fs * norm.cdf(d1) - dk * norm.cdf(d2)
    put = dk * norm.cdf(-d2) - fs * norm.cdf(-d1)
    return np.where(_is_call(kind), call, put)


def black76(F, K, T, D, sigma, kind) -> np.ndarray:
    """Section 5.1 Black-76 on forward F with discount factor D; broadcasts over every argument."""
    F, K, T, D, sigma = (np.asarray(x, dtype=float) for x in (F, K, T, D, sigma))
    sd = sigma * np.sqrt(T)
    d1 = (np.log(F / K) + 0.5 * sigma**2 * T) / sd
    d2 = d1 - sd
    call = D * (F * norm.cdf(d1) - K * norm.cdf(d2))
    put = D * (K * norm.cdf(-d2) - F * norm.cdf(-d1))
    return np.where(_is_call(kind), call, put)


def crr(S, K, T, r, q, sigma, kind, n, american) -> float:
    """Section 5.1 CRR tree with n steps: u = e^(sigma sqrt(dt)), d = 1/u, p = (e^((r-q)dt) - d)/(u - d).

    Backward induction is vectorised over the nodes of each step; American adds max(continuation,
    intrinsic) at every node. Raises ValueError if p is outside (0, 1).
    """
    is_call = bool(_is_call(kind))
    dt = T / n
    sdt = sigma * np.sqrt(dt)
    u = np.exp(sdt)
    d = 1.0 / u
    p = (np.exp((r - q) * dt) - d) / (u - d)
    if not 0.0 < p < 1.0:
        raise ValueError(f"CRR up probability p = {p} is outside (0, 1) (sigma={sigma}, r={r}, q={q}, n={n})")
    disc = np.exp(-r * dt)
    pu, pd_ = disc * p, disc * (1.0 - p)

    def intrinsic(spot: np.ndarray) -> np.ndarray:
        return np.maximum(spot - K, 0.0) if is_call else np.maximum(K - spot, 0.0)

    # node j of step i has j up moves: S u^j d^(i - j) = S e^((2j - i) sigma sqrt(dt)), which is
    # node j of step i + 1 times u
    spot = S * np.exp((2 * np.arange(n + 1) - n) * sdt)
    v = intrinsic(spot)
    for _ in range(n):
        v = pu * v[1:] + pd_ * v[:-1]
        if american:
            spot = spot[:-1] * u
            v = np.maximum(v, intrinsic(spot))
    return float(v[0])


def early_exercise_premium(S, K, T, r, q, sigma, kind, n) -> float:
    """Section 5.1: CRR American minus CRR European at the same n."""
    return crr(S, K, T, r, q, sigma, kind, n, True) - crr(S, K, T, r, q, sigma, kind, n, False)
