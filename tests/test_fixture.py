from pathlib import Path

import numpy as np
import pandas as pd

from volsurf.snapshots import CHAINS_COLUMNS

FIXTURES = Path(__file__).resolve().parent / "fixtures"


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
