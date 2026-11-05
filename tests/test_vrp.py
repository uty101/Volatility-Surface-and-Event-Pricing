import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm

from volsurf.config import load_config
from volsurf.pricing import black76
from volsurf.vrp import (
    SPEC_COLUMNS,
    STRATEGY_COLUMNS,
    VRP_COLUMNS,
    append_spec,
    deflated_sharpe,
    expected_max_sharpe,
    family_table,
    garch_monthly_forecasts,
    level_at,
    log_returns,
    month_ends,
    probabilistic_sharpe,
    realised_var,
    series_moments,
    spec_signals,
    straddle_mark,
    strategy_returns,
    timed_positions,
    vrp_monthly,
)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CFG = load_config(ROOT / "config.toml")


def _gspc() -> pd.Series:
    return pd.read_parquet(RAW / "prices" / "index.parquet")["^GSPC"]


def test_realised_var_constant_returns():
    h = CFG.vrp.horizon
    r = pd.Series(0.01, index=pd.bdate_range("2026-01-01", periods=60))
    rv = realised_var(r, h)
    assert rv.iloc[: 60 - h].to_numpy() == pytest.approx(252 * 0.01**2, rel=1e-14)  # (252 / h) x h x 0.01^2
    assert rv.iloc[60 - h:].isna().all()  # fewer than h returns follow
    # one shock at position 30 enters the windows of t = 9 to 29 only (r_{t+1} .. r_{t+21})
    r2 = r.copy()
    r2.iloc[30] = 0.05
    d = realised_var(r2, h) - rv
    assert (d.iloc[9:30] > 0).all() and (d.iloc[:9] == 0).all() and (d.iloc[30:60 - h] == 0).all()


def test_garch_no_lookahead():
    """PLAN 8.1: the forecast at a month end uses no data after it; truncating the returns at that month end and
    refitting gives the same number."""
    r = log_returns(_gspc(), CFG.vrp.start)
    r = r[r.index <= "1994-04-29"]
    full = garch_monthly_forecasts(r, CFG.vrp.horizon, CFG.vrp.garch_min_obs)
    cut = garch_monthly_forecasts(r[r.index <= "1994-02-28"], CFG.vrp.horizon, CFG.vrp.garch_min_obs)
    print(pd.DataFrame({"full": full, "truncated": cut}).dropna(how="all").to_string())
    assert full.dropna().index[0] == pd.Timestamp("1993-12-31")  # the first month end with 1,000 returns
    for m in ["1993-12-31", "1994-01-31", "1994-02-28"]:
        assert cut[pd.Timestamp(m)] == full[pd.Timestamp(m)]
    assert full[pd.Timestamp("1994-03-31")] != full[pd.Timestamp("1994-02-28")]


def test_month_ends_completed_only():
    """Instruction 08 point 1: the current, incomplete month is never a month end."""
    s = pd.DatetimeIndex(_gspc().index)
    ends = month_ends(s[s <= "2026-11-02"])
    assert ends[-1] == pd.Timestamp("2026-10-30") and ends[-2] == pd.Timestamp("2026-09-30")
    assert month_ends(s[s <= "2026-10-30"])[-1] == pd.Timestamp("2026-10-30")  # 10-30 is October's last session
    assert month_ends(s[s <= "2026-10-29"])[-1] == pd.Timestamp("2026-09-30")
    assert pd.Timestamp("2002-03-28") in month_ends(s)  # Good Friday 2002-03-29 is not a session


def test_level_on_or_before():
    """Instruction 08 point 2: the last available close on or before the session."""
    x = pd.Series([1.0, np.nan, 3.0], index=pd.to_datetime(["2026-10-27", "2026-10-29", "2026-11-02"]))
    got = level_at(x, pd.DatetimeIndex(["2026-10-27", "2026-10-30", "2026-11-02"]))
    assert got.tolist() == [1.0, 1.0, 3.0]


