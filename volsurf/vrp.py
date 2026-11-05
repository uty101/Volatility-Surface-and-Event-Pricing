"""Volatility risk premium (PLAN 8.1 and 8.2, kickoff Section 5.9, instruction 08).

VIX squared against the variance of the S&P 500 over the next 21 sessions from 1990, a GARCH(1,1) forecast as the ex
ante gap, Cboe PUT and BXM as investable short volatility return series, and a timed PUT that holds PUT only when
implied variance is above the GARCH forecast. The timed PUT is 1 specification out of a closed family of 5 (instruction
12), so its Sharpe ratio is reported beside the deflated Sharpe ratio, with the number of specifications tried.
"""

from __future__ import annotations

import json
import warnings
from datetime import UTC, datetime
from pathlib import Path

import exchange_calendars as xcals
import numpy as np
import pandas as pd
from arch import arch_model
from scipy.stats import norm

from volsurf.pricing import black76
from volsurf.ssvi import ssvi_w, theta_at

VRP_COLUMNS = ["month_end", "vix", "iv", "garch_fc", "signal", "rv_fwd_21", "vrp"]
STRATEGY_COLUMNS = ["month_end", "put", "bxm", "sp500tr", "timed_put", "tbill"]
SPEC_COLUMNS = ["run_utc", "spec_id", "description", "params_json", "sharpe", "n_months"]
STATS_COLUMNS = ["strategy", "first_month", "last_month", "n_months", "ann_mean", "ann_vol", "sharpe", "worst_month",
                 "worst_drawdown", "skew", "excess_kurtosis", "q01", "q05", "n_trials", "deflated_sharpe",
                 "dsr_status"]
STRADDLE_COLUMNS = ["open_day", "expiry", "strike", "mark_day", "T", "S", "F", "D", "vol", "value", "delta",
                    "option_pnl", "hedge_pnl", "total_pnl", "status"]
FAMILY_COLUMNS = ["series", "spec_id", "n_months", "sharpe", "sharpe_monthly", "skew", "kurt_pearson", "n_trials",
                  "sr_var", "sr0", "deflated_sharpe", "psr_zero"]
SPEC_FAMILY = ("timed_put_main", "iv_minus_rv21", "iv_minus_rv63", "iv_minus_ewma", "garch_above_median")  # instruction 12
MAIN_ID = SPEC_FAMILY[0]
MONTHS = 12  # Convention 4.14: monthly series x 12 for means, sqrt(12) for vol
EULER_GAMMA = 0.5772156649015329  # Bailey and Lopez de Prado (2014), the expected maximum of N Sharpe ratios


