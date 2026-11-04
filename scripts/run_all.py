"""Rebuild entry point (O-1 (a)): each step's driver is a stage, run with --stage <name>; with no --stage every stage
runs in section order, from data/raw/, data/manual/ and the `snapshots` release (PLAN 11.1).

Section 1 adds the capture_health stage, Section 2 the eep stage and Section 3 the clean_log and iv stages, Section 4
the surface stage, Section 5 the density and tails stages, Section 6 the events stage, Section 7 the cor3m and
live_corr stages, Section 8 the vrp and strategies stages, Section 9 the attribution stage, Section 10 the risk and
report stages, Section 11 the snapshots, pricer_check, iv_tree, answers and readme stages.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import io
import json
import re
import subprocess
import sys
import time
from datetime import date
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import QuantLib as ql

from volsurf.attribution import attribute_live, bs_path_attribution, simulate_hedging
from volsurf.config import load_config
from volsurf.correlation import STUDY_COLUMNS, cor3m_study, live_implied_corr, rv_screen
from volsurf.data import RATE_TENORS, SPX, capture_health, clean_chain, load_snapshot
from volsurf.density import (
    CHECK_COLUMNS,
    FD_GAP_MAX,
    density_check,
    fd_gap,
    fd_step,
    pit_table,
    svi_density,
    tail_probs,
)
from volsurf.events import (
    event_summary,
    event_table,
    event_windows,
    macro_windows,
    pre_event_snapshot,
)
from volsurf.forwards import clean_with_forwards
from volsurf.greeks import greeks
from volsurf.iv import iv_chain, iv_inputs, iv_summary
from volsurf.pricing import K_BIN_LABELS, black76, bsm, crr, eep_rows, eep_summary
from volsurf.report import build_risk_report
from volsurf.risk import (
    VOL_POINT,
    book_risk,
    day_surface,
    limit_breaches,
    select_book,
    shock_grid,
)
from volsurf.ssvi import ssvi_w, surface_day, theta_at
from volsurf.svi import ACCEPTED, PARAMS, svi_w
from volsurf.vrp import (
    STATS_COLUMNS,
    append_spec,
    deflated_sharpe,
    drawdown,
    live_straddles,
    monthly_returns,
    strategy_returns,
    strategy_stats,
    tbill_returns,
    timed_positions,
    vrp_monthly,
)

SNAPSHOTS = ROOT / "data" / "snapshots"
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
FIXTURES = ROOT / "tests" / "fixtures"
TABLES = ROOT / "outputs" / "tables"
FIGURES = ROOT / "outputs" / "figures"
REPORTS = ROOT / "outputs" / "reports"
GREEK_NAMES = ("delta", "gamma", "vega", "theta", "rho")  # the Greeks checked against QuantLib, kickoff Section 8 item 2.2
CAPTURE_START = date(2026, 10, 28)  # kickoff Section 3.3: capture window starts 2026-10-28
FIXTURE_DAY = date(2026, 10, 28)  # instruction 01d part B: the fixture day
CSV = {"index": False, "float_format": "%.10g", "lineterminator": "\n", "encoding": "utf-8"}
FULL = "%.17g"  # O-39 (a), instruction 06: SVI parameters in svi_fits.csv at full precision
GRID_SPOT, GRID_R, GRID_Q = 100.0, 0.045, 0.015  # the 2.1 grid, instruction 02 Section B
GRID = list(product("CP", range(70, 131, 10), (7, 30, 91, 182, 365, 730), (0.15, 0.30, 0.60)))
GREEK_BOUND = 1e-8  # against QuantLib, kickoff Section 8 item 2.2
BLACK76_BOUND = 1e-12  # kickoff Section 8 item 2.1


def stage_snapshots(cfg) -> Path:
    """Instruction 11 step 11.1: every asset of the `snapshots` release into data/snapshots/, so that the days are
    every capture day in the release when the script runs. Prints the day count."""
    from scripts.pull_snapshots import pull

    out = RAW / "snapshot_manifest.csv"
    print(pull(cfg.snapshot.release_tag, SNAPSHOTS, out))
    days = _days()
    print(f"capture days: {len(days)}, {days[0]} to {days[-1]} (the fixture day and {len(days) - 1} in the release)")
    return out


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


def _ql_option(K: float, days: int, sigma: float, kind: str, steps: int | None = None) -> ql.VanillaOption:
    """QuantLib vanilla option per instruction 02 Section B: dates today + days, Actual365Fixed, flat continuous r and
    q. AnalyticEuropeanEngine, or BinomialVanillaEngine("crr") American when `steps` is given."""
    today = ql.Date(FIXTURE_DAY.day, FIXTURE_DAY.month, FIXTURE_DAY.year)
    ql.Settings.instance().evaluationDate = today
    dc = ql.Actual365Fixed()
    process = ql.BlackScholesMertonProcess(
        ql.QuoteHandle(ql.SimpleQuote(GRID_SPOT)),
        ql.YieldTermStructureHandle(ql.FlatForward(today, GRID_Q, dc)),
        ql.YieldTermStructureHandle(ql.FlatForward(today, GRID_R, dc)),
        ql.BlackVolTermStructureHandle(ql.BlackConstantVol(today, ql.NullCalendar(), sigma, dc)))
    payoff = ql.PlainVanillaPayoff(ql.Option.Call if kind == "C" else ql.Option.Put, K)
    if steps is None:
        option = ql.VanillaOption(payoff, ql.EuropeanExercise(today + days))
        option.setPricingEngine(ql.AnalyticEuropeanEngine(process))
    else:
        option = ql.VanillaOption(payoff, ql.AmericanExercise(today, today + days))
        option.setPricingEngine(ql.BinomialVanillaEngine(process, "crr", steps))
    return option


def stage_pricer_check(cfg) -> Path:
    """O-50 (a): the largest gap of each kickoff Section 8 pricer check over the 2.1 grid, so that research question 1
    has a source table (pricer_check.csv); the CRR rows are in units of S, as their bounds are."""
    tol, n = cfg.tolerances, cfg.pricing.n_validate
    gaps = {name: [] for name in ("bsm_vs_quantlib", "black76_vs_bsm", "crr_american_vs_quantlib_rel_spot",
                                  "crr_european_vs_analytic_rel_spot", *[f"{g}_vs_quantlib" for g in GREEK_NAMES])}
    args = (GRID_R, GRID_Q)
    for kind, K, days, sigma in GRID:
        T = days / 365
        price = float(bsm(GRID_SPOT, K, T, *args, sigma, kind))
        option = _ql_option(K, days, sigma, kind)
        gaps["bsm_vs_quantlib"].append(abs(price - option.NPV()))
        F, D = GRID_SPOT * np.exp((GRID_R - GRID_Q) * T), np.exp(-GRID_R * T)
        gaps["black76_vs_bsm"].append(abs(float(black76(F, K, T, D, sigma, kind)) - price))
        american = _ql_option(K, days, sigma, kind, n).NPV()
        gaps["crr_american_vs_quantlib_rel_spot"].append(
            abs(crr(GRID_SPOT, K, T, *args, sigma, kind, n, True) - american) / GRID_SPOT)
        gaps["crr_european_vs_analytic_rel_spot"].append(
            abs(crr(GRID_SPOT, K, T, *args, sigma, kind, n, False) - price) / GRID_SPOT)
        ours = greeks(GRID_SPOT, K, T, *args, sigma, kind)
        for g in GREEK_NAMES:
            gaps[f"{g}_vs_quantlib"].append(abs(float(ours[g]) - getattr(option, g)()))
    bounds = {"bsm_vs_quantlib": tol.bsm_vs_quantlib, "black76_vs_bsm": BLACK76_BOUND,
              "crr_american_vs_quantlib_rel_spot": tol.crr_amer_vs_quantlib_rel_spot,
              "crr_european_vs_analytic_rel_spot": tol.crr_euro_vs_analytic_rel_spot}
    table = pd.DataFrame([{"check": name, "n_cases": len(v), "largest_gap": max(v),
                           "bound": bounds.get(name, GREEK_BOUND)} for name, v in gaps.items()])
    table["passed"] = table["largest_gap"] <= table["bound"]
    TABLES.mkdir(parents=True, exist_ok=True)
    out = TABLES / "pricer_check.csv"
    table.to_csv(out, **CSV)
    print(table.to_string())
    return out


def stage_iv_tree(cfg) -> Path:
    """Instruction 04 step 4.0: the N = n_prod against N = n_validate measurement of scripts/measure_iv_tree.py."""
    from scripts.measure_iv_tree import main as measure

    measure()
    return TABLES / "iv_tree_convergence.csv"


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


def _days() -> list[date]:
    """The fixture day plus every downloaded snapshot day (instruction 03 step 3.3, instruction 04 step 4.3)."""
    snaps = sorted(date.fromisoformat(p.stem.removeprefix("chains_")) for p in SNAPSHOTS.glob("chains_*.parquet"))
    return [FIXTURE_DAY, *[d for d in snaps if d != FIXTURE_DAY]]


def surface_tables(ivs: list[pd.DataFrame], cfg) -> dict[str, pd.DataFrame]:
    """PLAN 4.3: `surface_day` on each day's IV table, concatenated in day order."""
    return concat_surface([surface_day(iv, cfg) for iv in ivs])


