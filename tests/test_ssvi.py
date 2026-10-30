from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import bisect
from scipy.stats import norm

from volsurf.config import load_config
from volsurf.ssvi import (
    delta_strike,
    fit_ssvi,
    slice_delta_k,
    slice_metrics,
    ssvi_w,
    surface_metrics,
    surface_row,
)
from volsurf.svi import fit_svi, svi_w

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "config.toml")
K = np.linspace(-0.4, 0.3, 29)
EXPIRIES = [("e1", 30 / 365, 0.004), ("e2", 60 / 365, 0.008), ("e3", 91 / 365, 0.012), ("e4", 182 / 365, 0.022)]


def _synthetic(rho, eta, gamma):
    """Accepted SVI slices and quotes from an SSVI surface: each expiry's quotes are SSVI vols at its theta, and
    its SVI slice is fitted to them, so theta_i = w_i(0) comes from the SVI fit as in the daily run."""
    slices, quotes = [], []
    for expiry, T, theta in EXPIRIES:
        iv = np.sqrt(ssvi_w(K, theta, rho, eta, gamma) / T)
        fit = fit_svi(K, iv, T, CFG)
        assert fit["status"] in ("ok", "ok_refit")
        slices.append({"expiry": expiry, "T": T, "params": fit["params"]})
        quotes.append(pd.DataFrame({"expiry": expiry, "k": K, "iv": iv}))
    return slices, pd.concat(quotes, ignore_index=True)


def test_constraint_respected():
    # quotes from eta (1 + |rho|) = 1.6 x 1.7 = 2.72 > 2: the fit has to sit on the constraint
    fit = fit_ssvi(*_synthetic(-0.7, 1.6, 0.4), CFG)
    wing = fit["eta"] * (1 + abs(fit["rho"]))
    print({k: fit[k] for k in ("rho", "eta", "gamma", "rmse", "status")}, f"eta (1 + |rho|) = {wing!r}")
    assert fit["status"] == "ok"
    assert wing <= 2.0
    assert abs(fit["rho"]) <= 0.999 and fit["eta"] > 0 and 0 < fit["gamma"] <= 0.5


def test_no_calendar_violation_on_grid():
    fit = fit_ssvi(*_synthetic(-0.6, 1.0, 0.4), CFG)
    grid = np.linspace(K.min() - CFG.svi.grid_pad, K.max() + CFG.svi.grid_pad, CFG.svi.grid_points)
    w = np.array([ssvi_w(grid, th, fit["rho"], fit["eta"], fit["gamma"]) for th in fit["thetas"]["theta_used"]])
    diff = np.diff(w, axis=0)
    print(f"smallest w_(i+1) - w_i on the grid: {diff.min():.6g}")
    assert (diff >= -1e-10).all()


def test_theta_cumulative_maximum_recorded():
    slices, quotes = _synthetic(-0.6, 1.0, 0.4)
    a, *rest = slices[2]["params"]
    a -= float(svi_w(0.0, *slices[2]["params"])) - 0.006  # shift e3 so w(0) = 0.006, below e2's 0.008
    slices[2] = {**slices[2], "params": (a, *rest)}
    fit = fit_ssvi(slices, quotes, CFG)
    th = fit["thetas"]
    print(th.to_string())
    assert list(th["theta_capped"]) == [False, False, True, False]
    assert th["theta_used"].is_monotonic_increasing
    assert th["theta_used"].iloc[2] == th["theta_svi"].iloc[1]


def test_too_few_expiries():
    slices, quotes = _synthetic(-0.6, 1.0, 0.4)
    fit = fit_ssvi(slices[:2], quotes, CFG)
    row = surface_metrics(fit, CFG)
    assert fit["status"] == row["status"] == "too_few_expiries" and row["n_expiries"] == 2
    assert np.isnan([row[c] for c in ("atm_30", "rr25_30", "bf25_30", "atm_90", "ssvi_rho")]).all()


def test_25_delta_strikes():
    rho, eta, gamma, theta = -0.6, 1.0, 0.4, 0.004
    for target, kind in ((0.25, "call"), (-0.25, "put")):
        k = delta_strike(target if target > 0 else 1 + target, theta, rho, eta, gamma)
        sw = np.sqrt(ssvi_w(k, theta, rho, eta, gamma))
        d1 = -k / sw + sw / 2
        delta = norm.cdf(d1) if kind == "call" else norm.cdf(d1) - 1
        print(f"{kind}: k = {k:.10f}, forward delta = {delta:.15f}")
        assert abs(delta - target) <= 1e-10


