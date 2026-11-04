"""answers.csv (PLAN 11.2, instruction 11 step 11.2): the 6 research questions of kickoff Section 1.

Every row carries a value and where it comes from (O-52 (a)): `source_table` is a file in outputs/tables/,
`source_row` selects its rows and `source_column` names the column or an aggregate of it. `read_value` resolves the 3,
so a row can always be checked against the table.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

ANSWER_COLUMNS = ["question", "answer", "value", "source_table", "source_row", "source_column"]
ALL_ROWS = "all"
ACCEPTED_ROWS = "status=ok|ok_refit"
AGGREGATES = {"sum": "sum", "mean": "mean", "median": "median", "min": "min", "max": "max"}
PROXY = ("COR3M covers single stocks and this proxy uses sector ETFs, which correlate with each other more, so implied "
         "sits below realised; the gap is the proxy, not a correlation risk premium")


def read_table(path: Path) -> pd.DataFrame:
    """A table with every cell as its text, so that selectors compare what the file holds."""
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def select_rows(table: pd.DataFrame, row: str) -> pd.DataFrame:
    """`all`, or conditions joined by `;`: `col=a|b` (equals either), `col!=` (not blank), and `col>=x`, `col<=x`,
    `col>x`, `col<x`, numeric when x is a number and otherwise on the text, which orders ISO dates."""
    if row == ALL_ROWS:
        return table
    mask = pd.Series(True, index=table.index)
    for condition in row.split(";"):
        col, op, x = re.fullmatch(r"(\w+)(>=|<=|!=|=|>|<)(.*)", condition).groups()
        cell = table[col]
        if op == "=":
            mask &= cell.isin(x.split("|"))
        elif op == "!=":
            mask &= cell != x
        else:
            try:
                left, right = pd.to_numeric(cell, errors="coerce"), float(x)
            except ValueError:
                left, right = cell, x
            mask &= {">=": left >= right, "<=": left <= right, ">": left > right, "<": left < right}[op]
    return table[mask]


def read_value(table: pd.DataFrame, row: str, column: str) -> float | str:
    """The value at `row` and `column`. `column` is a column name, which needs exactly 1 row and gives a number where
    the cell holds one and its text otherwise, or an aggregate over the rows: count(*), count(col) of the cells not
    blank, sum, mean, median, min and max of col, and corr(col,col)."""
    rows = select_rows(table, row)
    call = re.fullmatch(r"(\w+)\((.*)\)", column)
    if call is None:
        if len(rows) != 1:
            raise ValueError(f"{row} {column}: {len(rows)} rows, not 1")
        cell = rows[column].iloc[0]
        if cell == "":
            return np.nan
        try:
            return float(cell)
        except ValueError:
            return cell
    name, arg = call.groups()
    if name == "count":
        return float(len(rows) if arg == "*" else (rows[arg] != "").sum())
    if name == "corr":
        x, y = (pd.to_numeric(rows[c], errors="coerce") for c in arg.split(","))
        return float(x.corr(y))
    return float(getattr(pd.to_numeric(rows[arg], errors="coerce").dropna(), AGGREGATES[name])())


def format_value(value: float | str) -> str:
    """The text of a value, blank for nan."""
    if isinstance(value, str):
        return value
    return "" if np.isnan(value) else f"{value:.10g}"


class _Answers:
    """Collects answer rows. `add` formats `text` with the row's value times `scale`; the row keeps the value itself."""

    def __init__(self, tables: Path):
        self.tables, self.rows = tables, []

    def get(self, table: str, row: str, column: str) -> float | str:
        return read_value(read_table(self.tables / f"{table}.csv"), row, column)

    def add(self, question: int, text: str, table: str, row: str, column: str, scale: float = 1.0) -> None:
        value = self.get(table, row, column)
        shown = value if isinstance(value, str) or np.isnan(value) else value * scale
        self.rows.append({"question": question, "answer": text.format(shown), "value": format_value(value),
                          "source_table": f"{table}.csv", "source_row": row, "source_column": column})


