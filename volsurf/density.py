"""Risk-neutral density from an SVI slice (PLAN 5.1 and 5.2, kickoff Section 5.6, instructions 05 and 05b).

Tail probabilities and PIT values use the SVI slice's closed-form distribution function (O-35 (a)):
P(S_T > K) = N(d-) - phi(d-) w'(k) / (2 sqrt(w(k))), which is -(1/D) dC/dK of the Black price on the slice, so it is
the exact integral of `svi_density` from K to infinity. Tail rows are flagged `extrapolated` when a level lies
outside [K_min, K_max] of the quotes used (kickoff Correction 11). The integral checks run on the slice's sinh grid
over [-K, K], K = `[svi] k_check`, with the closed-form mass beyond +-K added (instruction 05b B4); a slice that misses
`int_tol` has density status `density_fail` and no tail table or PIT value (O-36 (a), instruction 05b part C). So do
slices with s at the `s_min` floor (`kink`) and slices whose analytic density misses the finite-difference one by more
than 5e-3 x peak at the step F min(`bl_dk`, s / 10) (`fd_gap`) (O-38 (b), instruction 06).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.integrate import trapezoid
from scipy.stats import norm

from volsurf.pricing import black76
from volsurf.svi import ACCEPTED, check_grid, svi_g, svi_w, svi_w1

TAIL_COLUMNS = ["measure", "move", "x", "prob", "extrapolated"]
CHECK_COLUMNS = ["day", "ticker", "expiry", "T", "F", "integral", "int_err", "tail_mass", "mean", "mean_rel_err",
                 "min_g", "min_density", "fd_rel_gap", "density_status"]
PIT_COLUMNS = ["ticker", "expiry", "day", "T", "F", "S_realised", "u", "status"]
SLICE_KEYS = ["day", "ticker", "expiry", "T", "F"]
TAIL_PROBS_COLUMNS = [*SLICE_KEYS, "K_min", "K_max", *TAIL_COLUMNS]


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


def k_grid(params, cfg) -> np.ndarray:
    """Instruction 05b B4 integration grid: the slice's `[density] int_points`-point sinh grid over [-K, K]."""
    return check_grid(params, cfg, cfg.density.int_points)


def is_kink(params, cfg) -> bool:
    """O-38 (b) part 1, instruction 06: s at the `[svi] s_min` floor, s <= s_min x (1 + 1e-6), is a corner in the
    fitted smile, and its density gets status `kink`."""
    return float(params[4]) <= cfg.svi.s_min * (1 + 1e-6)  # instruction 06 part B, O-38: s_min x (1 + 1e-6)


def density_check(params, F, cfg) -> dict:
    """Instruction 05b B4: trapezoid integrals of the density on the sinh grid over [F e^(-K), F e^(K)], as p_k dk
    and F e^k p_k dk; the integral adds the closed-form mass beyond +-K, tail_mass = P(S_T < F e^(-K)) +
    P(S_T > F e^(K)). Errors against 1 and F (relative), the smallest g and density on the grid, and
    density_status `kink` (`is_kink`, O-38 (b)), else `density_fail` (either error above `int_tol`; O-36 (a)), else
    `ok`. The `fd_gap` status is set afterwards from `fd_gap` on the quoted range."""
    k = k_grid(params, cfg)
    p = density_k(k, params)
    tail = float(prob_below(F * np.exp(k[0]), F, params) + prob_above(F * np.exp(k[-1]), F, params))
    integral, mean = float(trapezoid(p, k)) + tail, float(trapezoid(F * np.exp(k) * p, k))
    out = {"integral": integral, "int_err": integral - 1, "tail_mass": tail, "mean": mean,
           "mean_rel_err": mean / F - 1, "min_g": float(svi_g(k, params).min()), "min_density": float(p.min())}
    ok = abs(out["int_err"]) <= cfg.density.int_tol and abs(out["mean_rel_err"]) <= cfg.density.int_tol
    status = "kink" if is_kink(params, cfg) else "ok" if ok else "density_fail"
    return out | {"density_status": status}


