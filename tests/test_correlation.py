import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

from volsurf.config import load_config
from volsurf.correlation import (
    STUDY_COLUMNS,
    avg_pairwise_corr,
    cor3m_study,
    implied_correlation,
    newey_west,
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

