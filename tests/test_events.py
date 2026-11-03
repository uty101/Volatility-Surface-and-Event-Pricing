import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from volsurf.config import load_config
from volsurf.events import (
    EVENTS_COLUMNS,
    SUMMARY_COLUMNS,
    event_summary,
    event_table,
    event_windows,
    macro_windows,
    straddle_move,
    term_structure_move,
)

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "config.toml")
FLAT = {"b": 0.0, "rho": 0.0, "m": 0.0, "s": 0.1}  # flat SVI slice: w(k) = a, so theta = a


def _earnings(*rows) -> pd.DataFrame:
    """EARNINGS rows (snap_date, ticker, event_ts_ny, timing) as stored in the release assets."""
    cols = ["snap_date", "ticker", "event_ts_ny", "timing", "eps_estimate", "reported_eps", "surprise_pct"]
    return pd.DataFrame([[*r, np.nan, np.nan, np.nan] for r in rows], columns=cols)


NO_OVERRIDES = pd.DataFrame(columns=["ticker", "event_date", "timing", "source_url"])


def _fits(day: str, ticker: str, slices: list[tuple[str, float, str]]) -> pd.DataFrame:
    return pd.DataFrame([{"day": day, "ticker": ticker, "expiry": e, "a": theta, **FLAT, "status": st}
                         for e, theta, st in slices])


def _chain(day: str, ticker: str, expiry: str, S: float, F: float, mids: dict[float, tuple[float, float]]):
    rows = []
    for K, (c, p) in mids.items():
        rows += [{"day": day, "ticker": ticker, "expiry": expiry, "kind": "C", "strike": K, "S": S, "F": F, "mid": c},
                 {"day": day, "ticker": ticker, "expiry": expiry, "kind": "P", "strike": K, "S": S, "F": F, "mid": p}]
    return pd.DataFrame(rows).dropna(subset=["mid"])


def _case(theta1=0.004, theta2=0.012):
    """AAPL AMC on 2026-10-29: window close(10-29) to close(10-30), pre-event snapshot 10-29. The 10-29 expiry ends
    before the window and the poor_fit 11-06 slice is not accepted, so E1 = 10-30 and E2 = 11-13."""
    windows = event_windows(_earnings(("2026-10-29", "AAPL", "2026-10-29 16:00:00-04:00", "AMC")), NO_OVERRIDES)
    fits = _fits("2026-10-29", "AAPL", [("2026-10-29", 0.001, "ok"), ("2026-10-30", theta1, "ok"),
                                         ("2026-11-06", 0.02, "poor_fit"), ("2026-11-13", theta2, "ok_refit")])
    iv = _chain("2026-10-29", "AAPL", "2026-10-30", 100.0, 100.4, {98.0: (3.0, 0.9), 100.0: (1.8, 1.4),
                                                                   102.0: (0.8, 2.6)})
    closes = {"AAPL": pd.Series({"2026-10-29": 100.0, "2026-10-30": 105.0, "2026-11-02": 104.0})}
    return windows, iv, fits, closes, {"AAPL": {"2026-10-29"}}


def test_term_structure_hand_example():
    # the docstring example: theta1 0.0100 (n1 3), theta2 0.0130 (n2 8), v_d 0.0006, v_e 0.0088
    m_t, status = term_structure_move(0.0100, 0.0130, 3, 8)
    assert status == "ok"
    assert abs(m_t - math.sqrt(2 / math.pi) * math.sqrt(0.0088)) <= 1e-15
    assert abs(m_t - 0.0748482) <= 5e-8
    assert "0.0748482" in term_structure_move.__doc__
    m_t, status = term_structure_move(0.0100, 0.0300, 4, 8)  # the docstring's no premium case
    assert status == "no_event_premium" and math.isnan(m_t)


def test_bmo_window():
    # BMO on Monday 2026-11-30: close(Friday 2026-11-27, an early close session) to close(2026-11-30)
    w = event_windows(_earnings(("2026-11-20", "WMT", "2026-11-30 07:00:00-05:00", "BMO")), NO_OVERRIDES)
    print(w.to_string())
    assert (w.loc[0, "start"], w.loc[0, "end"]) == ("2026-11-27", "2026-11-30")
    m = macro_windows(pd.DataFrame([{"date": "2026-11-27", "kind": "CPI", "release_time_ny": "08:30",
                                     "source_url": ""}]))
    assert (m.loc[0, "ticker"], m.loc[0, "start"], m.loc[0, "end"]) == ("^SPX", "2026-11-25", "2026-11-27")


