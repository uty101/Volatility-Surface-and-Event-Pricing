"""Rebuild entry point (O-1 (a)): each step's driver is a stage, run with --stage <name>.

Section 11.1 completes this script; Section 1 adds the capture_health stage, Section 2 the eep stage and
Section 3 the clean_log stage.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

from volsurf.config import load_config
from volsurf.data import RATE_TENORS, capture_health, clean_chain
from volsurf.forwards import clean_with_forwards
from volsurf.pricing import K_BIN_LABELS, eep_rows, eep_summary

SNAPSHOTS = ROOT / "data" / "snapshots"
RAW = ROOT / "data" / "raw"
FIXTURES = ROOT / "tests" / "fixtures"
TABLES = ROOT / "outputs" / "tables"
CAPTURE_START = date(2026, 10, 28)  # kickoff Section 3.3: capture window starts 2026-10-28
FIXTURE_DAY = date(2026, 10, 28)  # instruction 01d part B: the fixture day
CSV = {"index": False, "float_format": "%.10g", "lineterminator": "\n", "encoding": "utf-8"}


def stage_capture_health(cfg) -> Path:
    out = TABLES / "capture_health.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    table = capture_health(SNAPSHOTS, CAPTURE_START, cfg)
    table.to_csv(out, **CSV)
    print(table.to_string())
    return out


def _fred() -> dict[str, pd.DataFrame]:
    return {sid: pd.read_csv(RAW / "fred" / f"{sid}.csv") for sid in RATE_TENORS}


def stage_clean_log(cfg) -> Path:
    """Instruction 03 step 3.1: the fixture CLEAN_LOG with rule e for ^SPX on the parity forward."""
    chains = pd.read_parquet(FIXTURES / "chains_sample.parquet")
    underlying = pd.read_csv(FIXTURES / "underlying_sample.csv")
    _, log, _ = clean_with_forwards(chains, underlying, _fred(), FIXTURE_DAY, cfg)
    out = TABLES / "clean_log_fixture.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    log.to_csv(out, **CSV)
    print(log.to_string())
    return out


def stage_eep(cfg) -> Path:
    """Instruction 02 step 2.3: early exercise premium on the fixture day's clean American chains."""
    chains = pd.read_parquet(FIXTURES / "chains_sample.parquet")
    underlying = pd.read_csv(FIXTURES / "underlying_sample.csv")
    clean, _ = clean_chain(chains, underlying, cfg)
    fred = _fred()
    divs = pd.read_csv(RAW / "prices" / "dividends.csv")
    rows = eep_rows(clean, underlying, fred, divs, FIXTURE_DAY, cfg)
    summary = eep_summary(rows)
    TABLES.mkdir(parents=True, exist_ok=True)
    rows.to_csv(TABLES / "eep_rows.csv", **CSV)
    out = TABLES / "eep_summary.csv"
    summary.to_csv(out, **CSV)
    print(summary.to_string())
    print(rows.groupby(["ticker", "status"], sort=False).size().to_string())
    # sanity checks, printed and not tested (instruction 02 step 2.3)
    deep_itm_put = summary[(summary["kind"] == "P") & (summary["k_bin"] == K_BIN_LABELS[-1])]
    print("deep ITM puts (k > 0.10), against the largest median premium per ticker:")
    print(deep_itm_put.to_string())
    print(summary.loc[summary.groupby("ticker", sort=False)["median_vol_pts"].idxmax()].to_string())
    print("AAPL OTM calls (k > 0.02):")
    print(summary[(summary["ticker"] == "AAPL") & (summary["kind"] == "C")
                  & summary["k_bin"].isin(K_BIN_LABELS[-2:])].to_string())
    return out


STAGES = {"capture_health": stage_capture_health, "clean_log": stage_clean_log, "eep": stage_eep}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage", choices=[*STAGES, "all"], required=True)
    args = p.parse_args(argv)
    cfg = load_config()
    for name in STAGES if args.stage == "all" else [args.stage]:
        print(f"{name}: wrote {STAGES[name](cfg)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