def test_vrp_monthly_schema_and_identities():
    g = _gspc()
    g = g[pd.DatetimeIndex(g.index) <= "1994-06-30"]
    vix = pd.read_csv(RAW / "cboe" / "VIX.csv")
    vix = pd.Series(vix["CLOSE"].to_numpy(), index=pd.to_datetime(vix["DATE"], format="%m/%d/%Y"))
    vm = vrp_monthly(vix, g, CFG)
    print(vm.dropna().head(3).to_string())
    assert list(vm.columns) == VRP_COLUMNS and vm["month_end"].iloc[0] == "1990-01-31"
    assert vm["iv"].to_numpy() == pytest.approx((vm["vix"] / 100).to_numpy() ** 2, rel=1e-15)
    ok = vm.dropna()
    assert (ok["signal"] - (ok["iv"] - ok["garch_fc"])).abs().max() == 0
    assert (ok["vrp"] - (ok["iv"] - ok["rv_fwd_21"])).abs().max() == 0
    row = vm.set_index("month_end").loc["1993-12-31"]  # instruction 08: the reviewer's first GARCH row
    assert (round(row["iv"], 5), round(row["garch_fc"], 5), round(row["rv_fwd_21"], 5)) == (0.0136, 0.00471, 0.00505)
    assert math.isnan(vm.set_index("month_end").loc["1994-06-30", "rv_fwd_21"])  # no 21 sessions follow


def test_switch_cost_applied_on_change():
    ends = pd.DatetimeIndex(["2026-01-30", "2026-02-27", "2026-03-31", "2026-04-30", "2026-05-29", "2026-06-30"])
    signal = pd.Series([0.01, 0.02, -0.01, -0.02, 0.03, 0.01], index=ends)  # PUT, PUT, bills, bills, PUT in m+1
    put = pd.Series([100.0, 102.0, 101.0, 104.0, 103.0, 105.0], index=ends)
    other = pd.Series(100.0, index=ends)
    dtb3 = pd.Series([1.2, 2.4, 3.6, 4.8, 6.0, 7.2], index=ends)  # percent, on each month end
    s = strategy_returns(put, other, other, dtb3, signal, 10)
    print(s.to_string())
    assert list(s.columns) == STRATEGY_COLUMNS and len(s) == 5
    r_put = (put / put.shift(1) - 1).iloc[1:].to_numpy()
    tbill = np.array([1.2, 2.4, 3.6, 4.8, 6.0]) / 1200  # O-16 (b): month m+1 earns DTB3 at month end m / 1200
    assert s["tbill"].to_numpy() == pytest.approx(tbill, rel=1e-15)
    assert timed_positions(signal).tolist() == [True, True, False, False, True]
    cost = 10 / 10_000
    expected = [r_put[0] - cost, r_put[1], tbill[2] - cost, tbill[3], r_put[4] - cost]  # first position is a change
    assert s["timed_put"].to_numpy() == pytest.approx(expected, abs=1e-15)
    assert s["put"].to_numpy() == pytest.approx(r_put, abs=1e-15) and (s["bxm"] == 0).all()


def test_deflated_sharpe_known_value():
    """Hand case, monthly units. SR = 0.3, n_obs = 121, skew -0.5, Pearson kurtosis 5; trials 0.1, 0.2, 0.3, 0.2:
    N = 4, V = 0.02 / 3 (ddof 1), sqrt V = 0.0816497.
    Phi^-1(1 - 1/4) = 0.6744898, Phi^-1(1 - 1/(4e)) = 1.3287219;
    SR_0 = 0.0816497 x (0.4227843 x 0.6744898 + 0.5772157 x 1.3287219) = 0.0816497 x 1.0521257 = 0.0859055.
    1 - (-0.5)(0.3) + (5 - 1)/4 x 0.09 = 1.24, sqrt 1.1135529;
    z = (0.3 - 0.0859055) x sqrt(120) / 1.1135529 = 2.1061309; DSR = Phi(z) = 0.9824035."""
    trials = pd.Series([0.1, 0.2, 0.3, 0.2])
    got = deflated_sharpe(sr=0.3, n_obs=121, skew=-0.5, kurt_pearson=5.0, sr_trials=trials)
    assert got == pytest.approx(0.9824035, abs=5e-8)
    assert got == pytest.approx(norm.cdf(2.1061309), abs=1e-7)
    # instruction 08 point 3: the argument is Pearson kurtosis; passing the excess value (2) gives another number
    assert deflated_sharpe(sr=0.3, n_obs=121, skew=-0.5, kurt_pearson=2.0, sr_trials=trials) != pytest.approx(got)
    # instruction 08 point 4: fewer than 2 trials gives a blank
    assert math.isnan(deflated_sharpe(sr=0.3, n_obs=121, skew=-0.5, kurt_pearson=5.0, sr_trials=trials.iloc[:1]))


