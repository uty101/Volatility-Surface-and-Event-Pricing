"""The `^SPX` forward from put-call parity (PLAN 3.1, kickoff Section 5.2 as corrected by instruction 03 part B).

D comes from the Treasury curve and only F is backed out from parity (the Cboe VIX approach).
"""

from __future__ import annotations

from datetime import date, time

import numpy as np
import pandas as pd

from volsurf.data import SPX, clean_chain, rate_curve
from volsurf.pricing import time_to_expiry

FORWARD_COLUMNS = ["expiry", "T", "r", "D", "F", "mad_bp", "n_pairs", "q_impl", "r_reg", "status"]
R_REG_MIN_T = 30 / 365  # instruction 03 part B: the regression implied r is reported for T >= 30/365


def _mids(frame: pd.DataFrame) -> pd.Series:
    return ((frame["bid"] + frame["ask"]) / 2).set_axis(frame["strike"].to_numpy())  # Convention 4.3


def parity_forward(calls: pd.DataFrame, puts: pd.DataFrame, spot: float, T: float, D: float, n: int,
                   min_pairs: int, mad_max_bp: float) -> dict:
    """Instruction 03 part B on one expiry's clean calls and puts (columns strike, bid, ask): over the n strikes
    nearest spot with both mids (a tie goes to the lower strike), F_i = K_i + (C_i - P_i) / D, F = median F_i and
    mad_bp = 10,000 x median |F_i - F| / F. Gate: n_pairs >= min_pairs and mad_bp <= mad_max_bp, else status
    parity_fail with F and q_impl blank (Convention 4.15); mad_bp and n_pairs are kept to show why. Reported,
    not gated: q_impl = r - ln(F / S) / T with r = -ln(D) / T, and r_reg = -ln(-slope) / T from the OLS of
    C - P on K over the same pairs, for T >= 30/365 only."""
    pairs = pd.concat({"C": _mids(calls), "P": _mids(puts)}, axis=1, join="inner").sort_index()
    pairs = pairs.iloc[np.argsort(np.abs(pairs.index.to_numpy() - spot), kind="stable")[:n]]
    K, cp = pairs.index.to_numpy(dtype=float), (pairs["C"] - pairs["P"]).to_numpy()
    n_pairs = len(K)
    f_i = K + cp / D
    F = float(np.median(f_i)) if n_pairs else np.nan
    mad_bp = 1e4 * float(np.median(np.abs(f_i - F))) / F if n_pairs else np.nan  # instruction 03 part B
    r_reg = np.nan
    if T >= R_REG_MIN_T and n_pairs >= 2:
        slope = np.polyfit(K, cp, 1)[0]
        r_reg = -np.log(-slope) / T if slope < 0 else np.nan
    ok = n_pairs >= min_pairs and mad_bp <= mad_max_bp
    r = -np.log(D) / T
    return {"F": F if ok else np.nan, "mad_bp": mad_bp, "n_pairs": n_pairs,
            "q_impl": r - np.log(F / spot) / T if ok else np.nan, "r_reg": r_reg,
            "status": "ok" if ok else "parity_fail"}


def spx_forwards(clean: pd.DataFrame, underlying: pd.DataFrame, fred: dict[str, pd.DataFrame], day: date,
                 cfg) -> pd.DataFrame:
    """One row per `^SPX` expiry of a day's clean chain (FORWARD_COLUMNS): T by Convention 4.1 from that
    expiry's snap_utc, r = rate_curve(day)(T), D = exp(-r T), and `parity_forward` on the expiry's quotes."""
    fw = cfg.forwards
    close_ny = time.fromisoformat(cfg.snapshot.close_ny)
    curve = rate_curve(fred, day)
    spot = float(underlying.set_index("ticker").loc[SPX, "price"])
    rows = []
    for expiry, chain in clean[clean["ticker"] == SPX].groupby("expiry", sort=True):
        T = time_to_expiry(expiry, chain["snap_utc"].iloc[0], close_ny)
        r = curve(T)
        D = float(np.exp(-r * T))  # Convention 4.6 discount factor
        out = parity_forward(chain[chain["kind"] == "C"], chain[chain["kind"] == "P"], spot, T, D,
                             fw.parity_n_strikes, fw.parity_min_pairs, fw.parity_mad_max_bp)
        rows.append({"expiry": expiry, "T": T, "r": r, "D": D, **out})
    return pd.DataFrame(rows, columns=FORWARD_COLUMNS)


def clean_with_forwards(chains: pd.DataFrame, underlying: pd.DataFrame, fred: dict[str, pd.DataFrame], day: date,
                        cfg) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Instruction 03 step 3.1: rules a to d, the `^SPX` parity forward on the rows they keep, then rule e for
    `^SPX` on the European bounds with that D and F. Returns (clean, CLEAN_LOG, forwards)."""
    first, _ = clean_chain(chains, underlying, cfg)
    forwards = spx_forwards(first, underlying, fred, day, cfg) if (first["ticker"] == SPX).any() else None
    clean, log = clean_chain(chains, underlying, cfg, forwards=forwards)
    return clean, log, forwards if forwards is not None else pd.DataFrame(columns=FORWARD_COLUMNS)
