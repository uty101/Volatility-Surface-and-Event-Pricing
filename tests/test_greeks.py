import itertools
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from volsurf.config import load_config
from volsurf.greeks import BOOK_COLUMNS, GREEKS, book_greeks, fd_greeks, greeks

CFG = load_config(Path(__file__).resolve().parents[1] / "config.toml")
TOL = CFG.tolerances
H = {k: getattr(TOL, k) for k in ("fd_h_spot_rel", "fd_h_vol", "fd_h_t", "fd_h_rate")}

# PLAN 2.1 / instruction 02 Section B grid: 7 strikes x 6 tenors x 3 vols x 2 kinds = 252 cases
S, R, Q = 100.0, 0.045, 0.015
STRIKES = [70, 80, 90, 100, 110, 120, 130]
DAYS = [7, 30, 91, 182, 365, 730]
SIGMAS = [0.15, 0.30, 0.60]
KINDS = ["C", "P"]
GRID = list(itertools.product(KINDS, STRIKES, DAYS, SIGMAS))


def _cases(names):
    cases = [(g, *point) for g in names for point in GRID]
    return cases, [f"{g}-{k}-K{K}-d{d}-s{s}" for g, k, K, d, s in cases]


FD_CASES, FD_IDS = _cases(["delta", "gamma", "vega", "vanna", "volga"])
THETA_RHO_CASES, THETA_RHO_IDS = _cases(["theta", "rho"])
QL_CASES, QL_IDS = _cases(["delta", "gamma", "vega", "theta", "rho"])


def _fd_gap_within_bound(greek, kind, K, days, sigma):
    T = days / 365
    analytic = float(greeks(S, K, T, R, Q, sigma, kind)[greek])
    fd = float(fd_greeks(S, K, T, R, Q, sigma, kind, H)[greek])
    bound = TOL.greeks_fd_rel * abs(analytic) + getattr(TOL.greeks_fd_abs, greek)
    assert abs(analytic - fd) <= bound, f"{greek}: analytic {analytic!r} fd {fd!r} bound {bound!r}"


@pytest.mark.parametrize(("greek", "kind", "K", "days", "sigma"), FD_CASES, ids=FD_IDS)
def test_greeks_vs_fd(greek, kind, K, days, sigma):
    _fd_gap_within_bound(greek, kind, K, days, sigma)


@pytest.mark.parametrize(("greek", "kind", "K", "days", "sigma"), THETA_RHO_CASES, ids=THETA_RHO_IDS)
def test_theta_rho_vs_fd(greek, kind, K, days, sigma):
    # bounds set in instruction 02 Section B ([tolerances.greeks_fd_abs] theta and rho); no longer MEASURE
    _fd_gap_within_bound(greek, kind, K, days, sigma)


@pytest.mark.parametrize(("greek", "kind", "K", "days", "sigma"), QL_CASES, ids=QL_IDS)
def test_greeks_vs_quantlib(greek, kind, K, days, sigma, ql_option):
    # QuantLib theta is per year and vega, rho per unit, as ours (instruction 02 Section B): no conversion
    ours = float(greeks(S, K, days / 365, R, Q, sigma, kind)[greek])
    theirs = getattr(ql_option(S, K, days, R, Q, sigma, kind), greek)()
    assert abs(ours - theirs) <= 1e-8


def _positions(rows):
    cols = ["underlying", "expiry", "kind", "strike", "quantity", "S", "T", "r", "q", "sigma"]
    return pd.DataFrame(rows, columns=cols)


def test_book_greeks_sums():
    pos = _positions([
        ("AAPL", "2026-11-20", "C", 350.0, 3, 345.0, 0.06, 0.04, 0.003, 0.30),
        ("AAPL", "2026-11-20", "P", 330.0, -2, 345.0, 0.06, 0.04, 0.003, 0.32),
        ("AAPL", "2026-12-18", "C", 360.0, 5, 345.0, 0.14, 0.04, 0.003, 0.28),
        ("SPY", "2026-11-20", "P", 740.0, -4, 770.0, 0.06, 0.04, 0.011, 0.18),
    ])
    book = book_greeks(pos)
    assert list(book.columns) == BOOK_COLUMNS
    assert book[["underlying", "expiry"]].values.tolist() == [
        ["AAPL", "2026-11-20"], ["AAPL", "2026-12-18"], ["AAPL", "total"], ["SPY", "2026-11-20"], ["SPY", "total"]]
    g = greeks(pos["S"], pos["strike"], pos["T"], pos["r"], pos["q"], pos["sigma"], pos["kind"])
    for name in GREEKS:
        each = g[name] * pos["quantity"].to_numpy() * 100
        got = book.set_index(["underlying", "expiry"])[name]
        assert got[("AAPL", "2026-11-20")] == pytest.approx(each[0] + each[1], rel=1e-14, abs=1e-12)
        assert got[("AAPL", "2026-12-18")] == pytest.approx(each[2], rel=1e-14, abs=1e-12)
        assert got[("AAPL", "total")] == pytest.approx(each[:3].sum(), rel=1e-14, abs=1e-12)
        assert got[("SPY", "total")] == pytest.approx(each[3], rel=1e-14, abs=1e-12)


def test_book_greeks_long_short_same_contract_nets_to_zero():
    # instruction 02 step 2.2: a long call and a short call on the same contract net to 0 to 1e-12
    contract = ("AAPL", "2026-11-20", "C", 350.0)
    market = (345.0, 0.06, 0.04, 0.003, 0.30)
    book = book_greeks(_positions([(*contract, 7, *market), (*contract, -7, *market)]))
    assert np.all(np.abs(book[list(GREEKS)].to_numpy(dtype=float)) <= 1e-12)
