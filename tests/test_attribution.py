import dataclasses
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from volsurf.attribution import (
    ATTRIBUTION_COLUMNS,
    COMPONENTS,
    HEDGING_COLUMNS,
    attribute_day,
    attribute_live,
    bs_path_attribution,
    hedge_run,
    heston_paths,
    heston_straddle_price,
    simulate_hedging,
    straddle_delta,
    straddle_greeks,
    straddle_value,
)
from volsurf.config import load_config
from volsurf.greeks import greeks
from volsurf.pricing import bsm
from volsurf.vrp import live_straddles, straddle_mark

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


def _small(paths):
    return dataclasses.replace(CFG, sim=dataclasses.replace(CFG.sim, paths=paths))


def _live_frame():
    days = ["2026-10-28", "2026-10-29", "2026-11-02"]
    expiry = "2026-11-27"
    quotes = pd.DataFrame({"day": days, "expiry": expiry, "strike": 7700.0, "T": [0.0822, 0.0795, 0.0685],
                           "S": [7700.0, 7640.0, 7690.0], "F": [7720.0, 7658.0, 7706.0], "r": 0.04})
    quotes = pd.concat([quotes, quotes.assign(strike=7650.0)], ignore_index=True)
    surface = pd.DataFrame({"day": days, "ssvi_rho": [-0.6, -0.65, -0.62], "ssvi_eta": 1.2, "ssvi_gamma": 0.4})
    thetas = pd.DataFrame({"day": np.repeat(days, 2), "T": [0.05, 0.12] * 3,
                           "theta_used": [0.001, 0.0026, 0.0012, 0.003, 0.0011, 0.0027]})
    return live_straddles(days, quotes, surface, thetas, 30)


def test_attribute_live_matches_live_straddles():
    live = _live_frame()
    table = attribute_live(live)
    assert list(table.columns) == ATTRIBUTION_COLUMNS
    assert len(table) == 3  # opened on 3 days: 2 moves, 1 move, no move
    first = live[live["open_day"] == "2026-10-28"]
    rows = table[table["open_day"] == "2026-10-28"]
    assert rows["total"].to_numpy() == pytest.approx(first["total_pnl"].diff().iloc[1:].to_numpy(), rel=1e-12)
    assert rows["option"].to_numpy() == pytest.approx(first["option_pnl"].diff().iloc[1:].to_numpy(), rel=1e-12)
    assert rows["hedge"].to_numpy() == pytest.approx(first["hedge_pnl"].diff().iloc[1:].to_numpy(), rel=1e-12)
    assert rows["dt"].to_numpy() == pytest.approx(-first["T"].diff().iloc[1:].to_numpy(), rel=1e-12)
    assert rows["dsigma"].to_numpy() == pytest.approx(first["vol"].diff().iloc[1:].to_numpy(), rel=1e-12)


def test_attribute_live_skips_rows_with_no_value():
    live = _live_frame()
    live.loc[(live["open_day"] == "2026-10-28") & (live["mark_day"] == "2026-10-29"), "status"] = "no_surface"
    rows = attribute_live(live)
    rows = rows[rows["open_day"] == "2026-10-28"]
    assert rows[["day0", "day1"]].to_numpy().tolist() == [["2026-10-28", "2026-11-02"]]


def test_simulation_deterministic():
    cfg = _small(500)
    for model in ("gbm", "heston"):
        a, b = simulate_hedging(model, cfg), simulate_hedging(model, cfg)
        assert list(a.columns) == HEDGING_COLUMNS
        pd.testing.assert_frame_equal(a, b, check_exact=True)


def test_more_frequent_hedging_lower_error_gbm():
    t = simulate_hedging("gbm", _small(5000))
    assert t["hedge_every_steps"].tolist() == list(CFG.sim.hedge_every_steps)
    assert t["error_sd"].is_monotonic_increasing  # rows run from the most frequent hedge to the least
    assert t["cost_mean"].is_monotonic_decreasing


def test_unknown_model_raises():
    with pytest.raises(ValueError):
        simulate_hedging("sabr", _small(10))


def test_hedge_run_by_hand():
    S = np.array([[100.0], [110.0], [121.0]])
    vol = np.full(3, 0.2)
    d0 = float(straddle_delta(100.0, 100.0, 1.0, 0.0, 0.2))
    d1 = float(straddle_delta(110.0, 100.0, 0.5, 0.0, 0.2))
    error, cost = hedge_run(S, vol, 100.0, 1.0, 0.0, 15.0, 1, 1.0)
    cash = 15.0 - d0 * 100 - (d1 - d0) * 110
    assert error[0] == pytest.approx(cash + d1 * 121 - 21)
    assert cost[0] == pytest.approx(1e-4 * (abs(d0) * 100 + abs(d1 - d0) * 110))
    error, cost = hedge_run(S, vol, 100.0, 1.0, 0.0, 15.0, 2, 1.0)  # step 2 is expiry: only step 0 trades
    assert error[0] == pytest.approx(15.0 - d0 * 100 + d0 * 121 - 21)
    assert cost[0] == pytest.approx(1e-4 * abs(d0) * 100)


def test_cash_accrues_at_r():
    S = np.array([[100.0], [100.0], [100.0]])
    d0 = float(straddle_delta(100.0, 100.0, 1.0, 0.1, 0.2))
    error, _ = hedge_run(S, np.full(3, 0.2), 100.0, 1.0, 0.1, 10.0, 2, 0.0)
    assert error[0] == pytest.approx((10.0 - d0 * 100) * np.exp(0.1) + d0 * 100)


def test_straddle_delta_is_call_plus_put_delta():
    c, p = greeks(95.0, 100.0, 0.05, 0.04, 0.0, 0.25, "C"), greeks(95.0, 100.0, 0.05, 0.04, 0.0, 0.25, "P")
    assert straddle_delta(95.0, 100.0, 0.05, 0.04, 0.25) == pytest.approx(float(c["delta"] + p["delta"]), rel=1e-12)


def test_straddle_delta_at_zero_vol_is_the_limit():
    assert straddle_delta(np.array([101.0, 99.0]), 100.0, 0.05, 0.0, np.zeros(2)).tolist() == [1.0, -1.0]


def test_heston_price_with_tiny_vol_of_vol_is_bsm():
    h = dataclasses.replace(CFG.sim.heston, xi=1e-3, rho=0.0)
    T = CFG.sim.days / 252
    want = float(sum(bsm(h.s0, h.s0, T, h.r, 0.0, np.sqrt(h.v0), k) for k in "CP"))
    assert heston_straddle_price(h, h.s0, CFG.sim.days) == pytest.approx(want, rel=1e-4)


def test_heston_paths_truncate_and_stay_finite():
    n, dt = 273, 1 / (252 * 13)
    S, vol = heston_paths(CFG.sim.heston, n, dt, 2000, np.random.default_rng(CFG.run.seed))
    assert S.shape == vol.shape == (n + 1, 2000)
    assert np.isfinite(S).all() and (S > 0).all() and (vol >= 0).all()
    assert vol[0] == pytest.approx(np.sqrt(CFG.sim.heston.v0))
