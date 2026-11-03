"""Implied and realised correlation (PLAN 7.1 and 7.2, kickoff Section 5.8, instruction 07).

Long history: Cboe COR3M against the forward realised average pairwise correlation of the 9 sector SPDRs, a
sector-level proxy. Sector ETFs are already diversified baskets and correlate with each other more than the 50 largest
S&P 500 stocks behind COR3M do, so implied sits below realised; that gap is the proxy, not a correlation risk premium.
The slope and R² are the usable result: how much of the next quarter's correlation the index options anticipate.

Live: XLK implied correlation from 30-day constant-maturity ATM vols (SURFACE_DAILY atm_30) and RV screens.
"""

from __future__ import annotations

import exchange_calendars as xcals
import numpy as np
import pandas as pd

from volsurf.events import group_of
from volsurf.snapshots import _xnys

GAP_NOTE = ("sector-level proxy: sector ETFs are diversified baskets and correlate with each other more than the single "
            "stocks behind COR3M, so implied sits below realised; the gap is the proxy, not a correlation risk premium")
STUDY_COLUMNS = ["n", "first_t", "last_t", "horizon", "maxlags", "intercept", "intercept_nw_se", "slope",
                 "slope_nw_se", "r2", "mean_implied", "mean_realised", "mean_gap", "gap_note"]
LIVE_COLUMNS = ["day", "index", "index_vol", "n_names", "covered_weight", "implied_corr", "realised_index_vol",
                "realised_implied_corr", "realised_avg_pairwise_corr", "status"]
RV_COLUMNS = ["day", "ticker", "group", "atm_30", "n_prior", "zscore", "group_median", "vol_minus_group_median",
              "status"]
INDEX = "XLK"  # kickoff Section 5.8: I = XLK


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


def window_complete(day: str, last_price: str, horizon: int) -> bool:
    """Instruction 07 step 7.2: True when the `horizon` XNYS sessions after `day` are all on or before `last_price`."""
    cal = _xnys()
    t = pd.Timestamp(day)
    end = cal.session_offset(t, horizon) if cal.is_session(t) else cal.session_offset(cal.date_to_session(t, "next"),
                                                                                        horizon - 1)
    return end.strftime("%Y-%m-%d") <= last_price


def window_returns(prices: pd.DataFrame, day: str, horizon: int) -> pd.DataFrame:
    """The daily log returns of every column of `prices` (adjusted closes indexed by date) over the `horizon` XNYS
    sessions after `day`, the first from the close of `day`; one row per session."""
    cal = _xnys()
    t = pd.Timestamp(day)
    start = t if cal.is_session(t) else cal.date_to_session(t, "previous")
    sessions = [start, *(cal.session_offset(start, j) for j in range(1, horizon + 1))]
    p = prices.copy()
    p.index = pd.DatetimeIndex(p.index)
    return np.log(p.reindex(pd.DatetimeIndex(sessions).tz_localize(None))).diff().iloc[1:]


def realised_vol(returns: pd.DataFrame) -> pd.Series:
    """O-42 (a) with the realised vol of (b), instruction 08: sqrt(252 / h x sum r^2) over the h daily log returns,
    not demeaned, as Section 5.9 RV (252: Convention 4.14). NaN for a column with a missing return."""
    h = len(returns)
    return np.sqrt(252 / h * (returns**2).sum(skipna=False))


def realised_side(prices: pd.DataFrame, day: str, names: pd.Index, weights: pd.Series, horizon: int) -> dict:
    """Kickoff 5.8 realised side with O-42 (a) and instruction 08: over sessions t+1 to t+`horizon`, the realised vol
    of XLK and of `names` (`realised_vol`), the implied correlation formula on those realised vols with the same
    renormalised weights (`implied_correlation`), and the average pairwise Pearson correlation (demeaned) of the
    names' daily log returns (`avg_pairwise_corr`, NaN with fewer than 2 names)."""
    rets = window_returns(prices[[INDEX, *names]], day, horizon)
    rv = realised_vol(rets)
    return {"realised_index_vol": float(rv[INDEX]),
            "realised_implied_corr": implied_correlation(float(rv[INDEX]), rv[list(names)], weights),
            "realised_avg_pairwise_corr": avg_pairwise_corr(rets[list(names)]) if len(names) >= 2 else np.nan}


