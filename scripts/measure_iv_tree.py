"""MEASURE of PLAN 3.2 (instruction 04 step 4.0): the American IV on fixture SPY and AAPL OTM rows at N = n_prod
against N = n_validate, written to outputs/tables/iv_tree_convergence.csv (ticker, expiry, kind, strike,
iv_200, iv_2000, gap). Rows that do not solve at n_prod are left out; a row whose refinement does not converge
keeps a blank iv_2000 and gap."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from scripts.run_all import CSV, FIXTURE_DAY, FIXTURES, RAW, TABLES, _fred
from volsurf.config import load_config
from volsurf.data import SPX
from volsurf.forwards import clean_with_forwards
from volsurf.iv import iv_american_batch, iv_american_refine, iv_inputs

COLUMNS = ["ticker", "expiry", "kind", "strike", "iv_200", "iv_2000", "gap"]


def main() -> int:
    cfg = load_config()
    chains = pd.read_parquet(FIXTURES / "chains_sample.parquet")
    underlying = pd.read_csv(FIXTURES / "underlying_sample.csv")
    fred, divs = _fred(), pd.read_csv(RAW / "prices" / "dividends.csv")
    clean, _, forwards = clean_with_forwards(chains, underlying, fred, FIXTURE_DAY, cfg)
    rows = iv_inputs(clean, underlying, fred, divs, forwards, FIXTURE_DAY, cfg)
    rows = rows[rows["ticker"] != SPX]
    rows = rows[np.where(rows["kind"] == "C", rows["strike"] >= rows["F"], rows["strike"] < rows["F"])]
    args = (rows["mid"], rows["S"], rows["strike"], rows["T"], rows["r"], rows["q"], rows["kind"])
    iv200, _ = iv_american_batch(*args, cfg)
    solved = np.isfinite(iv200)
    iv2000, iters = iv_american_refine(*(a[solved] for a in args), iv200[solved], cfg.pricing.n_validate, cfg)
    out = rows.loc[solved, ["ticker", "expiry", "kind", "strike"]].reset_index(drop=True)
    out["iv_200"] = iv200[solved]
    out["iv_2000"] = iv2000
    out["gap"] = np.abs(out["iv_2000"] - out["iv_200"])
    path = TABLES / "iv_tree_convergence.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    out[COLUMNS].to_csv(path, **CSV)
    print(f"N = {cfg.pricing.n_prod} against N = {cfg.pricing.n_validate}: {len(out)} rows, {iters} Newton "
          f"iterations, largest gap {out['gap'].max():.6g}, median {out['gap'].median():.6g}, "
          f"unconverged {out['gap'].isna().sum()} -> {path}")
    print(out.nlargest(5, "gap").to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
