import itertools
import time
from collections import Counter
from datetime import date
from functools import cache
from pathlib import Path

import numpy as np
import pandas as pd

from volsurf.config import load_config
from volsurf.data import RATE_TENORS, SPX
from volsurf.forwards import clean_with_forwards
from volsurf.iv import (
    _sens,
    iv_american,
    iv_american_batch,
    iv_american_refine,
    iv_european,
    iv_inputs,
    price_bounds,
)
from volsurf.pricing import black76, crr

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "config.toml")
TOL = CFG.tolerances.iv_roundtrip
NO_VOL = {"flat", "no_root", "bounds"}
FIXTURE_DAY = date(2026, 10, 28)  # instruction 01d part B

# PLAN 2.1 / instruction 02 Section B grid
S, R, Q = 100.0, 0.045, 0.015
GRID = list(itertools.product(["C", "P"], [70, 80, 90, 100, 110, 120, 130], [7, 30, 91, 182, 365, 730],
                              [0.15, 0.30, 0.60]))


def _euro_inputs(days):
    T = days / 365
    return T, np.exp(-R * T), S * np.exp((R - Q) * T)


def _check_roundtrip(results):
    """Instruction 03b part B: each case returns a vol within iv_roundtrip, or no vol with status flat,
    no_root or bounds. Prints the count of each status."""
    print(dict(Counter(m for *_, m in results)))
    wrong = [(case, v, m) for case, v, m in results
             if not (np.isfinite(v) and abs(v - case[3]) <= TOL) and not (np.isnan(v) and m in NO_VOL)]
    assert not wrong, wrong


def test_european_roundtrip_grid():
    results = []
    for case in GRID:
        kind, K, days, sigma = case
        T, D, F = _euro_inputs(days)
        v, m = iv_european(float(black76(F, K, T, D, sigma, kind)), F, K, T, D, kind, CFG)
        results.append((case, v, m))
    _check_roundtrip(results)


def test_american_roundtrip_grid():
    results = []
    for case in GRID:
        kind, K, days, sigma = case
        T = days / 365
        v, m = iv_american(crr(S, K, T, R, Q, sigma, kind, CFG.pricing.n_prod, True), S, K, T, R, Q, kind, CFG)
        results.append((case, v, m))
    _check_roundtrip(results)


def test_flat_rule():
    # a deep ITM 7-day call: a vol point moves the price by less than flat_tol, in both models
    T, D, F = _euro_inputs(7)
    v, m =iv_european(float(black76(F, 80, T, D, 0.30, "C")), F, 80, T, D, "C", CFG)
    assert np.isnan(v) and m == "flat"
    v, m = iv_american(crr(S, 80, T, R, Q, 0.30, "C", CFG.pricing.n_prod, True), S, 80, T, R, Q, "C", CFG)
    assert np.isnan(v) and m == "flat"
    # an ATM 30-day option returns a vol
    T, D, F = _euro_inputs(30)
    v, m = iv_european(float(black76(F, F, T, D, 0.30, "P")), F, F, T, D, "P", CFG)
    assert m == "newton" and abs(v - 0.30) <= TOL
    v, m = iv_american(crr(S, 100, T, R, Q, 0.30, "P", CFG.pricing.n_prod, True), S, 100, T, R, Q, "P", CFG)
    assert m == "brent" and abs(v - 0.30) <= TOL


def test_bounds_flagged():
    T, D, F = _euro_inputs(91)
    cases = [
        (D * (F - 90) - 0.01, 90, "C"),  # below the European call lower bound
        (D * F, 90, "C"),  # at the upper bound D F
        (D * (110 - F) - 0.01, 110, "P"),  # below the European put lower bound
        (D * 110, 110, "P"),  # at the upper bound D K
    ]
    for price, K, kind in cases:
        assert not price_bounds(price, None, F, K, D, kind, False)
        v, m = iv_european(price, F, K, T, D, kind, CFG)
        assert np.isnan(v) and m == "bounds"
    american = [(9.99, 90, "C"), (S, 90, "C"), (9.99, 110, "P"), (110.0, 110, "P")]  # below intrinsic, at S or K
    for price, K, kind in american:
        v, m = iv_american(price, S, K, T, R, Q, kind, CFG)
        assert np.isnan(v) and m == "bounds"
    iv, status = iv_american_batch([p for p, *_ in american], [S] * 4, [K for _, K, _ in american], [T] * 4,
                                   [R] * 4, [Q] * 4, [k for *_, k in american], CFG)
    assert np.isnan(iv).all() and (status == "bounds").all()