def month_ends(sessions: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Convention 4.13 and instruction 08 point 1: the last session in `sessions` of each calendar month, for
    completed months only. The last month in `sessions` is kept only if its last date is the month's last XNYS
    session; otherwise it is the current, incomplete month."""
    s = pd.DatetimeIndex(sessions).sort_values()
    ends = pd.Series(s, index=s).groupby(s.to_period("M")).max()
    last = ends.index[-1]
    cal = xcals.get_calendar("XNYS", start=last.start_time.strftime("%Y-%m-%d"),
                             end=last.end_time.strftime("%Y-%m-%d"))
    if ends.iloc[-1] < pd.Timestamp(cal.sessions[-1]).tz_localize(None):
        ends = ends.iloc[:-1]
    return pd.DatetimeIndex(ends.to_numpy())


def level_at(series: pd.Series, dates: pd.DatetimeIndex) -> pd.Series:
    """Instruction 08 point 2: the last available value of `series` on or before each date."""
    s = series.dropna().sort_index()
    s.index = pd.DatetimeIndex(s.index)
    return pd.Series(s.asof(dates).to_numpy(), index=dates)


def log_returns(close: pd.Series, start: str) -> pd.Series:
    """Daily log returns of `close` from the first close on or after `start` (its first return is the next session)."""
    c = close.dropna().sort_index()
    c.index = pd.DatetimeIndex(c.index)
    return np.log(c[c.index >= start]).diff().dropna()


def realised_var(returns: pd.Series, h: int) -> pd.Series:
    """Kickoff 5.9: RV_t,h = (252 / h) sum_{j=1..h} r_{t+j}^2 at every date t of `returns`; NaN where fewer than h
    returns follow t (252: Convention 4.14)."""
    return (returns**2).rolling(h).sum().shift(-h) * 252 / h


def garch_forecast(returns: pd.Series, h: int) -> float:
    """Kickoff 5.9: `arch` GARCH(1,1), constant mean, normal errors, on `returns` x 100, the forecast variance summed
    over horizons 1 to h, annualised x 252 / h / 10000 (Section 5.9)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # arch's scaling and convergence notices; the fit is used as it ends
        res = arch_model(returns * 100, mean="Constant", vol="GARCH", p=1, q=1, dist="normal").fit(disp="off")
        var = res.forecast(horizon=h, reindex=False).variance.iloc[-1]
    return float(var.sum()) * 252 / h / 10000


def garch_monthly_forecasts(returns: pd.Series, h: int, min_obs: int) -> pd.Series:
    """Kickoff 5.9: at each completed month end of `returns` (`month_ends`), `garch_forecast` fitted on the returns up
    to and including that session, an expanding window; NaN while fewer than `min_obs` returns are available."""
    returns = returns.sort_index()
    out = {}
    for m in month_ends(returns.index):
        x = returns[returns.index <= m]
        out[m] = garch_forecast(x, h) if len(x) >= min_obs else np.nan
    return pd.Series(out, dtype=float)


def vrp_monthly(vix: pd.Series, gspc: pd.Series, cfg) -> pd.DataFrame:
    """VRP_MONTHLY (PLAN 8.1): at each completed month end from `[vrp] start` (the last `^GSPC` session of the
    month), VIX on or before it, IV = (VIX / 100)^2, the GARCH forecast, signal = IV - GARCH, RV over the next
    `horizon` sessions and VRP = IV - RV. Returns are `^GSPC` log returns from the close of `[vrp] start`."""
    v = cfg.vrp
    r = log_returns(gspc, v.start)
    fc = garch_monthly_forecasts(r, v.horizon, v.garch_min_obs)
    ends = fc.index
    rv = realised_var(r, v.horizon).reindex(ends)
    vx = level_at(vix, ends)
    iv = (vx / 100) ** 2  # kickoff 5.9: IV_t = (VIX_t / 100)^2
    out = pd.DataFrame({"month_end": ends.strftime("%Y-%m-%d"), "vix": vx.to_numpy(), "iv": iv.to_numpy(),
                        "garch_fc": fc.to_numpy(), "signal": (iv - fc).to_numpy(), "rv_fwd_21": rv.to_numpy(),
                        "vrp": (iv - rv).to_numpy()})
    return out[VRP_COLUMNS]


def monthly_returns(level: pd.Series, ends: pd.DatetimeIndex) -> pd.Series:
    """Simple returns month end to month end from the level on or before each of `ends`; the first end is the base."""
    lv = level_at(level, ends)
    return (lv / lv.shift(1) - 1).iloc[1:]


def tbill_returns(dtb3: pd.Series, ends: pd.DatetimeIndex) -> pd.Series:
    """O-16 (b): the T-bill return for month m+1 is DTB3 on or before the last session of month m / 1200 (the rate
    known at the decision), labelled at month end m+1."""
    return (level_at(dtb3, ends) / 1200).shift(1).iloc[1:]


def timed_positions(signal: pd.Series) -> pd.Series:
    """Instruction 08 point 6: the position held in month m+1, labelled at month end m+1, is PUT if s_m > 0, else
    T-bills; True for PUT."""
    return (signal > 0).shift(1).iloc[1:].astype(bool)


def strategy_returns(put: pd.Series, bxm: pd.Series, sp500tr: pd.Series, dtb3: pd.Series, signal: pd.Series,
                     switch_cost_bp: float) -> pd.DataFrame:
    """STRATEGIES (PLAN 8.2, kickoff 5.9). `signal`: s_m indexed by the month ends of the window (from `[vrp]
    strategy_start`); the first month end is the base. Monthly simple returns month end to month end from each index
    level on or before the month end (instruction 08 point 2). T-bill return for month m+1 = DTB3 on or before the
    last session of month m / 1200 (O-16 (b)). The timed PUT holds PUT in month m+1 if s_m > 0, else earns the
    T-bill; every change of position, the first included, costs `switch_cost_bp` / 10,000 off that month's return."""
    ends = pd.DatetimeIndex(signal.index)
    rets = pd.DataFrame({k: monthly_returns(s, ends) for k, s in (("put", put), ("bxm", bxm), ("sp500tr", sp500tr))})
    tbill = tbill_returns(dtb3, ends)
    hold = timed_positions(signal)
    timed = rets["put"].where(hold, tbill)
    change = hold.ne(hold.shift(1))  # the first position counts as a change (instruction 08 point 6)
    timed = timed - change * switch_cost_bp / 10_000
    out = pd.DataFrame({"month_end": rets.index.strftime("%Y-%m-%d"), **{c: rets[c].to_numpy() for c in rets},
                        "timed_put": timed.to_numpy(), "tbill": tbill.to_numpy()})
    return out[STRATEGY_COLUMNS]


def drawdown(r: pd.Series) -> pd.Series:
    """Wealth W_t = prod (1 + r) from 1 at the start, against its running maximum: W / max W - 1."""
    w = pd.concat([pd.Series([1.0]), (1 + r.reset_index(drop=True)).cumprod()], ignore_index=True)
    return (w / w.cummax() - 1).iloc[1:].set_axis(r.index)


def strategy_stats(name: str, r: pd.Series, tbill: pd.Series, month_end: pd.Series) -> dict:
    """PLAN 8.2 statistics of the monthly simple returns `r`: annualised mean and vol (Convention 4.14), Sharpe on
    excess returns over `tbill` (instruction 08 point 5) x sqrt(12), worst month, worst drawdown (`drawdown`),
    skew and excess kurtosis (pandas, bias corrected), 1% and 5% monthly quantiles (linear)."""
    ex = r - tbill
    return {"strategy": name, "first_month": month_end.iloc[0], "last_month": month_end.iloc[-1], "n_months": len(r),
            "ann_mean": float(r.mean() * MONTHS), "ann_vol": float(r.std() * np.sqrt(MONTHS)),
            "sharpe": float(ex.mean() / ex.std() * np.sqrt(MONTHS)), "worst_month": float(r.min()),
            "worst_drawdown": float(drawdown(r).min()), "skew": float(r.skew()), "excess_kurtosis": float(r.kurt()),
            "q01": float(r.quantile(0.01)), "q05": float(r.quantile(0.05))}


def spec_signals(main: pd.Series, iv: pd.Series, returns: pd.Series) -> pd.DataFrame:
    """Instruction 12 step 12.1: s_m of the 5 specifications at the month ends of `main`, the VRP_MONTHLY signal, each
    using data up to and including m. `iv` is (VIX / 100)^2 at those month ends, `returns` the daily `^GSPC` log returns
    from `[vrp] start`. Column order is SPEC_FAMILY.

    The 21, the 63 and alpha = 0.06 (lambda = 0.94) are the constants of the instruction's table. The EWMA is
    `adjust=False`, so it starts at the first squared return. The expanding median is shifted by 1 month end, so it
    holds only month ends strictly before m."""
    r2 = returns**2
    ends = main.index

    def rv(n: int) -> pd.Series:
        return (r2.rolling(n).sum() * 252 / n).reindex(ends)

    ewma = (r2.ewm(alpha=0.06, adjust=False).mean() * 252).reindex(ends)
    out = pd.DataFrame({"timed_put_main": main, "iv_minus_rv21": iv - rv(21), "iv_minus_rv63": iv - rv(63),
                        "iv_minus_ewma": iv - ewma, "garch_above_median": main - main.expanding().median().shift(1)})
    return out[list(SPEC_FAMILY)]


def series_moments(x: pd.Series) -> dict:
    """What the Sharpe tests need of the monthly series `x` itself (instruction 12): monthly Sharpe mean / sd, the
    number of months, skew and non-excess kurtosis (pandas, bias corrected, as `strategy_stats`)."""
    return {"sr": float(x.mean() / x.std()), "n_obs": len(x), "skew": float(x.skew()), "kurt_pearson": float(x.kurt() + 3)}


def expected_max_sharpe(sr_trials: pd.Series) -> float:
    """SR_0 of `deflated_sharpe`: the Sharpe ratio expected of the best of N trials with no skill. NaN below 2 trials."""
    trials = pd.Series(sr_trials, dtype=float)
    n = len(trials)
    if n < 2:
        return float("nan")
    return float(np.sqrt(trials.var(ddof=1)) * ((1 - EULER_GAMMA) * norm.ppf(1 - 1 / n)
                                                + EULER_GAMMA * norm.ppf(1 - 1 / (n * np.e))))


def probabilistic_sharpe(sr: float, n_obs: int, skew: float, kurt_pearson: float, sr_star: float = 0.0) -> float:
    """Bailey and Lopez de Prado (2012): the probability that the true Sharpe ratio is above `sr_star`, in the units of
    one observation, with `kurt_pearson` as in `deflated_sharpe`:

        PSR = Phi((SR - SR*) sqrt(n_obs - 1) / sqrt(1 - gamma_3 SR + (gamma_4 - 1) / 4 SR^2))"""
    return float(norm.cdf((sr - sr_star) * np.sqrt(n_obs - 1) / np.sqrt(1 - skew * sr + (kurt_pearson - 1) / 4 * sr**2)))


def deflated_sharpe(sr: float, n_obs: int, skew: float, kurt_pearson: float, sr_trials: pd.Series) -> float:
    """Bailey and Lopez de Prado (2014), the deflated Sharpe ratio, with every Sharpe ratio in the units of one
    observation (O-17 (a): monthly, so annualised Sharpe / sqrt(12) and `n_obs` in months).

    `kurt_pearson` is the non-excess (Pearson) kurtosis gamma_4, 3 for a normal (instruction 08 point 3);
    `strategy_stats` reports excess kurtosis, which is gamma_4 - 3. With N = len(`sr_trials`) and V their sample
    variance (ddof 1):

        SR_0 = sqrt(V) ((1 - g) Phi^-1(1 - 1/N) + g Phi^-1(1 - 1/(N e))),  g = Euler-Mascheroni constant
        DSR  = Phi((SR - SR_0) sqrt(n_obs - 1) / sqrt(1 - gamma_3 SR + (gamma_4 - 1) / 4 SR^2))

    NaN with fewer than 2 trials (instruction 08 point 4)."""
    sr0 = expected_max_sharpe(sr_trials)
    return float("nan") if np.isnan(sr0) else probabilistic_sharpe(sr, n_obs, skew, kurt_pearson, sr0)


def family_row(series: str, spec_id: str, x: pd.Series) -> dict:
    """A row of spec_family.csv for the monthly series `x`, without the columns that need the family."""
    m = series_moments(x)
    return {"series": series, "spec_id": spec_id, "n_months": m["n_obs"], "sharpe": m["sr"] * np.sqrt(MONTHS),
            "sharpe_monthly": m["sr"], "skew": m["skew"], "kurt_pearson": m["kurt_pearson"],
            "psr_zero": probabilistic_sharpe(**m)}


def family_rows(series: str, returns: pd.DataFrame) -> list[dict]:
    """Rows of spec_family.csv for `returns`, 1 monthly column per specification. The main specification also gets N,
    the variance of the family's monthly Sharpes, SR_0 and the deflated Sharpe against them (instruction 12)."""
    rows = [family_row(series, c, returns[c]) for c in returns]
    trials = pd.Series([r["sharpe_monthly"] for r in rows], dtype=float)
    main = next(r for r in rows if r["spec_id"] == MAIN_ID)
    main.update(n_trials=len(trials), sr_var=trials.var(ddof=1), sr0=expected_max_sharpe(trials),
                deflated_sharpe=deflated_sharpe(**series_moments(returns[MAIN_ID]), sr_trials=trials))
    return rows


def family_table(excess: pd.DataFrame, timed_minus_put: pd.DataFrame, put_excess: pd.Series) -> pd.DataFrame:
    """spec_family.csv (O-56 (a)): the 5 specifications on excess returns over T-bills, PUT alone on excess returns,
    which is outside the family and so has no deflated Sharpe, and the 5 on timed minus PUT."""
    rows = [*family_rows("excess", excess), family_row("excess", "put", put_excess),
            *family_rows("timed_minus_put", timed_minus_put)]
    return pd.DataFrame(rows, columns=FAMILY_COLUMNS)


def append_spec(path: Path, spec_id: str, description: str, params: dict, sharpe: float, n_months: int) -> pd.DataFrame:
    """Kickoff 5.9: append a specification run to spec_log.csv (columns SPEC_COLUMNS, `sharpe` annualised, O-17 (a))
    and return the log. A run whose spec_id and params_json are already in the log is not appended again; its
    sharpe and n_months are updated in place (the data window can grow), so the log counts specifications tried,
    not times the stage ran."""
    log = pd.read_csv(path, dtype={"params_json": str}) if path.exists() else pd.DataFrame(columns=SPEC_COLUMNS)
    params_json = json.dumps(params, sort_keys=True)
    same = (log["spec_id"] == spec_id) & (log["params_json"] == params_json)
    if same.any():
        log.loc[same, ["sharpe", "n_months"]] = [sharpe, n_months]
    else:
        row = {"run_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"), "spec_id": spec_id,
               "description": description, "params_json": params_json, "sharpe": sharpe, "n_months": n_months}
        log = pd.concat([log, pd.DataFrame([row])], ignore_index=True)[SPEC_COLUMNS]
    log = log.astype({"sharpe": float, "n_months": int})  # the first write starts from an untyped frame
    path.parent.mkdir(parents=True, exist_ok=True)
    log.to_csv(path, index=False, float_format="%.10g", lineterminator="\n", encoding="utf-8")
    return log


