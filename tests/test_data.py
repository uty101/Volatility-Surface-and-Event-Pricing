import json
from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from volsurf.config import load_config
from volsurf.data import (
    CLEAN_LOG_COLUMNS,
    clean_chain,
    dividend_yield,
    last_completed_session,
    load_snapshot,
    rate_curve,
    sessions_between,
)
from volsurf.snapshots import CHAINS_COLUMNS, UNDERLYING_COLUMNS

CFG = load_config(Path(__file__).resolve().parents[1] / "config.toml")
SNAP = pd.Timestamp("2026-10-28 19:31:00", tz="UTC")  # 15:31 New York
DAY = date(2026, 10, 28)


def chain(rows, ticker="AAPL", snap=SNAP):
    """rows: (id, kind, strike, bid, ask[, last_trade_utc]) -> CHAINS frame; id goes into contract_symbol."""
    recs = []
    for r in rows:
        last = r[5] if len(r) > 5 else snap
        recs.append({
            "snap_utc": snap, "ticker": ticker, "expiry": "2026-11-20", "kind": r[1], "contract_symbol": r[0],
            "strike": float(r[2]), "last_price": 1.0, "bid": float(r[3]), "ask": float(r[4]), "change": 0.0,
            "pct_change": 0.0, "volume": 1.0, "open_interest": 1.0, "yahoo_iv": 0.2, "in_the_money": False,
            "last_trade_utc": pd.Timestamp(last) if last is not None else pd.NaT,
            "contract_size": "REGULAR", "currency": "USD",
        })
    return pd.DataFrame(recs, columns=CHAINS_COLUMNS)


def underlying(prices):
    return pd.DataFrame([{**dict.fromkeys(UNDERLYING_COLUMNS), "ticker": t, "price": p} for t, p in prices.items()],
                        columns=UNDERLYING_COLUMNS)


GOOD = [("ok1", "C", 100, 2.0, 2.2), ("ok2", "P", 100, 1.9, 2.1)]  # S = 100: inside every rule


def run(rows, ticker="AAPL", spot=100.0):
    return clean_chain(chain(rows, ticker), underlying({ticker: spot}), CFG)


def dropped(log, rule):
    return int(log.loc[log["rule"] == rule, "rows_dropped"].iloc[0])


def kept_ids(clean):
    return sorted(clean["contract_symbol"])


def test_rule_a_bid_le_zero():
    clean, log = run(GOOD + [("a1", "C", 100, 0.0, 1.0), ("a2", "P", 100, -0.1, 1.0)])
    assert kept_ids(clean) == ["ok1", "ok2"]
    assert dropped(log, "a") == 2 and log["rows_dropped"].sum() == 2


def test_rule_b_ask_le_bid():
    clean, log = run(GOOD + [("b1", "C", 100, 2.0, 2.0), ("b2", "P", 100, 2.0, 1.9)])
    assert kept_ids(clean) == ["ok1", "ok2"]
    assert dropped(log, "b") == 2 and log["rows_dropped"].sum() == 2


def test_rule_c_min_mid():
    clean, log = run(GOOD + [("c1", "C", 150, 0.02, 0.04)])  # mid 0.03 < min_mid 0.05
    assert kept_ids(clean) == ["ok1", "ok2"]
    assert dropped(log, "c") == 1 and log["rows_dropped"].sum() == 1


def test_rule_d_max_rel_spread():
    clean, log = run(GOOD + [("d1", "C", 100, 1.0, 2.0)])  # spread 1.0 / mid 1.5 > 0.5
    assert kept_ids(clean) == ["ok1", "ok2"]
    assert dropped(log, "d") == 1 and log["rows_dropped"].sum() == 1


def test_rule_e_bounds():
    rows = GOOD + [
        ("e1", "C", 80, 14.9, 15.1),  # call mid 15 below intrinsic 20
        ("e2", "C", 1, 100.0, 100.1),  # call mid at or above S
        ("e3", "P", 10, 10.0, 10.1),  # put mid at or above K
        ("e4", "P", 130, 29.0, 29.2),  # put mid 29.1 below intrinsic 30
    ]
    clean, log = run(rows)
    assert kept_ids(clean) == ["ok1", "ok2"]
    assert dropped(log, "e") == 4 and log["rows_dropped"].sum() == 4


