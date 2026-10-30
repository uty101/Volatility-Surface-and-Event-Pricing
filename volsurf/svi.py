"""Raw SVI per expiry (PLAN 4.1, kickoff Section 5.4 with instruction 04 part B and instruction 05 part B).

Statuses (O-9 (a), instruction 04 part B): `ok` (the first fit passes the butterfly check), `ok_refit` (accepted
after the constrained refit or the neighbour retry), `butterfly_fail` (no refit passes), `poor_fit` (an otherwise
accepted fit whose RMSE is above `max_rmse_volpts`) and `too_few` (fewer than `min_quotes` quotes). `ok` and
`ok_refit` are accepted. Routes (instruction 05 step 5.0): `first`, `refit`, `neighbour`, the fit that was judged.
"""

from __future__ import annotations

from itertools import pairwise

import numpy as np
import pandas as pd
from scipy.optimize import minimize

PARAMS = ["a", "b", "rho", "m", "s"]
ACCEPTED = ("ok", "ok_refit")
RETRIED = ("poor_fit", "butterfly_fail")  # instruction 05 correction 3: failed slices retried from neighbours
RHO_MAX = 0.999  # kickoff Section 5.4: |rho| <= 0.999
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


def svi_w1(k, params) -> np.ndarray:
    """Analytic w'(k) of a raw SVI slice."""
    return _derivs(k, params)[1]


def svi_g(k, params) -> np.ndarray:
    """Butterfly function g(k) = (1 - k w'/(2w))^2 - (w'^2/4)(1/w + 1/4) + w''/2 with analytic w' and w''."""
    w, w1, w2 = _derivs(k, params)
    k = np.asarray(k, dtype=float)
    return (1 - k * w1 / (2 * w)) ** 2 - (w1 * w1 / 4) * (1 / w + 0.25) + w2 / 2


def butterfly_grid(k, cfg) -> np.ndarray:
    """`grid_points` points over [k_min - grid_pad, k_max + grid_pad] (kickoff Section 5.4); the calendar grid."""
    k = np.asarray(k, dtype=float)
    return np.linspace(k.min() - cfg.svi.grid_pad, k.max() + cfg.svi.grid_pad, cfg.svi.grid_points)


def wide_grid(k, params, cfg) -> np.ndarray:
    """Instruction 05 correction 2: the butterfly grid, `grid_points` points over [min(k_min - grid_pad, -L),
    max(k_max + grid_pad, L)] with L = `[density] k_sd` x sqrt(w(0)) of the slice `params`."""
    k = np.asarray(k, dtype=float)
    L = cfg.density.k_sd * np.sqrt(max(float(svi_w(0.0, *params)), 0.0))
    return np.linspace(min(k.min() - cfg.svi.grid_pad, -L), max(k.max() + cfg.svi.grid_pad, L), cfg.svi.grid_points)


def min_g(k, params, cfg) -> float:
    """Smallest g on the slice's wide butterfly grid."""
    return float(svi_g(wide_grid(k, params, cfg), params).min())


