"""Implied volatility (PLAN 3.2 and 3.3, kickoff Section 5.3, instructions 03 and 03b).

Methods: `newton`, `brent` (European Brent fallback, and the scalar American solver), `batch` (the vectorised
American bisection), `bounds` (outside the Section 5.3 bounds), `no_root` (inside the bounds, but no root in
[iv_lo, iv_hi]) and `flat` (the flat-price rule of instruction 03b: the price barely moves with vol at the
solved value, so no vol is returned).
"""

from __future__ import annotations

from datetime import date, time

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import norm

from volsurf.data import (
    SPX,
    _american_in_bounds,
    _european_in_bounds,
    dividend_yield,
    rate_curve,
)
from volsurf.pricing import _is_call, black76, crr, time_to_expiry

IV_COLUMNS = ["day", "ticker", "expiry", "kind", "strike", "T", "S", "F", "r", "q", "mid", "iv", "method", "flag"]
SUMMARY_COLUMNS = ["day", "ticker", "n_in", "n_solved", "n_newton", "n_brent", "n_batch", "n_bounds", "n_no_root",
                   "n_flat", "n_parity_fail"]
METHODS = ["newton", "brent", "batch", "bounds", "no_root", "flat"]
BRENT_TOL = 1e-14  # instruction 03b part B: brentq xtol and rtol in the scalar solvers
FLAT_BUMP = 0.01  # instruction 04 step 4.0: sens = min(|P(sigma + 0.01) - P(sigma)|, |P(sigma) - P(sigma - 0.01)|)


def price_bounds(price, S, F, K, D, kind, american) -> bool:
    """Section 5.3 bounds: European call in (max(D(F - K), 0), D F), put in (max(D(K - F), 0), D K); American
    call in [max(S - K, 0), S), put in [max(K - S, 0), K). Broadcasts; a scalar input gives a bool."""
    if american:
        inside = _american_in_bounds(np.asarray(price), np.asarray(kind), np.asarray(K), np.asarray(S))
    else:
        inside = _european_in_bounds(np.asarray(price), np.asarray(kind), np.asarray(K), np.asarray(F),
                                     np.asarray(D))
    inside = np.asarray(inside, dtype=bool)
    return bool(inside) if inside.ndim == 0 else inside


def _sens(pricer, sigma: float, cfg) -> float:
    """One-sided flat-price rule (instruction 04 step 4.0): min(|P(sigma + 0.01) - P(sigma)|,
    |P(sigma) - P(sigma - 0.01)|), both bumped vols clipped to [iv_lo, iv_hi]."""
    lo, hi = cfg.iv.iv_lo, cfg.iv.iv_hi
    p = pricer(sigma)
    return min(abs(pricer(min(sigma + FLAT_BUMP, hi)) - p), abs(p - pricer(max(sigma - FLAT_BUMP, lo))))


def _brent(f, cfg) -> float | None:
    """brentq on [iv_lo, iv_hi] at BRENT_TOL; None when the bracket holds no sign change."""
    lo, hi = cfg.iv.iv_lo, cfg.iv.iv_hi
    f_lo, f_hi = f(lo), f(hi)
    if f_lo * f_hi > 0:
        return None
    return brentq(f, lo, hi, xtol=BRENT_TOL, rtol=BRENT_TOL)


