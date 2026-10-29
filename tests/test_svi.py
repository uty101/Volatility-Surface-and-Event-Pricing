from datetime import date
from functools import cache
from pathlib import Path

import numpy as np
import pandas as pd

from volsurf.config import load_config
from volsurf.data import RATE_TENORS, SPX
from volsurf.forwards import clean_with_forwards
from volsurf.iv import iv_chain, iv_inputs
from volsurf.svi import (
    ACCEPTED,
    PARAMS,
    butterfly_grid,
    calendar_violations,
    fit_svi,
    svi_g,
    svi_w,
)

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "config.toml")
FIXTURE_DAY = date(2026, 10, 28)  # instruction 01d part B
MIN_ACCEPTED = {SPX: 28, "SPY": 23, "AAPL": 13}  # instruction 04 step 4.1
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


@cache
def fixture_iv() -> pd.DataFrame:
    """The fixture day's OTM IV table (PLAN 3.3), built from the committed fixture and data/raw."""
    chains = pd.read_parquet(ROOT / "tests" / "fixtures" / "chains_sample.parquet")
    underlying = pd.read_csv(ROOT / "tests" / "fixtures" / "underlying_sample.csv")
    fred = {sid: pd.read_csv(ROOT / "data" / "raw" / "fred" / f"{sid}.csv") for sid in RATE_TENORS}
    divs = pd.read_csv(ROOT / "data" / "raw" / "prices" / "dividends.csv")
    clean, _, forwards = clean_with_forwards(chains, underlying, fred, FIXTURE_DAY, CFG)
    return iv_chain(iv_inputs(clean, underlying, fred, divs, forwards, FIXTURE_DAY, CFG), CFG)


def test_fixture_accepted_slices():
    # instruction 04 step 4.1: accepted (ok plus ok_refit) slices on the fixture day, per ticker
    iv = fixture_iv()
    iv = iv[iv["iv"].notna()]
    rows = []
    for (ticker, expiry), g in iv.groupby(["ticker", "expiry"], sort=False):
        fit = fit_svi(np.log(g["strike"] / g["F"]), g["iv"], g["T"].iloc[0], CFG)
        rows.append({"ticker": ticker, "expiry": expiry, "T": g["T"].iloc[0], "n_quotes": fit["n_quotes"],
                     **dict(zip(PARAMS, fit["params"], strict=True)), "rmse_volpts": fit["rmse_volpts"],
                     "min_g": fit["min_g"], "refit": fit["refit"], "status": fit["status"]})
    table = pd.DataFrame(rows)
    print(table.to_string())
    print(pd.crosstab(table["ticker"], table["status"]).to_string())
    accepted = table[table["status"].isin(ACCEPTED)].groupby("ticker").size()
    for ticker, bound in MIN_ACCEPTED.items():
        assert accepted.get(ticker, 0) >= bound, (ticker, int(accepted.get(ticker, 0)), bound)
