from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import QuantLib as ql

QL_TODAY = ql.Date(28, 10, 2026)
ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DAY = date(2026, 10, 28)  # instruction 01d part B


def _ql_option(S, K, days, r, q, sigma, kind, american=False, steps=None):
    """QuantLib vanilla option per instruction 02 Section B: dates today + days, Actual365Fixed, flat
    continuous r and q. European options get AnalyticEuropeanEngine; American get BinomialVanillaEngine("crr")."""
    ql.Settings.instance().evaluationDate = QL_TODAY
    dc = ql.Actual365Fixed()
    expiry = QL_TODAY + days
    process = ql.BlackScholesMertonProcess(
        ql.QuoteHandle(ql.SimpleQuote(S)),
        ql.YieldTermStructureHandle(ql.FlatForward(QL_TODAY, q, dc)),
        ql.YieldTermStructureHandle(ql.FlatForward(QL_TODAY, r, dc)),
        ql.BlackVolTermStructureHandle(ql.BlackConstantVol(QL_TODAY, ql.NullCalendar(), sigma, dc)),
    )
    payoff = ql.PlainVanillaPayoff(ql.Option.Call if kind == "C" else ql.Option.Put, K)
    if american:
        option = ql.VanillaOption(payoff, ql.AmericanExercise(QL_TODAY, expiry))
        option.setPricingEngine(ql.BinomialVanillaEngine(process, "crr", steps))
    else:
        option = ql.VanillaOption(payoff, ql.EuropeanExercise(expiry))
        option.setPricingEngine(ql.AnalyticEuropeanEngine(process))
    return option


@pytest.fixture
def ql_option():
    return _ql_option


@pytest.fixture(scope="session")
def fixture_iv() -> pd.DataFrame:
    """The fixture day's OTM IV table (PLAN 3.3), built from the committed fixture and data/raw, rows with a vol,
    with k = ln(K / F)."""
    from volsurf.config import load_config
    from volsurf.data import RATE_TENORS
    from volsurf.forwards import clean_with_forwards
    from volsurf.iv import iv_chain, iv_inputs

    cfg = load_config(ROOT / "config.toml")
    chains = pd.read_parquet(ROOT / "tests" / "fixtures" / "chains_sample.parquet")
    underlying = pd.read_csv(ROOT / "tests" / "fixtures" / "underlying_sample.csv")
    fred = {sid: pd.read_csv(ROOT / "data" / "raw" / "fred" / f"{sid}.csv") for sid in RATE_TENORS}
    divs = pd.read_csv(ROOT / "data" / "raw" / "prices" / "dividends.csv")
    clean, _, forwards = clean_with_forwards(chains, underlying, fred, FIXTURE_DAY, cfg)
    iv = iv_chain(iv_inputs(clean, underlying, fred, divs, forwards, FIXTURE_DAY, cfg), cfg)
    iv = iv[iv["iv"].notna()].copy()
    iv["k"] = np.log(iv["strike"] / iv["F"])
    return iv


@pytest.fixture(scope="session")
def fixture_fits(fixture_iv) -> pd.DataFrame:
    """Every fixture slice fitted per ticker with `fit_expiries` (instruction 05 correction 3): one row per (ticker,
    expiry) with T, F, r, k_min, k_max, n_quotes, params, rmse_volpts, min_g, refit, exit, route, cut_rounds and status."""
    from volsurf.config import load_config
    from volsurf.svi import PARAMS, fit_expiries

    cfg = load_config(ROOT / "config.toml")
    rows = []
    for ticker, t_rows in fixture_iv.groupby("ticker", sort=False):
        quotes = [{"expiry": e, "T": float(g["T"].iloc[0]), "F": float(g["F"].iloc[0]), "r": float(g["r"].iloc[0]),
                   "k": g["k"].to_numpy(), "iv": g["iv"].to_numpy()} for e, g in t_rows.groupby("expiry", sort=True)]
        for q, fit in zip(quotes, fit_expiries(quotes, cfg), strict=True):
            rows.append({"ticker": ticker, "expiry": q["expiry"], "T": q["T"], "F": q["F"], "r": q["r"],
                         "k_min": q["k"].min(), "k_max": q["k"].max(), "n_quotes": fit["n_quotes"],
                         **dict(zip(PARAMS, fit["params"], strict=True)), "rmse_volpts": fit["rmse_volpts"],
                         "min_g": fit["min_g"], "refit": fit["refit"], "exit": fit["exit"], "route": fit["route"],
                         "cut_rounds": fit["cut_rounds"], "status": fit["status"]})
    return pd.DataFrame(rows)