def test_amc_window():
    # AMC on Wednesday 2026-11-25: close(11-25) to close(11-27), skipping Thanksgiving 2026-11-26
    w = event_windows(_earnings(("2026-11-20", "NVDA", "2026-11-25 16:05:00-05:00", "AMC")), NO_OVERRIDES)
    print(w.to_string())
    assert (w.loc[0, "timing"], w.loc[0, "start"], w.loc[0, "end"]) == ("AMC", "2026-11-25", "2026-11-27")


def test_latest_asset_defines_event():
    # O-12 (b): the row from the latest asset that lists the event; its 15:00 time makes the timing unknown
    e = _earnings(("2026-10-29", "XOM", "2026-10-30 08:00:00-04:00", "BMO"),
                  ("2026-10-30", "XOM", "2026-10-30 06:00:00-04:00", "BMO"),
                  ("2026-10-29", "AMD", "2026-11-03 16:00:00-05:00", "AMC"),
                  ("2026-10-30", "AMD", "2026-11-03 15:00:00-05:00", "AMC"))
    w = event_windows(e, NO_OVERRIDES).set_index("ticker")
    print(w.to_string())
    assert w.loc["XOM", "snap_date"] == "2026-10-30" and w.loc["XOM", "event_ts_ny"].startswith("2026-10-30 06:00")
    assert w.loc["AMD", "timing"] == "unknown" and pd.isna(w.loc["AMD", "start"])


def test_classify_unknown_excluded_until_override():
    e = _earnings(("2026-10-28", "AAPL", "2026-10-29 15:00:00-04:00", "unknown"))
    _, iv, fits, closes, days = _case()
    before = event_table(event_windows(e, NO_OVERRIDES), iv, fits, closes, days, CFG)
    print(before.to_string())
    assert before.loc[0, "status"] == "unknown" and before[["straddle_move", "ts_move"]].isna().all(axis=None)
    over = pd.DataFrame([{"ticker": "AAPL", "event_date": "2026-10-29", "timing": "AMC", "source_url": ""}])
    w = event_windows(e, over)
    assert w.loc[0, "override"] and w.loc[0, "timing"] == "AMC"
    after = event_table(w, iv, fits, closes, days, CFG)
    print(after.to_string())
    assert after.loc[0, "status"] == "ok" and np.isfinite(after.loc[0, "ts_move"])
    with pytest.raises(ValueError):
        event_windows(e, over.assign(event_date="2026-10-30"))


def test_event_table_values():
    windows, iv, fits, closes, days = _case()
    ev = event_table(windows, iv, fits, closes, days, CFG)
    print(ev.to_string())
    r = ev.iloc[0]
    assert (r["E1"], r["E2"], r["n1"], r["n2"]) == ("2026-10-30", "2026-11-13", 1, 11)
    assert (r["theta1"], r["theta2"], r["group"]) == (0.004, 0.012, "xlk_holdings")
    assert r["straddle_move"] == pytest.approx((1.8 + 1.4) / 100.0, abs=1e-15)
    # n1 = 1, so v_e = theta1 - v_d x 0 = theta1: the whole of theta1 is event variance
    assert r["ts_move"] == pytest.approx(math.sqrt(2 / math.pi) * math.sqrt(0.004), abs=1e-15)
    assert r["realised_move"] == pytest.approx(math.log(1.05), abs=1e-15)
    assert r["log_ratio"] == pytest.approx(math.log(math.log(1.05) / r["ts_move"]), abs=1e-12)
    assert r["status"] == "ok"


def test_straddle_strike_rule():
    # O-11 (a): nearest strike among those with both clean mids; a tie goes to the lower strike
    chain = _chain("d", "X", "E", 100.0, 101.0, {100.0: (1.0, 2.0), 102.0: (3.0, 4.0)})
    assert straddle_move(chain, 101.0, 100.0, "E") == pytest.approx(0.03, abs=1e-15)
    gap = _chain("d", "X", "E", 100.0, 100.2, {100.0: (1.0, np.nan), 101.0: (5.0, 6.0), 99.0: (7.0, 8.0)})
    assert straddle_move(gap, 100.2, 100.0, "E") == pytest.approx(0.11, abs=1e-15)  # 100 has no put; 101 is nearer
    assert math.isnan(straddle_move(_chain("d", "X", "E", 100.0, 100.0, {100.0: (1.0, np.nan)}), 100.0, 100.0, "E"))


