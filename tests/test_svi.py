from pathlib import Path

import numpy as np
import pandas as pd

from volsurf.config import load_config
from volsurf.data import SPX
from volsurf.svi import (
    ACCEPTED,
    PARAMS,
    butterfly_grid,
    calendar_violations,
    check_grid,
    fit_svi,
    neighbour_starts,
    svi_g,
    svi_w,
)

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "config.toml")
TRUE = (0.02, 0.15, -0.4, 0.05, 0.2)
# Axel Vogt's raw SVI slice (Gatheral and Jacquier 2014, Section 5.1): negative density near the money
VOGT = (-0.0410, 0.1331, 0.3060, 0.3586, 0.4153)


def test_recovers_known_params():
    # k over [-2, 2] so the wings pin b and rho: at ftol 1e-14 (instruction 04 part B) narrower grids stop
    # with a, b, rho and s traded off against each other at about 1e-5 (review/section_4.md)
    T = 0.5
    k = np.linspace(-2.0, 2.0, 161)
    fit = fit_svi(k, np.sqrt(svi_w(k, *TRUE) / T), T, CFG)
    print(fit)
    assert fit["status"] == "ok" and not fit["refit"]
    np.testing.assert_allclose(fit["params"], TRUE, rtol=0, atol=1e-6)


def test_g_analytic_vs_fd():
    k = np.linspace(-1.0, 1.0, 201)
    h = 1e-4
    for params in (TRUE, VOGT):
        w = svi_w(k, *params)
        w1 = (svi_w(k + h, *params) - svi_w(k - h, *params)) / (2 * h)
        w2 = (svi_w(k + h, *params) - 2 * w + svi_w(k - h, *params)) / h**2
        g_fd = (1 - k * w1 / (2 * w)) ** 2 - (w1**2 / 4) * (1 / w + 0.25) + w2 / 2
        gap = np.abs(svi_g(k, params) - g_fd).max()
        print(f"{params}: largest |g - g_fd| {gap:.3g}")
        assert gap <= 1e-6


def test_arbitrageable_params_fail_butterfly():
    grid = butterfly_grid(np.array([-0.5, 0.5]), CFG)
    assert svi_g(grid, VOGT).min() < -1e-10
    assert svi_g(grid, TRUE).min() >= -1e-10


def test_calendar_flags_crossing_pair():
    grid = np.linspace(-1.0, 1.0, CFG.svi.grid_points)
    near = {"expiry": "near", "T": 0.25, "params": (0.01, 0.1, -0.5, 0.0, 0.1)}
    far = {"expiry": "far", "T": 0.5, "params": (0.02, 0.1, -0.5, 0.0, 0.1)}  # w shifted up: no crossing
    cross = {"expiry": "cross", "T": 0.5, "params": (0.0, 0.2, -0.9, 0.0, 0.1)}  # below near on the put wing
    ok = calendar_violations([far, near], grid)
    assert list(ok[["expiry_1", "expiry_2"]].iloc[0]) == ["near", "far"] and not ok["violated"].any()
    bad = calendar_violations([near, cross], grid)
    print(bad.to_string())
    assert bad["violated"].iloc[0] and bad["n_violations"].iloc[0] > 0 and bad["min_diff"].iloc[0] < -1e-10


def test_too_few_status():
    T = 0.5
    k = np.linspace(-0.3, 0.3, CFG.svi.min_quotes - 1)
    fit = fit_svi(k, np.sqrt(svi_w(k, *TRUE) / T), T, CFG)
    assert fit["status"] == "too_few" and fit["n_quotes"] == CFG.svi.min_quotes - 1
    assert np.isnan(fit["params"]).all() and np.isnan(fit["rmse_vol"])


def test_fixture_accepted_slices(fixture_fits):
    # instruction 04b part B: per fixture ticker, accepted (ok plus ok_refit) slices / slices with at least
    # min_quotes quotes >= [svi] min_accept_share; slices fitted per ticker with the neighbour retry (instruction 05)
    table = fixture_fits
    print(table.to_string())
    print(pd.crosstab(table["ticker"], [table["status"], table["route"]]).to_string())
    fitted = table[table["n_quotes"] >= CFG.svi.min_quotes]
    share = pd.DataFrame({"accepted": fitted["status"].isin(ACCEPTED).groupby(fitted["ticker"], sort=False).sum(),
                          "fitted": fitted.groupby("ticker", sort=False).size()})
    share["share"] = share["accepted"] / share["fitted"]
    print(share.to_string())
    print(table.loc[table["status"] != "ok", ["ticker", "expiry", "T", "n_quotes", "refit", "exit", "route",
                                              "cut_rounds", "rmse_volpts", "min_g", "status"]].to_string())
    assert set(share.index) == {SPX, "SPY", "AAPL"}
    assert (share["share"] >= CFG.svi.min_accept_share).all(), share


def test_fixture_accepted_wing_and_wide_grid(fixture_fits):
    # instruction 05 step 5.0 item 2, with instruction 05b part B: every accepted fixture slice has b (1 + |rho|) <= 2
    # (and <= wing_max = 1.98) and min g >= -1e-10 on the acceptance grid (the 200,001-point sinh grid)
    acc = fixture_fits[fixture_fits["status"].isin(ACCEPTED)].copy()
    acc["wing"] = acc["b"] * (1 + acc["rho"].abs())
    acc["min_g_check"] = [float(svi_g(check_grid(p, CFG, CFG.density.int_points), p).min())
                          for p in acc[PARAMS].itertuples(index=False)]
    print(acc[["ticker", "expiry", "T", "wing", "min_g_check", "route", "cut_rounds"]].to_string())
    print(f"largest wing {acc['wing'].max()!r}, smallest min g {acc['min_g_check'].min()!r}")
    assert (acc["wing"] <= 2.0).all() and (acc["wing"] <= CFG.svi.wing_max).all()
    assert (acc["min_g_check"] >= -1e-10).all()