def straddle_mark(K: float, F: float, T: float, D: float, S: float, ssvi: dict, thetas: pd.DataFrame) -> dict:
    """One mark of a straddle at strike K off that day's SSVI surface: vol = sqrt(w(ln(K / F), theta(T)) / T) with
    theta by Convention 4.12, value = Black-76 call + put, spot delta = D (F / S) (2 N(d1) - 1)."""
    theta = theta_at(T, thetas)
    if not np.isfinite(theta):
        return {"vol": np.nan, "value": np.nan, "delta": np.nan}
    vol = float(np.sqrt(ssvi_w(np.log(K / F), theta, ssvi["rho"], ssvi["eta"], ssvi["gamma"]) / T))
    value = float(black76(F, K, T, D, vol, "C") + black76(F, K, T, D, vol, "P"))
    d1 = (np.log(F / K) + vol**2 * T / 2) / (vol * np.sqrt(T))
    return {"vol": vol, "value": value, "delta": float(D * F / S * (2 * norm.cdf(d1) - 1))}


def live_straddles(days: list[str], quotes: pd.DataFrame, surface: pd.DataFrame, thetas: pd.DataFrame,
                   target_days: int) -> pd.DataFrame:
    """Kickoff 5.9 live descriptive, 1 row per position per snapshot day. On each day in `days` a short ^SPX
    straddle opens on the expiry with T nearest `target_days` / 365 (ties to the shorter) at the quoted strike nearest
    F (ties to the lower), from `quotes` (one row per day, expiry and strike: T, S, F, r). It is marked off each later
    day's SSVI (`straddle_mark`; `surface` rows with ssvi_rho, ssvi_eta, ssvi_gamma, `thetas` with T and theta_used)
    until expiry or the last day, and delta hedged at each mark by holding delta units of the index. Short P&L:
    option_pnl = value at open - value now; hedge_pnl = sum of delta_prev (S_now - S_prev); no financing.
    Status `open` (marked), `closed` (marked on its expiry day), `no_quote` (the expiry has no F that day) or
    `no_surface` (no SSVI fit, or T outside the accepted expiries)."""
    rows = []
    for open_day in days:
        q0 = quotes[quotes["day"] == open_day]
        exp = q0.groupby("expiry", sort=True)["T"].first()
        expiry = exp.index[np.argmin(np.abs(exp.to_numpy() - target_days / 365))]  # argmin: first, the shorter
        e0 = q0[q0["expiry"] == expiry]
        F0 = float(e0["F"].iloc[0])
        K = float(e0["strike"].to_numpy()[np.argmin(np.abs(e0["strike"].to_numpy() - F0))])
        open_value, prev = np.nan, None
        for mark_day in [d for d in days if open_day <= d <= expiry]:
            row = {"open_day": open_day, "expiry": expiry, "strike": K, "mark_day": mark_day}
            e = quotes[(quotes["day"] == mark_day) & (quotes["expiry"] == expiry)]
            s = surface[surface["day"] == mark_day]
            if e.empty or not np.isfinite(float(e["F"].iloc[0])):
                rows.append({**row, "status": "no_quote"})
                if prev is None:
                    break  # never opened
                continue
            T, S, F, r = (float(e[c].iloc[0]) for c in ("T", "S", "F", "r"))
            D = float(np.exp(-r * T))
            mark = {"vol": np.nan, "value": np.nan, "delta": np.nan}
            if not s.empty and s["ssvi_rho"].notna().iloc[0]:
                ssvi = {"rho": s["ssvi_rho"].iloc[0], "eta": s["ssvi_eta"].iloc[0], "gamma": s["ssvi_gamma"].iloc[0]}
                mark = straddle_mark(K, F, T, D, S, ssvi, thetas[thetas["day"] == mark_day].sort_values("T"))
            row.update(T=T, S=S, F=F, D=D, **mark)
            if not np.isfinite(mark["value"]):
                rows.append({**row, "status": "no_surface"})
                if prev is None:
                    break  # never opened
                continue
            if prev is None:
                open_value, hedge = mark["value"], 0.0
            else:
                hedge = prev["hedge_pnl"] + prev["delta"] * (S - prev["S"])
            row.update(option_pnl=open_value - mark["value"], hedge_pnl=hedge,
                       total_pnl=open_value - mark["value"] + hedge, status="closed" if mark_day == expiry else "open")
            rows.append(row)
            prev = row
    return pd.DataFrame(rows, columns=STRADDLE_COLUMNS)
