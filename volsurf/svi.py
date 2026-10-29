"""Raw SVI per expiry (PLAN 4.1, kickoff Section 5.4 with instruction 04 part B).

Statuses (O-9 (a), instruction 04 part B): `ok` (the first fit passes the butterfly check), `ok_refit` (accepted
after the constrained refit), `butterfly_fail` (no refit passes), `poor_fit` (an otherwise accepted fit whose RMSE
is above `max_rmse_volpts`) and `too_few` (fewer than `min_quotes` quotes). `ok` and `ok_refit` are accepted.
"""

from __future__ import annotations

from itertools import pairwise

import numpy as np
import pandas as pd
from scipy.optimize import minimize

PARAMS = ["a", "b", "rho", "m", "s"]
ACCEPTED = ("ok", "ok_refit")
RHO_MAX = 0.999  # kickoff Section 5.4: |rho| <= 0.999
WING_MAX = 4.0  # kickoff Section 5.4: b (1 + |rho|) <= 4
G_TOL = 1e-10  # kickoff Section 5.4: butterfly pass if min g >= -1e-10; calendar w_{i+1} >= w_i - 1e-10
W_FLOOR = 1e-12  # instruction 04 part B: w clipped below at 1e-12 inside the square root
SLSQP = {"maxiter": 1000, "ftol": 1e-14}  # instruction 04 part B: SLSQP fit settings
SLSQP_MAXITER = 9  # scipy SLSQP exit status "Iteration limit reached" (O-32 (a), instruction 04b)
CALENDAR_COLUMNS = ["day", "ticker", "expiry_1", "expiry_2", "T_1", "T_2", "n_grid", "n_violations", "min_diff",
                    "k_at_min", "violated"]


def svi_w(k, a, b, rho, m, s) -> np.ndarray:
    """Raw SVI total variance w(k) = a + b [rho (k - m) + sqrt((k - m)^2 + s^2)]."""
    x = np.asarray(k, dtype=float) - m
    return a + b * (rho * x + np.sqrt(x * x + s * s))


def _derivs(k, params):
    a, b, rho, m, s = params
    x = np.asarray(k, dtype=float) - m
    root = np.sqrt(x * x + s * s)
    return a + b * (rho * x + root), b * (rho + x / root), b * s * s / root**3


def svi_g(k, params) -> np.ndarray:
    """Butterfly function g(k) = (1 - k w'/(2w))^2 - (w'^2/4)(1/w + 1/4) + w''/2 with analytic w' and w''."""
    w, w1, w2 = _derivs(k, params)
    k = np.asarray(k, dtype=float)
    return (1 - k * w1 / (2 * w)) ** 2 - (w1 * w1 / 4) * (1 / w + 0.25) + w2 / 2


def butterfly_grid(k, cfg) -> np.ndarray:
    """`grid_points` points over [k_min - grid_pad, k_max + grid_pad] (kickoff Section 5.4)."""
    k = np.asarray(k, dtype=float)
    return np.linspace(k.min() - cfg.svi.grid_pad, k.max() + cfg.svi.grid_pad, cfg.svi.grid_points)


def _constraints(cfg):
    """Kickoff Section 5.4 inequalities as SLSQP dicts (>= 0); |rho| and b (1 + |rho|) split into smooth halves."""
    return [
        {"type": "ineq", "fun": lambda p: p[0] + p[1] * p[4] * np.sqrt(max(1 - p[2] ** 2, 0.0))},
        {"type": "ineq", "fun": lambda p: WING_MAX - p[1] * (1 + p[2])},
        {"type": "ineq", "fun": lambda p: WING_MAX - p[1] * (1 - p[2])},
    ]


def _bounds(cfg):
    return [(None, None), (0.0, None), (-RHO_MAX, RHO_MAX), (None, None), (cfg.svi.s_min, None)]


def _violation(p, constraints, bounds) -> float:
    """Largest violation of the Section 5.4 bounds and constraints at p, 0 when every one is met exactly."""
    gaps = [lo - x for x, (lo, _) in zip(p, bounds, strict=True) if lo is not None]
    gaps += [x - hi for x, (_, hi) in zip(p, bounds, strict=True) if hi is not None]
    gaps += [-float(np.min(c["fun"](p))) for c in constraints]
    return max(0.0, *gaps)


def _fit(objective, start, constraints, bounds):
    return minimize(objective, np.asarray(start, dtype=float), method="SLSQP", bounds=bounds,
                    constraints=constraints, options=SLSQP)


def _exit(r) -> str:
    """O-32 (a): `success`, `maxiter` (SLSQP status 9, the iteration limit), or SLSQP's own status code."""
    return "success" if r.success else "maxiter" if r.status == SLSQP_MAXITER else f"slsqp_{r.status}"