def concat_surface(parts: list[dict[str, pd.DataFrame]]) -> dict[str, pd.DataFrame]:
    return {name: pd.concat([p[name] for p in parts], ignore_index=True) for name in parts[0]}


def surface_key(iv_path: Path, cfg) -> str:
    """Instruction 07 step 7.0: sha256 over volsurf/svi.py, volsurf/ssvi.py, the [svi], [surface] and (instruction 08
    step 8.0, because `int_points` sets the acceptance grid) [density] config tables and the day's IV file (the sha256
    of each part, concatenated, hashed again)."""
    tables = [json.dumps(dataclasses.asdict(t), sort_keys=True).encode() for t in (cfg.svi, cfg.surface, cfg.density)]
    parts = [(ROOT / "volsurf" / "svi.py").read_bytes(), (ROOT / "volsurf" / "ssvi.py").read_bytes(), *tables,
             iv_path.read_bytes()]
    return hashlib.sha256(b"".join(hashlib.sha256(p).digest() for p in parts)).hexdigest()


def _write_cache(tables: dict[str, pd.DataFrame], key: str, path: Path) -> None:
    """One day's `surface_day` frames in one parquet file, each frame stored as its own parquet bytes so that dtypes
    and values come back exactly; the key in the file's metadata."""
    blobs = []
    for frame in tables.values():
        buf = io.BytesIO()
        frame.to_parquet(buf, index=False)
        blobs.append(buf.getvalue())
    table = pa.table({"name": list(tables), "data": pa.array(blobs, pa.binary())}).replace_schema_metadata(
        {"key": key})
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)


def _read_cache(path: Path, key: str) -> dict[str, pd.DataFrame] | None:
    """The cached frames if `path` exists and carries `key`, else None."""
    if not path.exists():
        return None
    table = pq.read_table(path)
    if (table.schema.metadata or {}).get(b"key", b"").decode() != key:
        return None
    return {n: pd.read_parquet(io.BytesIO(b)) for n, b in zip(table["name"].to_pylist(), table["data"].to_pylist(),
                                                               strict=True)}


def cached_surface_day(day: date, cfg, iv_dir: Path = PROCESSED / "iv", cache_dir: Path = PROCESSED / "surface",
                       force: bool = False) -> tuple[dict[str, pd.DataFrame], bool]:
    """Instruction 07 step 7.0: `surface_day` for one day through data/processed/surface/{day}.parquet. A cache file
    whose key (`surface_key`) matches is read, not refitted; `force` refits. Returns the frames and whether the day
    was fitted."""
    iv_path = iv_dir / f"{day.isoformat()}.parquet"
    key, path = surface_key(iv_path, cfg), cache_dir / f"{day.isoformat()}.parquet"
    if not force and (tables := _read_cache(path, key)) is not None:
        return tables, False
    tables = surface_day(pd.read_parquet(iv_path), cfg)
    _write_cache(tables, key, path)
    return tables, True


SURFACE_FILES = {"svi_fits": "svi_fits.csv", "surface": "surface_daily.csv", "calendar": "calendar_violations.csv",
                 "theta": "ssvi_theta.csv"}


