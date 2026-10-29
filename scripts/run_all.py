"""Rebuild entry point (O-1 (a)): each step's driver is a stage, run with --stage <name>.

Section 11.1 completes this script; Section 1 adds the capture_health stage, Section 2 the eep stage and
Section 3 the clean_log and iv stages.
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
from volsurf.data import RATE_TENORS, capture_health, clean_chain, load_snapshot
from volsurf.forwards import clean_with_forwards
from volsurf.iv import iv_chain, iv_inputs, iv_summary
from volsurf.pricing import K_BIN_LABELS, eep_rows, eep_summary

SNAPSHOTS = ROOT / "data" / "snapshots"
PROCESSED = ROOT / "data" / "processed"
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


def _iv_day(day: date, chains: pd.DataFrame, underlying: pd.DataFrame, cfg) -> tuple[pd.DataFrame, pd.DataFrame]:
    """One day's IV table (PLAN 3.3) and its `^SPX` forwards; the IV table goes to data/processed/iv/{day}.parquet."""
    fred, divs = _fred(), pd.read_csv(RAW / "prices" / "dividends.csv")
    clean, _, forwards = clean_with_forwards(chains, underlying, fred, day, cfg)
    iv = iv_chain(iv_inputs(clean, underlying, fred, divs, forwards, day, cfg), cfg)
    out = PROCESSED / "iv" / f"{day.isoformat()}.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    iv.to_parquet(out, index=False)
    print(f"{day}: {len(iv)} IV rows -> {out}")
    return iv, forwards


def stage_iv(cfg) -> Path:
    """Instruction 03 step 3.3 with 03b: OTM IVs for the fixture day and every downloaded snapshot day, each
    ticker used only if its SNAPLOG status is ok (O-5 (b)); iv_summary.csv, and the fixture day's ^SPX forwards
    in parity_forwards_fixture.csv."""
    chains = pd.read_parquet(FIXTURES / "chains_sample.parquet")
    underlying = pd.read_csv(FIXTURES / "underlying_sample.csv")
    iv, forwards = _iv_day(FIXTURE_DAY, chains, underlying, cfg)
    summaries = [iv_summary(iv)]
    days = sorted(date.fromisoformat(p.stem.removeprefix("chains_")) for p in SNAPSHOTS.glob("chains_*.parquet"))
    for day in days:
        snap = load_snapshot(day, SNAPSHOTS)
        ok = set(snap["snaplog"].loc[snap["snaplog"]["status"] == "ok", "ticker"])
        day_iv, _ = _iv_day(day, snap["chains"][snap["chains"]["ticker"].isin(ok)],
                            snap["underlying"][snap["underlying"]["ticker"].isin(ok)], cfg)
        summaries.append(iv_summary(day_iv))
    TABLES.mkdir(parents=True, exist_ok=True)
    forwards.to_csv(TABLES / "parity_forwards_fixture.csv", **CSV)
    summary = pd.concat(summaries, ignore_index=True)
    out = TABLES / "iv_summary.csv"
    summary.to_csv(out, **CSV)
    print(forwards.to_string())
    print(summary.to_string())
    return out


STAGES = {"capture_health": stage_capture_health, "clean_log": stage_clean_log, "eep": stage_eep, "iv": stage_iv}


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
