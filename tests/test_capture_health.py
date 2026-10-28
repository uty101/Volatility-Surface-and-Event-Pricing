import json
from datetime import date
from pathlib import Path

import pandas as pd

from volsurf.config import load_config
from volsurf.data import CAPTURE_HEALTH_COLUMNS, capture_health

CFG = load_config(Path(__file__).resolve().parents[1] / "config.toml")
START = date(2026, 10, 28)


def write_day(root: Path, day: str, snaplog: dict, snap_utc: list[str], prefix: str = ""):
    pd.DataFrame({"snap_utc": pd.to_datetime(snap_utc, utc=True)}).to_parquet(root / f"{prefix}chains_{day}.parquet")
    (root / f"{prefix}snaplog_{day}.json").write_text(json.dumps(snaplog))


def build(root: Path) -> pd.DataFrame:
    # 2026-10-28: normal day, Actions, started 15:31:10 New York, 32 tickers ok, 1 row captured after 16:00
    write_day(root, "2026-10-28", {"runner": "actions", "ny_start": "2026-10-28T15:31:10-04:00", "n_ok": 32,
                                   "n_error": 0},
              ["2026-10-28 19:31:12", "2026-10-28 19:45:00", "2026-10-28 20:00:30"])
    # 2026-10-29: no real asset (a gap); a test_ asset that must be ignored
    write_day(root, "2026-10-29", {"runner": "local", "ny_start": "2026-10-29T15:30:00-04:00", "n_ok": 32},
              ["2026-10-29 19:30:00"], prefix="test_")
    # 2026-10-30: local backup, started 16:02 New York, 2 tickers in error
    write_day(root, "2026-10-30", {"runner": "local", "ny_start": "2026-10-30T16:02:00-04:00", "n_ok": 30,
                                   "n_error": 2},
              ["2026-10-30 20:02:05", "2026-10-30 20:03:00"])
    return capture_health(root, START, CFG)


def test_health_rows_one_per_session(tmp_path):
    table = build(tmp_path)
    assert list(table.columns) == CAPTURE_HEALTH_COLUMNS
    assert table["session"].tolist() == ["2026-10-28", "2026-10-29", "2026-10-30"]
    normal, error_day = table.iloc[0], table.iloc[2]
    assert (normal["runner"], normal["start_ny"], normal["tickers_ok"], normal["rows"]) == ("actions", "15:31:10", 32, 3)
    assert normal["after_close_rows"] == 1 and abs(normal["minutes_after_1530"] - 70 / 60) < 1e-12
    assert normal["ny_start"] == "2026-10-28T15:31:10-04:00"
    assert (error_day["runner"], error_day["tickers_ok"], error_day["rows"]) == ("local", 30, 2)
    assert error_day["after_close_rows"] == 2 and error_day["minutes_after_1530"] == 32


def test_gap_flagged(tmp_path):
    table = build(tmp_path)
    assert table["gap"].tolist() == [False, True, False]
    gap = table.iloc[1]
    assert pd.isna(gap["runner"]) and pd.isna(gap["rows"]) and pd.isna(gap["tickers_ok"])


def test_empty_snapshot_dir_gives_header_only(tmp_path):
    table = capture_health(tmp_path, START, CFG)
    assert list(table.columns) == CAPTURE_HEALTH_COLUMNS and table.empty