def test_brent_fallback_7d_30pct_otm_put():
    T, D, F = _euro_inputs(7)
    K, sigma = 0.7 * F, 1.0
    sens = _sens(lambda s: float(black76(F, K, T, D, s, "P")), sigma, CFG)
    print(f"sens = {sens:.6g}")
    assert sens >= 1e-3  # instruction 03b step 3.2 test 4
    v, m = iv_european(float(black76(F, K, T, D, sigma, "P")), F, K, T, D, "P", CFG)
    assert m == "brent" and abs(v - sigma) <= TOL


@cache
def _fixture_american():
    chains = pd.read_parquet(ROOT / "tests" / "fixtures" / "chains_sample.parquet")
    underlying = pd.read_csv(ROOT / "tests" / "fixtures" / "underlying_sample.csv")
    fred = {sid: pd.read_csv(ROOT / "data" / "raw" / "fred" / f"{sid}.csv") for sid in RATE_TENORS}
    divs = pd.read_csv(ROOT / "data" / "raw" / "prices" / "dividends.csv")
    clean, _, forwards = clean_with_forwards(chains, underlying, fred, FIXTURE_DAY, CFG)
    rows = iv_inputs(clean, underlying, fred, divs, forwards, FIXTURE_DAY, CFG)
    return rows[rows["ticker"] != SPX].reset_index(drop=True)


def _otm(rows):
    return rows[np.where(rows["kind"] == "C", rows["strike"] >= rows["F"], rows["strike"] < rows["F"])]


def test_batch_matches_scalar_on_200_fixture_rows():
    rows = _fixture_american()
    pick = rows.iloc[np.sort(np.random.default_rng(CFG.run.seed).choice(len(rows), 200, replace=False))]
    iv_b, st_b = iv_american_batch(pick["mid"], pick["S"], pick["strike"], pick["T"], pick["r"], pick["q"],
                                   pick["kind"], CFG)
    scalar = [iv_american(x.mid, x.S, x.strike, x.T, x.r, x.q, x.kind, CFG) for x in pick.itertuples()]
    iv_s = np.array([v for v, _ in scalar])
    st_s = np.array(["batch" if m == "brent" else m for _, m in scalar])
    gap = np.abs(iv_b - iv_s)
    print(f"statuses {dict(Counter(st_b))}; largest gap {np.nanmax(gap):.3g}, median {np.nanmedian(gap):.3g}")
    assert (st_b == st_s).all()
    assert np.array_equal(np.isnan(iv_b), np.isnan(iv_s))
    assert np.nanmax(gap) <= 1e-6


def test_batch_timing_fixture_american_otm():
    rows = _otm(_fixture_american())
    t0 = time.perf_counter()
    _, status = iv_american_batch(rows["mid"], rows["S"], rows["strike"], rows["T"], rows["r"], rows["q"],
                                   rows["kind"], CFG)
    seconds = time.perf_counter() - t0
    print(f"batch on {len(rows)} fixture American OTM rows: {seconds:.1f} s; {dict(Counter(status))}")
    assert seconds < 300  # instruction 03 step 3.2


def test_american_n200_vs_n2000_measure():
    # MEASURE (PLAN 3.2): the largest American IV gap between N = 200 and N = 2000 on fixture OTM rows
    rows = _otm(_fixture_american())
    args = (rows["mid"], rows["S"], rows["strike"], rows["T"], rows["r"], rows["q"], rows["kind"])
    iv200, _ = iv_american_batch(*args, CFG)
    solved = np.isfinite(iv200)
    iv2000, iters = iv_american_refine(*(a[solved] for a in args), iv200[solved], CFG.pricing.n_validate, CFG)
    gap = np.abs(iv2000 - iv200[solved])
    print(f"N = 200 against N = {CFG.pricing.n_validate}: {solved.sum()} rows, {iters} Newton iterations, "
          f"largest gap {np.nanmax(gap):.6g}, median {np.nanmedian(gap):.6g}, unconverged {np.isnan(gap).sum()}")
    assert np.isfinite(np.nanmax(gap))