def _constraints(cfg):
    """Section 5.4 inequalities as SLSQP dicts (>= 0), with the wing bound b (1 + |rho|) <= `[svi] wing_max`
    (instruction 05 correction 1); |rho| and the wing bound split into smooth halves."""
    wing = cfg.svi.wing_max
    return [
        {"type": "ineq", "fun": lambda p: p[0] + p[1] * p[4] * np.sqrt(max(1 - p[2] ** 2, 0.0))},
        {"type": "ineq", "fun": lambda p: wing - p[1] * (1 + p[2])},
        {"type": "ineq", "fun": lambda p: wing - p[1] * (1 - p[2])},
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


class _Slice:
    """One expiry's quotes with its objective, RMSE and constraints, shared by the 3 routes."""

    def __init__(self, k, iv, T, cfg):
        self.k, self.iv, self.T, self.cfg = np.asarray(k, dtype=float), np.asarray(iv, dtype=float), T, cfg
        self.cons, self.bounds = _constraints(cfg), _bounds(cfg)
        self.max_rmse = cfg.svi.max_rmse_volpts / 100

    def resid(self, p):
        return np.sqrt(np.maximum(svi_w(self.k, *p), W_FLOOR) / self.T) - self.iv

    def objective(self, p):
        return float(np.sum(self.resid(p) ** 2))

    def rmse(self, p):
        return float(np.sqrt(np.mean(self.resid(p) ** 2)))

    def constrained(self, starts) -> tuple[list, list]:
        """SLSQP with g >= 0 at every point of the wide grid as a hard vector constraint, from each start. A result
        counts if SLSQP reports success or stops at the iteration limit, meets every Section 5.4 bound and constraint
        exactly and has min g >= -1e-10 (O-32 (a)). Returns (counting, counting with RMSE <= max_rmse_volpts)."""
        g_con = self.cons + [{"type": "ineq", "fun": lambda p: svi_g(wide_grid(self.k, p, self.cfg), p)}]
        counting = []
        for start in starts:
            with np.errstate(divide="ignore", invalid="ignore"):  # trial points with w = 0 on the grid give nan
                r = _fit(self.objective, start, g_con, self.bounds)
            if (_exit(r) in ("success", "maxiter") and _violation(r.x, self.cons, self.bounds) == 0
                    and min_g(self.k, r.x, self.cfg) >= -G_TOL):
                counting.append(r)
        return counting, [r for r in counting if self.rmse(r.x) <= self.max_rmse]

    def result(self, r, status, route, refit) -> dict:
        e = self.rmse(r.x)
        return {"n_quotes": len(self.k), "params": tuple(float(x) for x in r.x), "rmse_vol": e, "rmse_volpts": 100 * e,
                "min_g": min_g(self.k, r.x, self.cfg), "refit": refit, "exit": _exit(r), "status": status,
                "route": route}


def fit_svi(k, iv, T, cfg) -> dict:
    """Instruction 04 part B fit of raw SVI to one expiry's OTM quotes (k, iv) at T, with O-32 (a) (instruction 04b)
    and instruction 05 corrections 1 and 2.

    Objective sum (sqrt(max(w, 1e-12) / T) - iv)^2 under the Section 5.4 constraints with b (1 + |rho|) <=
    `wing_max`, SLSQP from each `[svi] starts` vector, lowest objective kept (route `first`). If its min g on the
    wide grid (`wide_grid`) is below -1e-10, refit with g >= 0 on the wide grid as a hard vector constraint, from the
    first fit's parameters and then each start (route `refit`); the best counting refit with RMSE <= `max_rmse_volpts`
    gives `ok_refit`. If refits count but every one is above the RMSE gate, the best of them gives `poor_fit`; if none
    counts, `butterfly_fail`. An `ok` first fit above the RMSE gate becomes `poor_fit`. Returns params (tuple, nan for
    too_few), rmse_vol, rmse_volpts, min_g, refit, exit (of the fit judged), n_quotes, status and route; the
    parameters of a rejected fit are those of the fit that was judged, for diagnostics."""
    sl = _Slice(k, iv, T, cfg)
    if len(sl.k) < cfg.svi.min_quotes:
        return {"n_quotes": len(sl.k), "params": (np.nan,) * 5, "rmse_vol": np.nan, "rmse_volpts": np.nan,
                "min_g": np.nan, "refit": False, "exit": "", "status": "too_few", "route": ""}
    first = min((_fit(sl.objective, start, sl.cons, sl.bounds) for start in cfg.svi.starts), key=lambda r: r.fun)
    if min_g(sl.k, first.x, cfg) >= -G_TOL:
        return sl.result(first, "ok" if sl.rmse(first.x) <= sl.max_rmse else "poor_fit", "first", False)
    counting, good = sl.constrained([first.x, *cfg.svi.starts])
    if not counting:
        return sl.result(first, "butterfly_fail", "first", True)
    return sl.result(min(good or counting, key=lambda r: r.fun), "ok_refit" if good else "poor_fit", "refit", True)


def neighbour_starts(T: float, accepted: list[tuple[float, tuple]], n: int) -> list[tuple]:
    """Instruction 05 correction 3: the parameters of the n accepted expiries nearest in T (ties to the earlier in
    `accepted` order), with a and b scaled by T / T_neighbour."""
    near = sorted(accepted, key=lambda a: abs(a[0] - T))[:n]
    return [(p[0] * T / Tn, p[1] * T / Tn, *p[2:]) for Tn, p in near]


def fit_expiries(quotes: list[dict], cfg) -> list[dict]:
    """`fit_svi` on every expiry of one ticker-day (dicts with T, k, iv), then instruction 05 correction 3: each
    `poor_fit` or `butterfly_fail` slice is refitted under the wide-grid g constraint (as in the refit route) from
    `neighbour_starts` of the slices accepted in the first pass, `[svi] neighbour_retries` of them. The best counting
    result with RMSE <= `max_rmse_volpts` replaces the fit with status `ok_refit` and route `neighbour`; otherwise
    the first-pass fit stands. Returns the fit dicts in input order."""
    fits = [fit_svi(q["k"], q["iv"], q["T"], cfg) for q in quotes]
    accepted = [(q["T"], f["params"]) for q, f in zip(quotes, fits, strict=True) if f["status"] in ACCEPTED]
    for i, (q, f) in enumerate(zip(quotes, fits, strict=True)):
        if f["status"] not in RETRIED or not accepted:
            continue
        sl = _Slice(q["k"], q["iv"], q["T"], cfg)
        _, good = sl.constrained(neighbour_starts(q["T"], accepted, cfg.svi.neighbour_retries))
        if good:
            fits[i] = sl.result(min(good, key=lambda r: r.fun), "ok_refit", "neighbour", f["refit"])
    return fits


def calendar_violations(slices: list[dict], grid) -> pd.DataFrame:
    """Kickoff Section 5.4 calendar check between consecutive accepted expiries (sorted by T): a violation is a
    grid point where w_{i+1}(k) < w_i(k) - 1e-10. One row per pair (O-31 (a)); each slice dict carries day, ticker,
    expiry, T and params. When both slices of a pair carry k_min and k_max (their quoted k range), only grid points
    inside the overlap of the 2 ranges are checked (instruction 05 step 5.0 item 4), and n_grid counts them.
    min_diff is the smallest w_{i+1} - w_i on the checked points and k_at_min where it occurs (nan if none)."""
    grid = np.asarray(grid, dtype=float)
    ordered = sorted(slices, key=lambda s: s["T"])
    rows = []
    for s1, s2 in pairwise(ordered):
        pts = grid
        if all("k_min" in s and "k_max" in s for s in (s1, s2)):
            lo, hi = max(s1["k_min"], s2["k_min"]), min(s1["k_max"], s2["k_max"])
            pts = grid[(grid >= lo) & (grid <= hi)]
        diff = svi_w(pts, *s2["params"]) - svi_w(pts, *s1["params"])
        n_bad = int((diff < -G_TOL).sum())
        i = int(np.argmin(diff)) if len(pts) else None
        rows.append({"day": s1.get("day", ""), "ticker": s1.get("ticker", ""), "expiry_1": s1["expiry"],
                     "expiry_2": s2["expiry"], "T_1": s1["T"], "T_2": s2["T"], "n_grid": len(pts),
                     "n_violations": n_bad, "min_diff": np.nan if i is None else float(diff[i]),
                     "k_at_min": np.nan if i is None else float(pts[i]), "violated": n_bad > 0})
    return pd.DataFrame(rows, columns=CALENDAR_COLUMNS)