def live_implied_corr(surface: pd.DataFrame, weights: pd.Series, prices: pd.DataFrame, last_price: str,
                      cfg) -> pd.DataFrame:
    """PLAN 7.2 with instructions 07 and 08, one row per day of SURFACE_DAILY: the XLK implied correlation from
    atm_30 with the holdings `weights` (ticker -> decimal weight) of the captured XLK names that have an atm_30 that
    day, renormalised (`live_weights`), and the covered weight; once the next `live_horizon` sessions are all on or
    before `last_price`, the realised side from the adjusted closes `prices` over the same names (`realised_side`).
    Status `ok`, or the conditions joined with `|`: `no_index_vol` (XLK has no atm_30 that day; implied blank),
    `pending` (the window is not complete, so the realised columns are blank). Columns LIVE_COLUMNS."""
    rows = []
    for day, g in surface.groupby("day", sort=True):
        vols = g.set_index("ticker")["atm_30"].astype(float)
        names = vols[vols.index.isin(weights.index) & (vols.index != INDEX)]
        w, covered = live_weights(weights, names)
        sig_i = float(vols.get(INDEX, np.nan))
        flags = [] if np.isfinite(sig_i) else ["no_index_vol"]
        realised = {"realised_index_vol": np.nan, "realised_implied_corr": np.nan,
                    "realised_avg_pairwise_corr": np.nan}
        if window_complete(day, last_price, cfg.correlation.live_horizon):
            realised = realised_side(prices, day, w.index, weights, cfg.correlation.live_horizon)
        else:
            flags.append("pending")
        rows.append({"day": day, "index": INDEX, "index_vol": sig_i, "n_names": len(w), "covered_weight": covered,
                     "implied_corr": implied_correlation(sig_i, names, weights) if np.isfinite(sig_i) else np.nan,
                     **realised, "status": "|".join(flags) or "ok"})
    return pd.DataFrame(rows, columns=LIVE_COLUMNS)


def rv_screen(surface: pd.DataFrame, cfg) -> pd.DataFrame:
    """PLAN 7.2 with O-15 (a) and instruction 07, one row per SURFACE_DAILY row: the name's atm_30 minus the median
    atm_30 of its kickoff Section 3.1 group that day (from day 1), and the z-score of atm_30 against the mean and
    standard deviation (ddof 1) of the name's atm_30 on its prior snapshot days, excluding today, blank with status
    `below_min_days` until it has `rv_min_days` prior days with an atm_30. A row with no atm_30 has status `no_vol`.
    Columns RV_COLUMNS, in day then SURFACE_DAILY order."""
    s = surface[["day", "ticker", "atm_30"]].copy()
    s["atm_30"] = s["atm_30"].astype(float)
    s["group"] = [group_of(t, cfg) for t in s["ticker"]]
    s["group_median"] = s.groupby(["day", "group"], sort=False)["atm_30"].transform("median")
    s["vol_minus_group_median"] = s["atm_30"] - s["group_median"]
    rows = []
    for r in s.itertuples():
        prior = s.loc[(s["ticker"] == r.ticker) & (s["day"] < r.day), "atm_30"].dropna()
        z, status = np.nan, "ok"
        if not np.isfinite(r.atm_30):
            status = "no_vol"
        elif len(prior) < cfg.correlation.rv_min_days:
            status = "below_min_days"
        else:
            z = (r.atm_30 - prior.mean()) / prior.std(ddof=1)  # O-15 (a): ddof 1, today excluded
        rows.append({"day": r.day, "ticker": r.ticker, "group": r.group, "atm_30": r.atm_30, "n_prior": len(prior),
                     "zscore": z, "group_median": r.group_median, "vol_minus_group_median": r.vol_minus_group_median,
                     "status": status})
    return pd.DataFrame(rows, columns=RV_COLUMNS).sort_values("day", kind="stable", ignore_index=True)
