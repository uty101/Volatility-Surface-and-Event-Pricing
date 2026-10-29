"""SSVI across expiries and the daily surface run (PLAN 4.2 and 4.3, kickoff Section 5.5, O-10 (a), instruction 04).

SURFACE_DAILY statuses (O-9 (a), instruction 04 step 4.2): `ok`, `too_few_expiries` (fewer than 3 accepted SVI
slices) and `ssvi_fail` (SLSQP did not converge); both failures keep the row with blank metrics (Convention 4.15).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import brentq, minimize
from scipy.stats import norm

from volsurf.iv import BRENT_TOL
from volsurf.svi import (
    ACCEPTED,
    PARAMS,
    RHO_MAX,
    W_FLOOR,
    butterfly_grid,
    calendar_violations,
    fit_svi,
    svi_w,
)

SVI_FITS_COLUMNS = ["day", "ticker", "expiry", "T", "n_quotes", "a", "b", "rho", "m", "s", "rmse_vol", "min_g",
                    "status", "refit", "rmse_volpts", "exit"]
SURFACE_COLUMNS = ["day", "ticker", "atm_30", "rr25_30", "bf25_30", "atm_90", "term_slope", "ssvi_rho", "ssvi_eta",
                   "ssvi_gamma", "ssvi_rmse", "n_expiries", "status"]
THETA_COLUMNS = ["day", "ticker", "expiry", "theta_svi", "theta_used", "theta_capped"]
MIN_EXPIRIES = 3  # instruction 04 step 4.2: fewer than 3 accepted slices gives too_few_expiries
START = (-0.5, 1.0, 0.5)  # O-10 (a): SLSQP from 1 start (rho, eta, gamma)
GAMMA_MAX = 0.5  # kickoff Section 5.5: 0 < gamma <= 0.5
ETA_WING = 2.0  # kickoff Section 5.5: eta (1 + |rho|) <= 2


def ssvi_w(k, theta, rho, eta, gamma) -> np.ndarray:
    """SSVI total variance w(k, theta) = (theta/2)[1 + rho phi k + sqrt((phi k + rho)^2 + 1 - rho^2)] with
    phi(theta) = eta / (theta^gamma (1 + theta)^(1 - gamma)); k and theta broadcast."""
    k, theta = np.asarray(k, dtype=float), np.asarray(theta, dtype=float)
    phi = eta / (theta**gamma * (1 + theta) ** (1 - gamma))
    x = phi * k
    return theta / 2 * (1 + rho * x + np.sqrt((x + rho) ** 2 + 1 - rho * rho))


def _thetas(slices: list[dict]) -> pd.DataFrame:
    """theta_i = SVI w_i(0), made non-decreasing in T by cumulative maximum (O-10 (a): theta_capped where it binds)."""
    rows = sorted(slices, key=lambda s: s["T"])
    out = pd.DataFrame({"expiry": [s["expiry"] for s in rows], "T": [s["T"] for s in rows],
                        "theta_svi": [float(svi_w(0.0, *s["params"])) for s in rows]})
    out["theta_used"] = out["theta_svi"].cummax()
    out["theta_capped"] = out["theta_used"] > out["theta_svi"]
    return out


def fit_ssvi(slices: list[dict], quotes: pd.DataFrame, cfg) -> dict:
    """Kickoff 5.5 SSVI on the accepted SVI slices (dicts with expiry, T, params) and their quotes (columns expiry,
    k, iv). theta per expiry from `_thetas`; rho, eta, gamma by SLSQP at scipy default settings (O-33 (a)) from the O-10
    (a) start, equal weights on every quote, minimising sum (sqrt(max(w, 1e-12) / T) - iv)^2 under |rho| <= 0.999,
    eta > 0, 0 < gamma <= 0.5 and eta (1 + |rho|) <= 2. Returns rho, eta, gamma, rmse (decimal vol), n_expiries,
    n_quotes, status and thetas (expiry, T, theta_svi, theta_used, theta_capped); parameters blank unless ok."""
    out = {"rho": np.nan, "eta": np.nan, "gamma": np.nan, "rmse": np.nan, "n_expiries": len(slices),
           "n_quotes": 0, "status": "too_few_expiries", "thetas": _thetas(slices) if slices else None}
    if len(slices) < MIN_EXPIRIES:
        return out
    th = out["thetas"].set_index("expiry")
    q = quotes[quotes["expiry"].isin(th.index)]
    k, iv = q["k"].to_numpy(float), q["iv"].to_numpy(float)
    theta, T = q["expiry"].map(th["theta_used"]).to_numpy(float), q["expiry"].map(th["T"]).to_numpy(float)
    out["n_quotes"] = len(q)

    def resid(p):
        return np.sqrt(np.maximum(ssvi_w(k, theta, *p), W_FLOOR) / T) - iv

    cons = [{"type": "ineq", "fun": lambda p: ETA_WING - p[1] * (1 + p[0])},
            {"type": "ineq", "fun": lambda p: ETA_WING - p[1] * (1 - p[0])}]
    bounds = [(-RHO_MAX, RHO_MAX), (0.0, None), (0.0, GAMMA_MAX)]
    r = minimize(lambda p: float(np.sum(resid(p) ** 2)), np.asarray(START), method="SLSQP", bounds=bounds,
                 constraints=cons)
    if not r.success:
        out["status"] = "ssvi_fail"
        return out
    rho, eta, gamma = (float(x) for x in r.x)
    out.update(rho=rho, eta=eta, gamma=gamma, rmse=float(np.sqrt(np.mean(resid(r.x) ** 2))), status="ok")
    return out


def theta_at(tau: float, thetas: pd.DataFrame) -> float:
    """Convention 4.12: theta linear in T between the 2 bracketing accepted expiries' theta_used; nan outside."""
    T, th = thetas["T"].to_numpy(float), thetas["theta_used"].to_numpy(float)
    if not T[0] <= tau <= T[-1]:
        return np.nan
    return float(np.interp(tau, T, th))