def write_surface_tables(tables: dict[str, pd.DataFrame], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, file in SURFACE_FILES.items():
        table = tables[name]
        if name == "svi_fits":
            table = table.assign(**{c: table[c].map(lambda v: "" if pd.isna(v) else FULL % v) for c in PARAMS})
        table.to_csv(out_dir / file, **CSV)
        paths.append(out_dir / file)
    return paths


def _plt():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _save(fig, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120, metadata={"Software": None})
    _plt().close(fig)
    print(f"figure {path}")
    return path


def _spx(fits: pd.DataFrame, day: str) -> pd.DataFrame:
    return fits[(fits["day"] == day) & (fits["ticker"] == SPX)].sort_values("T")


def fig_smiles(fits: pd.DataFrame, day: str) -> Path:
    """spx_smiles_{day}.png: the SVI smile of every accepted ^SPX expiry, vol against k, coloured by T."""
    plt = _plt()
    acc = _spx(fits, day)
    acc = acc[acc["status"].isin(ACCEPTED)]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    cmap = plt.get_cmap("viridis")
    k = np.linspace(-0.3, 0.15, 300)
    for i, r in enumerate(acc.itertuples()):
        vol = np.sqrt(svi_w(k, r.a, r.b, r.rho, r.m, r.s) / r.T) * 100
        ax.plot(k, vol, color=cmap(i / max(len(acc) - 1, 1)), lw=1.2,
                label=f"{r.expiry} ({r.T * 365:.0f}d)" if i % 4 == 0 else None)
    ax.set_xlabel("log-moneyness k = ln(K / F)")
    ax.set_ylabel("implied vol (%)")
    ax.set_title(f"^SPX SVI smiles, {day}: {len(acc)} accepted expiries")
    ax.legend(fontsize=7, ncol=2)
    ax.grid(alpha=0.3)
    return _save(fig, FIGURES / f"spx_smiles_{day}.png")


def fig_smile_fits(fits: pd.DataFrame, iv: pd.DataFrame, day: str) -> Path:
    """spx_smile_fits_{day}.png (instruction 04 step 4.3): one panel per accepted ^SPX expiry, first 12 by T,
    market IVs as dots and the SVI fit as a line; rejected slices listed in the title."""
    plt = _plt()
    f = _spx(fits, day)
    acc = f[f["status"].isin(ACCEPTED)].head(12)
    rejected = f[~f["status"].isin(ACCEPTED)]
    q = iv[(iv["ticker"] == SPX) & iv["iv"].notna()]
    fig, axes = plt.subplots(3, 4, figsize=(16, 10.5), squeeze=False)
    for ax, r in zip(axes.flat, acc.itertuples(), strict=False):
        g = q[q["expiry"] == r.expiry]
        k = np.log(g["strike"] / g["F"]).to_numpy()
        kk = np.linspace(k.min(), k.max(), 300)
        ax.plot(k, g["iv"] * 100, ".", ms=2.5, color="0.35", label="market")
        ax.plot(kk, np.sqrt(svi_w(kk, r.a, r.b, r.rho, r.m, r.s) / r.T) * 100, color="C3", lw=1.3, label="SVI")
        ax.set_title(f"{r.expiry} ({r.T * 365:.1f}d) {r.status}, RMSE {r.rmse_volpts:.2f} pts", fontsize=9)
        ax.tick_params(labelsize=7)
        ax.grid(alpha=0.3)
    for ax in list(axes.flat)[len(acc):]:
        ax.set_visible(False)
    axes[0, 0].legend(fontsize=7)
    rej = ", ".join(f"{r.expiry} ({r.status})" for r in rejected.itertuples()) or "none"
    fig.suptitle(f"^SPX market IV (dots) and SVI fit (line), {day}, first 12 accepted expiries by T\n"
                 f"rejected: {rej}", fontsize=10)
    fig.supxlabel("k = ln(K / F)")
    fig.supylabel("implied vol (%)")
    fig.tight_layout()
    return _save(fig, FIGURES / f"spx_smile_fits_{day}.png")


def fig_surface(tables: dict[str, pd.DataFrame], day: str) -> Path | None:
    """spx_surface_last.png: the SSVI implied vol surface over k and T on the last day, with theta(T) by
    Convention 4.12 between the accepted expiries."""
    surface = tables["surface"]
    row = surface[(surface["day"] == day) & (surface["ticker"] == SPX)].iloc[0]
    if row["status"] != "ok":
        print(f"spx_surface_last.png not drawn: ^SPX SSVI status {row['status']} on {day}")
        return None
    plt = _plt()
    theta = tables["theta"]
    th = theta[(theta["day"] == day) & (theta["ticker"] == SPX)]
    th = th.merge(_spx(tables["svi_fits"], day)[["expiry", "T"]], on="expiry").sort_values("T")
    T = np.linspace(th["T"].iloc[0], th["T"].iloc[-1], 60)
    k = np.linspace(-0.3, 0.15, 60)
    KK, TT = np.meshgrid(k, T)
    theta_T = np.array([theta_at(t, th) for t in T])[:, None]
    vol = np.sqrt(ssvi_w(KK, theta_T, row["ssvi_rho"], row["ssvi_eta"], row["ssvi_gamma"]) / TT) * 100
    fig = plt.figure(figsize=(9, 6.5))
    ax = fig.add_subplot(projection="3d")
    ax.plot_surface(KK, TT * 365, vol, cmap="viridis", linewidth=0, antialiased=True)
    ax.set_xlabel("k = ln(K / F)")
    ax.set_ylabel("days to expiry")
    ax.set_zlabel("implied vol (%)")
    ax.set_title(f"^SPX SSVI surface, {day} (rho {row['ssvi_rho']:.3f}, eta {row['ssvi_eta']:.3f}, "
                 f"gamma {row['ssvi_gamma']:.3f})")
    return _save(fig, FIGURES / "spx_surface_last.png")


def fig_metrics(surface: pd.DataFrame) -> Path:
    """spx_metrics.png: ATM 30d, RR 25d, BF 25d and term slope of ^SPX over the captured window, drawn as points
    joined by lines, so 1 or 2 days still show (instruction 04 step 4.3)."""
    plt = _plt()
    s = surface[surface["ticker"] == SPX]
    x = np.arange(len(s))  # one tick per captured day, labelled with the day
    panels = [("atm_30", "ATM vol 30d (%)"), ("rr25_30", "25d risk reversal 30d (vol pts)"),
              ("bf25_30", "25d butterfly 30d (vol pts)"), ("term_slope", "term slope, ATM 90d - 30d (vol pts)")]
    fig, axes = plt.subplots(2, 2, figsize=(10, 6.5), sharex=True)
    for ax, (col, label) in zip(axes.flat, panels, strict=True):
        ax.plot(x, s[col] * 100, "o-", ms=6)
        ax.set_title(label, fontsize=10)
        ax.grid(alpha=0.3)
        ax.set_xticks(x, s["day"], rotation=30, fontsize=8)
        ax.set_xlim(-0.5, len(s) - 0.5)
    fig.suptitle(f"^SPX surface metrics from the accepted SVI slices, {len(s)} captured day(s)")
    fig.tight_layout()
    return _save(fig, FIGURES / "spx_metrics.png")


def stage_surface(cfg, force: bool = False) -> Path:
    """Instruction 04 step 4.3: SVI and SSVI on the fixture day and every downloaded snapshot day, from the iv
    stage's data/processed/iv/{day}.parquet, each day through the cache of instruction 07 step 7.0
    (`cached_surface_day`; `force` refits every day); the 4 surface tables and the Section 4 figures."""
    days = _days()
    start = time.perf_counter()
    parts, fitted = [], []
    for d in days:
        tables, refit = cached_surface_day(d, cfg, force=force)
        parts.append(tables)
        print(f"{d}: {'fitted' if refit else 'read from cache'}")
        fitted += [d] if refit else []
    tables = concat_surface(parts)
    print(f"surface: {len(fitted)} of {len(days)} days fitted, {time.perf_counter() - start:.1f} s")
    ivs = [pd.read_parquet(PROCESSED / "iv" / f"{FIXTURE_DAY.isoformat()}.parquet")]
    paths = write_surface_tables(tables, TABLES)
    fits, surface = tables["svi_fits"], tables["surface"]
    print(pd.crosstab([fits["day"], fits["ticker"]], fits["status"]).to_string())
    print(fits[fits["status"] != "ok"].to_string())
    fx = fits[fits["day"] == FIXTURE_DAY.isoformat()]
    fitted = fx[fx["n_quotes"] >= cfg.svi.min_quotes]
    share = fitted.groupby("ticker", sort=False)["status"].agg(
        accepted=lambda st: int(st.isin(ACCEPTED).sum()), fitted="size")
    share["share"] = share["accepted"] / share["fitted"]
    print(share.to_string())
    print(pd.crosstab([fits["day"], fits["ticker"]], [fits["status"], fits["route"]]).to_string())
    print(surface.to_string())
    fs = surface[surface["day"] == FIXTURE_DAY.isoformat()]
    print("SSVI RMSE (vol points), fixture day:",
          dict(zip(fs["ticker"], (fs["ssvi_rmse"] * 100).round(4), strict=True)))
    cal = tables["calendar"]
    print(cal.groupby(["day", "ticker"], sort=False)["violated"].agg(["size", "sum"]).to_string())
    print(cal.groupby("day")["violated"].agg(["size", "sum"]).to_string())
    for day in days:  # instruction 06 part B status 5: every day, so no stale figure stays behind
        fig_smiles(fits, day.isoformat())
    fig_smile_fits(fits, ivs[0], FIXTURE_DAY.isoformat())
    fig_surface(tables, days[-1].isoformat())
    fig_metrics(surface)
    return paths[1]


def _closes() -> dict[str, pd.Series]:
    """Unadjusted closes by ISO date: close.parquet per ticker, `^SPX` from `^GSPC` in index.parquet (O-3 (a))."""
    close = pd.read_parquet(RAW / "prices" / "close.parquet")
    index = pd.read_parquet(RAW / "prices" / "index.parquet")

    def iso(s: pd.Series) -> pd.Series:
        return pd.Series(s.to_numpy(), index=pd.to_datetime(s.index).strftime("%Y-%m-%d")).dropna()

    return {**{t: iso(close[t]) for t in close.columns}, SPX: iso(index["^GSPC"])}


def density_slices(ivs: list[pd.DataFrame], fits: pd.DataFrame) -> pd.DataFrame:
    """SVI_FITS rows of every day joined with each slice's F, r and quoted k range from that day's IV table."""
    quotes = pd.concat([iv[iv["iv"].notna()] for iv in ivs], ignore_index=True)
    quotes["k"] = np.log(quotes["strike"] / quotes["F"])
    quotes["day"] = quotes["day"].astype(str)
    q = quotes.groupby(["day", "ticker", "expiry"], sort=False).agg(F=("F", "first"), r=("r", "first"),
                                                                     k_min=("k", "min"), k_max=("k", "max"))
    return fits.merge(q.reset_index(), on=["day", "ticker", "expiry"], how="left", validate="one_to_one")


def _nearest(acc: pd.DataFrame, days: int) -> pd.Series:
    """The accepted slice with T nearest days / 365, ties to the shorter (O-14 (a))."""
    return acc.loc[(acc["T"] - days / 365).abs().sort_values(kind="stable").index[0]]


def fig_density(acc: pd.DataFrame, day: str) -> Path:
    """spx_density_last.png (PLAN 5.2, O-14 (a)): the density q(K) of the accepted ^SPX expiries nearest 30, 90 and
    180 days on the last day, the quoted strike range shaded."""
    plt = _plt()
    spx = acc[(acc["day"] == day) & (acc["ticker"] == SPX)].sort_values("T")
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    for ax, d in zip(axes, (30, 90, 180), strict=True):
        r = _nearest(spx, d)
        p = tuple(r[PARAMS])
        sw = np.sqrt(svi_w(0.0, *p))
        K = r["F"] * np.exp(np.linspace(-6 * sw, 4 * sw, 1500))
        ax.axvspan(r["F"] * np.exp(r["k_min"]), r["F"] * np.exp(r["k_max"]), color="C0", alpha=0.12,
                   label="quoted strike range")
        ax.plot(K, svi_density(K, r["F"], r["T"], p), color="C3", lw=1.4, label="SVI density")
        ax.axvline(r["F"], color="0.4", lw=0.8, ls="--", label=f"F = {r['F']:.1f}")
        ax.set_title(f"{r['expiry']} ({r['T'] * 365:.1f}d, nearest {d}d)", fontsize=10)
        ax.set_xlabel("S_T at expiry")
        ax.set_xlim(K[0], K[-1])
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("risk-neutral density q(K)")
    axes[0].legend(fontsize=8)
    fig.suptitle(f"^SPX risk-neutral densities from SVI slices, {day}")
    fig.tight_layout()
    return _save(fig, FIGURES / "spx_density_last.png")


def fd_gaps(acc: pd.DataFrame, cfg) -> pd.DataFrame:
    """O-38 (b), instruction 06: `fd_gap` (step F min(bl_dk, s / 10)) on 2,001 strikes over each slice's quoted
    range, absolute and relative to the slice's peak density."""
    rows = []
    for _, r in acc.iterrows():
        gap = fd_gap(tuple(r[PARAMS]), r["F"], r["T"], np.exp(-r["r"] * r["T"]), (r["k_min"], r["k_max"]), cfg)
        rows.append({"day": r["day"], "ticker": r["ticker"], "expiry": r["expiry"], "T": r["T"], "s": r["s"],
                     "dk": fd_step(tuple(r[PARAMS]), r["F"], cfg), **gap})
    return pd.DataFrame(rows, index=acc.index)


def read_fits() -> pd.DataFrame:
    """svi_fits.csv with the SVI parameters exactly as fitted (O-39 (a)): written at %.17g, read back round-trip."""
    return pd.read_csv(TABLES / "svi_fits.csv", dtype={"day": str, "expiry": str}, float_precision="round_trip")


def _density_inputs(cfg) -> tuple[list[date], pd.DataFrame]:
    """Every day's SVI_FITS rows joined with F, r and quoted k range (`density_slices`)."""
    days = _days()
    ivs = [pd.read_parquet(PROCESSED / "iv" / f"{d.isoformat()}.parquet") for d in days]
    return days, density_slices(ivs, read_fits())


def stage_density(cfg) -> Path:
    """Step 5.1 (instructions 05, 05b, 05c and 06): density checks with density_status for every accepted slice of
    every day (density_checks.csv). The analytic against finite-difference gap runs on every slice that is not
    `kink` or `density_fail`; one above 5e-3 x peak gets status `fd_gap` (O-38 (b))."""
    _, slices = _density_inputs(cfg)
    acc = slices[slices["status"].isin(ACCEPTED)].reset_index(drop=True)
    checks = pd.DataFrame([density_check(tuple(r[PARAMS]), r["F"], cfg) for _, r in acc.iterrows()])
    gaps = fd_gaps(acc[checks["density_status"] == "ok"], cfg)
    checks["fd_rel_gap"] = gaps["max_rel_gap_to_peak"]
    checks.loc[checks["fd_rel_gap"] > FD_GAP_MAX, "density_status"] = "fd_gap"
    checks = pd.concat([acc[["day", "ticker", "expiry", "T", "F"]], checks], axis=1)[CHECK_COLUMNS]
    TABLES.mkdir(parents=True, exist_ok=True)
    out = TABLES / "density_checks.csv"
    checks.to_csv(out, **CSV)
    err = checks.assign(abs_int_err=checks["int_err"].abs(), abs_mean_rel_err=checks["mean_rel_err"].abs())
    cols = ["min_g", "abs_int_err", "abs_mean_rel_err", "tail_mass", "min_density"]
    print(err.groupby(["day", "ticker"], sort=False)[cols].agg(["min", "max", "median"]).to_string())
    print(err.sort_values("abs_int_err", ascending=False).head(10).to_string())
    print(err.sort_values("abs_mean_rel_err", ascending=False).head(10).to_string())
    print(err.sort_values("min_g").head(10).to_string())
    wings = acc.assign(left_wing=acc["b"] * (1 - acc["rho"]), right_wing=acc["b"] * (1 + acc["rho"]))
    top = err.assign(left_wing=wings["left_wing"], right_wing=wings["right_wing"])
    print("10 largest tail_mass:")
    print(top.sort_values("tail_mass", ascending=False).head(10)[
        ["day", "ticker", "expiry", "T", "tail_mass", "left_wing", "right_wing", "int_err", "mean_rel_err"]].to_string())
    print(f"accepted slices {len(checks)}; largest |integral - 1| {err['abs_int_err'].max()!r}, largest "
          f"|mean / F - 1| {err['abs_mean_rel_err'].max()!r}, largest tail_mass {err['tail_mass'].max()!r}, "
          f"smallest g {checks['min_g'].min()!r}, smallest density {checks['min_density'].min()!r}")
    print("density status per day:")
    print(pd.crosstab(checks["day"], checks["density_status"]).to_string())
    print("density_fail slices:")
    print(checks[checks["density_status"] == "density_fail"].to_string())
    print("fd_gap slices:")
    print(gaps[gaps["max_rel_gap_to_peak"] > FD_GAP_MAX].to_string())
    print(gaps.groupby(["day", "ticker"], sort=False)[["max_abs_gap", "max_rel_gap_to_peak"]].max().to_string())
    worst = gaps.loc[gaps["max_rel_gap_to_peak"].idxmax()]
    print(f"largest |q - q_fd| relative to peak {worst['max_rel_gap_to_peak']!r} ({worst['day']} {worst['ticker']} "
          f"{worst['expiry']}), bound {FD_GAP_MAX} (instruction 05b part C); largest absolute "
          f"{gaps['max_abs_gap'].max()!r}")
    return out


def stage_tails(cfg) -> Path:
    """Step 5.2 (instructions 05, 05b and 05c): tail tables for the accepted slices whose density is ok
    (tail_probs.csv), PIT values for every captured expiry that has expired by the last close in close.parquet and
    index.parquet (pit.csv), and spx_density_last.png; reads density_checks.csv from the density stage."""
    days, slices = _density_inputs(cfg)
    checks = pd.read_csv(TABLES / "density_checks.csv", dtype={"day": str, "expiry": str})
    slices = slices.merge(checks[["day", "ticker", "expiry", "density_status"]], on=["day", "ticker", "expiry"],
                          how="left", validate="one_to_one")
    good = slices[slices["status"].isin(ACCEPTED) & (slices["density_status"] == "ok")].reset_index(drop=True)
    tails = tail_probs(good, cfg.density.moves)
    closes = _closes()
    last_close = min(pd.read_parquet(RAW / "prices" / f).index.max() for f in ("close.parquet", "index.parquet"))
    last_close = pd.Timestamp(last_close).strftime("%Y-%m-%d")
    pits = pit_table(slices, closes, last_close)
    TABLES.mkdir(parents=True, exist_ok=True)
    tails.to_csv(TABLES / "tail_probs.csv", **CSV)
    pits.to_csv(TABLES / "pit.csv", **CSV)
    last = days[-1].isoformat()
    spx30 = _nearest(good[(good["day"] == last) & (good["ticker"] == SPX)], 30)
    print(f"^SPX slice nearest 30 days on {last}: {spx30['expiry']}, T = {spx30['T']!r}, F = {spx30['F']!r}")
    print(tails[(tails["day"] == last) & (tails["ticker"] == SPX) & (tails["expiry"] == spx30["expiry"])].to_string())
    print(f"PIT: expiries on or before the last close {last_close}")
    print(pits.to_string())
    print(f"tail rows {len(tails)} over {good.groupby(['day', 'ticker', 'expiry']).ngroups} slices; "
          f"probabilities from {tails['prob'].min()!r} to {tails['prob'].max()!r}")
    fig_density(good, last)
    return TABLES / "tail_probs.csv"


def _chain_inputs(day: date, tickers: set[str], cfg) -> pd.DataFrame:
    """One day's clean chain, both sides, with the IV stage inputs (S, F, mid; `iv_inputs`) for `tickers`, each
    ticker used only if its SNAPLOG status is ok (O-5 (b)); the fixture day from tests/fixtures."""
    if day == FIXTURE_DAY:
        chains = pd.read_parquet(FIXTURES / "chains_sample.parquet")
        underlying = pd.read_csv(FIXTURES / "underlying_sample.csv")
    else:
        snap = load_snapshot(day, SNAPSHOTS)
        tickers = tickers & set(snap["snaplog"].loc[snap["snaplog"]["status"] == "ok", "ticker"])
        chains, underlying = snap["chains"], snap["underlying"]
    chains, underlying = chains[chains["ticker"].isin(tickers)], underlying[underlying["ticker"].isin(tickers)]
    fred, divs = _fred(), pd.read_csv(RAW / "prices" / "dividends.csv")
    clean, _, forwards = clean_with_forwards(chains, underlying, fred, day, cfg)
    return iv_inputs(clean, underlying, fred, divs, forwards, day, cfg)


def event_inputs(cfg) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, set[str]]]:
    """PLAN 6.2: windows for every earnings event dated on or after the capture start (from the fixture's and every
    snapshot day's EARNINGS asset, with data/manual/earnings_overrides.csv) and every macro event in
    data/manual/macro_events.csv; the SVI fits; and the days each ticker has fits on (its snapshot days)."""
    manual = ROOT / "data" / "manual"
    assets = [FIXTURES / "earnings_sample.csv", *sorted(SNAPSHOTS.glob("earnings_*.csv"))]
    earnings = pd.concat([pd.read_csv(p, dtype=str) for p in assets], ignore_index=True)
    earnings = earnings[earnings["event_ts_ny"].str[:10] >= CAPTURE_START.isoformat()]  # New York event date
    windows = event_windows(earnings, pd.read_csv(manual / "earnings_overrides.csv", dtype=str))
    windows = pd.concat([windows, macro_windows(pd.read_csv(manual / "macro_events.csv", dtype=str))],
                        ignore_index=True)
    windows = windows.sort_values(["event_date", "ticker"], kind="stable", ignore_index=True)
    fits = read_fits()
    return windows, fits, fits.groupby("ticker")["day"].agg(set).to_dict()