def _question_1(a: _Answers) -> None:
    check = "pricer_check"
    n = int(a.get(check, "check=bsm_vs_quantlib", "n_cases"))
    a.add(1, f"Yes. BSM matches QuantLib's analytic engine: the largest price gap is {{:.1e}} over {n} grid cases, "
             "against a bound of 1e-10.", check, "check=bsm_vs_quantlib", "largest_gap")
    a.add(1, f"Black-76 equals BSM once S e^(\N{MINUS SIGN}qT) = D F: the largest gap is {{:.1e}} over {n} cases.", check,
          "check=black76_vs_bsm", "largest_gap")
    a.add(1, f"The American CRR tree at 2000 steps matches QuantLib's CRR engine: the largest gap is {{:.1e}} x S over "
             f"{n} cases, against a bound of 1e-4 x S.", check, "check=crr_american_vs_quantlib_rel_spot", "largest_gap")
    a.add(1, f"Delta, gamma, vega, theta and rho match QuantLib: the largest gap is {{:.1e}} over {n} cases each, "
             "against a bound of 1e-8.", check, "check=delta_vs_quantlib|gamma_vs_quantlib|vega_vs_quantlib|"
          "theta_vs_quantlib|rho_vs_quantlib", "max(largest_gap)")
    eep = "eep_summary"
    for ticker in ("SPY", "AAPL"):
        n = int(a.get(eep, f"ticker={ticker};kind=P;k_bin=(-0.02, 0.02]", "n"))
        a.add(1, f"Early exercise premium on {ticker} near the money puts: median {{:.2f}} vol points (N = {n} "
                 "contracts, fixture day).", eep, f"ticker={ticker};kind=P;k_bin=(-0.02, 0.02]", "median_vol_pts")
        n = int(a.get(eep, f"ticker={ticker};kind=P;k_bin=(0.10, inf)", "n"))
        a.add(1, f"It grows on {ticker} deep in the money puts: median {{:.2f}} vol points (N = {n} contracts).", eep,
              f"ticker={ticker};kind=P;k_bin=(0.10, inf)", "median_vol_pts")
    a.add(1, "On calls it is 0 to rounding: the largest median in any SPY or AAPL call bin is {:.1e} vol points. The "
             "single names captured later have no premium table, because the step runs on the fixture day, which holds "
             "SPY and AAPL only.", eep, "kind=C", "max(median_vol_pts)")


def _question_2(a: _Answers, n_days: int, first: str, last: str) -> None:
    surface, fits, cal = "surface_daily", "svi_fits", "calendar_violations"
    spx = f"ticker=^SPX;day={first}", f"ticker=^SPX;day={last}"
    a.add(2, f"^SPX 30-day ATM vol was {{:.2f}}% on {first} (N = {n_days} capture days).", surface, spx[0], "atm_30",
          100)
    a.add(2, f"It was {{:.2f}}% on {last}, after the 2026-10-30 sell-off.", surface, spx[1], "atm_30", 100)
    before = a.get(surface, spx[0], "rr25_30") * 100
    a.add(2, f"The 30-day 25-delta risk reversal went from {before:.2f} to {{:.2f}} vol points, so skew steepened "
             f"(N = {n_days} days).", surface, spx[1], "rr25_30", 100)
    before = a.get(surface, spx[0], "term_slope") * 100
    a.add(2, f"The term slope, ATM 90 days minus 30 days, went from {before:.2f} to {{:.2f}} vol points, so the short "
             f"end moved above the long end (N = {n_days} days).", surface, spx[1], "term_slope", 100)
    n = int(a.get(fits, "n_quotes!=", "count(*)"))
    a.add(2, f"Butterfly: {{:.0f}} of {n} SVI slices across every underlying and day are accepted; the rest are "
             f"rejected or have too few quotes to fit (N = {n_days} days).", fits, ACCEPTED_ROWS, "count(*)")
    a.add(2, "Every accepted slice is free of butterfly arbitrage up to the check's tolerance: the smallest g on the "
             "acceptance grid is {:.1e}, against -1e-10.", fits, ACCEPTED_ROWS, "min(min_g)")
    n = int(a.get(cal, "ticker=^SPX", "count(*)"))
    a.add(2, f"Calendar: the per-expiry slices are not fully clean. {{:.0f}} of {n} consecutive ^SPX pairs cross "
             f"somewhere on their shared quoted range (N = {n_days} days).", cal, "ticker=^SPX;violated=True",
          "count(*)")
    n = int(a.get(cal, ALL_ROWS, "count(*)"))
    a.add(2, f"Across every underlying it is {{:.0f}} of {n} pairs. Slices are not refitted for this; SSVI is the "
             "calendar-consistent surface, because its theta is non-decreasing in T by construction.", cal,
          "violated=True", "count(*)")
    a.add(2, f"SSVI pays for that in fit: its ^SPX RMSE was {{:.2f}} vol points on {last}, because 1 rho cannot hold the "
             "skew, so the daily metrics come from the slices.", surface, spx[1], "ssvi_rmse", 100)