def test_check_grid_sinh_span():
    # instruction 05b B1: k = m + s sinh(u), u evenly spaced, over [-k_check, k_check]; s floored at s_min
    a, b, rho, m, s = TRUE
    grid = check_grid(TRUE, CFG, CFG.svi.grid_points)
    assert len(grid) == CFG.svi.grid_points == 801
    np.testing.assert_allclose(grid[[0, -1]], [-CFG.svi.k_check, CFG.svi.k_check], rtol=0, atol=1e-12)
    np.testing.assert_allclose(np.diff(np.arcsinh((grid - m) / s)), np.diff(np.arcsinh((grid - m) / s))[0], rtol=1e-9)
    step = np.diff(grid)
    assert step[np.argmin(np.abs(grid[:-1] - m))] < step[0] / 20  # dense near m (0.0023 against 0.115 at the ends)
    floored = check_grid((a, b, rho, m, 0.0), CFG, 5)
    np.testing.assert_allclose(floored, m + CFG.svi.s_min * np.sinh(
        np.linspace(np.arcsinh((-10 - m) / 1e-4), np.arcsinh((10 - m) / 1e-4), 5)), rtol=1e-15)


def test_qqq_short_slice_never_accepted_with_negative_g():
    # instruction 05b step 5b.1: QQQ 2026-11-03 on 2026-10-29 (g = -1.19 at k = -0.94 in session 5) is either
    # accepted with min g >= -1e-10 or rejected; checked on the acceptance grid and on a uniform grid of 2,000,001
    # points over [-10, 10]
    q = pd.read_csv(ROOT / "tests" / "fixtures" / "qqq_2026-11-03_iv.csv")
    fit = fit_svi(np.log(q["strike"] / q["F"]), q["iv"], float(q["T"].iloc[0]), CFG)
    print({k: fit[k] for k in ("status", "route", "exit", "rmse_volpts", "min_g", "cut_rounds", "params")})
    if fit["status"] in ACCEPTED:
        dense = np.linspace(-CFG.svi.k_check, CFG.svi.k_check, 2_000_001)
        with np.errstate(divide="ignore", invalid="ignore"):
            g = np.concatenate([svi_g(dense, fit["params"]),
                                svi_g(check_grid(fit["params"], CFG, CFG.density.int_points), fit["params"])])
        print(f"smallest g on the 2 grids {np.nanmin(g)!r}")
        assert np.isfinite(g).all() and g.min() >= -1e-10 and fit["min_g"] >= -1e-10
    else:
        assert fit["status"] in ("poor_fit", "butterfly_fail")


def test_neighbour_starts_scale_a_and_b():
    # instruction 05 correction 3: the 3 nearest accepted expiries, a and b scaled by T / T_neighbour
    accepted = [(0.1, (0.01, 0.1, -0.5, 0.0, 0.1)), (0.2, (0.02, 0.2, -0.6, 0.01, 0.2)),
                (0.4, (0.04, 0.3, -0.7, 0.02, 0.3)), (0.8, (0.08, 0.4, -0.8, 0.03, 0.4))]
    starts = neighbour_starts(0.3, accepted, CFG.svi.neighbour_retries)
    print(starts)
    assert len(starts) == 3
    np.testing.assert_allclose(starts[0], (0.03, 0.3, -0.6, 0.01, 0.2), rtol=1e-15)  # 0.2 and 0.4 tie: 0.2 first
    np.testing.assert_allclose(starts[1], (0.03, 0.225, -0.7, 0.02, 0.3), rtol=1e-15)
    np.testing.assert_allclose(starts[2], (0.03, 0.3, -0.5, 0.0, 0.1), rtol=1e-15)


def test_calendar_only_inside_quoted_overlap():
    # instruction 05 step 5.0 item 4: w_cross - w_near = 0.01 + 0.1 k crosses only on the put wing (k < -0.1); with
    # quoted ranges that overlap only on k >= 0.1 the pair is not a violation, and over all of the grid it is
    grid = np.linspace(-1.0, 1.0, CFG.svi.grid_points)
    near = {"expiry": "near", "T": 0.25, "params": (0.01, 0.1, -0.5, 0.0, 0.1), "k_min": -0.5, "k_max": 0.5}
    cross = {"expiry": "cross", "T": 0.5, "params": (0.02, 0.1, 0.5, 0.0, 0.1), "k_min": 0.1, "k_max": 0.9}
    diff = svi_w(grid, *cross["params"]) - svi_w(grid, *near["params"])
    assert (diff[grid >= 0.1] > 0).all() and (diff[grid < 0] < -1e-10).any()
    row = calendar_violations([near, cross], grid).iloc[0]
    print(row.to_string())
    assert not row["violated"] and row["n_violations"] == 0
    assert row["n_grid"] == int(((grid >= 0.1) & (grid <= 0.5)).sum())
    disjoint = calendar_violations([near, {**cross, "k_min": 0.6}], grid).iloc[0]
    assert disjoint["n_grid"] == 0 and not disjoint["violated"] and np.isnan(disjoint["min_diff"])
    unbounded = calendar_violations([{k: v for k, v in s.items() if not k.startswith("k_")} for s in (near, cross)],
                                    grid).iloc[0]
    assert unbounded["violated"] and unbounded["n_grid"] == len(grid)