def fig_event_scatter(events: pd.DataFrame) -> Path:
    """event_scatter.png (PLAN 6.2): implied move (term structure and straddle) against realised, 45-degree line."""
    plt = _plt()
    done = events[events["realised_move"].notna()]
    fig, ax = plt.subplots(figsize=(7, 6.5))
    top = float(np.nanmax(done[["straddle_move", "ts_move", "realised_move"]].to_numpy() * 100)) * 1.15
    ax.plot([0, top], [0, top], color="0.5", lw=1, ls="--", label="45-degree line")
    ax.plot(done["ts_move"] * 100, done["realised_move"] * 100, "o", color="C0", label="term structure M_t")
    ax.plot(done["straddle_move"] * 100, done["realised_move"] * 100, "x", color="C3", label="straddle M_s")
    for r in done.itertuples():
        ax.annotate(f"{r.ticker} {r.event_date}", (np.nanmax([r.ts_move, r.straddle_move]) * 100,
                                                    r.realised_move * 100), fontsize=7, xytext=(4, 2),
                    textcoords="offset points")
    ax.set_xlim(0, top)
    ax.set_ylim(0, top)
    ax.set_xlabel("implied move (%)")
    ax.set_ylabel("realised move |ln(close_end / close_start)| (%)")
    ax.set_title(f"Implied against realised event moves, {len(done)} events with a realised move")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    return _save(fig, FIGURES / "event_scatter.png")


