from datetime import date
from functools import cache
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.run_all import SURFACE_FILES, surface_tables, write_surface_tables
from volsurf.config import load_config
from volsurf.data import RATE_TENORS
from volsurf.forwards import clean_with_forwards
from volsurf.iv import iv_chain, iv_inputs
from volsurf.ssvi import SURFACE_COLUMNS, SVI_FITS_COLUMNS, THETA_COLUMNS
from volsurf.svi import CALENDAR_COLUMNS

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "config.toml")
FIXTURE_DAY = date(2026, 10, 28)  # instruction 01d part B
SCHEMAS = {"svi_fits": SVI_FITS_COLUMNS, "surface": SURFACE_COLUMNS, "calendar": CALENDAR_COLUMNS,
           "theta": THETA_COLUMNS}


@cache
def _fixture_iv() -> pd.DataFrame:
    """The fixture day's IV table, cut to each ticker's 6th to 11th expiries (6 per ticker, so SSVI has at least 3
    to fit) to keep the tests quick."""
    chains = pd.read_parquet(ROOT / "tests" / "fixtures" / "chains_sample.parquet")
    underlying = pd.read_csv(ROOT / "tests" / "fixtures" / "underlying_sample.csv")
    fred = {sid: pd.read_csv(ROOT / "data" / "raw" / "fred" / f"{sid}.csv") for sid in RATE_TENORS}
    divs = pd.read_csv(ROOT / "data" / "raw" / "prices" / "dividends.csv")
    clean, _, forwards = clean_with_forwards(chains, underlying, fred, FIXTURE_DAY, CFG)
    keep = clean.groupby("ticker")["expiry"].transform(lambda e: e.isin(sorted(e.unique())[5:11]))
    return iv_chain(iv_inputs(clean[keep].reset_index(drop=True), underlying, fred, divs, forwards, FIXTURE_DAY,
                              CFG), CFG)


@cache
def _tables():
    return surface_tables([_fixture_iv()], CFG)


def test_surface_run_fixture():
    tables = _tables()
    for name, columns in SCHEMAS.items():
        assert list(tables[name].columns) == columns, name
    fits, surface = tables["svi_fits"], tables["surface"]
    print(fits.to_string())
    print(surface.to_string())
    assert len(fits) == 18 and set(surface["ticker"]) == {"^SPX", "SPY", "AAPL"}
    assert fits["status"].isin(["ok", "ok_refit", "butterfly_fail", "poor_fit", "too_few"]).all()
    assert surface["status"].isin(["ok", "too_few_expiries", "ssvi_fail"]).all()
    accepted = fits["status"].isin(["ok", "ok_refit"])
    assert fits.loc[accepted, ["a", "b", "rho", "m", "s"]].notna().all().all()
    assert fits.loc[~accepted, ["a", "b", "rho", "m", "s"]].isna().all().all()  # Convention 4.15
    ok = surface["status"] == "ok"
    assert surface.loc[ok, ["ssvi_rho", "ssvi_eta", "ssvi_gamma", "ssvi_rmse"]].notna().all().all()
    assert (surface.loc[ok, "ssvi_eta"] * (1 + surface.loc[ok, "ssvi_rho"].abs()) <= 2).all()
    assert np.array_equal(surface["n_expiries"], fits[accepted].groupby("ticker", sort=False).size()
                          .reindex(surface["ticker"]).fillna(0).to_numpy())


def test_run_twice_byte_identical(tmp_path):
    first = write_surface_tables(_tables(), tmp_path / "first")
    second = write_surface_tables(surface_tables([_fixture_iv()], CFG), tmp_path / "second")
    assert [p.name for p in first] == list(SURFACE_FILES.values())
    for a, b in zip(first, second, strict=True):
        assert a.read_bytes() == b.read_bytes(), a.name