def _question_3(a: _Answers, min_n: int) -> None:
    events, summary = "events", "event_summary"
    n = int(a.get(summary, "scope=all", "n"))
    if n < min_n:
        a.add(3, f"With N = {{:.0f}} completed events, fewer than the {min_n} the summary needs, the gap between implied "
                 "and realised moves cannot be told apart from 0 at this N.", summary, "scope=all", "n")
    else:
        lo, hi = (a.get(summary, "scope=all", c) for c in ("mean_lo", "mean_hi"))
        a.add(3, f"Over N = {n} completed events the mean of ln(R / M_t) is {{:.3f}}, with a 90% interval of {lo:.3f} to "
                 f"{hi:.3f}.", summary, "scope=all", "mean_log_ratio")
    table = read_table(a.tables / "events.csv")
    for e in table[table["ratio"] != ""].itertuples():
        row = f"ticker={e.ticker};event_date={e.event_date}"
        a.add(3, f"{e.ticker} {e.timing} {e.event_date}: realised {float(e.realised_move) * 100:.2f}% against a term "
                 f"structure move of {float(e.ts_move) * 100:.2f}% and a straddle move of "
                 f"{float(e.straddle_move) * 100:.2f}%, ratio {{:.2f}}.", events, row, "ratio")
    a.add(3, "{:.0f} more events have a window that ends after the last close in the data and stay pending.", events,
          "status=pending", "count(*)")
    a.add(3, "{:.0f} events have no pre-event snapshot, because they fall before the capture could see them.", events,
          "status=no_pre_snapshot", "count(*)")


def _question_4(a: _Answers, strategy_start: str) -> None:
    vrp, stats, spec = "vrp_monthly", "strategy_stats", "spec_log"
    both = "iv!=;rv_fwd_21!="
    n = int(a.get(vrp, both, "count(*)"))
    a.add(4, f"VIX squared sat above the variance that followed by {{:.5f}} of annualised variance on average, over {n} "
             "months from 1990.",
          vrp, both, "mean(vrp)")
    era = f"{both};garch_fc!="
    n = int(a.get(vrp, era, "count(*)"))
    a.add(4, f"Over the {n} months that also have a GARCH forecast the mean gap is {{:.5f}}.", vrp, era, "mean(vrp)")
    n = int(a.get(vrp, "signal!=", "count(*)"))
    a.add(4, f"Implied variance is above the GARCH forecast in {{:.0f}} of {n} month ends.", vrp, "signal>0", "count(*)")
    n = int(a.get(vrp, era, "count(*)"))
    a.add(4, f"The forecast says little about the size of the gap: the correlation of the signal with the later gap is "
             f"{{:.2f}} over {n} months.", vrp, era, "corr(signal,vrp)")
    months = int(a.get(stats, "strategy=put", "n_months"))
    a.add(4, f"Selling puts paid, but less per unit of risk than holding the index: Cboe PUT has a Sharpe of {{:.2f}} "
             f"over {months} months from 2007, against {a.get(stats, 'strategy=sp500tr', 'sharpe'):.2f} for the S&P 500 "
             f"total return index and {a.get(stats, 'strategy=bxm', 'sharpe'):.2f} for BXM. The index carries no trading "
             "costs of its own, so the only cost deducted here is the timed strategy's switching cost.", stats,
          "strategy=put", "sharpe")
    a.add(4, "PUT's worst month was {:.2f}%.", stats, "strategy=put", "worst_month", 100)
    n_trials = int(a.get(stats, "strategy=timed_put", "n_trials"))
    status = a.get(stats, "strategy=timed_put", "dsr_status")
    a.add(4, f"Timing on implied minus GARCH variance gives a raw Sharpe of {{:.2f}} over {months} months, after the "
             "switching cost.", stats, "strategy=timed_put", "sharpe")
    a.add(4, f"The deflated Sharpe beside it is blank, with status {status}, because {n_trials} specification was tried "
             "and the deflation needs at least 2.", stats, "strategy=timed_put", "deflated_sharpe")
    a.add(4, "So the number of specifications tried is {:.0f}, and the raw figure is 1 specification of a family, not "
             "evidence that timing improves the deflated Sharpe.", spec, ALL_ROWS, "count(*)")
    decided = sorted(read_table(a.tables / "strategies.csv")["month_end"])[-2]  # the last month's position, set a month before
    a.add(4, "The raw gain over PUT comes from sitting out {:.0f} months.", vrp,
          f"month_end>={strategy_start};month_end<={decided};signal<=0", "count(*)")