def fig_event_term_structures(events: pd.DataFrame, fits: pd.DataFrame) -> Path:
    """event_term_structures.png (PLAN 6.2): for the 4 events with the largest term structure move, the ATM total
    variance theta = w(0) of every accepted slice on the pre-event snapshot day against T, with E1 and E2 marked."""
    plt = _plt()
    top = events[events["ts_move"].notna()].sort_values("ts_move", ascending=False, kind="stable").head(4)
    fig, axes = plt.subplots(1, 4, figsize=(17, 4.5), squeeze=False)
    for ax, r in zip(axes.flat, top.itertuples(), strict=False):
        f = fits[(fits["day"] == r.pre_snap_date) & (fits["ticker"] == r.ticker) & fits["status"].isin(ACCEPTED)]
        f = f.sort_values("T")
        theta = svi_w(0.0, f["a"], f["b"], f["rho"], f["m"], f["s"])
        ax.plot(f["T"] * 365, theta, "o-", ms=3, color="C0", label="accepted slices")
        for e, label in ((r.E1, "E1"), (r.E2, "E2")):
            x = f[f["expiry"] == e]
            ax.plot(x["T"] * 365, svi_w(0.0, x["a"], x["b"], x["rho"], x["m"], x["s"]), "o", ms=8, mfc="none",
                    color="C3")
            ax.annotate(label, (x["T"].iloc[0] * 365, float(svi_w(0.0, *x[PARAMS].iloc[0]))), xytext=(5, -10),
                        textcoords="offset points", color="C3")
        ax.set_xlim(0, min(f["T"].max() * 365, 120))
        ax.set_ylim(0, float(theta[f["T"] * 365 <= 120].max()) * 1.1)
        ax.set_title(f"{r.ticker} {r.timing} {r.event_date}, snapshot {r.pre_snap_date}\n"
                     f"M_t {r.ts_move * 100:.2f}%, M_s {r.straddle_move * 100:.2f}%", fontsize=9)
        ax.set_xlabel("days to expiry")
        ax.grid(alpha=0.3)
    for ax in list(axes.flat)[len(top):]:
        ax.set_visible(False)
    axes[0, 0].set_ylabel("ATM total variance theta = w(0)")
    axes[0, 0].legend(fontsize=8)
    fig.suptitle("Term structure before the event: the 4 largest term structure implied moves (first 120 days)")
    fig.tight_layout()
    return _save(fig, FIGURES / "event_term_structures.png")


def stage_events(cfg) -> Path:
    """PLAN 6.2 with instruction 06: events.csv (EVENTS) for every earnings and macro event, event_summary.csv
    (kickoff 5.7, descriptive only below `[events] min_n`), and the 2 event figures."""
    windows, fits, snapshot_days = event_inputs(cfg)
    pre = [pre_event_snapshot(w.start, snapshot_days.get(w.ticker, set())) if isinstance(w.start, str) else None
           for w in windows.itertuples()]
    need = windows.assign(pre=pre).dropna(subset=["pre"])
    chains = pd.concat([_chain_inputs(date.fromisoformat(d), set(g["ticker"]), cfg)
                        for d, g in need.groupby("pre", sort=True)], ignore_index=True)
    events = event_table(windows, chains, fits, _closes(), snapshot_days, cfg)
    summary = event_summary(events, cfg)
    TABLES.mkdir(parents=True, exist_ok=True)
    events.to_csv(TABLES / "events.csv", **CSV)
    summary.to_csv(TABLES / "event_summary.csv", **CSV)
    print(windows.to_string())
    print(events.to_string())
    print(summary.to_string())
    print(events["status"].value_counts().to_string())
    print(f"no_pre_snapshot events: {int((events['status'] == 'no_pre_snapshot').sum())}")
    fig_event_scatter(events)
    fig_event_term_structures(events, fits)
    return TABLES / "events.csv"


def fig_cor3m(series: pd.DataFrame, study: dict) -> Path:
    """cor3m_vs_realised.png (instruction 07 part C): COR3M / 100 on day t and the forward realised average pairwise
    correlation of the 9 sector SPDRs over sessions t+1 to t+63, the gap between them shaded."""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(11, 5))
    t = series["t"]
    ax.fill_between(t, series["implied"], series["realised"], where=series["gap"] >= 0, color="C0", alpha=0.25,
                    lw=0, label="implied above realised")
    ax.fill_between(t, series["implied"], series["realised"], where=series["gap"] < 0, color="C3", alpha=0.25,
                    lw=0, label="implied below realised")
    ax.plot(t, series["implied"], color="C0", lw=0.8, label="COR3M / 100 on day t (implied)")
    ax.plot(t, series["realised"], color="C3", lw=0.8, label="sector SPDR realised, sessions t+1 to t+63")
    ax.set_ylabel("correlation")
    ax.set_title(f"COR3M against forward realised sector correlation, {study['first_t']} to {study['last_t']} "
                 f"(n {study['n']}): slope {study['slope']:.3f}, R² {study['r2']:.3f}, mean gap "
                 f"{study['mean_gap']:.3f}", fontsize=10)
    fig.text(0.01, 0.01, "Sector-level proxy: sector ETFs are diversified baskets and correlate with each other more "
             "than the single stocks behind COR3M,\nso implied sits below realised. The gap is the proxy, not a "
             "correlation risk premium.", fontsize=8)
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.3)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    return _save(fig, FIGURES / "cor3m_vs_realised.png")


