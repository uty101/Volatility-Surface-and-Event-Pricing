"""Rebuild entry point (O-1 (a)): each step's driver is a stage, run with --stage <name>.

Section 11.1 completes this script; Section 1 adds the capture_health stage, Section 2 the eep stage and
Section 3 the clean_log and iv stages, Section 4 the surface stage.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from volsurf.config import load_config
from volsurf.data import RATE_TENORS, SPX, capture_health, clean_chain, load_snapshot
from volsurf.forwards import clean_with_forwards
from volsurf.iv import iv_chain, iv_inputs, iv_summary
from volsurf.pricing import K_BIN_LABELS, eep_rows, eep_summary
from volsurf.ssvi import ssvi_w, surface_day, theta_at
from volsurf.svi import ACCEPTED, svi_w

SNAPSHOTS = ROOT / "data" / "snapshots"
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
FIXTURES = ROOT / "tests" / "fixtures"
TABLES = ROOT / "outputs" / "tables"
FIGURES = ROOT / "outputs" / "figures"
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


def _days() -> list[date]:
    """The fixture day plus every downloaded snapshot day (instruction 03 step 3.3, instruction 04 step 4.3)."""
    snaps = sorted(date.fromisoformat(p.stem.removeprefix("chains_")) for p in SNAPSHOTS.glob("chains_*.parquet"))
    return [FIXTURE_DAY, *[d for d in snaps if d != FIXTURE_DAY]]


def surface_tables(ivs: list[pd.DataFrame], cfg) -> dict[str, pd.DataFrame]:
    """PLAN 4.3: `surface_day` on each day's IV table, concatenated in day order."""
    parts = [surface_day(iv, cfg) for iv in ivs]
    return {name: pd.concat([p[name] for p in parts], ignore_index=True) for name in parts[0]}


SURFACE_FILES = {"svi_fits": "svi_fits.csv", "surface": "surface_daily.csv", "calendar": "calendar_violations.csv",
                 "theta": "ssvi_theta.csv"}


def write_surface_tables(tables: dict[str, pd.DataFrame], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, file in SURFACE_FILES.items():
        tables[name].to_csv(out_dir / file, **CSV)
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


def stage_surface(cfg) -> Path:
    """Instruction 04 step 4.3: SVI and SSVI on the fixture day and every downloaded snapshot day, from the iv
    stage's data/processed/iv/{day}.parquet; the 4 surface tables and the Section 4 figures."""
    days = _days()
    ivs = [pd.read_parquet(PROCESSED / "iv" / f"{d.isoformat()}.parquet") for d in days]
    tables = surface_tables(ivs, cfg)
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
    for day in dict.fromkeys([days[0].isoformat(), days[-1].isoformat()]):
        fig_smiles(fits, day)
    fig_smile_fits(fits, ivs[0], FIXTURE_DAY.isoformat())
    fig_surface(tables, days[-1].isoformat())
    fig_metrics(surface)
    return paths[1]


STAGES = {"capture_health": stage_capture_health, "clean_log": stage_clean_log, "eep": stage_eep, "iv": stage_iv,
          "surface": stage_surface}


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
