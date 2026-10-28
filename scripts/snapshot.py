"""Daily option chain capture (kickoff Section 9, step 0.1).

Writes chains_, underlying_, earnings_ and snaplog_ files for the New York date to --out and
uploads them as assets of a GitHub release. --force skips the session and window checks,
prefixes every file with test_ and uploads to the test release.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import tomllib
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import pandas as pd
import yfinance as yf

from volsurf.snapshots import (
    CHAINS_COLUMNS,
    EARNINGS_COLUMNS,
    NY,
    UNDERLYING_COLUMNS,
    chain_frame,
    earnings_frame,
    filter_expiries,
    in_window,
    is_session,
    keep_spxw,
    snapshot_log,
)

ROOT = Path(__file__).resolve().parents[1]
LIBS = ["yfinance", "pandas", "numpy", "pyarrow", "exchange_calendars", "curl_cffi"]


def now_utc() -> datetime:
    return datetime.now(UTC)


def call(fn, snap: dict):
    """Run fn with the retry and backoff rule, then wait request_interval_s."""
    last = None
    for attempt in range(snap["retries"] + 1):
        try:
            result = fn()
            time.sleep(snap["request_interval_s"])
            return result
        except Exception as exc:  # noqa: BLE001 - yfinance raises many types; every one is retried
            last = exc
            if attempt < snap["retries"]:
                time.sleep(snap["backoff_s"][attempt])
    raise last


def nonempty(x):
    if x is None or len(x) == 0:
        raise ValueError("empty response")
    return x


def describe(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}".replace("\n", " ")[:300]


def capture_ticker(ticker: str, cfg: dict, today, want_earnings: bool):
    snap = cfg["snapshot"]
    tk = yf.Ticker(ticker)
    start = now_utc()
    under = dict.fromkeys(UNDERLYING_COLUMNS)
    under.update(ticker=ticker, snap_utc=start, n_expiries_listed=0, n_expiries_kept=0, n_rows=0,
                 n_spx_am_dropped=0, error="")
    frames, errors = [], []
    try:
        listed = list(call(lambda: nonempty(tk.options), snap))
    except Exception as exc:  # noqa: BLE001 - recorded, capture continues
        listed = []
        errors.append(f"options: {describe(exc)}")
    kept = filter_expiries(listed, today, cfg["universe"]["max_days_to_expiry"])
    under.update(n_expiries_listed=len(listed), n_expiries_kept=len(kept))
    failed_expiries = 0
    for expiry in kept:
        try:
            oc = call(lambda e=expiry: tk.option_chain(e), snap)
            frame = chain_frame(oc.calls, oc.puts, ticker, expiry, now_utc())
            if ticker == "^SPX":
                frame, dropped = keep_spxw(frame)
                under["n_spx_am_dropped"] += dropped
            frames.append(frame)
        except Exception as exc:  # noqa: BLE001 - recorded, capture continues
            failed_expiries += 1
            errors.append(f"{expiry}: {describe(exc)}")
    price_ok = False
    try:
        hist = call(lambda: nonempty(tk.history(period="1d", interval="1m")), snap)
        under["price"] = float(hist["Close"].iloc[-1])
        under["price_time_utc"] = pd.Timestamp(hist.index[-1]).tz_convert("UTC")
        price_ok = True
    except Exception as exc:  # noqa: BLE001 - recorded, capture continues
        errors.append(f"price: {describe(exc)}")
    earnings, earnings_error = None, ""
    if want_earnings:
        try:
            raw = call(lambda: tk.get_earnings_dates(limit=12), snap)
            earnings = earnings_frame(raw, ticker, today)
        except Exception as exc:  # noqa: BLE001 - recorded, capture continues
            earnings_error = describe(exc)
    n_rows = int(sum(len(f) for f in frames))
    under["n_rows"] = n_rows
    under["error"] = " | ".join(errors)
    if not price_ok or n_rows == 0:
        status = "error"
    elif failed_expiries or not listed:
        status = "partial"
    else:
        status = "ok"
    end = now_utc()
    log = {
        "ticker": ticker, "status": status, "start_utc": start.isoformat(), "end_utc": end.isoformat(),
        "seconds": round((end - start).total_seconds(), 1), "n_rows": n_rows, "n_expiries_kept": len(kept),
        "failed_expiries": failed_expiries, "earnings_rows": None if earnings is None else len(earnings),
        "earnings_error": earnings_error, "error": under["error"],
    }
    return frames, under, earnings, log


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gh(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args], cwd=ROOT, capture_output=True, text=True, check=False)


def upload(files: list[Path], tag: str, chains_name: str, mode: str) -> str:
    if gh("release", "view", tag).returncode != 0:
        made = gh("release", "create", tag, "--title", tag, "--notes", "daily option chain snapshots")
        if made.returncode != 0 and gh("release", "view", tag).returncode != 0:
            raise RuntimeError(f"gh release create failed: {made.stderr.strip()}")
    if mode == "if-missing":
        names = gh("release", "view", tag, "--json", "assets", "--jq", ".assets[].name")
        if names.returncode != 0:
            raise RuntimeError(f"gh release view failed: {names.stderr.strip()}")
        if chains_name in names.stdout.split():
            return f"skipped: {chains_name} already in release {tag}"
    done = gh("release", "upload", tag, *[str(f) for f in files], "--clobber")
    if done.returncode != 0:
        raise RuntimeError(f"gh release upload failed: {done.stderr.strip()}")
    return f"uploaded {len(files)} files to release {tag}"


def append_log(out: Path, line: str) -> None:
    print(line, flush=True)
    with open(out / "snapshot.log", "a", encoding="utf-8", newline="\n") as fh:
        fh.write(line + "\n")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--force", action="store_true")
    p.add_argument("--runner", choices=["actions", "local"], required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--upload", choices=["always", "if-missing", "never"], required=True)
    args = p.parse_args(argv)

    with open(ROOT / "config.toml", "rb") as fh:
        cfg = tomllib.load(fh)
    snap, uni = cfg["snapshot"], cfg["universe"]
    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    out.mkdir(parents=True, exist_ok=True)

    start = now_utc()
    ny_start = start.astimezone(NY)
    today = ny_start.date()
    window_ok, session_ok = in_window(start, cfg), is_session(today)
    if not args.force and not (window_ok and session_ok):
        append_log(out, f"{start.isoformat()} skip runner={args.runner} ny={ny_start:%Y-%m-%d %H:%M:%S} "
                        f"session={session_ok} in_window={window_ok}")
        return 0

    prefix = "test_" if args.force else ""
    tag = snap["test_release_tag"] if args.force else snap["release_tag"]
    tickers = uni["index"] + uni["etfs"] + uni["xlk_holdings"] + uni["singles"]
    with_earnings = set(uni["xlk_holdings"] + uni["singles"])
    append_log(out, f"{start.isoformat()} start runner={args.runner} ny={ny_start:%Y-%m-%d %H:%M:%S} "
                    f"forced={args.force} tickers={len(tickers)}")

    chains, unders, earns, logs = [], [], [], []
    for ticker in tickers:
        frames, under, earnings, log = capture_ticker(ticker, cfg, today, ticker in with_earnings)
        chains.extend(frames)
        unders.append(under)
        if earnings is not None:
            earns.append(earnings)
        logs.append(log)
        print(f"{ticker:6s} {log['status']:7s} rows={log['n_rows']:6d} expiries={log['n_expiries_kept']:3d} "
              f"failed={log['failed_expiries']} {log['seconds']:6.1f}s {log['error'][:150]}", flush=True)

    day = today.isoformat()
    files = {
        "chains": out / f"{prefix}chains_{day}.parquet",
        "underlying": out / f"{prefix}underlying_{day}.csv",
        "earnings": out / f"{prefix}earnings_{day}.csv",
        "snaplog": out / f"{prefix}snaplog_{day}.json",
    }
    chains_df = pd.concat(chains, ignore_index=True) if chains else pd.DataFrame(columns=CHAINS_COLUMNS)
    chains_df.to_parquet(files["chains"], index=False)
    csv = {"index": False, "float_format": "%.10g", "lineterminator": "\n", "encoding": "utf-8"}
    pd.DataFrame(unders, columns=UNDERLYING_COLUMNS).to_csv(files["underlying"], **csv)
    earnings_df = pd.concat(earns, ignore_index=True) if earns else pd.DataFrame(columns=EARNINGS_COLUMNS)
    earnings_df.to_csv(files["earnings"], **csv)

    summary = snapshot_log(logs)
    end = now_utc()
    snaplog = {
        "run_id": os.environ.get("GITHUB_RUN_ID") or f"local-{start:%Y%m%dT%H%M%SZ}",
        "runner": args.runner,
        "start_utc": start.isoformat(),
        "end_utc": end.isoformat(),
        "ny_start": ny_start.isoformat(),
        "in_window": window_ok,
        "is_session": session_ok,
        "forced": args.force,
        "upload": args.upload,
        "release_tag": tag,
        "min_tickers_ok": snap["min_tickers_ok"],
        **summary,
        "versions": {"python": platform.python_version(), **{lib: version(lib) for lib in LIBS}},
        "sha256": {files[k].name: sha256(files[k]) for k in ("chains", "underlying", "earnings")},
    }
    files["snaplog"].write_text(json.dumps(snaplog, indent=2, default=str) + "\n", encoding="utf-8", newline="\n")
    append_log(out, f"{end.isoformat()} done ok={summary['n_ok']} partial={summary['n_partial']} "
                    f"error={summary['n_error']} rows={len(chains_df)}")

    code = 0 if summary["n_ok"] >= snap["min_tickers_ok"] else 1
    if args.upload != "never":
        try:
            append_log(out, upload(list(files.values()), tag, files["chains"].name, args.upload))
        except Exception as exc:  # noqa: BLE001 - recorded, capture continues
            append_log(out, f"upload failed: {describe(exc)}")
            code = code or 2
    return code


if __name__ == "__main__":
    sys.exit(main())