def iv_european(price, F, K, T, D, kind, cfg) -> tuple[float, str]:
    """Section 5.3 European solver on Black-76: bounds check; Brenner-Subrahmanyam start on the OTM price;
    Newton on vega with tolerance iv_tol on price for at most newton_max_iter steps; Brent on [iv_lo, iv_hi]
    if vega < min_vega x F x D (instruction 03b) at any step, if Newton leaves [iv_lo, iv_hi] or if it does
    not converge; then the flat-price rule. Returns (vol, method), vol nan unless the method is newton or brent."""
    c = cfg.iv
    if not price_bounds(price, None, F, K, D, kind, False):
        return np.nan, "bounds"

    def pricer(s):
        return float(black76(F, K, T, D, s, kind))

    call = bool(_is_call(kind))
    otm = price - D * (F - K) if call and K < F else price - D * (K - F) if not call and K > F else price
    sigma = np.sqrt(2 * np.pi / T) * otm / (D * F)  # Brenner-Subrahmanyam, Section 5.3
    method = None
    if c.iv_lo <= sigma <= c.iv_hi:
        sqrt_t = np.sqrt(T)
        for _ in range(c.newton_max_iter):
            diff = pricer(sigma) - price
            if abs(diff) < c.iv_tol:
                method = "newton"
                break
            d1 = (np.log(F / K) + 0.5 * sigma**2 * T) / (sigma * sqrt_t)
            vega = D * F * norm.pdf(d1) * sqrt_t
            if vega < c.min_vega * F * D:
                break
            sigma -= diff / vega
            if not c.iv_lo <= sigma <= c.iv_hi:
                break
    if method is None:
        sigma = _brent(lambda s: pricer(s) - price, cfg)
        if sigma is None:
            return np.nan, "no_root"
        method = "brent"
    if _sens(pricer, sigma, cfg) < c.flat_tol:
        return np.nan, "flat"
    return float(sigma), method


def iv_american(price, S, K, T, r, q, kind, cfg) -> tuple[float, str]:
    """Section 5.3 American solver: bounds check; brentq on CRR American at n_prod minus the price over
    [iv_lo, iv_hi]; then the flat-price rule on the same tree. Returns (vol, method), method brent on success."""
    if not price_bounds(price, S, None, K, None, kind, True):
        return np.nan, "bounds"
    n = cfg.pricing.n_prod

    def pricer(s):
        return crr(S, K, T, r, q, s, kind, n, True)

    sigma = _brent(lambda s: pricer(s) - price, cfg)
    if sigma is None:
        return np.nan, "no_root"
    if _sens(pricer, sigma, cfg) < cfg.iv.flat_tol:
        return np.nan, "flat"
    return float(sigma), "brent"


def crr_batch(S, K, T, r, q, sigma, is_call, n) -> np.ndarray:
    """CRR American at n steps (Section 5.1) for many options at once: node arrays of shape options x nodes,
    the same recursion as `crr`. Raises ValueError if any up probability is outside (0, 1)."""
    S, K, T, r, q, sigma = (np.asarray(x, dtype=float) for x in (S, K, T, r, q, sigma))
    dt = T / n
    sdt = sigma * np.sqrt(dt)
    u = np.exp(sdt)
    d = 1.0 / u
    p = (np.exp((r - q) * dt) - d) / (u - d)
    if not ((p > 0) & (p < 1)).all():
        raise ValueError(f"CRR up probability outside (0, 1) for {int(((p <= 0) | (p >= 1)).sum())} options")
    disc = np.exp(-r * dt)
    pu, pd_ = disc * p, disc * (1 - p)
    w = np.where(is_call, 1.0, -1.0)
    # nodes x options, so each step's slice is contiguous; updated in place step by step. Node j of step i is
    # node j of step i + 1 times u, as in `crr`; v >= 0, so max(v, w (spot - K)) is max(v, intrinsic).
    spot = S * np.exp((2 * np.arange(n + 1) - n)[:, None] * sdt)
    v = np.maximum(w * (spot - K), 0.0)
    buf = np.empty_like(v)
    for i in range(n, 0, -1):
        b, lo, hi_ = buf[:i], v[:i], v[1 : i + 1]
        np.multiply(hi_, pu, out=b)
        np.multiply(lo, pd_, out=lo)
        np.add(lo, b, out=lo)
        s = spot[:i]
        np.multiply(s, u, out=s)
        np.subtract(s, K, out=b)
        np.multiply(b, w, out=b)
        np.maximum(lo, b, out=lo)
    return v[0].copy()


