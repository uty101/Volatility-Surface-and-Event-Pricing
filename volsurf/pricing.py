"""BSM, Black-76, the CRR tree and the early exercise premium (PLAN 2.1, kickoff Section 5.1), and the early
exercise premium table (PLAN 2.3, instruction 02 step 2.3, instruction 03 step 3.0)."""

from __future__ import annotations

from datetime import date, time

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import norm

from volsurf.data import dividend_yield, rate_curve
from volsurf.snapshots import NY

EEP_ROW_COLUMNS = [
    "ticker", "expiry", "kind", "strike", "contract_symbol", "snap_utc", "bid", "ask", "mid", "S", "T", "r", "q",
    "F", "k", "k_bin", "iv_american", "iv_european", "premium_vol_pts", "premium_price", "premium_pct_mid", "status",
]
EEP_SUMMARY_COLUMNS = ["ticker", "kind", "k_bin", "n", "median_vol_pts", "max_vol_pts", "median_pct_mid",
                       "max_pct_mid"]
# O-8 (a), decided in instruction 01: k = ln(K/F) bins, right-closed
K_BIN_EDGES = [-np.inf, -0.10, -0.02, 0.02, 0.10, np.inf]
K_BIN_LABELS = ["(-inf, -0.10]", "(-0.10, -0.02]", "(-0.02, 0.02]", "(0.02, 0.10]", "(0.10, inf)"]


def _is_call(kind) -> np.ndarray:
    """True where kind is 'C', False where 'P' (CHAINS convention); anything else raises."""
    k = np.asarray(kind)
    bad = ~np.isin(k, ["C", "P"])
    if bad.any():
        raise ValueError(f"kind must be 'C' or 'P', got {sorted(set(np.atleast_1d(k[bad]).tolist()))}")
    return k == "C"


def bsm(S, K, T, r, q, sigma, kind) -> np.ndarray:
    """Section 5.1 Black-Scholes-Merton with continuous dividend yield q; broadcasts over every argument."""
    S, K, T, r, q, sigma = (np.asarray(x, dtype=float) for x in (S, K, T, r, q, sigma))
    sd = sigma * np.sqrt(T)
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / sd
    d2 = d1 - sd
    fs, dk = S * np.exp(-q * T), K * np.exp(-r * T)
    call = fs * norm.cdf(d1) - dk * norm.cdf(d2)
    put = dk * norm.cdf(-d2) - fs * norm.cdf(-d1)
    return np.where(_is_call(kind), call, put)


def black76(F, K, T, D, sigma, kind) -> np.ndarray:
    """Section 5.1 Black-76 on forward F with discount factor D; broadcasts over every argument."""
    F, K, T, D, sigma = (np.asarray(x, dtype=float) for x in (F, K, T, D, sigma))
    sd = sigma * np.sqrt(T)
    d1 = (np.log(F / K) + 0.5 * sigma**2 * T) / sd
    d2 = d1 - sd
    call = D * (F * norm.cdf(d1) - K * norm.cdf(d2))
    put = D * (K * norm.cdf(-d2) - F * norm.cdf(-d1))
    return np.where(_is_call(kind), call, put)


def crr(S, K, T, r, q, sigma, kind, n, american) -> float:
    """Section 5.1 CRR tree with n steps: u = e^(sigma sqrt(dt)), d = 1/u, p = (e^((r-q)dt) - d)/(u - d).

    Backward induction is vectorised over the nodes of each step; American adds max(continuation,
    intrinsic) at every node. Raises ValueError if p is outside (0, 1).
    """
    is_call = bool(_is_call(kind))
    dt = T / n
    sdt = sigma * np.sqrt(dt)
    u = np.exp(sdt)
    d = 1.0 / u
    p = (np.exp((r - q) * dt) - d) / (u - d)
    if not 0.0 < p < 1.0:
        raise ValueError(f"CRR up probability p = {p} is outside (0, 1) (sigma={sigma}, r={r}, q={q}, n={n})")
    disc = np.exp(-r * dt)
    pu, pd_ = disc * p, disc * (1.0 - p)

    def intrinsic(spot: np.ndarray) -> np.ndarray:
        return np.maximum(spot - K, 0.0) if is_call else np.maximum(K - spot, 0.0)

    # node j of step i has j up moves: S u^j d^(i - j) = S e^((2j - i) sigma sqrt(dt)), which is
    # node j of step i + 1 times u
    spot = S * np.exp((2 * np.arange(n + 1) - n) * sdt)
    v = intrinsic(spot)
    for _ in range(n):
        v = pu * v[1:] + pd_ * v[:-1]
        if american:
            spot = spot[:-1] * u
            v = np.maximum(v, intrinsic(spot))
    return float(v[0])


def early_exercise_premium(S, K, T, r, q, sigma, kind, n) -> float:
    """Section 5.1: CRR American minus CRR European at the same n."""
    return crr(S, K, T, r, q, sigma, kind, n, True) - crr(S, K, T, r, q, sigma, kind, n, False)


def time_to_expiry(expiry: str, snap_utc, close_ny: time) -> float:
    """Convention 4.1: (expiry at the New York close - snapshot time) / (365 x 86400 s)."""
    end = pd.Timestamp.combine(date.fromisoformat(expiry), close_ny).tz_localize(NY)
    return (end - pd.Timestamp(snap_utc)).total_seconds() / (365 * 86400)  # Convention 4.1


def _tree_price(sigma, S, K, T, r, q, kind, n, american) -> float:
    return crr(S, K, T, r, q, sigma, kind, n, american)