FD_GAP_MAX = 5e-3  # instruction 05b part C: largest |q - q_fd| <= 5e-3 x the slice's peak density on the quoted range


def fd_step(params, F, cfg) -> float:
    """O-38 (b) part 2, instruction 06: dk = F x min(`bl_dk`, s / 10)."""
    return F * min(cfg.density.bl_dk, float(params[4]) / 10)  # instruction 06 part B, O-38: s / 10


def fd_gap(params, F, T, D, k_range, cfg) -> dict:
    """Analytic density against `fd_density` with step `fd_step` on 2,001 strikes over the quoted range F e^k_range:
    the largest absolute gap, where it is, and the largest gap relative to the slice's peak density there."""
    K = F * np.exp(np.linspace(k_range[0], k_range[1], 2001))
    q = svi_density(K, F, T, params)
    gap = np.abs(q - fd_density(K, F, T, D, params, fd_step(params, F, cfg)))
    i = int(np.argmax(gap))
    return {"max_abs_gap": float(gap[i]), "K_at_max": float(K[i]), "q_at_max": float(q[i]),
            "max_rel_gap_to_peak": float(gap.max() / q.max())}


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


def _params(r) -> tuple:
    return (r.a, r.b, r.rho, r.m, r.s)


def tail_probs(slices: pd.DataFrame, moves) -> pd.DataFrame:
    """PLAN 5.2 (O-1 (a) helper): `tail_table` for every slice given. `slices` has columns day, ticker, expiry, T, F,
    k_min, k_max, a, b, rho, m, s (accepted slices whose density status is ok); output TAIL_PROBS_COLUMNS."""
    parts = []
    for r in slices.itertuples():
        t = tail_table(_params(r), r.F, r.T, (r.k_min, r.k_max), moves)
        keys = {"day": r.day, "ticker": r.ticker, "expiry": r.expiry, "T": r.T, "F": r.F,
                "K_min": r.F * np.exp(r.k_min), "K_max": r.F * np.exp(r.k_max)}
        parts.append(t.assign(**keys)[TAIL_PROBS_COLUMNS])
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=TAIL_PROBS_COLUMNS)


def pit_table(fits: pd.DataFrame, closes: dict[str, pd.Series], last_day: str) -> pd.DataFrame:
    """PLAN 5.2 with O-14 (a) and instructions 05 and 05b: one row per captured (ticker, expiry) in `fits` (SVI_FITS
    rows of every day, with F and, optionally, density_status) whose expiry is on or before `last_day`, the latest
    capture day. u comes from the first day with an accepted slice whose density status is ok; S_realised is the
    unadjusted close on the expiry date from `closes` (ticker -> Series indexed by ISO date). Status `ok`,
    `no_accepted_slice`, the first accepted slice's density status (`density_fail`, `kink` or `fd_gap`) when accepted
    slices exist but none has an ok density, or `no_close`, with blank values where they cannot be computed
    (Convention 4.15). Columns PIT_COLUMNS."""
    rows = []
    expired = fits[fits["expiry"] <= last_day]
    for (ticker, expiry), g in expired.groupby(["ticker", "expiry"], sort=True):
        acc = g[g["status"].isin(ACCEPTED)].sort_values("day")
        good = acc[acc["density_status"] == "ok"] if "density_status" in acc else acc
        row = dict.fromkeys(PIT_COLUMNS, np.nan) | {"ticker": ticker, "expiry": expiry, "day": ""}
        close = closes.get(ticker, pd.Series(dtype=float)).get(expiry, np.nan)
        if acc.empty:
            row["status"] = "no_accepted_slice"
        elif good.empty:
            row["status"] = acc["density_status"].iloc[0]
        else:
            r = next(good.itertuples())
            row.update(day=r.day, T=r.T, F=r.F, S_realised=close)
            ok = bool(np.isfinite(close))
            row.update(u=pit(_params(r), r.F, close) if ok else np.nan, status="ok" if ok else "no_close")
        rows.append(row)
    return pd.DataFrame(rows, columns=PIT_COLUMNS)