def iv_american_batch(prices, S, K, T, r, q, kind, cfg) -> tuple[np.ndarray, np.ndarray]:
    """Instruction 03 step 3.2: bisection on [iv_lo, iv_hi] for all rows at once on `crr_batch` at n_prod,
    until the bracket is narrower than am_vol_tol; the vol is the bracket midpoint. Rows outside the American
    bounds get bounds, rows with no sign change no_root, then the flat-price rule (instruction 03b) on the same
    tree; solved rows get batch. Returns (iv, status) arrays."""
    c, n = cfg.iv, cfg.pricing.n_prod
    prices, S, K, T, r, q = (np.asarray(x, dtype=float) for x in (prices, S, K, T, r, q))
    is_call = np.asarray(_is_call(kind))
    m = len(prices)
    iv = np.full(m, np.nan)
    status = np.full(m, "bounds", dtype=object)
    inside = np.asarray(price_bounds(prices, S, None, K, None, np.where(is_call, "C", "P"), True), dtype=bool)
    idx = np.flatnonzero(inside)
    if idx.size == 0:
        return iv, status

    def f(rows, sigma):
        return crr_batch(S[rows], K[rows], T[rows], r[rows], q[rows], sigma, is_call[rows], n) - prices[rows]

    f_lo = f(idx, np.full(idx.size, c.iv_lo))
    f_hi = f(idx, np.full(idx.size, c.iv_hi))
    root = f_lo * f_hi <= 0
    status[idx[~root]] = "no_root"
    idx, f_lo = idx[root], f_lo[root]
    lo, hi = np.full(idx.size, c.iv_lo), np.full(idx.size, c.iv_hi)
    hi[f_lo == 0] = c.iv_lo  # the root is the lower end, as brentq returns it
    while idx.size and (hi - lo).max() > c.am_vol_tol:
        mid = (lo + hi) / 2
        f_mid = f(idx, mid)
        up = np.sign(f_mid) == np.sign(f_lo)  # the root lies above mid
        lo = np.where(up, mid, lo)
        hi = np.where(up, hi, mid)
        f_lo = np.where(up, f_mid, f_lo)
    sigma = (lo + hi) / 2
    up_s, dn_s = np.minimum(sigma + FLAT_BUMP, c.iv_hi), np.maximum(sigma - FLAT_BUMP, c.iv_lo)
    f_s = f(idx, sigma)
    sens = np.minimum(np.abs(f(idx, up_s) - f_s), np.abs(f_s - f(idx, dn_s)))  # the price cancels
    flat = sens < c.flat_tol
    status[idx[flat]] = "flat"
    status[idx[~flat]] = "batch"
    iv[idx[~flat]] = sigma[~flat]
    return iv, status


def iv_american_refine(prices, S, K, T, r, q, kind, sigma0, n, cfg) -> tuple[np.ndarray, int]:
    """For the PLAN 3.2 N = 200 against N = 2000 measurement: the American IV on `crr_batch` at n steps, by
    Newton from sigma0 (the n_prod vols) with BSM vega as the slope, until every step is below am_vol_tol, for
    at most newton_max_iter iterations. Rows that have not converged by then are nan. Returns (iv, iterations)."""
    from volsurf.greeks import greeks

    c = cfg.iv
    prices, S, K, T, r, q, sigma = (np.asarray(x, dtype=float) for x in (prices, S, K, T, r, q, sigma0))
    is_call = np.asarray(_is_call(kind))
    kinds = np.where(is_call, "C", "P")
    sigma = sigma.copy()
    done = np.zeros(len(sigma), dtype=bool)
    for it in range(1, c.newton_max_iter + 1):
        live = np.flatnonzero(~done)
        diff = crr_batch(S[live], K[live], T[live], r[live], q[live], sigma[live], is_call[live], n) - prices[live]
        vega = greeks(S[live], K[live], T[live], r[live], q[live], sigma[live], kinds[live])["vega"]
        step = diff / vega
        sigma[live] -= step
        done[live[np.abs(step) < c.am_vol_tol]] = True
        if done.all():
            return sigma, it
    sigma[~done] = np.nan
    return sigma, c.newton_max_iter


