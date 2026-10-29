from datetime import date
from functools import cache
from pathlib import Path

import numpy as np
import pandas as pd

from volsurf.config import load_config
from volsurf.data import RATE_TENORS, SPX
from volsurf.forwards import clean_with_forwards
from volsurf.iv import IV_COLUMNS, SUMMARY_COLUMNS, iv_chain, iv_inputs, iv_summary

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "config.toml")
FIXTURE_DAY = date(2026, 10, 28)  # instruction 01d part B


@cache
def _inputs():
    """The fixture day's iv_inputs rows, cut to each ticker's first 2 expiries so the tests stay quick."""
    chains = pd.read_parquet(ROOT / "tests" / "fixtures" / "chains_sample.parquet")
    underlying = pd.read_csv(ROOT / "tests" / "fixtures" / "underlying_sample.csv")
    fred = {sid: pd.read_csv(ROOT / "data" / "raw" / "fred" / f"{sid}.csv") for sid in RATE_TENORS}
    divs = pd.read_csv(ROOT / "data" / "raw" / "prices" / "dividends.csv")
    clean, _, forwards = clean_with_forwards(chains, underlying, fred, FIXTURE_DAY, CFG)
    first = clean.groupby("ticker")["expiry"].transform(lambda e: e.isin(sorted(e.unique())[:2]))
    return iv_inputs(clean[first].reset_index(drop=True), underlying, fred, divs, forwards, FIXTURE_DAY, CFG)


def test_iv_chain_schema():
    iv = iv_chain(_inputs(), CFG)
    assert list(iv.columns) == IV_COLUMNS
    assert set(iv["ticker"]) == {SPX, "SPY", "AAPL"}
    # OTM only (Convention 4.5)
    assert (np.where(iv["kind"] == "C", iv["strike"] >= iv["F"], iv["strike"] < iv["F"])).all()
    assert (iv["iv"].notna() == iv["method"].isin(["newton", "brent", "batch"])).all()
    summary = iv_summary(iv)
    assert list(summary.columns) == SUMMARY_COLUMNS
    assert summary["n_in"].sum() == len(iv)


def test_iv_chain_spx_uses_european_and_others_american():
    iv = iv_chain(_inputs(), CFG)
    spx = iv[iv["ticker"] == SPX]
    assert set(spx["method"]) <= {"newton", "brent", "bounds", "no_root", "flat"} and len(spx) > 0
    assert set(iv.loc[iv["ticker"] != SPX, "method"]) <= {"batch", "bounds", "no_root", "flat"}
    # ^SPX rows carry the parity forward and its q_impl; American rows carry F = S exp((r - q) T)
    inputs = _inputs()
    spx_in = inputs[inputs["ticker"] == SPX]
    assert set(spx["F"].round(6)) <= set(spx_in["F"].round(6))
    am = iv[iv["ticker"] != SPX]
    np.testing.assert_allclose(am["F"], am["S"] * np.exp((am["r"] - am["q"]) * am["T"]), rtol=1e-15)


def test_iv_chain_parity_fail_expiry_flagged_without_vol():
    inputs = _inputs().copy()
    spx_expiry = inputs.loc[inputs["ticker"] == SPX, "expiry"].min()
    hit = (inputs["ticker"] == SPX) & (inputs["expiry"] == spx_expiry)
    inputs.loc[hit, ["F", "q"]] = np.nan
    inputs.loc[hit, "parity_fail"] = True
    iv = iv_chain(inputs, CFG)
    rows = iv[(iv["ticker"] == SPX) & (iv["expiry"] == spx_expiry)]
    assert len(rows) == hit.sum()  # every clean row of the expiry is kept, since OTM cannot be chosen
    assert rows["iv"].isna().all() and (rows["method"] == "").all()
    assert rows["flag"].str.split("|").apply(lambda f: "parity_fail" in f).all()
    assert iv_summary(iv).set_index("ticker").loc[SPX, "n_parity_fail"] == hit.sum()