def test_rule_e_spx_deferred():
    clean, log = run(GOOD + [("s1", "C", 80, 14.9, 15.1)], ticker="^SPX")  # outside American bounds, kept
    assert kept_ids(clean) == ["ok1", "ok2", "s1"]
    e = log[log["rule"] == "e"].iloc[0]
    assert e["rows_dropped"] == 0 and e["note"] == "deferred to section 3"


def test_rule_order():
    clean, log = run(GOOD + [("ad", "C", 100, 0.0, 1.0)])  # bid <= 0 and spread 1.0 / 0.5 > 0.5
    assert kept_ids(clean) == ["ok1", "ok2"]
    assert dropped(log, "a") == 1 and dropped(log, "d") == 0


def test_clean_log_one_row_per_ticker_and_rule():
    chains = pd.concat([chain(GOOD, "AAPL"), chain(GOOD, "SPY")], ignore_index=True)
    _, log = clean_chain(chains, underlying({"AAPL": 100.0, "SPY": 100.0}), CFG)
    assert list(log.columns) == CLEAN_LOG_COLUMNS
    assert log[["ticker", "rule"]].values.tolist() == [[t, r] for t in ("AAPL", "SPY") for r in "abcde"]
    assert log["rows_before"].tolist() == [2] * 10 and (log["day"] == "2026-10-28").all()


def test_stale_and_after_close_flags():
    rows = [
        ("same_day", "C", 100, 2.0, 2.2, "2026-10-28 15:00:00+00:00"),
        ("five", "C", 100, 2.0, 2.2, "2026-10-21 15:00:00+00:00"),  # 5 sessions before: not stale
        ("six", "C", 100, 2.0, 2.2, "2026-10-20 15:00:00+00:00"),  # 6 sessions before: stale
        ("missing", "C", 100, 2.0, 2.2, None),
    ]
    clean, _ = run(rows)
    stale = dict(zip(clean["contract_symbol"], clean["stale"], strict=True))
    assert stale == {"same_day": False, "five": False, "six": True, "missing": True}
    assert not clean["after_close"].any()
    late = pd.Timestamp("2026-10-28 20:05:00", tz="UTC")  # 16:05 New York
    clean_late, _ = clean_chain(chain(GOOD, snap=late), underlying({"AAPL": 100.0}), CFG)
    assert clean_late["after_close"].all()


def fred_frames(values: dict[str, list[tuple[str, str]]]) -> dict[str, pd.DataFrame]:
    return {sid: pd.DataFrame(rows, columns=["observation_date", sid]) for sid, rows in values.items()}


def flat_fred(y: str, obs_date: str = "2026-10-27"):
    return fred_frames({sid: [(obs_date, y)] for sid in ("DGS1MO", "DGS3MO", "DGS6MO", "DGS1")})


def test_rate_conversion_hand_value():
    assert rate_curve(flat_fred("4.00"), DAY)(0.25) == pytest.approx(0.03960525459235946, abs=1e-15)
    assert abs(rate_curve(flat_fred("4.00"), DAY)(0.25) - 2 * np.log(1.02)) <= 1e-15
    assert abs(rate_curve(flat_fred("3.87"), DAY)(0.25) - 0.03833033852202173) <= 1e-15


def test_rate_interpolation_and_flat_extrapolation():
    ys = {"DGS1MO": "4.00", "DGS3MO": "3.90", "DGS6MO": "3.80", "DGS1": "3.60"}
    curve = rate_curve(fred_frames({sid: [("2026-10-27", y)] for sid, y in ys.items()}), DAY)
    r = {sid: 2 * np.log(1 + float(y) / 200) for sid, y in ys.items()}
    assert abs(curve(0.25) - r["DGS3MO"]) <= 1e-15
    assert abs(curve(0.375) - (r["DGS3MO"] + r["DGS6MO"]) / 2) <= 1e-15
    assert abs(curve(0.75) - (r["DGS6MO"] + r["DGS1"]) / 2) <= 1e-15
    assert abs(curve(0.01) - r["DGS1MO"]) <= 1e-15 and abs(curve(5.0) - r["DGS1"]) <= 1e-15