def iv_inputs(clean: pd.DataFrame, underlying: pd.DataFrame, fred: dict[str, pd.DataFrame], divs: pd.DataFrame,
              forwards: pd.DataFrame, day: date, cfg) -> pd.DataFrame:
    """The columns `iv_chain` reads, added to a day's clean chain: day, T (Convention 4.1 from each row's
    snap_utc), S (UNDERLYING), r (rate_curve at T), mid (Convention 4.3), and per Convention 4.8 F, D and q:
    for `^SPX` the parity F and D of the row's expiry and q = q_impl (instruction 03b; F blank on a parity_fail
    expiry, with parity_fail True); for every other ticker q from dividend_yield, D = exp(-r T),
    F = S exp((r - q) T)."""
    close_ny = time.fromisoformat(cfg.snapshot.close_ny)
    curve = rate_curve(fred, day)
    spot = underlying.set_index("ticker")["price"]
    out = clean.copy()
    out["day"] = day.isoformat()
    out["T"] = [time_to_expiry(e, s, close_ny) for e, s in zip(out["expiry"], out["snap_utc"], strict=True)]
    out["S"] = out["ticker"].map(spot).astype(float)
    out["r"] = [curve(t) for t in out["T"]]
    out["mid"] = (out["bid"] + out["ask"]) / 2  # Convention 4.3
    q_div = {t: dividend_yield(divs[divs["ticker"] == t], float(spot[t]), day)
             for t in out["ticker"].unique() if t != SPX}
    out["q"] = out["ticker"].map(q_div)
    out["D"] = np.exp(-out["r"] * out["T"])
    out["F"] = out["S"] * np.exp((out["r"] - out["q"]) * out["T"])  # Convention 4.8, American underlyings
    out["parity_fail"] = False
    spx = out["ticker"] == SPX
    if spx.any():
        fw = forwards.set_index("expiry")
        ok = fw["status"] == "ok"
        out.loc[spx, "F"] = out.loc[spx, "expiry"].map(fw["F"].where(ok))
        out.loc[spx, "D"] = out.loc[spx, "expiry"].map(fw["D"])
        out.loc[spx, "q"] = out.loc[spx, "expiry"].map(fw["q_impl"].where(ok))
        out.loc[spx, "parity_fail"] = out.loc[spx, "F"].isna()
    return out


def iv_chain(clean: pd.DataFrame, cfg) -> pd.DataFrame:
    """PLAN 3.3 IV table from a clean chain carrying the `iv_inputs` columns. OTM quotes only (Convention 4.5:
    calls with K >= F, puts with K < F); `^SPX` by `iv_european` on its parity F and D, every other ticker by
    `iv_american_batch` on S, r, q. Rows of a `^SPX` parity_fail expiry have no F, so every one is kept with
    flag parity_fail and no vol or method. Flags stale, after_close and parity_fail are joined with |."""
    otm = np.where(clean["kind"] == "C", clean["strike"] >= clean["F"], clean["strike"] < clean["F"])
    rows = clean[otm | clean["parity_fail"]].copy()
    rows["iv"], rows["method"] = np.nan, ""
    spx = (rows["ticker"] == SPX) & ~rows["parity_fail"]
    for i, row in rows[spx].iterrows():
        rows.loc[i, ["iv", "method"]] = iv_european(row["mid"], row["F"], row["strike"], row["T"], row["D"],
                                                   row["kind"], cfg)
    am = rows["ticker"] != SPX
    if am.any():
        a = rows[am]
        iv, status = iv_american_batch(a["mid"], a["S"], a["strike"], a["T"], a["r"], a["q"], a["kind"], cfg)
        rows.loc[am, "iv"], rows.loc[am, "method"] = iv, status
    flags = pd.DataFrame({name: np.where(rows[name].astype(bool), name, "")
                          for name in ("stale", "after_close", "parity_fail")}, index=rows.index)
    rows["flag"] = flags.apply(lambda f: "|".join(x for x in f if x), axis=1) if len(rows) else ""
    rows["iv"] = rows["iv"].astype(float)
    return rows[IV_COLUMNS].reset_index(drop=True)


def iv_summary(iv: pd.DataFrame) -> pd.DataFrame:
    """PLAN 3.3 summary, one row per (day, ticker) in table order, columns of instruction 03b."""
    out = []
    for (day, ticker), g in iv.groupby(["day", "ticker"], sort=False):
        row = {"day": day, "ticker": ticker, "n_in": len(g), "n_solved": int(g["iv"].notna().sum())}
        row.update({f"n_{m}": int((g["method"] == m).sum()) for m in METHODS})
        row["n_parity_fail"] = int(g["flag"].str.split("|").apply(lambda f: "parity_fail" in f).sum())
        out.append(row)
    return pd.DataFrame(out, columns=SUMMARY_COLUMNS)