def delta_strike(delta: float, theta: float, rho: float, eta: float, gamma: float) -> float:
    """Log-moneyness k where the Black forward delta N(d1) equals `delta` (a call delta; a put delta -x is the call
    delta 1 - x), with d1 = -k / sqrt(w(k)) + sqrt(w(k)) / 2 on the SSVI slice. Brackets outward from k = 0 in
    steps of sqrt(theta), doubling, then brentq at the Section 3 Brent tolerances."""

    def f(k):
        sw = np.sqrt(ssvi_w(k, theta, rho, eta, gamma))
        return float(norm.cdf(-k / sw + sw / 2)) - delta

    step = np.sqrt(theta) * (1.0 if f(0.0) > 0 else -1.0)  # N(d1) falls as k rises
    lo, hi = 0.0, step
    while np.sign(f(hi)) == np.sign(f(lo)):
        lo, hi, step = hi, hi + 2 * step, 2 * step
    return brentq(f, min(lo, hi), max(lo, hi), xtol=BRENT_TOL, rtol=BRENT_TOL)


def surface_metrics(fit: dict, cfg) -> dict:
    """SURFACE_DAILY values (kickoff 5.5) from an SSVI fit at tau = `[surface] tenors_days` / 365 (30 and 90 days):
    ATM vol sqrt(theta(tau) / tau), 25-delta call and put vols at the `[surface] delta` forward-delta strikes,
    RR = sigma_25c - sigma_25p, BF = (sigma_25c + sigma_25p)/2 - sigma_ATM, term slope = ATM 90 - ATM 30. Vols are
    decimals; blank where tau is outside the accepted expiries (Convention 4.12) or the fit is not ok."""
    row = {c: np.nan for c in SURFACE_COLUMNS[2:-2]}
    row.update(n_expiries=fit["n_expiries"], status=fit["status"])
    if fit["status"] != "ok":
        return row
    p = (fit["rho"], fit["eta"], fit["gamma"])
    t30, t90 = (d / 365 for d in cfg.surface.tenors_days)
    atm = {}
    for name, tau in (("30", t30), ("90", t90)):
        theta = theta_at(tau, fit["thetas"])
        atm[name] = np.sqrt(theta / tau)
        if name == "30" and np.isfinite(theta):
            vol = {}
            for side, target in (("c", cfg.surface.delta), ("p", 1 - cfg.surface.delta)):
                k = delta_strike(target, theta, *p)
                vol[side] = float(np.sqrt(ssvi_w(k, theta, *p) / tau))
            row["rr25_30"] = vol["c"] - vol["p"]
            row["bf25_30"] = (vol["c"] + vol["p"]) / 2 - atm["30"]
    row.update(atm_30=atm["30"], atm_90=atm["90"], term_slope=atm["90"] - atm["30"], ssvi_rho=fit["rho"],
               ssvi_eta=fit["eta"], ssvi_gamma=fit["gamma"], ssvi_rmse=fit["rmse"])
    return row