def test_rate_publication_rule():
    rows = [("2026-10-27", "4.00"), ("2026-10-28", "9.99")]  # the observation dated `day` is not used
    fred = fred_frames({sid: rows for sid in ("DGS1MO", "DGS3MO", "DGS6MO", "DGS1")})
    assert abs(rate_curve(fred, DAY)(0.25) - 2 * np.log(1.02)) <= 1e-15


def test_rate_missing_t_minus_1_uses_t_minus_2():
    rows = [("2026-10-26", "4.00"), ("2026-10-27", "."), ("2026-10-28", "9.99")]
    fred = fred_frames({sid: rows for sid in ("DGS1MO", "DGS3MO", "DGS6MO", "DGS1")})
    assert abs(rate_curve(fred, DAY)(0.25) - 2 * np.log(1.02)) <= 1e-15


def test_dividend_yield_window():
    divs = pd.DataFrame({"date": ["2025-10-28", "2026-01-15", "2026-10-28", "2026-10-29"],
                         "ticker": "AAPL", "dividend": [1.0, 0.5, 0.25, 2.0]})
    # 2025-10-28 is exactly t - 365 days (excluded); 2026-10-28 is t (included); 2026-10-29 is after t
    assert dividend_yield(divs, 100.0, DAY) == pytest.approx(0.0075, abs=1e-15)
    assert dividend_yield(divs.iloc[:0], 100.0, DAY) == 0.0


def test_sessions_between_thanksgiving():
    assert sessions_between(date(2026, 11, 25), date(2026, 11, 30)) == 2  # 11-26 closed, 11-27 early close
    assert sessions_between(date(2026, 12, 24), date(2026, 12, 28)) == 1  # 12-25 closed


def test_last_completed_session_during_session():
    assert last_completed_session(datetime(2026, 10, 28, 14, 56, tzinfo=UTC)) == date(2026, 10, 27)


def test_last_completed_session_after_close():
    assert last_completed_session(datetime(2026, 10, 28, 20, 1, tzinfo=UTC)) == date(2026, 10, 28)  # 16:00 NY


def test_last_completed_session_early_close():
    assert last_completed_session(datetime(2026, 11, 27, 18, 30, tzinfo=UTC)) == date(2026, 11, 27)  # 13:00 NY


def test_last_completed_session_holiday():
    assert last_completed_session(datetime(2026, 11, 26, 23, 0, tzinfo=UTC)) == date(2026, 11, 25)  # Thanksgiving


def _write_day(root: Path, day: str, skip: str | None = None):
    files = {
        f"chains_{day}.parquet": lambda p: chain(GOOD).to_parquet(p, index=False),
        f"underlying_{day}.csv": lambda p: underlying({"AAPL": 100.0}).to_csv(p, index=False),
        f"earnings_{day}.csv": lambda p: p.write_text("snap_date,ticker,event_ts_ny,timing,eps_estimate,"
                                                      "reported_eps,surprise_pct\n"),
        f"snaplog_{day}.json": lambda p: p.write_text(json.dumps(
            {"runner": "actions", "n_ok": 1, "tickers": [{"ticker": "AAPL", "status": "ok"}]})),
    }
    for name, write in files.items():
        if not name.startswith(skip or "\0"):
            write(root / name)


def test_load_snapshot_reads_four_assets(tmp_path):
    _write_day(tmp_path, "2026-10-28")
    snap = load_snapshot(DAY, tmp_path)
    assert set(snap) == {"chains", "underlying", "earnings", "snaplog"}
    assert list(snap["chains"].columns) == CHAINS_COLUMNS and len(snap["chains"]) == 2
    assert snap["snaplog"]["status"].tolist() == ["ok"] and snap["snaplog"].attrs["runner"] == "actions"


def test_load_snapshot_missing_chains_names_asset(tmp_path):
    _write_day(tmp_path, "2026-10-28", skip="chains_")
    with pytest.raises(FileNotFoundError, match=r"chains_2026-10-28\.parquet"):
        load_snapshot(DAY, tmp_path)