def test_spec_log_appends(tmp_path):
    path = tmp_path / "spec_log.csv"
    log = append_spec(path, "main", "the main specification", {"threshold": 0.0, "cost": 10}, 0.8025587878123456, 237)
    assert list(log.columns) == SPEC_COLUMNS and len(log) == 1
    once = path.read_bytes()
    assert b",0.8025587878,237\n" in once  # %.10g from the first write
    append_spec(path, "main", "the main specification", {"threshold": 0.0, "cost": 10}, 0.8025587878123456, 237)
    assert path.read_bytes() == once  # rerunning the same spec leaves the file byte-identical (rule 9)
    log = append_spec(path, "main", "the main specification", {"threshold": 0.0, "cost": 10}, 0.80, 237)
    log = append_spec(path, "alt", "threshold 0.005", {"threshold": 0.005, "cost": 10}, 0.70, 237)
    assert len(log) == 2 and log["spec_id"].tolist() == ["main", "alt"]
    first = path.read_bytes()
    log = append_spec(path, "main", "the main specification", {"cost": 10, "threshold": 0.0}, 0.80, 237)
    assert len(log) == 2 and path.read_bytes() == first  # same spec and params (key order aside): not appended
    log = append_spec(path, "main", "the main specification", {"threshold": 0.0, "cost": 10}, 0.81, 238)
    assert len(log) == 2 and log.loc[0, ["sharpe", "n_months"]].tolist() == [0.81, 238]  # window grew: updated
    back = pd.read_csv(path)
    assert back["sharpe"].tolist() == [0.81, 0.70] and json.loads(back.loc[1, "params_json"])["threshold"] == 0.005


def test_straddle_mark_atm():
    """At k = 0 the SSVI total variance is theta, so the vol is sqrt(theta(T) / T); value is Black-76 call + put
    and the spot delta is D (F / S) (2 N(d1) - 1)."""
    thetas = pd.DataFrame({"T": [0.05, 0.10], "theta_used": [0.002, 0.004]})
    F, K, T, D, S = 100.0, 100.0, 0.075, 0.997, 99.8
    m = straddle_mark(K, F, T, D, S, {"rho": -0.6, "eta": 1.2, "gamma": 0.5}, thetas)
    vol = math.sqrt(0.003 / T)
    assert m["vol"] == pytest.approx(vol, rel=1e-14)
    assert m["value"] == pytest.approx(float(black76(F, K, T, D, vol, "C") + black76(F, K, T, D, vol, "P")), rel=1e-14)
    assert m["delta"] == pytest.approx(D * F / S * (2 * norm.cdf(vol * math.sqrt(T) / 2) - 1), rel=1e-12)
    assert math.isnan(straddle_mark(K, F, 0.2, D, S, {"rho": -0.6, "eta": 1.2, "gamma": 0.5}, thetas)["vol"])


def _family_inputs(n=1500):
    rng = np.random.default_rng(20261028)
    days = pd.bdate_range("2000-01-03", periods=n)
    returns = pd.Series(rng.normal(0.0, 0.01, n), index=days)
    ends = pd.DatetimeIndex(pd.Series(days, index=days).groupby(days.to_period("M")).max().to_numpy())
    main = pd.Series(rng.normal(0.01, 0.01, len(ends)), index=ends)
    iv = pd.Series(rng.uniform(0.01, 0.09, len(ends)), index=ends)
    return main, iv, returns


