"""Rebuild entry point (O-1 (a)): each step's driver is a stage, run with --stage <name>.

Section 11.1 completes this script; Section 1 adds the capture_health stage.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from volsurf.config import load_config
from volsurf.data import capture_health

SNAPSHOTS = ROOT / "data" / "snapshots"
TABLES = ROOT / "outputs" / "tables"
CAPTURE_START = date(2026, 10, 28)  # kickoff Section 3.3: capture window starts 2026-10-28
CSV = {"index": False, "float_format": "%.10g", "lineterminator": "\n", "encoding": "utf-8"}


def stage_capture_health(cfg) -> Path:
    out = TABLES / "capture_health.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    table = capture_health(SNAPSHOTS, CAPTURE_START, cfg)
    table.to_csv(out, **CSV)
    print(table.to_string())
    return out


STAGES = {"capture_health": stage_capture_health}


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