def test_surface_metrics_hand_values():
    # ATM vol from theta interpolated in T, RR and BF from the 25-delta vols, term slope (kickoff 5.5)
    fit = fit_ssvi(*_synthetic(-0.6, 1.0, 0.4), CFG)
    row = surface_metrics(fit, CFG)
    th = fit["thetas"]
    t30, t90 = 30 / 365, 90 / 365
    theta30, theta90 = np.interp(t30, th["T"], th["theta_used"]), np.interp(t90, th["T"], th["theta_used"])
    assert row["status"] == "ok"
    assert abs(row["atm_30"] - np.sqrt(theta30 / t30)) <= 1e-15
    assert abs(row["term_slope"] - (np.sqrt(theta90 / t90) - np.sqrt(theta30 / t30))) <= 1e-15
    p = (fit["rho"], fit["eta"], fit["gamma"])
    vc = np.sqrt(ssvi_w(delta_strike(0.25, theta30, *p), theta30, *p) / t30)
    vp = np.sqrt(ssvi_w(delta_strike(0.75, theta30, *p), theta30, *p) / t30)
    assert abs(row["rr25_30"] - (vc - vp)) <= 1e-15
    assert abs(row["bf25_30"] - ((vc + vp) / 2 - row["atm_30"])) <= 1e-15
    print({c: row[c] for c in ("atm_30", "rr25_30", "bf25_30", "atm_90", "term_slope")})


# instruction 05 correction 4: 2 known SVI slices bracketing 30 days, and a third beyond 90 days
NEAR = {"expiry": "n", "T": 20 / 365, "params": (0.0005, 0.03, -0.6, 0.01, 0.08), "k_min": -0.6, "k_max": 0.3}
FAR = {"expiry": "f", "T": 45 / 365, "params": (0.0012, 0.045, -0.55, 0.015, 0.1), "k_min": -0.7, "k_max": 0.35}
LONG = {"expiry": "l", "T": 120 / 365, "params": (0.004, 0.08, -0.5, 0.02, 0.15), "k_min": -0.9, "k_max": 0.5}


def _delta(k, params):
    sw = np.sqrt(svi_w(k, *params))
    return norm.cdf(-k / sw + sw / 2)


def test_slice_metrics_two_slice_hand_values():
    tau = 30 / 365
    x = (tau - NEAR["T"]) / (FAR["T"] - NEAR["T"])
    vols = {}
    for side, target in (("c", 0.25), ("p", 0.75)):
        ks = [bisect(lambda k, p=s["params"], t=target: _delta(k, p) - t, s["k_min"], s["k_max"], xtol=1e-15)
              for s in (NEAR, FAR)]
        for s, k in zip((NEAR, FAR), ks, strict=True):
            assert abs(slice_delta_k(target, s["params"], s["k_min"], s["k_max"]) - k) <= 1e-10
            assert abs(_delta(slice_delta_k(target, s["params"], s["k_min"], s["k_max"]), s["params"]) - target) <= 1e-12
        w1, w2 = (float(svi_w(k, *s["params"])) for s, k in zip((NEAR, FAR), ks, strict=True))
        vols[side] = np.sqrt((w1 + (w2 - w1) * x) / tau)
    theta1, theta2 = (float(svi_w(0.0, *s["params"])) for s in (NEAR, FAR))
    atm = np.sqrt((theta1 + (theta2 - theta1) * x) / tau)
    row, statuses = slice_metrics([FAR, NEAR, LONG], CFG)
    print(row, statuses, vols, atm)
    assert statuses == []
    assert abs(row["atm_30"] - atm) <= 1e-12
    assert abs(row["rr25_30"] - (vols["c"] - vols["p"])) <= 1e-10
    assert abs(row["bf25_30"] - ((vols["c"] + vols["p"]) / 2 - atm)) <= 1e-10
    theta3 = float(svi_w(0.0, *LONG["params"]))
    atm90 = np.sqrt((theta2 + (theta3 - theta2) * (90 / 365 - FAR["T"]) / (LONG["T"] - FAR["T"])) / (90 / 365))
    assert abs(row["atm_90"] - atm90) <= 1e-12 and abs(row["term_slope"] - (atm90 - atm)) <= 1e-12


def test_slice_metrics_no_bracket_and_delta_outside_quotes():
    row, statuses = slice_metrics([NEAR, FAR], CFG)  # nothing reaches 90 days
    assert statuses == ["no_bracket"] and np.isnan(row["atm_90"]) and np.isnan(row["term_slope"])
    assert np.isfinite([row["atm_30"], row["rr25_30"], row["bf25_30"]]).all()
    row, statuses = slice_metrics([FAR, LONG], CFG)  # 30 days lies before the first slice
    assert statuses == ["no_bracket"] and np.isnan([row["atm_30"], row["rr25_30"], row["bf25_30"]]).all()
    narrow = {**NEAR, "k_min": -0.02, "k_max": 0.02}  # the 25-delta strikes lie outside these quotes
    assert np.isnan(slice_delta_k(0.25, narrow["params"], narrow["k_min"], narrow["k_max"]))
    row, statuses = slice_metrics([narrow, FAR, LONG], CFG)
    print(row, statuses)
    assert statuses == ["delta_outside_quotes"] and np.isnan([row["rr25_30"], row["bf25_30"]]).all()
    assert np.isfinite([row["atm_30"], row["atm_90"], row["term_slope"]]).all()
    fit = fit_ssvi([narrow, FAR, LONG][:2], pd.DataFrame(columns=["expiry", "k", "iv"]), CFG)
    full = surface_row([narrow, FAR], fit, CFG)
    assert full["status"] == "too_few_expiries|delta_outside_quotes|no_bracket" and full["n_expiries"] == 2
