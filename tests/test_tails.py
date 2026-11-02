from pathlib import Path

import numpy as np
import pandas as pd

from volsurf.config import load_config
from volsurf.density import PIT_COLUMNS, TAIL_PROBS_COLUMNS, pit_table, tail_probs
from volsurf.svi import ACCEPTED

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "config.toml")
FIXTURE_DAY = "2026-10-28"  # instruction 01d part B


def _slices(fixture_fits) -> pd.DataFrame:
    return fixture_fits.assign(day=FIXTURE_DAY)


def test_tail_probs_sum_to_one(fixture_fits):
    s = _slices(fixture_fits)
    tails = tail_probs(s[s["status"].isin(ACCEPTED)], CFG.density.moves)
    assert list(tails.columns) == TAIL_PROBS_COLUMNS
    side = tails[tails["measure"] != "abs_log"].pivot_table(index=["ticker", "expiry", "move"], columns="measure",
                                                            values="prob")
    total = side["below"] + side["above"]
    print(f"{len(side)} levels; largest |P(S_T < x) + P(S_T > x) - 1| {(total - 1).abs().max():.3g}")
    assert ((total - 1).abs() <= CFG.density.int_tol).all()
    assert tails["prob"].between(0, 1).all()


def test_pit_in_unit_interval(fixture_fits):
    # every fixture expiry treated as expired, with closes far below, at and far above each forward
    s = _slices(fixture_fits)
    F = s.groupby("ticker")["F"].first()
    for scale in (0.5, 1.0, 2.0):
        closes = {t: pd.Series(F[t] * scale, index=s.loc[s["ticker"] == t, "expiry"].unique()) for t in F.index}
        table = pit_table(s, closes, "2099-12-31")
        assert list(table.columns) == PIT_COLUMNS
        ok = table["status"] == "ok"
        print(scale, table["status"].value_counts().to_dict(), table.loc[ok, "u"].describe().to_dict())
        assert ok.sum() == s[s["status"].isin(ACCEPTED)].groupby(["ticker", "expiry"]).ngroups
        assert table.loc[ok, "u"].between(0, 1).all()
        assert (table.loc[~ok, "status"] == "no_accepted_slice").all() and table.loc[~ok, "u"].isna().all()


def test_pit_first_accepted_day_and_statuses():
    # O-14 (a): the first day with an accepted slice gives u; expiries after last_day are left out
    base = {"T": 0.01, "F": 100.0, "a": 0.0004, "b": 0.0, "rho": 0.0, "m": 0.0, "s": 0.1}
    fits = pd.DataFrame([
        {**base, "day": "2026-10-28", "ticker": "X", "expiry": "2026-10-29", "status": "poor_fit"},
        {**base, "day": "2026-10-29", "ticker": "X", "expiry": "2026-10-29", "status": "ok", "F": 101.0},
        {**base, "day": "2026-10-28", "ticker": "Y", "expiry": "2026-10-29", "status": "ok"},
        {**base, "day": "2026-10-28", "ticker": "Z", "expiry": "2026-10-29", "status": "too_few"},
        {**base, "day": "2026-10-28", "ticker": "X", "expiry": "2026-11-20", "status": "ok"},
    ])
    closes = {"X": pd.Series({"2026-10-29": 101.0}), "Z": pd.Series({"2026-10-29": 99.0})}
    table = pit_table(fits, closes, "2026-10-29").set_index("ticker")
    print(table.to_string())
    assert list(table.index) == ["X", "Y", "Z"]
    assert table.loc["X", "day"] == "2026-10-29" and table.loc["X", "status"] == "ok"
    # flat slice, w = 0.0004: u = N(-d-) at S = F, d- = -sqrt(w)/2 = -0.01, so u = N(0.01)
    assert abs(table.loc["X", "u"] - 0.5039893563146316) <= 1e-12
    assert table.loc["Y", "status"] == "no_close" and np.isnan(table.loc["Y", "u"])
    assert table.loc["Z", "status"] == "no_accepted_slice" and table.loc["Z", "day"] == ""


def test_pit_skips_density_fail():
    # instruction 05b part C: a density_fail slice has no PIT value; a later day's valid slice of the expiry is used
    base = {"T": 0.01, "F": 100.0, "a": 0.0004, "b": 0.0, "rho": 0.0, "m": 0.0, "s": 0.1, "status": "ok",
            "ticker": "X", "expiry": "2026-10-29"}
    fits = pd.DataFrame([{**base, "day": "2026-10-27", "density_status": "density_fail"},
                         {**base, "day": "2026-10-28", "density_status": "ok", "F": 101.0},
                         {**base, "ticker": "Y", "day": "2026-10-28", "density_status": "density_fail"}])
    closes = {"X": pd.Series({"2026-10-29": 101.0}), "Y": pd.Series({"2026-10-29": 99.0})}
    table = pit_table(fits, closes, "2026-10-29").set_index("ticker")
    print(table.to_string())
    assert table.loc["X", "day"] == "2026-10-28" and table.loc["X", "status"] == "ok"
    assert table.loc["Y", "status"] == "density_fail" and np.isnan(table.loc["Y", "u"])
