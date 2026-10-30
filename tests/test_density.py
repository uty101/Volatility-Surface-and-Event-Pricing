from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy.integrate import cumulative_trapezoid

from volsurf.config import load_config
from volsurf.density import (
    density_check,
    density_k,
    fd_density,
    k_grid,
    prob_above,
    prob_below,
    svi_density,
    tail_table,
)
from volsurf.svi import ACCEPTED, PARAMS, svi_g

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "config.toml")
TRUE = (0.02, 0.15, -0.4, 0.05, 0.2)
VOGT = (-0.0410, 0.1331, 0.3060, 0.3586, 0.4153)  # Gatheral and Jacquier 2014, Section 5.1: fails butterfly


@pytest.fixture(scope="module")
def accepted(fixture_fits) -> pd.DataFrame:
    """Accepted fixture slices with their density integral and mean checks (instruction 05 part C)."""
    acc = fixture_fits[fixture_fits["status"].isin(ACCEPTED)].reset_index(drop=True)
    checks = pd.DataFrame([density_check(p, F, CFG) for p, F in
                           zip(acc[PARAMS].itertuples(index=False), acc["F"], strict=True)])
    return pd.concat([acc[["ticker", "expiry", "T", "F", "r", "k_min", "k_max", *PARAMS]], checks], axis=1)


def test_integrates_to_one(accepted):
    print(accepted[["ticker", "expiry", "T", "integral", "int_err", "tail_mass"]].to_string())
    err = accepted["int_err"].abs()
    print(err.groupby(accepted["ticker"], sort=False).agg(["max", "median"]).to_string())
    assert (err <= CFG.density.int_tol).all()


def test_mean_equals_forward(accepted):
    print(accepted[["ticker", "expiry", "T", "F", "mean", "mean_rel_err"]].to_string())
    err = accepted["mean_rel_err"].abs()
    print(err.groupby(accepted["ticker"], sort=False).agg(["max", "median"]).to_string())
    assert (err <= CFG.density.int_tol).all()


def test_nonnegative_when_butterfly_passes(accepted):
    # the density is g times a positive factor, so q >= 0 wherever g >= 0; every accepted slice passed the
    # butterfly check, and on the integration grid g stays at or above the same -1e-10
    min_g = [float(svi_g(k_grid(p, CFG), p).min())
             for p in accepted[PARAMS].itertuples(index=False)]
    print(pd.DataFrame({"ticker": accepted["ticker"], "expiry": accepted["expiry"], "min_g_int": min_g,
                        "min_density": accepted["min_density"]}).to_string())
    assert min(min_g) >= -1e-10
    assert (accepted["min_density"] >= 0).all()
    k = k_grid(VOGT, CFG)
    assert density_k(k, VOGT).min() < 0  # a slice that fails the butterfly check has a negative density
    assert density_k(k_grid(TRUE, CFG), TRUE).min() >= 0


def test_svi_density_is_p_k_over_k():
    F, K = 100.0, np.linspace(60.0, 150.0, 7)
    np.testing.assert_allclose(svi_density(K, F, 0.5, TRUE), density_k(np.log(K / F), TRUE) / K, rtol=1e-15)


def test_prob_above_matches_integrated_density():
    # O-35 (a): the closed-form P(S_T > x) is the integral of the density; against a cumulative trapezoid integral on
    # the sinh grid, started from the closed-form mass below -k_check
    k = k_grid(TRUE, CFG)
    F = 100.0
    cdf = prob_below(F * np.exp(k[0]), F, TRUE) + cumulative_trapezoid(density_k(k, TRUE), k, initial=0.0)
    x = F * np.exp(k[::20000])
    gap = np.abs(prob_below(x, F, TRUE) - cdf[::20000]).max()
    print(f"largest |closed form - trapezoid| {gap:.3g}")
    assert gap <= CFG.density.int_tol
    np.testing.assert_allclose(prob_above(x, F, TRUE) + prob_below(x, F, TRUE), 1.0, rtol=0, atol=1e-15)


def test_analytic_vs_fd(accepted):
    # instruction 05b part C (was MEASURE): analytic density against e^(rT) d2C/dK2 with step bl_dk x F, on 2,001
    # strikes over each accepted fixture slice's quoted range; the largest gap is <= 5e-3 x the slice's peak density
    # on the quoted range
    rows = []
    for r in accepted.itertuples():
        p = tuple(getattr(r, c) for c in PARAMS)
        K = r.F * np.exp(np.linspace(r.k_min, r.k_max, 2001))
        q = svi_density(K, r.F, r.T, p)
        q_fd = fd_density(K, r.F, r.T, np.exp(-r.r * r.T), p, CFG.density.bl_dk * r.F)
        gap = np.abs(q - q_fd)
        i = int(np.argmax(gap))
        rows.append({"ticker": r.ticker, "expiry": r.expiry, "T": r.T, "max_abs_gap": gap[i], "K_at_max": K[i],
                     "q_at_max": q[i], "max_rel_gap_to_peak": gap.max() / q.max()})
    table = pd.DataFrame(rows)
    print(table.to_string())
    worst = table.loc[table["max_abs_gap"].idxmax()]
    print(f"largest |q - q_fd| {worst['max_abs_gap']!r} ({worst['ticker']} {worst['expiry']}); "
          f"largest gap relative to peak density {table['max_rel_gap_to_peak'].max()!r}")
    assert np.isfinite(table[["max_abs_gap", "max_rel_gap_to_peak"]].to_numpy()).all()
    assert (table["max_rel_gap_to_peak"] <= 5e-3).all()


def test_tail_table_extrapolated_flag():
    F, k_range = 100.0, (-0.06, 0.04)  # quotes from K = 94.18 to 104.08
    table = tail_table(TRUE, F, 0.5, k_range, CFG.density.moves)
    print(table.to_string())
    assert list(table.columns) == ["measure", "move", "x", "prob", "extrapolated"]
    assert len(table) == 5 * len(CFG.density.moves)
    flag = table.set_index(["measure", "move"])["extrapolated"]
    assert not flag[("below", -0.025)] and not flag[("above", 0.025)] and not flag[("abs_log", 0.025)]
    assert not flag[("below", -0.05)] and flag[("above", 0.05)] and flag[("abs_log", 0.05)]  # 105 > 104.08
    assert flag[("below", -0.10)] and flag[("above", 0.20)]
    assert table["prob"].between(0, 1).all()


def test_density_check_tail_mass_and_status():
    # instruction 05b B4: the integral adds the closed-form mass beyond +-k_check; a slice that misses int_tol is
    # density_fail (O-36 (a))
    F = 100.0
    out = density_check(TRUE, F, CFG)
    print(out)
    k = k_grid(TRUE, CFG)
    tail = prob_below(F * np.exp(k[0]), F, TRUE) + prob_above(F * np.exp(k[-1]), F, TRUE)
    assert out["tail_mass"] == tail and out["density_status"] == "ok"
    assert abs(out["int_err"]) <= 1e-9 and abs(out["mean_rel_err"]) <= 1e-6
    flat_wing = (0.0, 1.0, 0.999, 0.0, 0.1)  # right wing slope b (1 + rho) = 1.999 > 1.98: the mean leaks (41%)
    leak = density_check(flat_wing, F, CFG)
    print(leak)
    assert leak["density_status"] == "density_fail" and abs(leak["mean_rel_err"]) > CFG.density.int_tol
