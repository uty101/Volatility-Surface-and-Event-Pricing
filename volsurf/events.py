"""Event pricing (PLAN 6.1 and 6.2, kickoff Section 5.7, Convention 4.11, instruction 06).

An event's window runs close to close: BMO on D from close(previous session) to close(D), AMC on D from close(D) to
close(next session), and a macro event on D (`^SPX`) as BMO. The pre-event snapshot is the last snapshot no later
than the window's start session (Convention 4.11, instruction 07 status 4). The implied move comes from that
snapshot's chain (straddle, O-11 (a)) and its accepted SVI slices (term structure); the realised move from unadjusted
closes.
"""

from __future__ import annotations

from datetime import date, time

import numpy as np
import pandas as pd
from scipy.stats import binomtest

from volsurf.data import sessions_between
from volsurf.snapshots import NY, _xnys
from volsurf.svi import ACCEPTED, PARAMS, svi_w

EVENTS_COLUMNS = ["ticker", "group", "event_date", "timing", "pre_snap_date", "pre_snap_age", "E1", "E2", "n1", "n2",
                  "theta1", "theta2", "S", "F", "straddle_move", "ts_move", "realised_move", "ratio", "log_ratio",
                  "status"]  # instruction 07 step 7.0: pre_snap_age after pre_snap_date
WINDOW_COLUMNS = ["ticker", "event_date", "timing", "event_ts_ny", "snap_date", "override", "start", "end"]
SUMMARY_COLUMNS = ["scope", "n", "mean_log_ratio", "median_log_ratio", "mean_lo", "mean_hi", "share_above",
                   "share_lo", "share_hi", "status"]
PLACEHOLDER = time(15, 0)  # O-12 (b), instruction 01: 15:00 New York is Yahoo's placeholder for unconfirmed dates
GROUPS = ("index", "etfs", "xlk_holdings", "singles")  # kickoff Section 3.1, the [universe] lists


def _session(d: date, step: int) -> str:
    """The XNYS session before (step -1) or after (step 1) session d, as an ISO date."""
    cal, ts = _xnys(), pd.Timestamp(d)
    return (cal.previous_session(ts) if step < 0 else cal.next_session(ts)).date().isoformat()


def window(event_date: str, timing: str) -> tuple[str, str] | tuple[None, None]:
    """Convention 4.11: (start session, end session) of the close-to-close window; BMO (and macro) on D runs
    close(previous session of D) to close(D), AMC on D runs close(D) to close(next session); unknown has none."""
    d = date.fromisoformat(event_date)
    if timing == "BMO":
        return _session(d, -1), event_date
    if timing == "AMC":
        return event_date, _session(d, 1)
    return None, None


def event_windows(earnings: pd.DataFrame, overrides: pd.DataFrame) -> pd.DataFrame:
    """Convention 4.11 windows, one row per (ticker, New York event date) found in the EARNINGS rows of any asset.

    O-12 (b): the row from the latest asset (largest snap_date) that lists the event defines it; if its time is 15:00
    New York the timing is `unknown` whatever `classify_timing` gave. An override row (ticker, event_date, timing)
    then replaces the timing (`override` True); an override that matches no event raises. `unknown` rows are kept
    with blank start and end, and are excluded until an override sets them. Columns WINDOW_COLUMNS."""
    e = earnings.copy()
    ts = pd.to_datetime(e["event_ts_ny"], utc=True).dt.tz_convert(NY)
    e["event_date"] = ts.dt.strftime("%Y-%m-%d")
    e["timing"] = np.where(ts.dt.time == PLACEHOLDER, "unknown", e["timing"])
    e["snap_date"] = e["snap_date"].astype(str)
    e = (e.sort_values(["ticker", "event_date", "snap_date"], kind="stable")
          .drop_duplicates(["ticker", "event_date"], keep="last").reset_index(drop=True))
    e["override"] = False
    keys = pd.MultiIndex.from_frame(e[["ticker", "event_date"]])
    for o in overrides.itertuples():
        hit = keys == (o.ticker, str(o.event_date))
        if not hit.any():
            raise ValueError(f"override {o.ticker} {o.event_date} matches no earnings row")
        e.loc[hit, ["timing", "override"]] = [o.timing, True]
    starts_ends = [window(d, t) for d, t in zip(e["event_date"], e["timing"], strict=True)]
    e["start"] = [s for s, _ in starts_ends]
    e["end"] = [x for _, x in starts_ends]
    return e[WINDOW_COLUMNS]


def macro_windows(macro: pd.DataFrame) -> pd.DataFrame:
    """Kickoff 5.7: `^SPX` macro events from data/manual/macro_events.csv, window close(previous session) to
    close(event date); timing holds the event kind (FOMC, NFP, CPI). Columns WINDOW_COLUMNS."""
    rows = []
    for m in macro.itertuples():
        start, end = window(str(m.date), "BMO")
        rows.append({"ticker": "^SPX", "event_date": str(m.date), "timing": m.kind,
                     "event_ts_ny": f"{m.date} {m.release_time_ny}", "snap_date": "", "override": False,
                     "start": start, "end": end})
    return pd.DataFrame(rows, columns=WINDOW_COLUMNS)