def stage_cor3m(cfg) -> Path:
    """PLAN 7.1 with instruction 07: the COR3M study on data/raw/cboe/COR3M.csv and data/raw/prices/sectors.parquet
    (cor3m_study.csv, STUDY_COLUMNS) and cor3m_vs_realised.png."""
    cor3m = pd.read_csv(RAW / "cboe" / "COR3M.csv", parse_dates=["date"]).set_index("date")["close"]
    sectors = pd.read_parquet(RAW / "prices" / "sectors.parquet")[list(cfg.universe.sector_spdrs)]
    study = cor3m_study(cor3m, sectors, cfg.correlation.cor3m_horizon, cfg.correlation.nw_maxlags)
    table = pd.DataFrame([{c: study[c] for c in STUDY_COLUMNS}])
    TABLES.mkdir(parents=True, exist_ok=True)
    out = TABLES / "cor3m_study.csv"
    table.to_csv(out, **CSV)
    print(table.T.to_string())
    print(study["series"].head(3).to_string())
    print(study["series"].tail(3).to_string())
    fig_cor3m(study["series"], study)
    return out


def stage_live_corr(cfg) -> Path:
    """PLAN 7.2 with instruction 07: implied_corr_live.csv (XLK implied correlation per SURFACE_DAILY day, weights from
    data/raw/ssga/xlk_holdings_2026-10-28.csv; the realised side from adj_close.parquet, instruction 08) and
    rv_screen.csv."""
    surface = pd.read_csv(TABLES / "surface_daily.csv", dtype={"day": str})
    holdings = pd.read_csv(RAW / "ssga" / "xlk_holdings_2026-10-28.csv")  # instruction 07 step 7.2: not refreshed
    weights = holdings.dropna(subset=["ticker"]).set_index("ticker")["weight"]
    adj = pd.read_parquet(RAW / "prices" / "adj_close.parquet")
    last_price = pd.Timestamp(adj.index.max()).strftime("%Y-%m-%d")
    live = live_implied_corr(surface, weights, adj, last_price, cfg)
    rv = rv_screen(surface, cfg)
    TABLES.mkdir(parents=True, exist_ok=True)
    live.to_csv(TABLES / "implied_corr_live.csv", **CSV)
    rv.to_csv(TABLES / "rv_screen.csv", **CSV)
    print(f"last close in close.parquet: {last_price}")
    print(live.to_string())
    last = rv[rv["day"] == rv["day"].max()].sort_values("vol_minus_group_median", ascending=False, kind="stable")
    print(f"RV screen on {rv['day'].max()}, top 5 by vol minus group median:")
    print(last.head(5).to_string())
    print("bottom 5:")
    print(last.dropna(subset=["vol_minus_group_median"]).tail(5).to_string())
    print(rv["status"].value_counts().to_string())
    return TABLES / "implied_corr_live.csv"


def _vix() -> pd.Series:
    vix = pd.read_csv(RAW / "cboe" / "VIX.csv")
    return pd.Series(vix["CLOSE"].to_numpy(), index=pd.to_datetime(vix["DATE"], format="%m/%d/%Y"))


def _cboe(name: str) -> pd.Series:
    d = pd.read_csv(RAW / "cboe" / f"{name}.csv")
    return pd.Series(d["close"].to_numpy(), index=pd.to_datetime(d["date"]))


def _dtb3() -> pd.Series:
    d = pd.read_csv(RAW / "fred" / "DTB3.csv")
    return pd.Series(pd.to_numeric(d["DTB3"], errors="coerce").to_numpy(), index=pd.to_datetime(d["observation_date"]))


def stage_vrp(cfg) -> Path:
    """PLAN 8.1 with instruction 08: vrp_monthly.csv (VRP_MONTHLY) at the completed month ends of `^GSPC` from
    `[vrp] start`."""
    index = pd.read_parquet(RAW / "prices" / "index.parquet")
    start = time.perf_counter()
    vm = vrp_monthly(_vix(), index["^GSPC"], cfg)
    print(f"vrp_monthly: {len(vm)} month ends, {time.perf_counter() - start:.1f} s")
    TABLES.mkdir(parents=True, exist_ok=True)
    out = TABLES / "vrp_monthly.csv"
    vm.to_csv(out, **CSV)
    print(vm.head(5).to_string())
    print(vm.tail(5).to_string())
    g = vm.dropna(subset=["garch_fc"])
    print(g.head(5).to_string())
    both, sig = vm.dropna(subset=["iv", "rv_fwd_21"]), vm["signal"].dropna()
    with_fc = both.dropna(subset=["garch_fc"])
    print(f"mean vrp: {both['vrp'].mean()!r} over {len(both)} rows with IV and RV; {with_fc['vrp'].mean()!r} over "
          f"{len(with_fc)} rows that also have a GARCH forecast; signal > 0 in {int((sig > 0).sum())} of {len(sig)} "
          f"months ({(sig > 0).mean()!r})")
    return out


def fig_vrp(vm: pd.DataFrame) -> Path:
    """vrp_vix2_vs_rv.png (PLAN 8.2): VIX^2 at each month end against the S&P 500 variance over the next 21
    sessions, with the GARCH forecast, annualised variance."""
    plt = _plt()
    t = pd.to_datetime(vm["month_end"])
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(t, vm["iv"], color="C0", lw=0.9, label="implied: (VIX / 100)^2 at the month end")
    ax.plot(t, vm["rv_fwd_21"], color="C3", lw=0.9, label="realised: S&P 500 variance over the next 21 sessions")
    ax.plot(t, vm["garch_fc"], color="0.3", lw=0.8, ls="--", label="GARCH(1,1) forecast, next 21 sessions")
    both = vm.dropna(subset=["iv", "rv_fwd_21"])
    ax.set_yscale("log")
    ax.set_ylabel("annualised variance (log scale)")
    ax.set_title(f"VIX squared against forward realised variance, {vm['month_end'].iloc[0]} to "
                 f"{vm['month_end'].iloc[-1]}: mean IV - RV {both['vrp'].mean():.4f} over {len(both)} months, IV "
                 f"above RV in {(both['vrp'] > 0).mean() * 100:.0f}% of them", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, which="both")
    fig.tight_layout()
    return _save(fig, FIGURES / "vrp_vix2_vs_rv.png")


LABELS = {"put": "PUT", "bxm": "BXM", "sp500tr": "S&P 500 TR", "timed_put": "timed PUT", "bxm_long": "BXM"}


def fig_cumulative(strat: pd.DataFrame, bxm_long: pd.DataFrame) -> Path:
    """vrp_cumulative.png (PLAN 8.2, O-28 (a)): cumulative excess return over T-bills, prod(1 + r - tbill), of the
    4 strategies on the common window, log scale; BXM from `[vrp] bxm_start` dashed, a separate window."""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for i, c in enumerate(["put", "bxm", "sp500tr", "timed_put"]):
        w = (1 + strat[c] - strat["tbill"]).cumprod()
        ax.plot(pd.to_datetime(strat["month_end"]), w, color=f"C{i}", lw=1.1, label=f"{LABELS[c]}")
    w = (1 + bxm_long["bxm"] - bxm_long["tbill"]).cumprod()
    ax.plot(pd.to_datetime(bxm_long["month_end"]), w, color="C1", lw=0.9, ls="--",
            label=f"BXM alone from {bxm_long['month_end'].iloc[0]} (separate window)")
    ax.set_yscale("log")
    ax.set_ylabel("growth of 1 in excess of T-bills (log scale)")
    ax.set_title(f"Cumulative excess return, common window {strat['month_end'].iloc[0]} to "
                 f"{strat['month_end'].iloc[-1]} ({len(strat)} months)", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, which="both")
    fig.tight_layout()
    return _save(fig, FIGURES / "vrp_cumulative.png")


