"""Pure functions behind the daily chain capture (scripts/snapshot.py). No network here."""

from __future__ import annotations

from datetime import date, datetime, time
from functools import lru_cache
from zoneinfo import ZoneInfo

import exchange_calendars as xcals
import pandas as pd

NY = ZoneInfo("America/New_York")

CHAINS_COLUMNS = [
    "snap_utc", "ticker", "expiry", "kind", "contract_symbol", "strike", "last_price", "bid", "ask",
    "change", "pct_change", "volume", "open_interest", "yahoo_iv", "in_the_money", "last_trade_utc",
    "contract_size", "currency",
]
UNDERLYING_COLUMNS = [
    "ticker", "snap_utc", "price", "price_time_utc", "n_expiries_listed", "n_expiries_kept", "n_rows",
    "n_spx_am_dropped", "error",
]
EARNINGS_COLUMNS = [
    "snap_date", "ticker", "event_ts_ny", "timing", "eps_estimate", "reported_eps", "surprise_pct",
]

# yfinance option_chain column -> CHAINS column
_YAHOO_TO_CHAINS = {
    "contractSymbol": "contract_symbol",
    "strike": "strike",
    "lastPrice": "last_price",
    "bid": "bid",
    "ask": "ask",
    "change": "change",
    "percentChange": "pct_change",
    "volume": "volume",
    "openInterest": "open_interest",
    "impliedVolatility": "yahoo_iv",
    "inTheMoney": "in_the_money",
    "lastTradeDate": "last_trade_utc",
    "contractSize": "contract_size",
    "currency": "currency",
}
_YAHOO_TO_EARNINGS = {
    "EPS Estimate": "eps_estimate",
    "Reported EPS": "reported_eps",
    "Surprise(%)": "surprise_pct",
}


def in_window(now_utc: datetime, cfg) -> bool:
    """True when New York wall time is inside [window_start_ny, window_end_ny], both ends inclusive."""
    snap = cfg["snapshot"]
    t = now_utc.astimezone(NY).time()
    return time.fromisoformat(snap["window_start_ny"]) <= t <= time.fromisoformat(snap["window_end_ny"])


@lru_cache(maxsize=1)
def _xnys():
    return xcals.get_calendar("XNYS")


def is_session(day: date) -> bool:
    return bool(_xnys().is_session(pd.Timestamp(day)))


def chain_frame(
    raw_calls: pd.DataFrame, raw_puts: pd.DataFrame, ticker: str, expiry: str, snap_utc: datetime
) -> pd.DataFrame:
    """yfinance calls and puts for one expiry -> CHAINS rows, calls first."""
    parts = []
    for kind, raw in (("C", raw_calls), ("P", raw_puts)):
        part = raw.rename(columns=_YAHOO_TO_CHAINS).reindex(columns=list(_YAHOO_TO_CHAINS.values()))
        part.insert(0, "kind", kind)
        parts.append(part)
    out = pd.concat(parts, ignore_index=True)
    out["snap_utc"] = pd.Timestamp(snap_utc).tz_convert("UTC")
    out["ticker"] = ticker
    out["expiry"] = expiry
    out["last_trade_utc"] = pd.to_datetime(out["last_trade_utc"], utc=True)
    return out[CHAINS_COLUMNS]


def filter_expiries(expiries: list[str], today: date, max_days: int) -> list[str]:
    """Keep expiries with 0 < calendar days to expiry <= max_days (Section 3.1)."""
    return [e for e in expiries if 0 < (date.fromisoformat(e) - today).days <= max_days]


def keep_spxw(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Keep PM-settled SPXW contracts; return them and the count of dropped AM-settled rows."""
    mask = df["contract_symbol"].astype(str).str.startswith("SPXW")
    return df[mask].reset_index(drop=True), int((~mask).sum())


def classify_timing(ts_ny: pd.Timestamp) -> str:
    """BMO, AMC or unknown from the New York time of day (Convention 4.11)."""
    t = pd.Timestamp(ts_ny).time()
    if t == time(0, 0):
        return "unknown"
    if t < time(9, 30):  # Convention 4.11: before 09:30 -> BMO
        return "BMO"
    if t >= time(16, 0):  # Convention 4.11: at or after 16:00 -> AMC
        return "AMC"
    return "unknown"


def earnings_frame(raw: pd.DataFrame, ticker: str, snap_date: date) -> pd.DataFrame:
    """yfinance get_earnings_dates frame -> EARNINGS rows, in the order served."""
    if raw is None or raw.empty:
        return pd.DataFrame(columns=EARNINGS_COLUMNS)
    idx = pd.DatetimeIndex(raw.index)
    ts = idx.tz_localize(NY) if idx.tz is None else idx.tz_convert(NY)
    out = raw.rename(columns=_YAHOO_TO_EARNINGS).reindex(columns=list(_YAHOO_TO_EARNINGS.values()))
    out = out.reset_index(drop=True)
    out.insert(0, "timing", [classify_timing(t) for t in ts])
    out.insert(0, "event_ts_ny", ts)
    out.insert(0, "ticker", ticker)
    out.insert(0, "snap_date", snap_date.isoformat())
    return out[EARNINGS_COLUMNS]


def should_upload(existing_n_ok: int | None, new_n_ok: int) -> bool:
    """Upload rule `better` (instruction 01, step 1.0): no asset yet, or strictly more tickers ok; a tie keeps the release."""
    return existing_n_ok is None or new_n_ok > existing_n_ok


def seconds_until_target(now_utc: datetime, cfg) -> float | None:
    """Instruction 03c step 3c.1: None when the New York date is not a session or the New York time is after
    window_end_ny; 0.0 inside [window_start_ny, window_end_ny]; otherwise the seconds until target_ny on that
    New York date."""
    snap = cfg["snapshot"]
    ny = now_utc.astimezone(NY)
    t = ny.time()
    if not is_session(ny.date()) or t > time.fromisoformat(snap["window_end_ny"]):
        return None
    if time.fromisoformat(snap["window_start_ny"]) <= t:
        return 0.0
    target = datetime.combine(ny.date(), time.fromisoformat(snap["target_ny"]), tzinfo=NY)
    return (target - ny).total_seconds()


def already_captured(existing_n_ok: int | None, min_ok: int) -> bool:
    """Instruction 03c step 3c.1: the release already holds today's snaplog with at least min_ok tickers ok."""
    return existing_n_ok is not None and existing_n_ok >= min_ok


def snapshot_log(rows: list[dict]) -> dict:
    """Per-ticker status rows -> the per-ticker part of SNAPLOG with status counts."""
    counts = {s: sum(r["status"] == s for r in rows) for s in ("ok", "partial", "error")}
    return {"tickers": rows, "n_ok": counts["ok"], "n_partial": counts["partial"], "n_error": counts["error"]}
