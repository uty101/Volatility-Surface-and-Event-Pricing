import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from volsurf.config import load_config
from volsurf.vrp import (
    VRP_COLUMNS,
    garch_monthly_forecasts,
    level_at,
    log_returns,
    month_ends,
    realised_var,
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