def fig_drawdowns(strat: pd.DataFrame) -> Path:
    """vrp_drawdowns.png (PLAN 8.2): drawdown of each strategy's wealth from its running peak (`drawdown`)."""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(11, 4.8))
    for i, c in enumerate(["put", "bxm", "sp500tr", "timed_put"]):
        dd = drawdown(strat[c])
        ax.plot(pd.to_datetime(strat["month_end"]), dd * 100, color=f"C{i}", lw=1.0,
                label=f"{LABELS[c]} (worst {dd.min() * 100:.1f}%)")
    ax.set_ylabel("drawdown from peak (%)")
    ax.set_title(f"Drawdowns, {strat['month_end'].iloc[0]} to {strat['month_end'].iloc[-1]}", fontsize=10)
    ax.legend(fontsize=8, loc="lower center")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return _save(fig, FIGURES / "vrp_drawdowns.png")


MAIN_SPEC = {  # kickoff 5.9 and instruction 08: the main specification, row 1 of spec_log.csv
    "spec_id": "timed_put_main",
    "description": "timed PUT: hold Cboe PUT in month m+1 if (VIX/100)^2 minus the GARCH(1,1) 21-session forecast at "
                   "month end m is above 0, else T-bills; switch cost on every change, the first included",
}


def spec_params(cfg) -> dict:
    v = cfg.vrp
    return {"signal": "iv_minus_garch", "threshold": 0.0, "horizon": v.horizon, "garch_min_obs": v.garch_min_obs,
            "switch_cost_bp": v.switch_cost_bp, "strategy_start": v.strategy_start,
            "tbill": "DTB3 on the last session of month m / 1200"}


def straddle_inputs() -> tuple[list[str], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """^SPX inputs of the live straddles: the SURFACE_DAILY days, each day's quoted strikes with T, S, F, r from the
    IV table, SURFACE_DAILY rows, and the SSVI theta table with each expiry's T from svi_fits.csv."""
    surface = pd.read_csv(TABLES / "surface_daily.csv", dtype={"day": str})
    surface = surface[surface["ticker"] == SPX]
    days = sorted(surface["day"])
    quotes = []
    for d in days:
        iv = pd.read_parquet(PROCESSED / "iv" / f"{d}.parquet")
        iv = iv[(iv["ticker"] == SPX) & iv["iv"].notna()]
        quotes.append(iv.assign(day=d)[["day", "expiry", "strike", "T", "S", "F", "r"]])
    quotes = pd.concat(quotes, ignore_index=True).drop_duplicates(["day", "expiry", "strike"])
    quotes["expiry"] = quotes["expiry"].astype(str)
    theta = pd.read_csv(TABLES / "ssvi_theta.csv", dtype={"day": str, "expiry": str})
    theta = theta[theta["ticker"] == SPX].merge(read_fits()[["day", "ticker", "expiry", "T"]],
                                                on=["day", "ticker", "expiry"], how="left", validate="one_to_one")
    return days, quotes, surface, theta


def stage_strategies(cfg) -> Path:
    """PLAN 8.2 with instruction 08: strategies.csv (STRATEGIES) on the common window from `[vrp] strategy_start`,
    strategy_stats.csv (the 4 strategies, then `bxm_long` from `[vrp] bxm_start`, O-28 (a)), spec_log.csv with the
    deflated Sharpe of the timed PUT, live_straddles.csv, and the 3 Section 8 figures; reads vrp_monthly.csv."""
    v = cfg.vrp
    vm = pd.read_csv(TABLES / "vrp_monthly.csv", dtype={"month_end": str})
    sig = pd.Series(vm["signal"].to_numpy(), index=pd.to_datetime(vm["month_end"]))
    index, put, bxm, dtb3 = pd.read_parquet(RAW / "prices" / "index.parquet"), _cboe("PUT"), _cboe("BXM"), _dtb3()
    strat = strategy_returns(put, bxm, index["^SP500TR"], dtb3, sig[sig.index >= v.strategy_start],
                             v.switch_cost_bp)
    ends = sig.index[sig.index >= v.bxm_start]
    bxm_long = pd.DataFrame({"month_end": ends[1:].strftime("%Y-%m-%d"), "bxm": monthly_returns(bxm, ends).to_numpy(),
                             "tbill": tbill_returns(dtb3, ends).to_numpy()})
    stats = [strategy_stats(c, strat[c], strat["tbill"], strat["month_end"])
             for c in ["put", "bxm", "sp500tr", "timed_put"]]
    stats.append(strategy_stats("bxm_long", bxm_long["bxm"], bxm_long["tbill"], bxm_long["month_end"]))
    timed = stats[3]
    log = append_spec(TABLES / "spec_log.csv", MAIN_SPEC["spec_id"], MAIN_SPEC["description"], spec_params(cfg),
                      timed["sharpe"], timed["n_months"])
    trials = log["sharpe"].astype(float) / np.sqrt(12)  # O-17 (a): monthly Sharpe ratios
    dsr = deflated_sharpe(sr=timed["sharpe"] / np.sqrt(12), n_obs=timed["n_months"], skew=timed["skew"],
                          kurt_pearson=timed["excess_kurtosis"] + 3, sr_trials=trials)
    for s in stats:
        s.update(n_trials=np.nan, deflated_sharpe=np.nan, dsr_status="")
    timed.update(n_trials=len(log), deflated_sharpe=dsr, dsr_status="ok" if len(log) >= 2 else "too_few_trials")
    stats = pd.DataFrame(stats)[STATS_COLUMNS]
    hold = timed_positions(sig[sig.index >= v.strategy_start])
    straddles = live_straddles(*straddle_inputs(), v.straddle_target_days)
    TABLES.mkdir(parents=True, exist_ok=True)
    strat.to_csv(TABLES / "strategies.csv", **CSV)
    stats.to_csv(TABLES / "strategy_stats.csv", **CSV)
    straddles.to_csv(TABLES / "live_straddles.csv", **CSV)
    print(strat.head(3).to_string())
    print(strat.tail(3).to_string())
    print(f"timed PUT: PUT in {int(hold.sum())} of {len(hold)} months, {int(hold.ne(hold.shift(1)).sum())} changes "
          f"(the first position counts)")
    print(stats.to_string())
    print(log.to_string())
    for c in ["put", "bxm", "sp500tr", "timed_put"]:
        print(f"10 worst months, {c}:")
        print(strat.sort_values(c, kind="stable").head(10)[["month_end", c, "tbill"]].to_string())
    print(straddles.to_string())
    fig_vrp(vm)
    fig_cumulative(strat, bxm_long)
    fig_drawdowns(strat)
    return TABLES / "strategy_stats.csv"


def stage_attribution(cfg) -> Path:
    """PLAN 9.2 with instruction 09: hedging_frequency.csv and attribution_live.csv (reads live_straddles.csv), and
    the synthetic path of step 9.1 in attribution_synthetic.csv (O-51 (a))."""
    freq = pd.concat([simulate_hedging(m, cfg) for m in ("gbm", "heston")], ignore_index=True)
    live = attribute_live(pd.read_csv(TABLES / "live_straddles.csv", dtype={"open_day": str, "expiry": str,
                                                                           "mark_day": str}))
    TABLES.mkdir(parents=True, exist_ok=True)
    freq.to_csv(TABLES / "hedging_frequency.csv", **CSV)
    live.to_csv(TABLES / "attribution_live.csv", **CSV)
    path = bs_path_attribution(cfg)
    path.to_csv(TABLES / "attribution_synthetic.csv", **CSV)
    print(path.to_string())
    print(f"MEASURE median explained share, {len(path)} daily steps: {path['explained_share'].median():.6f}")
    print(freq.to_string())
    print(live.to_string())
    print(f"median explained share, {len(live)} live moves: {live['explained_share'].median():.6f}")
    return TABLES / "hedging_frequency.csv"


def risk_inputs(day: date) -> tuple[pd.DataFrame, dict[str, dict]]:
    """The day's IV table, and `day_surface` for each underlying with SSVI parameters that day, with each accepted
    expiry's T and SVI parameters from svi_fits.csv."""
    iv = pd.read_parquet(PROCESSED / "iv" / f"{day}.parquet")
    surface = pd.read_csv(TABLES / "surface_daily.csv", dtype={"day": str})
    surface = surface[(surface["day"] == str(day)) & surface["ssvi_rho"].notna()]
    theta = pd.read_csv(TABLES / "ssvi_theta.csv", dtype={"day": str, "expiry": str})
    fits = read_fits()
    theta = theta[theta["day"] == str(day)].merge(fits[["day", "ticker", "expiry", "T"]],
                                                  on=["day", "ticker", "expiry"], how="left", validate="one_to_one")
    acc = fits[(fits["day"] == str(day)) & fits["status"].isin(ACCEPTED)]
    slices = {t: {r["expiry"]: tuple(r[PARAMS]) for _, r in g.iterrows()} for t, g in acc.groupby("ticker")}
    return iv, {row["ticker"]: day_surface(row, theta[theta["ticker"] == row["ticker"]], slices.get(row["ticker"]))
                for _, row in surface.iterrows()}


def stage_risk(cfg) -> Path:
    """PLAN 10.1 with instruction 10, on the last captured day: risk_book.csv, risk_grid.csv, limit_breaches.csv."""
    day = _days()[-1]
    iv, surface = risk_inputs(day)
    book = select_book(day, cfg.book.positions, iv, surface)
    risk = book_risk(book, surface, cfg)
    grid = shock_grid(book, surface, cfg)
    breaches = limit_breaches(risk, cfg)
    TABLES.mkdir(parents=True, exist_ok=True)
    risk.to_csv(TABLES / "risk_book.csv", **CSV)
    grid.to_csv(TABLES / "risk_grid.csv", **CSV)
    breaches.to_csv(TABLES / "limit_breaches.csv", **CSV)
    print(risk.to_string())
    quote = iv.assign(expiry=iv["expiry"].astype(str))[["ticker", "expiry", "kind", "strike", "mid", "iv"]]
    vs = risk.merge(quote, left_on=["underlying", "expiry", "kind", "strike"],
                    right_on=["ticker", "expiry", "kind", "strike"], how="left", validate="one_to_one")
    vs = vs.assign(gap_pts=(vs["vol"] - vs["iv"]) * VOL_POINT)
    print(vs[["contract", "days", "select_delta", "vol_source", "vol", "iv", "gap_pts", "mid", "price"]].to_string())
    print(grid[grid["contract"] == "book"].pivot(index="spot_shock", columns="vol_shock_pts", values="pnl").to_string())
    print(breaches.to_string())
    return TABLES / "risk_grid.csv"


def stage_report(cfg) -> Path:
    """PLAN 10.2 with instruction 10: the PDF for the last captured day, from the risk stage's tables."""
    days = _days()
    grid, risk, breaches = (pd.read_csv(TABLES / f"{name}.csv", dtype={"day": str, "expiry": str})
                            for name in ("risk_grid", "risk_book", "limit_breaches"))
    return build_risk_report(days[-1], grid, risk, breaches, REPORTS / f"risk_{days[-1]}.pdf", len(days))


def stage_answers(cfg) -> Path:
    """PLAN 11.2 with instruction 11: answers.csv, each row tied to a source table and row."""
    from volsurf.answers import build_answers

    table = build_answers(TABLES, cfg)
    out = TABLES / "answers.csv"
    table.to_csv(out, index=False, lineterminator="\n", encoding="utf-8")
    print(table.to_string())
    return out


def _test_count() -> int:
    """The number of tests pytest collects, for the README's status line (instruction 11 step 11.3)."""
    res = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], cwd=ROOT, capture_output=True,
                         text=True, check=True)
    return int(re.search(r"(\d+) tests? collected", res.stdout).group(1))


