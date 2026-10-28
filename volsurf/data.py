"""Snapshot loader, chain cleaning, rates, dividend yield and session counts (PLAN 1.3)."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import date, datetime, time, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from volsurf.snapshots import NY, _xnys

CLEAN_LOG_COLUMNS = ["day", "ticker", "rule", "rows_before", "rows_dropped", "note"]
SPX = "^SPX"
SPX_RULE_E_NOTE = "deferred to section 3"  # instruction 01, step 1.3 (O-23 (b)), when no forwards are given

# Convention 4.6: CMT tenors in years
RATE_TENORS = {"DGS1MO": 1 / 12, "DGS3MO": 0.25, "DGS6MO": 0.5, "DGS1": 1.0}


def load_snapshot(day: date, root: Path) -> dict[str, pd.DataFrame]:
    """The 4 assets of one capture day: chains, underlying, earnings, snaplog (per-ticker rows, run fields in attrs)."""
    root = Path(root)
    d = day.isoformat()
    names = {
        "chains": f"chains_{d}.parquet",
        "underlying": f"underlying_{d}.csv",
        "earnings": f"earnings_{d}.csv",
        "snaplog": f"snaplog_{d}.json",
    }
    for key, name in names.items():
        if not (root / name).exists():
            raise FileNotFoundError(f"no {key} asset for {d}: {name} is not in {root}")
    snaplog = json.loads((root / names["snaplog"]).read_text(encoding="utf-8"))
    per_ticker = pd.DataFrame(snaplog.get("tickers", []))
    per_ticker.attrs = {k: v for k, v in snaplog.items() if k != "tickers"}
    return {
        "chains": pd.read_parquet(root / names["chains"]),
        "underlying": pd.read_csv(root / names["underlying"]),
        "earnings": pd.read_csv(root / names["earnings"]),
        "snaplog": per_ticker,
    }


def sessions_between(t: date, e: date) -> int:
    """Convention 4.2: number of XNYS sessions s with t < s <= e."""
    if e <= t:
        return 0
    return len(_xnys().sessions_in_range(pd.Timestamp(t + timedelta(days=1)), pd.Timestamp(e)))


def last_completed_session(now_utc: datetime) -> date:
    """The latest XNYS session whose close (early closes included) is at or before now_utc (instruction 01c, 1c.3)."""
    now = pd.Timestamp(now_utc).tz_convert("UTC")
    closes = _xnys().closes.loc[: now.tz_localize(None).normalize()]
    return closes[closes <= now].index[-1].date()


def _american_in_bounds(mid: pd.Series, kind: pd.Series, strike: pd.Series, spot: pd.Series) -> pd.Series:
    """Section 5.3 American bounds: call in [max(S - K, 0), S), put in [max(K - S, 0), K)."""
    call = (mid >= np.maximum(spot - strike, 0.0)) & (mid < spot)
    put = (mid >= np.maximum(strike - spot, 0.0)) & (mid < strike)
    return np.where(kind == "C", call, put)


def _european_in_bounds(mid, kind, strike, F, D):
    """Section 5.3 European bounds: call in (max(D(F - K), 0), D F), put in (max(D(K - F), 0), D K)."""
    call = (mid > np.maximum(D * (F - strike), 0.0)) & (mid < D * F)
    put = (mid > np.maximum(D * (strike - F), 0.0)) & (mid < D * strike)
    return np.where(kind == "C", call, put)


def _stale(chain: pd.DataFrame, stale_sessions: int) -> pd.Series:
    """Convention 4.4: last trade more than stale_sessions sessions before the snapshot, or missing."""
    snap_days = pd.to_datetime(chain["snap_utc"], utc=True).dt.tz_convert(NY).dt.date
    trade_days = pd.to_datetime(chain["last_trade_utc"], utc=True).dt.tz_convert(NY).dt.date
    out = []
    for snap_day, trade_day in zip(snap_days, trade_days, strict=True):
        out.append(pd.isna(trade_day) or sessions_between(trade_day, snap_day) > stale_sessions)
    return pd.Series(out, index=chain.index, dtype=bool)


def clean_chain(chains: pd.DataFrame, underlying: pd.DataFrame, cfg,
                forwards: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Convention 4.4 rules a to e in order, one CLEAN_LOG row per ticker and rule; flags stale and after_close.

    Rule e for `^SPX` uses the European bounds with each expiry's D and F from `forwards` (columns expiry, D, F,
    status; instruction 03 step 3.1). Rows of an expiry without an accepted forward cannot be checked and are
    kept (the IV step flags them parity_fail), with their count in the note. Without `forwards`, rule e for
    `^SPX` is deferred as in Section 1 (O-23 (b))."""
    c = cfg.clean
    close_ny = time.fromisoformat(cfg.snapshot.close_ny)
    spot_by_ticker = underlying.set_index("ticker")["price"]
    kept, log = [], []
    for ticker, chain in chains.groupby("ticker", sort=False):
        day = pd.Timestamp(chain["snap_utc"].iloc[0]).tz_convert(NY).date().isoformat()
        mid = (chain["bid"] + chain["ask"]) / 2  # Convention 4.3
        spot = pd.Series(spot_by_ticker.get(ticker, np.nan), index=chain.index)
        rules = [
            ("a", ~(chain["bid"] > 0), ""),
            ("b", ~(chain["ask"] > chain["bid"]), ""),
            ("c", ~(mid >= c.min_mid), ""),
            ("d", ~((chain["ask"] - chain["bid"]) / mid <= c.max_rel_spread), ""),
        ]
        if ticker == SPX and forwards is None:
            rules.append(("e", pd.Series(False, index=chain.index), SPX_RULE_E_NOTE))
        elif ticker == SPX:
            fw = forwards[forwards["status"] == "ok"].set_index("expiry")
            F, D = chain["expiry"].map(fw["F"]), chain["expiry"].map(fw["D"])
            inside = _european_in_bounds(mid, chain["kind"], chain["strike"], F, D)
            unchecked = F.isna()
            n_unchecked = int((unchecked & ~pd.concat([d for _, d, _ in rules], axis=1).any(axis=1)).sum())
            rules.append(("e", ~pd.Series(inside, index=chain.index) & ~unchecked,
                          f"{n_unchecked} rows on parity_fail expiries not checked" if n_unchecked else ""))
        else:
            inside = _american_in_bounds(mid, chain["kind"], chain["strike"], spot)
            rules.append(("e", ~pd.Series(inside, index=chain.index), ""))
        alive = pd.Series(True, index=chain.index)
        for rule, drop, note in rules:
            before = int(alive.sum())
            hit = alive & drop
            alive &= ~hit
            log.append({"day": day, "ticker": ticker, "rule": rule, "rows_before": before,
                        "rows_dropped": int(hit.sum()), "note": note})
        out = chain[alive].copy()
        out["stale"] = _stale(out, c.stale_sessions)
        snap_ny = pd.to_datetime(out["snap_utc"], utc=True).dt.tz_convert(NY)
        out["after_close"] = snap_ny.dt.time > close_ny
        kept.append(out)
    clean = pd.concat(kept) if kept else chains.assign(stale=pd.Series(dtype=bool), after_close=pd.Series(dtype=bool))
    return clean.reset_index(drop=True), pd.DataFrame(log, columns=CLEAN_LOG_COLUMNS)


