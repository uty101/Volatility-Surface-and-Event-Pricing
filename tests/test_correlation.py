import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

from volsurf.config import load_config
from volsurf.correlation import (
    LIVE_COLUMNS,
    RV_COLUMNS,
    STUDY_COLUMNS,
    avg_pairwise_corr,
    cor3m_study,
    implied_correlation,
    live_implied_corr,
    live_weights,
    newey_west,
    rv_screen,
)

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "config.toml")


def _panel(rho: float, n: int, k: int, seed: int) -> np.ndarray:
    """n draws of k equicorrelated standard normals with correlation rho."""
    cov = np.full((k, k), rho) + np.eye(k) * (1 - rho)
    return np.random.default_rng(seed).multivariate_normal(np.zeros(k), cov, size=n)


def test_avg_pairwise_corr_known():
    x = pd.DataFrame(_panel(0.6, 200_000, 3, CFG.run.seed), columns=["A", "B", "C"])
    est = avg_pairwise_corr(x)
    print(f"average pairwise correlation {est!r}, true 0.6")
    assert abs(est - 0.6) <= 5e-3
    # exact on a hand case: B = A, C = -A gives pairs +1, -1, -1
    a = np.array([1.0, 2.0, 0.5, -1.0])
    assert avg_pairwise_corr(pd.DataFrame({"A": a, "B": a, "C": -a})) == pytest.approx(-1 / 3, abs=1e-15)


def test_newey_west_matches_statsmodels():
    rng = np.random.default_rng(CFG.run.seed)
    n = 1500
    x = np.cumsum(rng.normal(size=n)) * 0.01 + 0.4
    e = np.convolve(rng.normal(size=n + 20), np.ones(21) / 21, mode="valid")[:n]  # autocorrelated errors
    y = 0.3 + 0.7 * x + e
    ours = newey_west(y, x, CFG.correlation.nw_maxlags)
    ref = sm.OLS(y, sm.add_constant(x)).fit(cov_type="HAC", cov_kwds={"maxlags": CFG.correlation.nw_maxlags})
    print(ours, ref.params, ref.bse, ref.rsquared)
    assert np.allclose(ours["params"], ref.params, rtol=0, atol=1e-12)
    assert np.allclose(ours["se"], ref.bse, rtol=1e-10, atol=0)
    assert ours["r2"] == pytest.approx(ref.rsquared, abs=1e-12)


def test_cor3m_study_windows_and_columns():
    # 9 sectors on every XNYS session of 2025; COR3M on 3 days, the last without a full forward window
    days = pd.DatetimeIndex(pd.date_range("2025-01-02", "2025-12-31", freq="B"))
    from volsurf.snapshots import _xnys

    days = days[[bool(_xnys().is_session(d)) for d in days]]
    rets = _panel(0.5, len(days), 9, CFG.run.seed) * 0.01
    sectors = pd.DataFrame(100 * np.exp(np.cumsum(rets, axis=0)), index=days, columns=list(CFG.universe.sector_spdrs))
    cor3m = pd.Series([40.0, 45.0, 50.0], index=[days[0], days[1], days[-10]])
    cor3m = pd.concat([cor3m, pd.Series([55.0], index=[days[2]])]).sort_index()
    out = cor3m_study(cor3m, sectors, 63, 5)
    print({k: v for k, v in out.items() if k != "series"})
    assert set(STUDY_COLUMNS) <= set(out)
    assert out["n"] == 3 and out["first_t"] == days[0].strftime("%Y-%m-%d")  # days[-10] has no full window
    s = out["series"]
    assert s.loc[0, "implied"] == 0.40
    expected = avg_pairwise_corr(np.log(sectors).diff().iloc[1:64])  # sessions t+1 to t+63 after days[0]
    assert s.loc[0, "realised"] == pytest.approx(expected, abs=1e-15)
    assert out["mean_gap"] == pytest.approx((s["implied"] - s["realised"]).mean(), abs=1e-15)
    assert "not a correlation risk premium" in out["gap_note"]