def straddle_move(chain: pd.DataFrame, F: float, S: float, expiry) -> float:
    """Kickoff 5.7: M_s = (C_K + P_K) / S at the strike K nearest F on `expiry`, from clean mids (American as quoted).
    O-11 (a): only strikes where both the call and the put have a clean mid; a tie goes to the lower strike. NaN when
    no strike has both. `chain` has columns expiry, kind, strike, mid."""
    c = chain[(chain["expiry"] == expiry) & chain["mid"].notna()]
    both = c.pivot_table(index="strike", columns="kind", values="mid", aggfunc="first").dropna()
    if both.empty or not {"C", "P"} <= set(both.columns):
        return float("nan")
    both = both.reset_index()
    both["dist"] = (both["strike"] - F).abs()
    k = both.sort_values(["dist", "strike"], kind="stable").iloc[0]
    return float((k["C"] + k["P"]) / S)


def term_structure_move(theta1, theta2, n1, n2) -> tuple[float, str]:
    """Kickoff 5.7 term structure move. Daily diffusive variance v_d = (theta2 - theta1) / (n2 - n1), event variance
    v_e = theta1 - v_d (n1 - 1); if v_e <= 0 the status is `no_event_premium` and the move is NaN, else
    M_t = sqrt(2 / pi) sqrt(v_e), the expected absolute log move under a normal jump.

    Hand-worked example: theta1 = 0.0100 on E1 with n1 = 3 sessions, theta2 = 0.0130 on E2 with n2 = 8.
    v_d = (0.0130 - 0.0100) / (8 - 3) = 0.0006; v_e = 0.0100 - 0.0006 x (3 - 1) = 0.0088;
    M_t = sqrt(2 / pi) x sqrt(0.0088) = 0.7978845608 x 0.0938083152 = 0.0748482.
    No premium: theta1 = 0.0100, theta2 = 0.0300, n1 = 4, n2 = 8 gives v_d = 0.005 and
    v_e = 0.0100 - 0.005 x 3 = -0.0050, so `no_event_premium`."""
    v_d = (theta2 - theta1) / (n2 - n1)
    v_e = theta1 - v_d * (n1 - 1)
    if not v_e > 0:
        return float("nan"), "no_event_premium"
    return float(np.sqrt(2 / np.pi) * np.sqrt(v_e)), "ok"  # kickoff 5.7: sqrt(2/pi) x sqrt(v_e)


def group_of(ticker: str, cfg) -> str:
    """The kickoff Section 3.1 group of a ticker: the `[universe]` list that holds it."""
    for g in GROUPS:
        if ticker in getattr(cfg.universe, g):
            return g
    raise KeyError(f"{ticker} is in no [universe] group")


def _theta(r) -> float:
    return float(svi_w(0.0, *(getattr(r, p) for p in PARAMS)))


def pre_event_snapshot(start: str, days: set[str]) -> str | None:
    """Convention 4.11 with instruction 07 status 4: the last snapshot day on a session strictly before the window's
    end close and no later than the window's start session, i.e. the latest of `days` on or before `start`; None if
    there is none. It does not have to fall on the start session."""
    before = [d for d in days if d <= start]
    return max(before) if before else None