def test_no_event_premium_status():
    # E1 = 11-06, E2 = 11-13 on a 10-30 window end; theta2 rises so fast that v_e <= 0
    windows, iv, fits, closes, days = _case()
    fits = _fits("2026-10-29", "AAPL", [("2026-11-06", 0.01, "ok"), ("2026-11-13", 0.03, "ok")])
    iv = iv.assign(expiry="2026-11-06")
    ev = event_table(windows, iv, fits, closes, days, CFG)
    print(ev.to_string())
    r = ev.iloc[0]
    assert (r["n1"], r["n2"]) == (6, 11)
    assert r["status"] == "no_event_premium" and np.isnan(r["ts_move"]) and np.isnan(r["log_ratio"])
    assert np.isfinite(r["straddle_move"]) and np.isfinite(r["realised_move"])


def test_missing_pre_snapshot_excluded_and_counted():
    windows, iv, fits, closes, days = _case()
    other = event_windows(_earnings(("2026-10-29", "AAPL", "2026-10-28 16:00:00-04:00", "AMC")), NO_OVERRIDES)
    future = event_windows(_earnings(("2026-10-29", "AAPL", "2026-11-17 16:00:00-05:00", "AMC")), NO_OVERRIDES)
    ev = event_table(pd.concat([windows, other, future], ignore_index=True), iv, fits, closes, days, CFG)
    print(ev.to_string())
    missing = ev["status"] == "no_pre_snapshot"
    print(f"no_pre_snapshot events: {int(missing.sum())}")
    assert int(missing.sum()) == 1 and ev.loc[missing, "event_date"].tolist() == ["2026-10-28"]
    assert ev.loc[missing, ["n1", "theta1", "straddle_move", "ts_move", "realised_move"]].isna().all(axis=None)
    assert ev.loc[ev["event_date"] == "2026-11-17", "status"].item() == "pending"  # starts after the last close
    assert event_summary(ev, CFG).loc[0, "n"] == 1  # only the ok event enters the summary


def test_pending_after_last_close():
    windows, iv, fits, closes, days = _case()
    closes = {"AAPL": closes["AAPL"].loc[:"2026-10-29"]}
    ev = event_table(windows, iv, fits, closes, days, CFG)
    print(ev.to_string())
    r = ev.iloc[0]
    assert r["status"] == "pending" and np.isfinite(r["ts_move"]) and np.isnan(r["realised_move"])


def test_events_schema():
    windows, iv, fits, closes, days = _case()
    ev = event_table(windows, iv, fits, closes, days, CFG)
    assert list(ev.columns) == EVENTS_COLUMNS
    assert EVENTS_COLUMNS == ["ticker", "group", "event_date", "timing", "pre_snap_date", "E1", "E2", "n1", "n2",
                              "theta1", "theta2", "S", "F", "straddle_move", "ts_move", "realised_move", "ratio",
                              "log_ratio", "status"]  # CLAUDE.md Section 6.2 EVENTS


def test_summary_blank_below_min_n():
    rng = np.random.default_rng(CFG.run.seed)
    groups = ["singles"] * 12 + ["xlk_holdings"] * 7 + ["index"] * 6
    events = pd.DataFrame({"group": groups, "log_ratio": rng.normal(0.1, 0.5, len(groups))})
    small = event_summary(events.head(CFG.events.min_n - 1), CFG)
    print(small.to_string())
    assert list(small.columns) == SUMMARY_COLUMNS
    assert (small["status"] == "below_min_n").all()
    assert small[["mean_lo", "mean_hi", "share_lo", "share_hi"]].isna().all(axis=None)
    full = event_summary(events, CFG).set_index("scope")
    print(full.to_string())
    assert list(full.index) == ["all", "singles"]  # xlk_holdings (7) and index (6) are below min_group_n = 8
    assert full.loc["all", "status"] == "ok" and full.loc["all", "n"] == len(events)
    assert full.loc["all", "mean_lo"] < full.loc["all", "mean_log_ratio"] < full.loc["all", "mean_hi"]
    assert full.loc["all", "share_lo"] < full.loc["all", "share_above"] < full.loc["all", "share_hi"]
    assert full.loc["singles", "status"] == "below_min_n"  # 12 events: a group row, but below min_n
    assert event_summary(events, CFG).equals(event_summary(events, CFG))  # seeded bootstrap