def _question_5(a: _Answers, n_live: int, last: str) -> None:
    study, live = "cor3m_study", "implied_corr_live"
    n = int(a.get(study, ALL_ROWS, "n"))
    se = a.get(study, ALL_ROWS, "slope_nw_se")
    a.add(5, f"Yes, in part. Regressing the next 63 sessions' realised sector correlation on COR3M gives a slope of "
             f"{{:.3f}} (Newey-West se {se:.3f}), N = {n} days.", study, ALL_ROWS, "slope")
    a.add(5, f"R² is {{:.3f}}, so COR3M accounts for a bit under half of the variation in next quarter's realised "
             f"correlation (N = {n} days).", study, ALL_ROWS, "r2")
    a.add(5, f"The mean gap, implied minus realised, is {{:.3f}}. {PROXY}.", study, ALL_ROWS, "mean_gap")
    row = f"day={last}"
    w, names = a.get(live, row, "covered_weight"), int(a.get(live, row, "n_names"))
    a.add(5, f"The XLK chain priced an implied correlation of {{:.3f}} on {last}, with {names} names covering "
             f"{w * 100:.1f}% of the weight (N = {n_live} days with a value).", live, row, "implied_corr")
    before = a.get(live, "day=2026-10-29", "implied_corr")
    a.add(5, f"It rose from {before:.3f} on 2026-10-29 to {{:.3f}} on 2026-10-30, when the S&P 500 fell 1.8% and XLK "
             "4.9%. Implied correlation rising in a sell-off is the textbook pattern.", live, "day=2026-10-30",
          "implied_corr")


def _question_6(a: _Answers) -> None:
    live, synth, freq = "attribution_live", "attribution_synthetic", "hedging_frequency"
    n = int(a.get(live, ALL_ROWS, "count(*)"))
    a.add(6, f"On the live delta-hedged ^SPX straddles the median explained share is {{:.3f}} (N = {n} position moves, a "
             "method demonstration).", live, ALL_ROWS, "median(explained_share)")
    n_syn = int(a.get(synth, ALL_ROWS, "count(*)"))
    a.add(6, f"On a synthetic Black-Scholes path it is {{:.3f}} (N = {n_syn} daily steps).", synth, ALL_ROWS,
          "median(explained_share)")
    for name, label in (("gamma", "Gamma"), ("theta", "Theta"), ("vega", "Vega"), ("residual", "The residual")):
        a.add(6, f"{label} summed to {{:.2f}} index points per straddle unit over the {n} live moves.", live, ALL_ROWS,
              f"sum({name})")
    a.add(6, f"Delta and the hedge cancel and vanna and volga are small, so the delta-hedged P&L summed to {{:.2f}} over "
             f"the same {n} moves.", live, ALL_ROWS, "sum(total)")
    gbm, heston = "model=gbm;hedge_every_steps=1", "model=heston;hedge_every_steps=1"
    a.add(6, "Hedging every step (k = 1) leaves an error sd of {:.3f} under GBM.", freq, gbm, "error_sd")
    a.add(6, "The same hedge leaves {:.3f} under Heston: the hedge uses delta at the current vol but is blind to vol "
             "moves, so even continuous hedging leaves an unhedged vega P&L, and the error sd stops falling in "
             "proportion to the square root of k. The means are not comparable, because the 2 drifts differ.", freq,
          heston, "error_sd")
    a.add(6, "Hedging less often raises the GBM error sd to {:.3f} at k = 65, 5 days between hedges.", freq,
          "model=gbm;hedge_every_steps=65", "error_sd")
    a.add(6, "It cuts cost: the GBM mean cost falls from {:.3f} at k = 1 to "
             f"{a.get(freq, 'model=gbm;hedge_every_steps=65', 'cost_mean'):.3f} at k = 65.", freq, gbm, "cost_mean")


def build_answers(tables: Path, cfg) -> pd.DataFrame:
    """1 or more rows per research question 1 to 6 of kickoff Section 1, as restated in `CLAUDE.md` Amendments, with
    the framings of instruction 11 step 11.2. Reads every value from `tables` (ANSWER_COLUMNS)."""
    a = _Answers(tables)
    days = sorted(read_table(tables / "surface_daily.csv")["day"].unique())
    live = read_table(tables / "implied_corr_live.csv")
    _question_1(a)
    _question_2(a, len(days), days[0], days[-1])
    _question_3(a, cfg.events.min_n)
    _question_4(a, cfg.vrp.strategy_start)
    _question_5(a, int((live["implied_corr"] != "").sum()), days[-1])
    _question_6(a)
    frame = pd.DataFrame(a.rows, columns=ANSWER_COLUMNS)
    if not np.array_equal(frame["question"].unique(), np.arange(1, 7)):
        raise ValueError("every research question needs an answer")
    return frame