def event_table(windows: pd.DataFrame, iv: pd.DataFrame, svi_fits: pd.DataFrame, closes: dict[str, pd.Series],
                snapshot_days: dict[str, set[str]], cfg) -> pd.DataFrame:
    """EVENTS (kickoff 5.7, Convention 4.11), one row per window in `windows` (WINDOW_COLUMNS).

    - `iv`: clean chain rows with the IV stage inputs (day, ticker, expiry, kind, strike, S, F, mid), both sides, for
      the pre-event snapshot days; `svi_fits`: SVI_FITS rows of every day (parameters at full precision, O-39 (a));
      `closes`: ticker -> unadjusted closes by ISO date; `snapshot_days`: ticker -> ISO days with that ticker captured.
    - Pre-event snapshot t: the last snapshot day of the ticker no later than the window's start session
      (`pre_event_snapshot`); pre_snap_age = sessions_between(t, start), 0 when t is the start session. E1 < E2: the
      first 2 accepted expiries on t with expiry on or after the window's end session; theta_i = SVI w_i(0);
      n_i = sessions_between(t, E_i). S and F (of E1) and the straddle mids come from `iv`.
      realised_move = |ln(close(end) / close(start))|, ratio = realised / ts_move, log_ratio = ln(ratio).

    Status (blank results where they cannot be computed, Convention 4.15): `unknown` (timing unknown, excluded until
    an override sets it); `pending` if the start session is after the ticker's last close and has no snapshot of its
    own (a later snapshot may still come before it); else `no_pre_snapshot` if no snapshot day is on or before the
    start session;
    `too_few_expiries` with fewer than 2 accepted expiries; otherwise `ok` or the
    distinct conditions joined with `|` in this order: `no_event_premium`, `no_straddle`, `pending` (window ends after
    the last close, so realised is blank)."""
    rows = []
    fits = svi_fits[svi_fits["status"].isin(ACCEPTED)]
    for w in windows.itertuples():
        row = dict.fromkeys(EVENTS_COLUMNS, np.nan) | {"ticker": w.ticker, "group": group_of(w.ticker, cfg),
                                                        "event_date": w.event_date, "timing": w.timing,
                                                        "pre_snap_date": "", "E1": "", "E2": ""}
        last = closes[w.ticker].index.max()
        if w.timing == "unknown":
            rows.append(row | {"status": "unknown"})
            continue
        t = pre_event_snapshot(w.start, snapshot_days.get(w.ticker, set()))
        if (w.start > last and t != w.start) or t is None:
            rows.append(row | {"status": "pending" if w.start > last else "no_pre_snapshot"})
            continue
        row["pre_snap_date"] = t
        row["pre_snap_age"] = sessions_between(date.fromisoformat(t), date.fromisoformat(w.start))
        acc = fits[(fits["day"] == t) & (fits["ticker"] == w.ticker) & (fits["expiry"] >= w.end)]
        acc = acc.sort_values("expiry").head(2)
        if len(acc) < 2:
            rows.append(row | {"status": "too_few_expiries"})
            continue
        e1, e2 = acc.itertuples()
        n1 = sessions_between(date.fromisoformat(t), date.fromisoformat(e1.expiry))
        n2 = sessions_between(date.fromisoformat(t), date.fromisoformat(e2.expiry))
        theta1, theta2 = _theta(e1), _theta(e2)
        chain = iv[(iv["day"] == t) & (iv["ticker"] == w.ticker)]
        e1_rows = chain[chain["expiry"] == e1.expiry]
        S, F = float(e1_rows["S"].iloc[0]), float(e1_rows["F"].iloc[0])
        m_s = straddle_move(chain, F, S, e1.expiry)
        m_t, ts_status = term_structure_move(theta1, theta2, n1, n2)
        row.update(E1=e1.expiry, E2=e2.expiry, n1=n1, n2=n2, theta1=theta1, theta2=theta2, S=S, F=F,
                   straddle_move=m_s, ts_move=m_t)
        flags = [] if ts_status == "ok" else [ts_status]
        if not np.isfinite(m_s):
            flags.append("no_straddle")
        if w.end > last:
            flags.append("pending")
        else:
            c = closes[w.ticker]
            r = abs(float(np.log(c[w.end] / c[w.start])))
            row["realised_move"] = r
            if np.isfinite(m_t):
                row.update(ratio=r / m_t, log_ratio=float(np.log(r / m_t)))
        rows.append(row | {"status": "|".join(flags) or "ok"})
    return pd.DataFrame(rows, columns=EVENTS_COLUMNS)


def _summary_row(scope: str, lr: pd.Series, cfg) -> dict:
    """One summary row: the descriptive values always, and the kickoff 5.7 intervals (O-13 (a): percentile bootstrap
    of the mean with `boot_reps` iid draws seeded from `[run] seed`, Clopper-Pearson for the share) only when n >=
    `[events] min_n`; status `ok` or `below_min_n`."""
    n, above = len(lr), int((lr > 0).sum())
    row = dict.fromkeys(SUMMARY_COLUMNS, np.nan) | {
        "scope": scope, "n": n, "mean_log_ratio": lr.mean() if n else np.nan,
        "median_log_ratio": lr.median() if n else np.nan, "share_above": above / n if n else np.nan}
    if n < cfg.events.min_n:
        return row | {"status": "below_min_n"}
    lo_q, hi_q = (1 - cfg.events.ci) / 2, (1 + cfg.events.ci) / 2
    rng = np.random.default_rng(cfg.run.seed)
    x = lr.to_numpy()
    means = x[rng.integers(0, n, size=(cfg.events.boot_reps, n))].mean(axis=1)
    ci = binomtest(above, n).proportion_ci(confidence_level=cfg.events.ci, method="exact")
    return row | {"mean_lo": float(np.quantile(means, lo_q)), "mean_hi": float(np.quantile(means, hi_q)),
                  "share_lo": ci.low, "share_hi": ci.high, "status": "ok"}


def event_summary(events: pd.DataFrame, cfg) -> pd.DataFrame:
    """Kickoff 5.7 summary over the events with a log_ratio: mean of ln(R / M_t) and the share with R > M_t, for
    scope `all` and for each group (kickoff Section 3.1) with at least `[events] min_group_n` such events. Below
    `[events] min_n` a row is descriptive only (n, mean, median, share; intervals blank, status `below_min_n`).
    Columns SUMMARY_COLUMNS."""
    used = events[np.isfinite(events["log_ratio"].astype(float))]
    rows = [_summary_row("all", used["log_ratio"].astype(float), cfg)]
    for g in GROUPS:
        lr = used.loc[used["group"] == g, "log_ratio"].astype(float)
        if len(lr) >= cfg.events.min_group_n:
            rows.append(_summary_row(g, lr, cfg))
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)