def test_implied_correlation_hand_value():
    # 2 names, w = (0.6, 0.4), sig = (0.30, 0.20), sig_I = 0.22:
    # own = 0.36 x 0.09 + 0.16 x 0.04 = 0.0388; cross = 2 x 0.6 x 0.4 x 0.30 x 0.20 = 0.0288
    # rho = (0.0484 - 0.0388) / 0.0288 = 0.3333...
    sig = pd.Series({"A": 0.30, "B": 0.20})
    w = pd.Series({"A": 0.6, "B": 0.4})
    assert implied_correlation(0.22, sig, w) == pytest.approx((0.0484 - 0.0388) / 0.0288, abs=1e-14)
    # perfect correlation: sig_I = sum w_i sig_i gives rho = 1
    assert implied_correlation(0.6 * 0.30 + 0.4 * 0.20, sig, w) == pytest.approx(1.0, abs=1e-14)
    assert math.isnan(implied_correlation(0.22, sig.iloc[:1], w))


def test_weights_renormalised_and_covered_weight():
    weights = pd.Series({"A": 0.30, "B": 0.20, "C": 0.10, "D": 0.05})  # D is not captured, C has no vol
    sig = pd.Series({"A": 0.30, "B": 0.20, "C": np.nan})
    w, covered = live_weights(weights, sig)
    assert covered == pytest.approx(0.50, abs=1e-15)
    assert w.to_dict() == pytest.approx({"A": 0.6, "B": 0.4}, abs=1e-15)
    assert implied_correlation(0.22, sig, weights) == implied_correlation(0.22, sig.iloc[:2], w)
    surface = pd.DataFrame({"day": ["2026-10-29"] * 4 + ["2026-10-30"] * 3,
                            "ticker": ["XLK", "A", "B", "C", "A", "B", "C"],
                            "atm_30": [0.22, 0.30, 0.20, np.nan, 0.31, 0.21, 0.25]})
    live = live_implied_corr(surface, weights, "2026-11-02", CFG)
    print(live.to_string())
    assert list(live.columns) == LIVE_COLUMNS
    r = live.set_index("day")
    assert r.loc["2026-10-29", "covered_weight"] == pytest.approx(0.50, abs=1e-15)
    assert r.loc["2026-10-29", "n_names"] == 2
    assert r.loc["2026-10-29", "implied_corr"] == pytest.approx((0.0484 - 0.0388) / 0.0288, abs=1e-14)
    assert r.loc["2026-10-29", "status"] == "pending"  # 21 sessions after 10-29 are not in the price data
    assert r.loc["2026-10-30", "covered_weight"] == pytest.approx(0.60, abs=1e-15)
    assert r.loc["2026-10-30", "status"] == "no_index_vol|pending" and np.isnan(r.loc["2026-10-30", "implied_corr"])
    assert r[["realised_index_vol", "realised_implied_corr", "realised_avg_pairwise_corr"]].isna().all(axis=None)


def test_rv_screen_blank_below_min_days():
    n = CFG.correlation.rv_min_days
    days = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2026-01-02", periods=n + 2)]
    vols = 0.20 + 0.01 * np.sin(np.arange(n + 2))
    surface = pd.concat([pd.DataFrame({"day": d, "ticker": ["NVDA", "AAPL", "AMD", "SPY"],
                                       "atm_30": [v, 0.25, np.nan if i == 0 else 0.40, 0.15]})
                         for i, (d, v) in enumerate(zip(days, vols, strict=True))], ignore_index=True)
    rv = rv_screen(surface, CFG)
    print(rv[rv["ticker"] == "NVDA"].to_string())
    assert list(rv.columns) == RV_COLUMNS
    nv = rv[rv["ticker"] == "NVDA"].reset_index(drop=True)
    assert (nv.loc[:n - 1, "status"] == "below_min_days").all() and nv.loc[:n - 1, "zscore"].isna().all()
    assert (nv.loc[n:, "status"] == "ok").all() and nv["n_prior"].tolist() == list(range(n + 2))
    expected = (vols[n] - vols[:n].mean()) / vols[:n].std(ddof=1)  # O-15 (a): prior days only, ddof 1
    assert nv.loc[n, "zscore"] == pytest.approx(expected, abs=1e-12)
    # group median from day 1: NVDA, AAPL, AMD are xlk_holdings; AMD has no vol on day 1
    first = rv[rv["day"] == days[0]].set_index("ticker")
    assert first.loc["NVDA", "group_median"] == pytest.approx((vols[0] + 0.25) / 2, abs=1e-15)
    assert first.loc["AMD", "status"] == "no_vol" and np.isnan(first.loc["AMD", "vol_minus_group_median"])
    assert first.loc["SPY", "vol_minus_group_median"] == 0.0 and first.loc["SPY", "group"] == "etfs"
    assert rv.loc[rv["ticker"] == "AMD", "n_prior"].tolist()[-1] == n  # the blank day is not a prior day
