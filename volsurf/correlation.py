"""Implied and realised correlation (PLAN 7.1 and 7.2, kickoff Section 5.8, instruction 07).

Long history: Cboe COR3M against the forward realised average pairwise correlation of the 9 sector SPDRs, a
sector-level proxy. Sector ETFs are already diversified baskets and correlate with each other more than the 50 largest
S&P 500 stocks behind COR3M do, so implied sits below realised; that gap is the proxy, not a correlation risk premium.
The slope and R² are the usable result: how much of the next quarter's correlation the index options anticipate.
"""

from __future__ import annotations

import exchange_calendars as xcals
import numpy as np
import pandas as pd

GAP_NOTE = ("sector-level proxy: sector ETFs are diversified baskets and correlate with each other more than the single "
            "stocks behind COR3M, so implied sits below realised; the gap is the proxy, not a correlation risk premium")
STUDY_COLUMNS = ["n", "first_t", "last_t", "horizon", "maxlags", "intercept", "intercept_nw_se", "slope",
                 "slope_nw_se", "r2", "mean_implied", "mean_realised", "mean_gap", "gap_note"]


def live_weights(weights: pd.Series, sig: pd.Series) -> tuple[pd.Series, float]:
    """Kickoff 5.8 and instruction 07 step 7.2: the holdings weights of the names with a finite vol, renormalised to
    sum to 1, and the covered weight (the sum of their holdings weights before renormalising). A name with a blank
    vol is left out and its weight renormalised away."""
    sig = sig[np.isfinite(sig.astype(float))]
    w = weights[weights.index.isin(sig.index)].astype(float)
    covered = float(w.sum())
    return (w / covered if covered > 0 else w), covered


def implied_correlation(sig_index: float, sig: pd.Series, w: pd.Series) -> float:
    """Kickoff 5.8: rho = (sig_I^2 - sum w_i^2 sig_i^2) / sum_{i != j} w_i w_j sig_i sig_j, with the weights of the
    names that have a finite vol renormalised to sum to 1 (`live_weights`). NaN with fewer than 2 such names."""
    w, _ = live_weights(w, sig)
    s = sig.astype(float).reindex(w.index).to_numpy()
    w = w.to_numpy()
    if len(w) < 2 or not np.isfinite(sig_index):
        return float("nan")
    own = float(np.sum(w**2 * s**2))
    cross = float(np.sum(w * s) ** 2) - own  # sum over i != j of w_i w_j sig_i sig_j
    return (float(sig_index) ** 2 - own) / cross


def avg_pairwise_corr(returns: pd.DataFrame) -> float:
    """The mean of the Pearson correlations of every pair of columns of `returns`."""
    c = np.corrcoef(returns.to_numpy(dtype=float), rowvar=False)
    upper = np.triu_indices_from(c, k=1)
    return float(c[upper].mean())


def newey_west(y: np.ndarray, x: np.ndarray, maxlags: int) -> dict:
    """OLS of y on a constant and x with Newey-West (Bartlett kernel, weights 1 - l / (maxlags + 1)) standard errors,
    no small-sample correction: params (intercept, slope), se, r2."""
    X = np.column_stack([np.ones_like(x), x])
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ X.T @ y
    u = y - X @ beta
    xu = X * u[:, None]
    s = xu.T @ xu
    for lag in range(1, maxlags + 1):
        g = xu[lag:].T @ xu[:-lag]
        s += (1 - lag / (maxlags + 1)) * (g + g.T)
    cov = xtx_inv @ s @ xtx_inv
    r2 = 1 - float(u @ u) / float(((y - y.mean()) ** 2).sum())
    return {"params": beta, "se": np.sqrt(np.diag(cov)), "r2": r2}


def forward_windows(dates: pd.DatetimeIndex, available: pd.DatetimeIndex, horizon: int) -> dict[pd.Timestamp, list]:
    """For each day t in `dates`, the XNYS sessions t+1 to t+horizon, kept only if all of them are in `available`."""
    cal = xcals.get_calendar("XNYS", start=dates.min().strftime("%Y-%m-%d"))  # the default starts 20 years back
    sessions = cal.sessions_in_range(dates.min(), available.max() + pd.Timedelta(days=1))
    sessions = pd.DatetimeIndex(sessions).tz_localize(None)
    have = set(available)
    out = {}
    for t in dates:
        i = sessions.searchsorted(t, side="right")
        window = sessions[i:i + horizon]
        if len(window) == horizon and all(s in have for s in window):
            out[t] = list(window)
    return out


def cor3m_study(cor3m: pd.Series, sectors: pd.DataFrame, horizon: int, maxlags: int) -> dict:
    """Kickoff 5.8 long history, PLAN 7.1. `cor3m`: COR3M closes indexed by date; `sectors`: adjusted closes of the 9
    sector SPDRs indexed by date. Implied = COR3M / 100 on day t; realised = `avg_pairwise_corr` of the daily log
    returns over sessions t+1 to t+horizon, using day t only if every one of those sessions has a return in the
    sector data. OLS of realised on implied with Newey-West standard errors (`maxlags`).

    Returns the STUDY_COLUMNS values and `series` (t, implied, realised, gap = implied - realised). The gap is the
    sector-level proxy's, not a correlation risk premium (GAP_NOTE)."""
    cor3m = cor3m.dropna().sort_index()
    cor3m.index = pd.DatetimeIndex(cor3m.index)
    rets = np.log(sectors.sort_index()).diff().dropna(how="any")
    rets.index = pd.DatetimeIndex(rets.index)
    windows = forward_windows(cor3m.index, rets.index, horizon)
    rows = [(t, cor3m[t] / 100, avg_pairwise_corr(rets.loc[w])) for t, w in windows.items()]  # kickoff 5.8: / 100
    series = pd.DataFrame(rows, columns=["t", "implied", "realised"])
    series["gap"] = series["implied"] - series["realised"]
    fit = newey_west(series["realised"].to_numpy(), series["implied"].to_numpy(), maxlags)
    return {"n": len(series), "first_t": series["t"].iloc[0].strftime("%Y-%m-%d"),
            "last_t": series["t"].iloc[-1].strftime("%Y-%m-%d"), "horizon": horizon, "maxlags": maxlags,
            "intercept": float(fit["params"][0]), "intercept_nw_se": float(fit["se"][0]),
            "slope": float(fit["params"][1]), "slope_nw_se": float(fit["se"][1]), "r2": fit["r2"],
            "mean_implied": float(series["implied"].mean()), "mean_realised": float(series["realised"].mean()),
            "mean_gap": float(series["gap"].mean()), "gap_note": GAP_NOTE, "series": series}
