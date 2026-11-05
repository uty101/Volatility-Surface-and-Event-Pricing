"""README.md from docs/README.template.md and the tables (PLAN 11.3, instruction 11 step 11.3).

The template holds the prose. `{{table:name}}` becomes the markdown table of TABLES, `{{answers:n}}` the answer rows of
research question n, and `{{name}}` a value of `readme_values`, so the tables and the numbers follow the data.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from volsurf.answers import read_table, read_value, select_rows

MINUS = "\N{MINUS SIGN}"  # no hyphens outside compound words, instruction 11 step 11.3
SPX_LAST_30 = "ticker=^SPX"


@dataclass(frozen=True)
class Column:
    """A CSV column shown under `header`, a number times `scale` to `places` decimals, or its text if places is None."""

    name: str
    header: str
    places: int | None = None
    scale: float = 1.0


@dataclass(frozen=True)
class Spec:
    file: str
    row: str
    columns: tuple[Column, ...]


TABLES = {
    "surface": Spec("surface_daily.csv", SPX_LAST_30, (
        Column("day", "day"), Column("atm_30", "ATM 30d %", 2, 100), Column("rr25_30", "RR 25d, pts", 2, 100),
        Column("bf25_30", "BF 25d, pts", 2, 100), Column("atm_90", "ATM 90d %", 2, 100),
        Column("term_slope", "term slope, pts", 2, 100), Column("n_expiries", "expiries", 0))),
    "events": Spec("events.csv", "ratio!=", (
        Column("ticker", "ticker"), Column("event_date", "date"), Column("timing", "timing"),
        Column("straddle_move", "straddle %", 2, 100), Column("ts_move", "term structure %", 2, 100),
        Column("realised_move", "realised %", 2, 100), Column("ratio", "ratio", 2))),
    "strategies": Spec("strategy_stats.csv", "all", (
        Column("strategy", "strategy"), Column("n_months", "months", 0), Column("ann_mean", "mean %", 2, 100),
        Column("ann_vol", "vol %", 2, 100), Column("sharpe", "Sharpe", 3), Column("worst_month", "worst month %", 2, 100),
        Column("worst_drawdown", "worst drawdown %", 2, 100), Column("skew", "skew", 2),
        Column("excess_kurtosis", "excess kurtosis", 2))),
    "cor3m": Spec("cor3m_study.csv", "all", (
        Column("n", "days", 0), Column("first_t", "first"), Column("last_t", "last"), Column("intercept", "intercept", 4),
        Column("slope", "slope", 4), Column("slope_nw_se", "slope se", 4), Column("r2", "R²", 4))),
    "implied_corr": Spec("implied_corr_live.csv", "implied_corr!=", (
        Column("day", "day"), Column("index_vol", "XLK vol %", 2, 100), Column("n_names", "names", 0),
        Column("covered_weight", "covered weight %", 1, 100), Column("implied_corr", "implied correlation", 3))),
    "hedging": Spec("hedging_frequency.csv", "all", (
        Column("model", "model"), Column("hedge_every_steps", "k", 0), Column("error_mean", "error mean", 3),
        Column("error_sd", "error sd", 3), Column("cost_mean", "cost mean", 3))),
    "risk_book": Spec("risk_book.csv", "all", (
        Column("contract", "contract"), Column("side", "side", 0), Column("contracts", "contracts", 0),
        Column("vol", "vol %", 2, 100), Column("vol_source", "vol source"), Column("dollar_delta", "dollar delta", 0),
        Column("dollar_gamma", "dollar gamma 1%", 0), Column("vega_pt", "vega per pt", 0))),
}


def _cell(text: str, column: Column) -> str:
    if column.places is None or text == "":
        return text
    return f"{float(text) * column.scale:.{column.places}f}".replace("-", MINUS)


def render_table(spec: Spec, tables: Path) -> str:
    """The rows `spec` selects as a markdown table."""
    rows = select_rows(read_table(tables / spec.file), spec.row)
    lines = ["| " + " | ".join(c.header for c in spec.columns) + " |", "|" + " --- |" * len(spec.columns)]
    lines += ["| " + " | ".join(_cell(r[c.name], c) for c in spec.columns) + " |" for _, r in rows.iterrows()]
    return "\n".join(lines)


def capture_window(tables: Path) -> dict[str, str]:
    """The window of instruction 11 step 11.3 from the data: first and last capture day, their count and the sessions
    in between with no capture."""
    days = sorted(read_table(tables / "surface_daily.csv")["day"].unique())
    health = read_table(tables / "capture_health.csv")
    missed = [d for d in health.loc[health["gap"] == "True", "session"] if d not in days]
    return {"first_day": days[0], "last_day": days[-1], "n_days": str(len(days)), "missed": ", ".join(missed)}


def readme_values(tables: Path, n_tests: int, min_n: int) -> dict[str, str]:
    """Every `{{name}}` of the template."""
    def get(file: str, row: str, column: str) -> float:
        return read_value(read_table(tables / file), row, column)

    window = capture_window(tables)
    last = f"ticker=^SPX;day={window['last_day']}"
    book = read_table(tables / "risk_grid.csv")
    book = book[book["contract"] == "book"]
    worst = pd.to_numeric(book["pnl"]).idxmin()
    breach = select_rows(read_table(tables / "limit_breaches.csv"), "breach=True")
    return {
        **window,
        "n_tests": f"{n_tests:,}",
        "atm_last": f"{get('surface_daily.csv', last, 'atm_30') * 100:.2f}",
        "rr_last": f"{get('surface_daily.csv', last, 'rr25_30') * 100:.2f}".replace("-", MINUS),
        "n_events": f"{get('event_summary.csv', 'scope=all', 'n'):.0f}",
        "min_n": str(min_n),
        "vrp_months": f"{get('vrp_monthly.csv', 'iv!=;rv_fwd_21!=', 'count(*)'):.0f}",
        "vrp_above": f"{get('vrp_monthly.csv', 'iv!=;rv_fwd_21!=;vrp>0', 'count(*)'):.0f}",
        "put_sharpe": f"{get('strategy_stats.csv', 'strategy=put', 'sharpe'):.2f}",
        "timed_sharpe": f"{get('strategy_stats.csv', 'strategy=timed_put', 'sharpe'):.2f}",
        "put_dd": f"{get('strategy_stats.csv', 'strategy=put', 'worst_drawdown') * 100:.1f}".replace("-", MINUS),
        "timed_dd": f"{get('strategy_stats.csv', 'strategy=timed_put', 'worst_drawdown') * 100:.1f}".replace("-", MINUS),
        "cor3m_slope": f"{get('cor3m_study.csv', 'all', 'slope'):.3f}",
        "cor3m_r2": f"{get('cor3m_study.csv', 'all', 'r2'):.3f}",
        "grid_worst": f"{abs(float(book.loc[worst, 'pnl'])) / 1000:,.1f}",
        "grid_spot": f"{float(book.loc[worst, 'spot_shock']) * 100:.0f}".replace("-", MINUS),
        "grid_vol": f"{float(book.loc[worst, 'vol_shock_pts']):.0f}",
        "n_breaches": str(len(breach)),
        "breach_underlying": ", ".join(breach["underlying"]),
        "breach_value": f"{float(breach['value'].iloc[0]):,.0f}".replace("-", MINUS) if len(breach) else "",
        "breach_limit": f"{float(breach['limit'].iloc[0]):,.0f}" if len(breach) else "",
    }


def build_readme(template: str, tables: Path, n_tests: int, min_n: int) -> str:
    values = readme_values(tables, n_tests, min_n)
    answers = read_table(tables / "answers.csv")

    def fill(match: re.Match) -> str:
        key = match.group(1)
        if key.startswith("table:"):
            return render_table(TABLES[key.removeprefix("table:")], tables)
        if key.startswith("answers:"):
            rows = answers[answers["question"] == key.removeprefix("answers:")]["answer"]
            return " ".join(rows).replace(" -", f" {MINUS}")
        return values[key]

    return re.sub(r"\{\{([\w:]+)\}\}", fill, template)