def surface_day(iv: pd.DataFrame, cfg) -> dict[str, pd.DataFrame]:
    """PLAN 4.3 for one day's IV table (O-1 (a) helper): SVI per (ticker, expiry) on the OTM rows with a vol,
    SSVI per ticker on the accepted slices, calendar check per ticker on the union grid (O-31 (a)). Returns frames
    svi_fits (SVI_FITS plus refit, rmse_volpts and exit; a to s blank unless accepted), surface (SURFACE_DAILY),
    calendar and theta (ssvi_theta.csv), each in ticker order of first appearance and expiry order."""
    iv = iv[iv["iv"].notna()].copy()
    iv["k"] = np.log(iv["strike"] / iv["F"])
    fits, surface, calendar, theta = [], [], [], []
    for ticker, t_rows in iv.groupby("ticker", sort=False):
        day = t_rows["day"].iloc[0]
        accepted, ks = [], []
        for expiry, g in t_rows.groupby("expiry", sort=True):
            T = float(g["T"].iloc[0])
            fit = fit_svi(g["k"], g["iv"], T, cfg)
            ok = fit["status"] in ACCEPTED
            row = {"day": day, "ticker": ticker, "expiry": expiry, "T": T, "n_quotes": fit["n_quotes"]}
            row.update({p: (v if ok else np.nan) for p, v in zip(PARAMS, fit["params"], strict=True)})
            row.update(rmse_vol=fit["rmse_vol"], min_g=fit["min_g"], status=fit["status"], refit=fit["refit"],
                       rmse_volpts=fit["rmse_volpts"], exit=fit["exit"])
            fits.append(row)
            if ok:
                accepted.append({"day": day, "ticker": ticker, "expiry": expiry, "T": T, "params": fit["params"]})
                ks.append(g["k"].to_numpy())
        ssvi = fit_ssvi(accepted, t_rows[t_rows["expiry"].isin([s["expiry"] for s in accepted])], cfg)
        surface.append({"day": day, "ticker": ticker, **surface_metrics(ssvi, cfg)})
        if ssvi["thetas"] is not None:
            th = ssvi["thetas"].drop(columns="T")
            theta.append(th.assign(day=day, ticker=ticker)[THETA_COLUMNS])
        if len(accepted) >= 2:
            calendar.append(calendar_violations(accepted, butterfly_grid(np.concatenate(ks), cfg)))
    return {
        "svi_fits": pd.DataFrame(fits, columns=SVI_FITS_COLUMNS),
        "surface": pd.DataFrame(surface, columns=SURFACE_COLUMNS),
        "calendar": pd.concat(calendar, ignore_index=True) if calendar else calendar_violations([], [0.0]),
        "theta": pd.concat(theta, ignore_index=True) if theta else pd.DataFrame(columns=THETA_COLUMNS),
    }
