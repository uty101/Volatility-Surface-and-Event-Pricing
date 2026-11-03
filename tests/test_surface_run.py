import dataclasses
from datetime import date
from functools import cache
from pathlib import Path

import numpy as np
import pandas as pd

from scripts import run_all
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
    statuses = {"too_few_expiries", "ssvi_fail", "no_bracket", "delta_outside_quotes"}  # instruction 05, O-34 (a)
    assert all(s == "ok" or set(s.split("|")) <= statuses for s in surface["status"])
    assert (fits["route"] == "").eq(fits["status"] == "too_few").all()
    assert fits.loc[fits["status"] != "too_few", "route"].isin(["first", "refit", "neighbour"]).all()
    accepted = fits["status"].isin(["ok", "ok_refit"])
    assert fits.loc[accepted, ["a", "b", "rho", "m", "s"]].notna().all().all()
    assert fits.loc[~accepted, ["a", "b", "rho", "m", "s"]].isna().all().all()  # Convention 4.15
    ok = surface["status"] == "ok"
    assert surface.loc[ok, ["ssvi_rho", "ssvi_eta", "ssvi_gamma", "ssvi_rmse"]].notna().all().all()
    assert (surface.loc[ok, "ssvi_eta"] * (1 + surface.loc[ok, "ssvi_rho"].abs()) <= 2).all()
    assert np.array_equal(surface["n_expiries"], fits[accepted].groupby("ticker", sort=False).size()
                          .reindex(surface["ticker"]).fillna(0).to_numpy())


def _cache_run(monkeypatch, tmp_path, cfg, days, force=False) -> int:
    """Instruction 07 step 7.0: the cache over `days`, each day's IV file the cut fixture table; `surface_day` returns
    the real fixture frames and counts its calls. Returns the number of days fitted; each day's frames must equal the
    fitted ones exactly, whether fitted or read."""
    calls, real = [], _tables()  # fitted before surface_day is replaced
    monkeypatch.setattr(run_all, "surface_day", lambda iv, c: calls.append(c) or real)
    iv_dir = tmp_path / "iv"
    iv_dir.mkdir(exist_ok=True)
    for d in days:
        if not (iv_dir / f"{d}.parquet").exists():
            _fixture_iv().to_parquet(iv_dir / f"{d}.parquet", index=False)
    fitted = 0
    for d in days:
        tables, refit = run_all.cached_surface_day(d, cfg, iv_dir=iv_dir, cache_dir=tmp_path / "surface", force=force)
        fitted += refit
        for name, frame in _tables().items():
            assert tables[name].equals(frame) and list(tables[name].dtypes) == list(frame.dtypes), (d, name)
    assert len(calls) == fitted
    return fitted


DAYS = [date(2026, 10, 28), date(2026, 10, 29), date(2026, 10, 30)]


def test_cache_second_run_refits_nothing(monkeypatch, tmp_path):
    assert _cache_run(monkeypatch, tmp_path, CFG, DAYS) == 3
    assert sorted(p.name for p in (tmp_path / "surface").iterdir()) == [f"{d}.parquet" for d in DAYS]
    assert _cache_run(monkeypatch, tmp_path, CFG, DAYS) == 0  # nothing changed: 0 days refitted
    assert _cache_run(monkeypatch, tmp_path, CFG, DAYS, force=True) == 3  # --force refits everything
    assert _cache_run(monkeypatch, tmp_path, CFG, [*DAYS, date(2026, 11, 3)]) == 1  # only the new day


def test_cache_svi_edit_refits_all_days(monkeypatch, tmp_path):
    assert _cache_run(monkeypatch, tmp_path, CFG, DAYS) == 3
    edited = dataclasses.replace(CFG, svi=dataclasses.replace(CFG.svi, max_rmse_volpts=CFG.svi.max_rmse_volpts + 1))
    assert _cache_run(monkeypatch, tmp_path, edited, DAYS) == 3  # an edited [svi] table refits every day
    assert _cache_run(monkeypatch, tmp_path, edited, DAYS) == 0
    surface = dataclasses.replace(CFG, surface=dataclasses.replace(CFG.surface, delta=0.2))
    assert _cache_run(monkeypatch, tmp_path, surface, DAYS) == 3
    (tmp_path / "iv" / f"{DAYS[1]}.parquet").write_bytes(
        (tmp_path / "iv" / f"{DAYS[1]}.parquet").read_bytes() + b"\0")  # one day's IV file changes
    assert run_all.surface_key(tmp_path / "iv" / f"{DAYS[1]}.parquet", surface) != run_all.surface_key(
        tmp_path / "iv" / f"{DAYS[0]}.parquet", surface)


def test_run_twice_byte_identical(tmp_path):
    first = write_surface_tables(_tables(), tmp_path / "first")
    second = write_surface_tables(surface_tables([_fixture_iv()], CFG), tmp_path / "second")
    assert [p.name for p in first] == list(SURFACE_FILES.values())
    for a, b in zip(first, second, strict=True):
        assert a.read_bytes() == b.read_bytes(), a.name
