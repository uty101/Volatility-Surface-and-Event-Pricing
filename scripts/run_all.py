"""Rebuild entry point (O-1 (a)): each step's driver is a stage, run with --stage <name>.

Section 11.1 completes this script; Section 1 adds the capture_health stage, Section 2 the eep stage and
Section 3 the clean_log and iv stages, Section 4 the surface stage, Section 5 the density and tails stages, Section 6
the events stage, Section 7 the cor3m stage.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import io
import json
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from volsurf.config import load_config
from volsurf.correlation import STUDY_COLUMNS, cor3m_study
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
from volsurf.iv import iv_chain, iv_inputs, iv_summary
from volsurf.pricing import K_BIN_LABELS, eep_rows, eep_summary
from volsurf.ssvi import ssvi_w, surface_day, theta_at
from volsurf.svi import ACCEPTED, PARAMS, svi_w

SNAPSHOTS = ROOT / "data" / "snapshots"
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
FIXTURES = ROOT / "tests" / "fixtures"
TABLES = ROOT / "outputs" / "tables"
FIGURES = ROOT / "outputs" / "figures"
CAPTURE_START = date(2026, 10, 28)  # kickoff Section 3.3: capture window starts 2026-10-28
FIXTURE_DAY = date(2026, 10, 28)  # instruction 01d part B: the fixture day
CSV = {"index": False, "float_format": "%.10g", "lineterminator": "\n", "encoding": "utf-8"}
FULL = "%.17g"  # O-39 (a), instruction 06: SVI parameters in svi_fits.csv at full precision


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
    """Instruction 07 step 7.0: sha256 over volsurf/svi.py, volsurf/ssvi.py, the [svi] and [surface] config tables
    and the day's IV file (the sha256 of each part, concatenated, hashed again)."""
    tables = [json.dumps(dataclasses.asdict(t), sort_keys=True).encode() for t in (cfg.svi, cfg.surface)]
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



STAGES = {"capture_health": stage_capture_health, "clean_log": stage_clean_log, "eep": stage_eep, "iv": stage_iv,
          "surface": stage_surface, "density": stage_density,
          "tails": stage_tails, "events": stage_events, "cor3m": stage_cor3m}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage", choices=[*STAGES, "all"], required=True)
    p.add_argument("--force", action="store_true", help="surface stage: refit every day, ignoring the cache")
    args = p.parse_args(argv)
    cfg = load_config()
    for name in STAGES if args.stage == "all" else [args.stage]:
        kwargs = {"force": args.force} if name == "surface" else {}
        print(f"{name}: wrote {STAGES[name](cfg, **kwargs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