def _implied_vol(price, args: tuple, mid: float, lo: float, hi: float) -> float:
    """brentq on price(sigma, *args) - mid over [lo, hi] (O-24 (a)); nan when the bracket holds no root."""
    try:
        return brentq(lambda s: price(s, *args) - mid, lo, hi)
    except ValueError:
        return np.nan


def eep_solve(mid, S, K, T, r, q, kind, cfg) -> dict:
    """Instruction 03 step 3.0 for one quote: the American and European IVs, each by brentq on a CRR tree at
    n_prod (American and European) minus the mid, so the tree's discretisation error cancels between them; the
    premium in vol points (European IV - American IV) x 100; and the premium in price, CRR American - CRR
    European at n_prod, both at the American IV, also as a percent of the mid. A failed solve blanks both vols
    and every premium (O-29 (a)); where BSM vega per vol point at the American IV is below [eep] min_vega_pt the
    vol premium is blank with status low_vega."""
    from volsurf.greeks import greeks  # volsurf.greeks imports this module

    lo, hi, n = cfg.iv.iv_lo, cfg.iv.iv_hi, cfg.pricing.n_prod
    iv_a = _implied_vol(_tree_price, (S, K, T, r, q, kind, n, True), mid, lo, hi)
    iv_e = _implied_vol(_tree_price, (S, K, T, r, q, kind, n, False), mid, lo, hi)
    fail_a, fail_e = np.isnan(iv_a), np.isnan(iv_e)
    if fail_a or fail_e:
        status = "both_fail" if fail_a and fail_e else "american_fail" if fail_a else "european_fail"
        return {"iv_american": np.nan, "iv_european": np.nan, "premium_vol_pts": np.nan, "premium_price": np.nan,
                "premium_pct_mid": np.nan, "status": status}
    premium_price = early_exercise_premium(S, K, T, r, q, iv_a, kind, n)
    vega_pt = float(greeks(S, K, T, r, q, iv_a, kind)["vega"]) / 100  # Convention 4.10: per vol point
    low_vega = vega_pt < cfg.eep.min_vega_pt
    return {"iv_american": iv_a, "iv_european": iv_e, "premium_vol_pts": np.nan if low_vega else (iv_e - iv_a) * 100,
            "premium_price": premium_price, "premium_pct_mid": premium_price / mid * 100,
            "status": "low_vega" if low_vega else "ok"}


def eep_rows(clean: pd.DataFrame, underlying: pd.DataFrame, fred: dict[str, pd.DataFrame], divs: pd.DataFrame,
             day: date, cfg) -> pd.DataFrame:
    """Instruction 02 step 2.3 with instruction 03 step 3.0, one row per clean contract of every American chain:
    `eep_solve` on the mid. S from UNDERLYING, r from rate_curve(day) at the row's T, q from dividend_yield, T by
    Convention 4.1, F and k by Conventions 4.8 and 4.9."""
    close_ny = time.fromisoformat(cfg.snapshot.close_ny)
    curve = rate_curve(fred, day)
    spot = underlying.set_index("ticker")["price"]
    out = []
    for ticker, chain in clean[~clean["ticker"].isin(cfg.universe.index)].groupby("ticker", sort=False):
        S = float(spot[ticker])
        q = dividend_yield(divs[divs["ticker"] == ticker], S, day)
        for row in chain.itertuples(index=False):
            K, kind = float(row.strike), row.kind
            T = time_to_expiry(row.expiry, row.snap_utc, close_ny)
            r = curve(T)
            mid = (row.bid + row.ask) / 2  # Convention 4.3
            F = S * np.exp((r - q) * T)  # Convention 4.8
            out.append({"ticker": ticker, "expiry": row.expiry, "kind": kind, "strike": K,
                        "contract_symbol": row.contract_symbol, "snap_utc": row.snap_utc, "bid": row.bid,
                        "ask": row.ask, "mid": mid, "S": S, "T": T, "r": r, "q": q, "F": F, "k": np.log(K / F),
                        **eep_solve(mid, S, K, T, r, q, kind, cfg)})
    rows = pd.DataFrame(out, columns=EEP_ROW_COLUMNS)
    rows["k_bin"] = pd.cut(rows["k"], K_BIN_EDGES, labels=K_BIN_LABELS).astype(str)
    return rows


def eep_summary(rows: pd.DataFrame) -> pd.DataFrame:
    """Median and max premium, in vol points and as a percent of the mid, per (ticker, kind, k bin) over the rows
    with a vol premium (status ok, instruction 03 step 3.0); tickers in row order, kinds C then P, bins in k
    order."""
    ok = rows[rows["status"] == "ok"]
    summary = (ok.groupby(["ticker", "kind", "k_bin"], sort=False)
               .agg(n=("premium_vol_pts", "size"), median_vol_pts=("premium_vol_pts", "median"),
                    max_vol_pts=("premium_vol_pts", "max"), median_pct_mid=("premium_pct_mid", "median"),
                    max_pct_mid=("premium_pct_mid", "max")).reset_index())
    tickers = {t: i for i, t in enumerate(pd.unique(rows["ticker"]))}
    order = pd.DataFrame({"t": summary["ticker"].map(tickers), "kind": summary["kind"],
                          "b": summary["k_bin"].map(K_BIN_LABELS.index)})
    return summary.loc[order.sort_values(["t", "kind", "b"]).index, EEP_SUMMARY_COLUMNS].reset_index(drop=True)
