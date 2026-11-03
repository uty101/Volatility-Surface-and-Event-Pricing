import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from volsurf.attribution import (
    COMPONENTS,
    attribute_day,
    bs_path_attribution,
    straddle_greeks,
    straddle_value,
)
from volsurf.config import load_config
from volsurf.greeks import greeks
from volsurf.vrp import straddle_mark

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "config.toml")
POS = pd.Series({"strike": 100.0, "side": -1})


def _mark(T, S, vol, r=0.04, carry=0.03):
    return {"T": T, "S": S, "F": S * np.exp(carry * T), "D": np.exp(-r * T), "vol": vol}


@pytest.mark.parametrize("seed", range(20))
def test_identity_exact(seed):
    # the residual is defined as the difference, so only floating point separates the 2 sides
    rng = np.random.default_rng(seed)
    t0 = _mark(0.08, 100 * np.exp(rng.normal(0, 0.05)), rng.uniform(0.1, 0.4))
    t1 = _mark(0.08 - rng.uniform(0.002, 0.012), t0["S"] * np.exp(rng.normal(0, 0.03)),
               t0["vol"] + rng.normal(0, 0.02))
    a = attribute_day(POS, t0, t1)
    assert math.fsum([a[c] for c in COMPONENTS] + [a["residual"]]) == pytest.approx(a["total"], rel=0, abs=1e-12)


def test_bs_path_explained_share_measure():
    # MEASURE (instruction 09 step 9.1): printed for the reviewer, asserts only that it is finite (rule 5)
    rows = bs_path_attribution(CFG)
    share = float(rows["explained_share"].median())
    print(rows[["day", "S", "dS", "dsigma", *COMPONENTS, "residual", "option", "total", "explained_share"]].to_string())
    print(f"MEASURE median explained share, {len(rows)} daily steps: {share:.6f}")
    assert np.isfinite(share)
    assert (rows["dsigma"] == 0).all()


def test_total_is_the_change_in_value_plus_hedge():
    t0, t1 = _mark(0.08, 101.0, 0.2), _mark(0.077, 99.5, 0.215)
    a = attribute_day(POS, t0, t1)
    v0 = straddle_value(t0["F"], 100.0, t0["T"], t0["D"], t0["vol"])
    v1 = straddle_value(t1["F"], 100.0, t1["T"], t1["D"], t1["vol"])
    delta = straddle_greeks(t0["S"], t0["F"], 100.0, t0["T"], t0["D"], t0["vol"])["delta"]
    assert a["option"] == pytest.approx(v0 - v1, rel=1e-14)
    assert a["hedge"] == pytest.approx(delta * (t1["S"] - t0["S"]), rel=1e-14)
    assert a["total"] == pytest.approx(v0 - v1 + delta * (t1["S"] - t0["S"]), rel=1e-14)
    assert a["delta"] + a["hedge"] == 0


def test_theta_reprices_with_only_t_shortened():
    t0, t1 = _mark(0.08, 101.0, 0.2), _mark(0.07, 90.0, 0.5)
    a = attribute_day(POS, t0, t1)
    want = straddle_value(t0["F"], 100.0, 0.07, t0["D"], 0.2) - straddle_value(t0["F"], 100.0, 0.08, t0["D"], 0.2)
    assert a["theta"] == pytest.approx(-want, rel=1e-12)


def test_dsigma_is_the_contract_vol_change():
    # the vol at t1 is already at the shorter T, so a term structure roll with spot and strike fixed shows as dsigma
    a = attribute_day(POS, _mark(0.08, 100.0, 0.20), _mark(0.07, 100.0, 0.23))
    assert a["dsigma"] == pytest.approx(0.03, abs=1e-15)
    assert a["vega"] != 0


@pytest.mark.parametrize("S,K,vol", [(100.0, 100.0, 0.2), (90.0, 100.0, 0.35), (112.0, 100.0, 0.15)])
def test_greeks_match_bsm_call_plus_put(S, K, vol):
    # F = S e^((r - q) T), D = e^(-r T) turn Black-76 into BSM, so the chain rule must give the BSM Greeks
    T, r, q = 0.08, 0.04, 0.01
    g = straddle_greeks(S, S * np.exp((r - q) * T), K, T, np.exp(-r * T), vol)
    c, p = greeks(S, K, T, r, q, vol, "C"), greeks(S, K, T, r, q, vol, "P")
    for name in ("delta", "gamma", "vega", "vanna", "volga"):
        assert g[name] == pytest.approx(float(c[name] + p[name]), rel=1e-10, abs=1e-12)


def test_value_and_delta_match_the_live_mark():
    S, F, K, T, D = 7700.0, 7720.0, 7750.0, 0.08, 0.9966
    ssvi = {"rho": -0.6, "eta": 1.2, "gamma": 0.4}
    thetas = pd.DataFrame({"T": [0.05, 0.12], "theta_used": [0.001, 0.0026]})
    m = straddle_mark(K, F, T, D, S, ssvi, thetas)
    assert straddle_value(F, K, T, D, m["vol"]) == pytest.approx(m["value"], rel=1e-14)
    assert straddle_greeks(S, F, K, T, D, m["vol"])["delta"] == pytest.approx(m["delta"], rel=1e-12)


def test_value_at_expiry_is_intrinsic():
    assert straddle_value(103.0, 100.0, 0.0, 1.0, 0.2) == pytest.approx(3.0)
