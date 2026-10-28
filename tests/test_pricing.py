import itertools
import time
from functools import cache
from pathlib import Path

import numpy as np
import pytest

from volsurf.config import load_config
from volsurf.pricing import black76, bsm, crr, early_exercise_premium

CFG = load_config(Path(__file__).resolve().parents[1] / "config.toml")
TOL = CFG.tolerances
N_VALIDATE = CFG.pricing.n_validate

# PLAN 2.1 / instruction 02 Section B grid: 7 strikes x 6 tenors x 3 vols x 2 kinds = 252 cases
S, R, Q = 100.0, 0.045, 0.015
STRIKES = [70, 80, 90, 100, 110, 120, 130]
DAYS = [7, 30, 91, 182, 365, 730]
SIGMAS = [0.15, 0.30, 0.60]
KINDS = ["C", "P"]
GRID = list(itertools.product(KINDS, STRIKES, DAYS, SIGMAS))
GRID_IDS = [f"{k}-K{K}-d{d}-s{s}" for k, K, d, s in GRID]
GRID_NO_KIND = list(itertools.product(STRIKES, DAYS, SIGMAS))
GRID_NO_KIND_IDS = [f"K{K}-d{d}-s{s}" for K, d, s in GRID_NO_KIND]


@cache
def _crr(kind, K, days, sigma, american):
    return crr(S, K, days / 365, R, Q, sigma, kind, N_VALIDATE, american)


@pytest.mark.parametrize(("kind", "K", "days", "sigma"), GRID, ids=GRID_IDS)
def test_bsm_vs_quantlib(kind, K, days, sigma, ql_option):
    ours = float(bsm(S, K, days / 365, R, Q, sigma, kind))
    theirs = ql_option(S, K, days, R, Q, sigma, kind).NPV()
    assert abs(ours - theirs) <= TOL.bsm_vs_quantlib


@pytest.mark.parametrize(("kind", "K", "days", "sigma"), GRID, ids=GRID_IDS)
def test_black76_equals_bsm(kind, K, days, sigma):
    T = days / 365
    D = np.exp(-R * T)
    F = S * np.exp((R - Q) * T)  # S e^(-qT) = D F
    assert abs(float(black76(F, K, T, D, sigma, kind)) - float(bsm(S, K, T, R, Q, sigma, kind))) <= 1e-12


@pytest.mark.parametrize(("K", "days", "sigma"), GRID_NO_KIND, ids=GRID_NO_KIND_IDS)
def test_european_parity(K, days, sigma):
    T = days / 365
    lhs = float(bsm(S, K, T, R, Q, sigma, "C")) - float(bsm(S, K, T, R, Q, sigma, "P"))
    assert abs(lhs - (S * np.exp(-Q * T) - K * np.exp(-R * T))) <= TOL.parity_european


@pytest.mark.parametrize(("kind", "K", "days", "sigma"), GRID, ids=GRID_IDS)
def test_crr_american_vs_quantlib(kind, K, days, sigma, ql_option):
    theirs = ql_option(S, K, days, R, Q, sigma, kind, american=True, steps=N_VALIDATE).NPV()
    assert abs(_crr(kind, K, days, sigma, True) - theirs) <= TOL.crr_amer_vs_quantlib_rel_spot * S


@pytest.mark.parametrize(("kind", "K", "days", "sigma"), GRID, ids=GRID_IDS)
def test_crr_european_vs_analytic(kind, K, days, sigma):
    analytic = float(bsm(S, K, days / 365, R, Q, sigma, kind))
    assert abs(_crr(kind, K, days, sigma, False) - analytic) <= TOL.crr_euro_vs_analytic_rel_spot * S


@pytest.mark.parametrize(("K", "days", "sigma"), GRID_NO_KIND, ids=GRID_NO_KIND_IDS)
def test_american_call_no_dividend_premium_zero(K, days, sigma):
    assert abs(early_exercise_premium(S, K, days / 365, R, 0.0, sigma, "C", N_VALIDATE)) <= 1e-12


def test_american_put_no_dividend_premium_positive():
    # instruction 02 step 2.1: K 120, 365 days, sigma 0.30, r 0.045, q 0: the put's early exercise premium is real
    assert early_exercise_premium(S, 120, 365 / 365, R, 0.0, 0.30, "P", N_VALIDATE) > 1e-4


def test_crr_raises_on_bad_probability():
    # (r - q) dt = 0.05 > sigma sqrt(dt) = 0.0032, so e^((r-q)dt) > u and p > 1
    with pytest.raises(ValueError, match="outside"):
        crr(S, 100, 1.0, 0.5, 0.0, 0.01, "P", 10, True)
    # negative carry the same size: e^((r-q)dt) < d, so p < 0
    with pytest.raises(ValueError, match="outside"):
        crr(S, 100, 1.0, 0.0, 0.5, 0.01, "C", 10, False)


def test_crr_n2000_under_one_second():
    # instruction 02 step 2.1: N = 2000 on 1 option in under 1 second
    start = time.perf_counter()
    crr(S, 100, 730 / 365, R, Q, 0.30, "P", N_VALIDATE, True)
    assert time.perf_counter() - start < 1.0


def test_kind_must_be_c_or_p():
    with pytest.raises(ValueError, match="kind"):
        bsm(S, 100, 1.0, R, Q, 0.2, "call")
