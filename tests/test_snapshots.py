import tomllib
from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd

from volsurf.snapshots import (
    CHAINS_COLUMNS,
    NY,
    chain_frame,
    classify_timing,
    filter_expiries,
    in_window,
    is_session,
    keep_spxw,
)

CFG = tomllib.loads((Path(__file__).resolve().parents[1] / "config.toml").read_text(encoding="utf-8"))


def test_in_window_across_clock_change():
    assert in_window(datetime(2026, 10, 30, 19, 30, tzinfo=UTC), CFG)  # 15:30 EDT
    assert not in_window(datetime(2026, 11, 2, 19, 30, tzinfo=UTC), CFG)  # 14:30 EST
    assert in_window(datetime(2026, 11, 2, 20, 30, tzinfo=UTC), CFG)  # 15:30 EST


def test_is_session():
    assert not is_session(date(2026, 11, 26))  # Thanksgiving
    assert not is_session(date(2026, 10, 31))  # Saturday
    assert is_session(date(2026, 10, 28))


def test_filter_expiries():
    today = date(2026, 10, 28)
    expiries = ["2026-10-27", "2026-10-28", "2026-10-29", "2027-12-02", "2027-12-03"]
    # 2027-12-02 is 400 days out, 2027-12-03 is 401
    assert filter_expiries(expiries, today, 400) == ["2026-10-29", "2027-12-02"]


def test_keep_spxw():
    df = pd.DataFrame({"contract_symbol": ["SPXW261030C05000000", "SPX261120C05000000",
                                           "SPXW261120P05000000", "SPX261120P05000000"],
                       "strike": [5000.0, 5000.0, 5000.0, 5000.0]})
    kept, dropped = keep_spxw(df)
    assert dropped == 2
    assert kept["contract_symbol"].tolist() == ["SPXW261030C05000000", "SPXW261120P05000000"]


def test_classify_timing():
    assert classify_timing(pd.Timestamp("2026-10-29 07:00", tz=NY)) == "BMO"
    assert classify_timing(pd.Timestamp("2026-10-29 16:05", tz=NY)) == "AMC"
    assert classify_timing(pd.Timestamp("2026-10-29 00:00", tz=NY)) == "unknown"


def _raw(symbols):
    n = len(symbols)
    return pd.DataFrame({
        "contractSymbol": symbols,
        "lastTradeDate": pd.to_datetime(["2026-10-28 18:00:00"] * n, utc=True),
        "strike": [100.0 + i for i in range(n)],
        "lastPrice": [1.0] * n, "bid": [0.9] * n, "ask": [1.1] * n, "change": [0.0] * n,
        "percentChange": [0.0] * n, "volume": [1.0] * n, "openInterest": [10] * n,
        "impliedVolatility": [0.2] * n, "inTheMoney": [False] * n,
        "contractSize": ["REGULAR"] * n, "currency": ["USD"] * n,
    })


def test_chain_frame_column_order():
    snap = datetime(2026, 10, 28, 19, 31, tzinfo=UTC)
    out = chain_frame(_raw(["A1", "A2"]), _raw(["B1"]), "AAPL", "2026-11-20", snap)
    assert list(out.columns) == CHAINS_COLUMNS
    assert out["kind"].tolist() == ["C", "C", "P"]
    assert (out["ticker"] == "AAPL").all() and (out["expiry"] == "2026-11-20").all()
