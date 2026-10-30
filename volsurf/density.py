"""Risk-neutral density from an SVI slice (PLAN 5.1 and 5.2, kickoff Section 5.6, instruction 05 part C).

Tail probabilities and PIT values use the SVI slice's closed-form distribution function (O-35 (a)):
P(S_T > K) = N(d-) - phi(d-) w'(k) / (2 sqrt(w(k))), which is -(1/D) dC/dK of the Black price on the slice, so it is
the exact integral of `svi_density` from K to infinity. Tail rows are flagged `extrapolated` when a level lies
outside [K_min, K_max] of the quotes used (kickoff Correction 11).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.integrate import trapezoid
from scipy.stats import norm

from volsurf.pricing import black76
from volsurf.svi import svi_g, svi_w, svi_w1

TAIL_COLUMNS = ["measure", "move", "x", "prob", "extrapolated"]
CHECK_COLUMNS = ["day", "ticker", "expiry", "T", "F", "L", "integral", "int_err", "mean", "mean_rel_err",
                 "min_density"]


def _d_minus(k, w):
    sw = np.sqrt(w)
    return -k / sw - sw / 2


def density_k(k, params) -> np.ndarray:
    """Kickoff 5.6 density of k = ln(S_T / F): p_k(k) = g(k) / sqrt(2 pi w) exp(-d-^2 / 2), d- = -k/sqrt(w) - sqrt(w)/2."""
    k = np.asarray(k, dtype=float)
    w = svi_w(k, *params)
    return svi_g(k, params) / np.sqrt(2 * np.pi * w) * np.exp(-_d_minus(k, w) ** 2 / 2)


def svi_density(K, F, T, params) -> np.ndarray:
    """Kickoff 5.6: q(K) = p_k(ln(K / F)) / K for an SVI slice (params of total variance, so T does not enter)."""
    K = np.asarray(K, dtype=float)
    return density_k(np.log(K / F), params) / K


def fd_density(K, F, T, D, params, dk) -> np.ndarray:
    """Kickoff 5.6 cross-check: e^(rT) d2C/dK2 = (1/D) d2C/dK2 by central differences with step dk (in K; the
    caller passes `[density] bl_dk` x F) of Black-76 call prices at sigma(K) = sqrt(w(ln(K / F)) / T) on the slice."""
    K = np.asarray(K, dtype=float)

    def call(strike):
        return black76(F, strike, T, D, np.sqrt(svi_w(np.log(strike / F), *params) / T), "C")

    return (call(K + dk) - 2 * call(K) + call(K - dk)) / (dk * dk) / D


def prob_above(x, F, params) -> np.ndarray:
    """P(S_T > x) = N(d-) - phi(d-) w' / (2 sqrt(w)) at k = ln(x / F) (O-35 (a))."""
    k = np.log(np.asarray(x, dtype=float) / F)
    w = svi_w(k, *params)
    dm = _d_minus(k, w)
    return norm.cdf(dm) - norm.pdf(dm) * svi_w1(k, params) / (2 * np.sqrt(w))


def prob_below(x, F, params) -> np.ndarray:
    """P(S_T < x) = N(-d-) + phi(d-) w' / (2 sqrt(w)) at k = ln(x / F), the complement of `prob_above`."""
    k = np.log(np.asarray(x, dtype=float) / F)
    w = svi_w(k, *params)
    dm = _d_minus(k, w)
    return norm.cdf(-dm) + norm.pdf(dm) * svi_w1(k, params) / (2 * np.sqrt(w))


def k_grid(params, k_sd: float, n_points: int) -> np.ndarray:
    """Instruction 05 part C integration grid: n_points in k over [-L, L], L = k_sd x sqrt(w(0))."""
    L = k_sd * np.sqrt(float(svi_w(0.0, *params)))
    return np.linspace(-L, L, n_points)


def density_check(params, F, cfg) -> dict:
    """Trapezoid integrals of the density over [F e^(-L), F e^(L)] on `[density] int_points` points in k
    (instruction 05 part C): integral of q dK and of K q dK (as p_k dk and F e^k p_k dk), their errors against 1 and
    F (relative), and the smallest density on the grid."""
    k = k_grid(params, cfg.density.k_sd, cfg.density.int_points)
    p = density_k(k, params)
    integral, mean = float(trapezoid(p, k)), float(trapezoid(F * np.exp(k) * p, k))
    return {"L": float(k[-1]), "integral": integral, "int_err": integral - 1, "mean": mean,
            "mean_rel_err": mean / F - 1, "min_density": float(p.min())}


def tail_table(params, F, T, k_range, moves) -> pd.DataFrame:
    """Kickoff 5.6 tail table for one slice: for each m in `moves`, P(S_T < x) (`below`) and P(S_T > x) (`above`)
    at x = F (1 - m) and F (1 + m) (move -m and +m), and P(|ln(S_T / F)| > m) (`abs_log`, move m, x blank). Each row
    is flagged `extrapolated` when a level it uses lies outside [K_min, K_max] = F e^k_range."""
    k_lo, k_hi = k_range
    K_min, K_max = F * np.exp(k_lo), F * np.exp(k_hi)
    rows = []
    for m in moves:
        for move in (-m, m):
            x = F * (1 + move)
            outside = bool(x < K_min or x > K_max)
            rows.append({"measure": "below", "move": move, "x": x, "prob": float(prob_below(x, F, params)),
                         "extrapolated": outside})
            rows.append({"measure": "above", "move": move, "x": x, "prob": float(prob_above(x, F, params)),
                         "extrapolated": outside})
        lo, hi = F * np.exp(-m), F * np.exp(m)
        rows.append({"measure": "abs_log", "move": m, "x": np.nan,
                     "prob": float(prob_below(lo, F, params) + prob_above(hi, F, params)),
                     "extrapolated": bool(lo < K_min or hi > K_max)})
    order = {"below": 0, "above": 1, "abs_log": 2}
    out = pd.DataFrame(rows, columns=TAIL_COLUMNS)
    return out.sort_values(["measure", "move"], key=lambda c: c.map(order) if c.name == "measure" else c,
                           kind="stable", ignore_index=True)


def pit(params, F, S_realised: float) -> float:
    """Kickoff 5.6 probability integral transform u = P_Q(S_T <= S_realised) on the slice."""
    return float(prob_below(S_realised, F, params))

