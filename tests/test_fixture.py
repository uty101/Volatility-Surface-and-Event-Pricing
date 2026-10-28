from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from volsurf.config import load_config
from volsurf.data import RATE_TENORS
from volsurf.forwards import clean_with_forwards
from volsurf.snapshots import CHAINS_COLUMNS

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
FIXTURE_DAY = date(2026, 10, 28)  # instruction 01d part B
CSV = {"index": False, "float_format": "%.10g", "lineterminator": "\n", "encoding": "utf-8"}


def _chains() -> pd.DataFrame:
    return pd.read_parquet(FIXTURES / "chains_sample.parquet")


def _spot(ticker: str) -> float:
    return float(pd.read_csv(FIXTURES / "underlying_sample.csv").set_index("ticker").loc[ticker, "price"])


def test_spx_contracts_are_spxw():
    spx = _chains().query("ticker == '^SPX'")
    assert not spx.empty
    assert spx["contract_symbol"].str.startswith("SPXW").all()


def test_spx_near_money_bids_live():
    # timing check (instruction 01d, step 1d.1): an in-session capture has live bids near the money
    spx = _chains().query("ticker == '^SPX'")
    near = spx[np.abs(np.log(spx["strike"] / _spot("^SPX"))) <= 0.10]
    assert not near.empty
    assert (near["bid"] > 0).mean() > 0.90


def test_chains_column_order_is_schema():
    assert list(_chains().columns) == CHAINS_COLUMNS


def test_clean_log_fixture_reproduced(tmp_path):
    # instruction 03 step 3.1: rule e for ^SPX on the European bounds with the parity forward
    underlying = pd.read_csv(FIXTURES / "underlying_sample.csv")
    fred = {sid: pd.read_csv(ROOT / "data" / "raw" / "fred" / f"{sid}.csv") for sid in RATE_TENORS}
    _, log, _ = clean_with_forwards(_chains(), underlying, fred, FIXTURE_DAY, load_config(ROOT / "config.toml"))
    log.to_csv(tmp_path / "clean_log_fixture.csv", **CSV)
    expected = (ROOT / "outputs" / "tables" / "clean_log_fixture.csv").read_bytes()
    assert (tmp_path / "clean_log_fixture.csv").read_bytes() == expected