CAPTURE_HEALTH_COLUMNS = [
    "session", "runner", "start_ny", "ny_start", "minutes_after_1530", "tickers_ok", "rows", "after_close_rows",
    "gap",
]


def capture_health(snap_dir: Path, first_session: date, cfg) -> pd.DataFrame:
    """PLAN 1.4: one row per XNYS session from first_session to the last downloaded day. A session is a gap
    when it has no non-test chains asset (O-5 (b)); test_ assets are ignored."""
    snap_dir = Path(snap_dir)
    days = sorted(date.fromisoformat(p.stem.removeprefix("chains_")) for p in snap_dir.glob("chains_*.parquet"))
    if not days or days[-1] < first_session:
        return pd.DataFrame(columns=CAPTURE_HEALTH_COLUMNS)
    close_ny = time.fromisoformat(cfg.snapshot.close_ny)
    target_ny = time.fromisoformat("15:30")  # instruction 01, step 1.4: minutes after 15:30 New York
    rows = []
    for session in _xnys().sessions_in_range(pd.Timestamp(first_session), pd.Timestamp(days[-1])):
        d = session.date()
        row = dict.fromkeys(CAPTURE_HEALTH_COLUMNS)
        row.update(session=d.isoformat(), gap=d not in days)
        if not row["gap"]:
            chains = pd.read_parquet(snap_dir / f"chains_{d.isoformat()}.parquet", columns=["snap_utc"])
            snap_ny = pd.to_datetime(chains["snap_utc"], utc=True).dt.tz_convert(NY)
            row.update(rows=len(chains), after_close_rows=int((snap_ny.dt.time > close_ny).sum()))
            log_path = snap_dir / f"snaplog_{d.isoformat()}.json"
            if log_path.exists():
                log = json.loads(log_path.read_text(encoding="utf-8"))
                start = pd.Timestamp(log["ny_start"]).tz_convert(NY)
                target = pd.Timestamp.combine(start.date(), target_ny).tz_localize(NY)
                row.update(runner=log["runner"], start_ny=start.strftime("%H:%M:%S"), ny_start=start.isoformat(),
                           minutes_after_1530=(start - target).total_seconds() / 60, tickers_ok=log["n_ok"])
        rows.append(row)
    return pd.DataFrame(rows, columns=CAPTURE_HEALTH_COLUMNS)


def _cmt_to_continuous(y: float) -> float:
    """Convention 4.6: bond-equivalent CMT yield y in percent -> continuous r = 2 ln(1 + y/200)."""
    return 2.0 * np.log1p(y / 200.0)


def rate_curve(fred: dict[str, pd.DataFrame], day: date) -> Callable[[float], float]:
    """Convention 4.6 curve for snapshot day `day`: per tenor the latest valid observation dated <= day - 1
    (O-7 (a)), converted to continuous r, linear in T between tenors and flat beyond."""
    tenors, rates = [], []
    for sid, tenor in RATE_TENORS.items():
        frame = fred[sid]
        obs = pd.DataFrame({
            "date": pd.to_datetime(frame.iloc[:, 0]).dt.date,
            "y": pd.to_numeric(frame[sid], errors="coerce"),  # FRED marks missing values with '.' or blank
        })
        valid = obs[(obs["date"] < day) & obs["y"].notna()].sort_values("date")
        if valid.empty:
            raise ValueError(f"{sid}: no valid observation dated on or before {day - timedelta(days=1)}")
        tenors.append(tenor)
        rates.append(_cmt_to_continuous(float(valid["y"].iloc[-1])))
    t_arr, r_arr = np.array(tenors), np.array(rates)

    def r(T: float) -> float:
        return float(np.interp(T, t_arr, r_arr))  # np.interp holds the end values flat beyond the tenors

    return r


def dividend_yield(divs: pd.DataFrame, spot: float, day: date) -> float:
    """Convention 4.7: cash dividends with ex-date in (day - 365 days, day], divided by spot; 0 if none."""
    ex = pd.to_datetime(divs["date"]).dt.date
    window = (ex > day - timedelta(days=365)) & (ex <= day)
    return float(divs.loc[window, "dividend"].sum()) / spot