def test_spec_signals_by_hand():
    main, iv, returns = _family_inputs()
    s = spec_signals(main, iv, returns)
    assert list(s.columns) == ["timed_put_main", "iv_minus_rv21", "iv_minus_rv63", "iv_minus_ewma", "garch_above_median"]
    m = main.index[10]
    upto = returns[returns.index <= m]
    assert s.loc[m, "timed_put_main"] == main[m]
    assert s.loc[m, "iv_minus_rv21"] == pytest.approx(iv[m] - 252 / 21 * (upto.iloc[-21:] ** 2).sum(), abs=1e-14)
    assert s.loc[m, "iv_minus_rv63"] == pytest.approx(iv[m] - 252 / 63 * (upto.iloc[-63:] ** 2).sum(), abs=1e-14)
    ewma = upto.iloc[0] ** 2
    for x in upto.iloc[1:]:
        ewma = 0.94 * ewma + 0.06 * x**2
    assert s.loc[m, "iv_minus_ewma"] == pytest.approx(iv[m] - 252 * ewma, abs=1e-12)
    assert s.loc[m, "garch_above_median"] == pytest.approx(main[m] - main.iloc[:10].median(), abs=1e-15)


def test_spec_rv_needs_a_full_window_and_the_median_a_prior_month():
    main, iv, returns = _family_inputs()
    s = spec_signals(main, iv, returns)
    assert np.isnan(s["iv_minus_rv63"].iloc[0])  # 1 month of returns is under 63 sessions
    assert np.isnan(s["garch_above_median"].iloc[0])  # no month end comes before the first


def test_spec_signals_no_lookahead():
    main, iv, returns = _family_inputs()
    m = main.index[30]
    full = spec_signals(main, iv, returns).loc[m]
    cut = spec_signals(main[main.index <= m], iv[iv.index <= m], returns[returns.index <= m]).loc[m]
    pd.testing.assert_series_equal(full, cut, rtol=0, atol=0)


def test_probabilistic_sharpe_known_value():
    # hand value: z = 0.1 sqrt(120) / sqrt(1 + 0.05 + 0.01) = 1.0640; Phi(z) = 0.85633
    assert probabilistic_sharpe(0.1, 121, -0.5, 5.0) == pytest.approx(0.8563, abs=1e-4)
    assert probabilistic_sharpe(0.1, 121, -0.5, 5.0, 0.1) == pytest.approx(0.5)


def test_deflated_sharpe_is_the_probabilistic_sharpe_at_sr0():
    trials = pd.Series([0.1, 0.2, 0.15, 0.05, 0.3])
    got = deflated_sharpe(sr=0.3, n_obs=121, skew=-0.5, kurt_pearson=5.0, sr_trials=trials)
    assert got == probabilistic_sharpe(0.3, 121, -0.5, 5.0, expected_max_sharpe(trials))


def test_series_moments_are_of_the_series_given():
    x = pd.Series(np.random.default_rng(20261028).normal(0.01, 0.04, 200))
    m = series_moments(x)
    assert m == {"sr": x.mean() / x.std(), "n_obs": 200, "skew": x.skew(), "kurt_pearson": x.kurt() + 3}


def test_family_table():
    rng = np.random.default_rng(20261028)
    ids = ["timed_put_main", "iv_minus_rv21", "iv_minus_rv63", "iv_minus_ewma", "garch_above_median"]
    excess = pd.DataFrame(rng.normal(0.01, 0.04, (120, 5)), columns=ids)
    diff = pd.DataFrame(rng.normal(0.0, 0.02, (120, 5)), columns=ids)
    put = pd.Series(rng.normal(0.005, 0.03, 120))
    t = family_table(excess, diff, put)
    assert len(t) == 11
    assert t["series"].value_counts().to_dict() == {"excess": 6, "timed_minus_put": 5}
    main = t[(t["spec_id"] == "timed_put_main") & (t["series"] == "timed_minus_put")].iloc[0]
    trials = diff.mean() / diff.std()
    assert main["n_trials"] == 5
    assert main["sr_var"] == pytest.approx(trials.var(ddof=1))
    assert main["deflated_sharpe"] == deflated_sharpe(**series_moments(diff["timed_put_main"]), sr_trials=trials)
    assert main["psr_zero"] == probabilistic_sharpe(**series_moments(diff["timed_put_main"]))
    others = t[t["spec_id"] != "timed_put_main"]
    assert others["deflated_sharpe"].isna().all() and others["psr_zero"].notna().all()
