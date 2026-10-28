from datetime import date, time
from pathlib import Path

import numpy as np
import pandas as pd

from volsurf.config import load_config
from volsurf.data import RATE_TENORS
from volsurf.pricing import (
    EEP_ROW_COLUMNS,
    EEP_SUMMARY_COLUMNS,
    crr,
    eep_rows,
    eep_summary,
    time_to_expiry,
)

CFG = load_config(Path(__file__).resolve().parents[1] / "config.toml")
DAY = date(2026, 10, 28)
SNAP = pd.Timestamp("2026-10-28 19:31:00", tz="UTC")
EXPIRY = "2027-10-15"  # about 1 year: the put premium is well above the n_prod tree error
SPOT = 100.0
# flat 4.00% CMT curve dated t - 1, and 1.00 of dividends in the trailing year (q = 0.01)
FRED = {sid: pd.DataFrame({"observation_date": ["2026-10-27"], sid: [4.0]}) for sid in RATE_TENORS}
DIVS = pd.DataFrame({"date": ["2026-06-01"], "ticker": ["XYZ"], "dividend": [1.0]})
UNDERLYING = pd.DataFrame({"ticker": ["XYZ"], "price": [SPOT]})


def _chain(rows):
    """rows: (kind, strike, mid) -> the clean-chain columns eep_rows reads, with a 0.02 wide quote around mid."""
    return pd.DataFrame([{"snap_utc": SNAP, "ticker": "XYZ", "expiry": EXPIRY, "kind": kind, "strike": float(K),
                          "contract_symbol": f"XYZ{kind}{K}", "bid": mid - 0.01, "ask": mid + 0.01}
                         for kind, K, mid in rows])


def _synthetic_puts(sigma=0.30):
    T = time_to_expiry(EXPIRY, SNAP, time.fromisoformat(CFG.snapshot.close_ny))
    r = 2 * np.log1p(4.0 / 200)  # Convention 4.6 on the flat 4.00 curve
    q = 1.0 / SPOT
    return _chain([("P", K, crr(SPOT, K, T, r, q, sigma, "P", CFG.pricing.n_prod, True)) for K in range(85, 135, 5)])


def test_eep_nonnegative_on_synthetic():
    rows = eep_rows(_synthetic_puts(), UNDERLYING, FRED, DIVS, DAY, CFG)
    assert (rows["status"] == "ok").all()
    np.testing.assert_allclose(rows["iv_american"], 0.30, atol=1e-9)  # the price came from the same tree
    assert (rows["iv_american"] <= rows["iv_european"]).all()
    assert (rows["premium_vol_pts"] >= 0).all()


def test_eep_summary_columns():
    rows = eep_rows(_synthetic_puts(), UNDERLYING, FRED, DIVS, DAY, CFG)
    assert list(rows.columns) == EEP_ROW_COLUMNS
    summary = eep_summary(rows)
    assert list(summary.columns) == EEP_SUMMARY_COLUMNS
    assert summary["n"].sum() == len(rows)


def test_eep_failed_solve_keeps_row_with_status():
    # a call mid above spot has no vol in [iv_lo, iv_hi] under either model
    rows = eep_rows(_chain([("C", 100, 150.0)]), UNDERLYING, FRED, DIVS, DAY, CFG)
    assert len(rows) == 1
    assert rows.loc[0, "status"] == "both_fail"
    assert rows[["iv_american", "iv_european", "premium_vol_pts"]].isna().all(axis=None)
    assert eep_summary(rows).empty