def fit_svi(k, iv, T, cfg) -> dict:
    """Instruction 04 part B fit of raw SVI to one expiry's OTM quotes (k, iv) at T, with O-32 (a) (instruction 04b).

    Objective sum (sqrt(max(w, 1e-12) / T) - iv)^2 under the Section 5.4 constraints, SLSQP from each
    `[svi] starts` vector, lowest objective kept (Section 5.4). If its min g on the butterfly grid is below -1e-10,
    refit with g >= 0 at every grid point as a hard vector constraint, from the first fit's parameters and then
    each start. A refit counts if SLSQP reports success or stops at the iteration limit, and its result meets every
    Section 5.4 bound and constraint exactly and has min g >= -1e-10; the best counting refit with RMSE <=
    `max_rmse_volpts` gives `ok_refit`. If refits count but every one is above the RMSE gate, the best of them gives
    `poor_fit`; if none counts, `butterfly_fail`. An `ok` first fit above the RMSE gate becomes `poor_fit`.
    Returns params (tuple, nan for too_few), rmse_vol, rmse_volpts, min_g, refit, exit (of the fit judged),
    n_quotes and status; the parameters of a rejected fit are those of the fit that was judged, for diagnostics."""
    k, iv = np.asarray(k, dtype=float), np.asarray(iv, dtype=float)
    out = {"n_quotes": len(k), "params": (np.nan,) * 5, "rmse_vol": np.nan, "rmse_volpts": np.nan,
           "min_g": np.nan, "refit": False, "exit": "", "status": "too_few"}
    if len(k) < cfg.svi.min_quotes:
        return out

    def rmse(p):
        return float(np.sqrt(np.mean((np.sqrt(np.maximum(svi_w(k, *p), W_FLOOR) / T) - iv) ** 2)))

    def objective(p):
        return float(np.sum((np.sqrt(np.maximum(svi_w(k, *p), W_FLOOR) / T) - iv) ** 2))

    grid = butterfly_grid(k, cfg)
    cons, bounds = _constraints(cfg), _bounds(cfg)
    max_rmse = cfg.svi.max_rmse_volpts / 100

    first = min((_fit(objective, start, cons, bounds) for start in cfg.svi.starts), key=lambda r: r.fun)
    kept, status = first, "ok"
    min_g = float(svi_g(grid, first.x).min())
    if min_g < -G_TOL:
        out["refit"] = True
        g_con = cons + [{"type": "ineq", "fun": lambda p: svi_g(grid, p)}]
        counting = []
        for start in [first.x, *cfg.svi.starts]:
            r = _fit(objective, start, g_con, bounds)
            if (_exit(r) in ("success", "maxiter") and _violation(r.x, cons, bounds) == 0
                    and svi_g(grid, r.x).min() >= -G_TOL):
                counting.append(r)
        good = [r for r in counting if rmse(r.x) <= max_rmse]
        if good or counting:
            kept = min(good or counting, key=lambda r: r.fun)
            status, min_g = ("ok_refit" if good else "poor_fit"), float(svi_g(grid, kept.x).min())
        else:
            status = "butterfly_fail"
    if status == "ok" and rmse(first.x) > max_rmse:
        status = "poor_fit"
    e = rmse(kept.x)
    out.update(params=tuple(float(x) for x in kept.x), rmse_vol=e, rmse_volpts=100 * e, min_g=min_g,
               exit=_exit(kept), status=status)
    return out


def calendar_violations(slices: list[dict], grid) -> pd.DataFrame:
    """Kickoff Section 5.4 calendar check between consecutive accepted expiries (sorted by T): a violation is a
    grid point where w_{i+1}(k) < w_i(k) - 1e-10. One row per pair (O-31 (a)); each slice dict carries day, ticker,
    expiry, T and params. min_diff is the smallest w_{i+1} - w_i on the grid and k_at_min where it occurs."""
    grid = np.asarray(grid, dtype=float)
    ordered = sorted(slices, key=lambda s: s["T"])
    rows = []
    for s1, s2 in pairwise(ordered):
        diff = svi_w(grid, *s2["params"]) - svi_w(grid, *s1["params"])
        n_bad = int((diff < -G_TOL).sum())
        i = int(np.argmin(diff))
        rows.append({"day": s1.get("day", ""), "ticker": s1.get("ticker", ""), "expiry_1": s1["expiry"],
                     "expiry_2": s2["expiry"], "T_1": s1["T"], "T_2": s2["T"], "n_grid": len(grid),
                     "n_violations": n_bad, "min_diff": float(diff[i]), "k_at_min": float(grid[i]),
                     "violated": n_bad > 0})
    return pd.DataFrame(rows, columns=CALENDAR_COLUMNS)