def stage_readme(cfg) -> Path:
    """PLAN 11.3 with instruction 11: README.md from docs/README.template.md and the tables."""
    from volsurf.readme import build_readme

    out = ROOT / "README.md"
    template = (ROOT / "docs" / "README.template.md").read_text(encoding="utf-8")
    out.write_text(build_readme(template, TABLES, _test_count(), cfg.events.min_n), encoding="utf-8", newline="\n")
    print(f"README.md: {out.stat().st_size} bytes")
    return out


STAGES = {"snapshots": stage_snapshots, "capture_health": stage_capture_health, "pricer_check": stage_pricer_check,
          "eep": stage_eep, "clean_log": stage_clean_log, "iv_tree": stage_iv_tree, "iv": stage_iv,
          "surface": stage_surface, "density": stage_density,
          "tails": stage_tails, "events": stage_events, "cor3m": stage_cor3m, "live_corr": stage_live_corr,
          "vrp": stage_vrp, "strategies": stage_strategies, "attribution": stage_attribution,
          "risk": stage_risk, "report": stage_report, "answers": stage_answers, "readme": stage_readme}

STAGE_OUTPUTS = {  # what each stage writes, {day} for any capture day; tests/test_run_all.py holds PLAN.md to it
    "snapshots": ["data/raw/snapshot_manifest.csv"],
    "capture_health": ["outputs/tables/capture_health.csv"],
    "pricer_check": ["outputs/tables/pricer_check.csv"],
    "eep": ["outputs/tables/eep_rows.csv", "outputs/tables/eep_summary.csv"],
    "clean_log": ["outputs/tables/clean_log_fixture.csv"],
    "iv_tree": ["outputs/tables/iv_tree_convergence.csv"],
    "iv": ["outputs/tables/iv_summary.csv", "outputs/tables/parity_forwards_fixture.csv"],
    "surface": ["outputs/tables/svi_fits.csv", "outputs/tables/surface_daily.csv",
                "outputs/tables/calendar_violations.csv", "outputs/tables/ssvi_theta.csv",
                "outputs/figures/spx_smiles_{day}.png", "outputs/figures/spx_smile_fits_{day}.png",
                "outputs/figures/spx_surface_last.png", "outputs/figures/spx_metrics.png"],
    "density": ["outputs/tables/density_checks.csv"],
    "tails": ["outputs/tables/tail_probs.csv", "outputs/tables/pit.csv", "outputs/figures/spx_density_last.png"],
    "events": ["outputs/tables/events.csv", "outputs/tables/event_summary.csv", "outputs/figures/event_scatter.png",
               "outputs/figures/event_term_structures.png"],
    "cor3m": ["outputs/tables/cor3m_study.csv", "outputs/figures/cor3m_vs_realised.png"],
    "live_corr": ["outputs/tables/implied_corr_live.csv", "outputs/tables/rv_screen.csv"],
    "vrp": ["outputs/tables/vrp_monthly.csv"],
    "strategies": ["outputs/tables/strategies.csv", "outputs/tables/strategy_stats.csv", "outputs/tables/spec_log.csv",
                   "outputs/tables/live_straddles.csv", "outputs/figures/vrp_vix2_vs_rv.png",
                   "outputs/figures/vrp_cumulative.png", "outputs/figures/vrp_drawdowns.png"],
    "attribution": ["outputs/tables/hedging_frequency.csv", "outputs/tables/attribution_live.csv",
                    "outputs/tables/attribution_synthetic.csv"],
    "risk": ["outputs/tables/risk_book.csv", "outputs/tables/risk_grid.csv", "outputs/tables/limit_breaches.csv"],
    "report": ["outputs/reports/risk_{day}.pdf"],
    "answers": ["outputs/tables/answers.csv"],
    "readme": ["README.md"],
}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage", choices=[*STAGES, "all"], default="all")
    p.add_argument("--force", action="store_true", help="surface stage: refit every day, ignoring the cache")
    args = p.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")  # answers holds U+2212, which a piped Windows stdout (cp1252) cannot encode
    cfg = load_config()
    begin = time.perf_counter()
    for name in STAGES if args.stage == "all" else [args.stage]:
        kwargs = {"force": args.force} if name == "surface" else {}
        start = time.perf_counter()
        print(f"{name}: wrote {STAGES[name](cfg, **kwargs)}")
        print(f"runtime {name}: {time.perf_counter() - start:.1f} s", flush=True)
    print(f"runtime total: {time.perf_counter() - begin:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
