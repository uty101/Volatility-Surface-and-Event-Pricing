"""README.md from docs/README.template.md and the tables (PLAN 11.3, instruction 11 step 11.3, instruction 13).

The template holds the prose. `{{table:name}}` becomes the markdown table of TABLES, `{{answers:n}}` the answer rows of
research question n (`{{answers:n:summary}}` without the per-event rows), `{{findings}}` the "What it found"
paragraphs and `{{name}}` a value of `readme_values`, so the tables and the numbers follow the data.
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
    """A CSV column shown under `header`, a number times `scale` to `places` decimals (in e notation if `exp`), or its
    text if places is None."""

    name: str
    header: str
    places: int | None = None
    scale: float = 1.0
    exp: bool = False


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


@dataclass(frozen=True)
class Finding:
    """A "What it found" paragraph: the question in bold, then `text` filled from the named groups of `patterns`,
    each matched against the question's answer text in answers.csv, so every number comes from that file."""

    question: str
    heading: str
    patterns: tuple[str, ...]
    text: str


FINDINGS = (
    Finding("1", "Question 1: does the pricer match QuantLib?", (
        r"^(?P<verdict>[^.]+)\.",
        r"largest price gap is (?P<bsm>\S+) over (?P<cases>\d+) grid cases",
        r"CRR engine: the largest gap is (?P<crr>\S+) x S",
        r"Delta, gamma, vega, theta and rho match QuantLib: the largest gap is (?P<greeks>\S+) over"),
        "{verdict}: over {cases} grid cases each, the largest gap is {bsm} for BSM prices, {greeks} for the Greeks "
        "and {crr} x S for the American CRR tree."),
    Finding("2", "Question 2: how did the S&P 500 surface move, and is it free of arbitrage?", (
        r"ATM vol was (?P<atm0>[\d.]+)% on \S+ \(N = (?P<days>\d+) capture days\)\. It was (?P<atm1>[\d.]+)%",
        r"risk reversal went from (?P<rr0>\S+) to (?P<rr1>\S+) vol points, (?P<skew>so skew \w+)",
        r"Butterfly: (?P<acc>\d+) of"),
        "Over {days} capture days, ^SPX 30-day ATM vol went from {atm0}% to {atm1}% and the 25-delta risk reversal "
        "from {rr0} to {rr1} vol points, {skew}. All {acc} accepted SVI slices pass the butterfly arbitrage check."),
    Finding("3", "Question 3: do event moves differ from what the options priced?", (
        r"With N = (?P<n>\d+) completed events, fewer than the (?P<min_n>\d+) the summary needs",),
        "With N = {n} completed events, fewer than the {min_n} the summary needs, the gap cannot be told apart from 0. "
        "{below} of the {n} moved less than the options priced."),
    Finding("4", "Question 4: does selling S&P 500 volatility pay, and does timing it help?", (
        r"Cboe PUT has a Sharpe of (?P<put>[\d.]+) over (?P<months>\d+) months from (?P<start>\d{4})",
        r"gives a raw Sharpe of (?P<timed>[\d.]+)",
        r"After counting the (?P<k>\d+) rules tried, its deflated Sharpe is (?P<dsr>[\d.]+)"),
        "Selling puts paid: Cboe PUT has a Sharpe of {put} over {months} months from {start}. Timing it on implied "
        "minus GARCH variance gives {timed}, but after the {k} rules tried its gain over PUT has a deflated Sharpe of "
        "{dsr}, so it cannot be told apart from luck."),
    Finding("5", "Question 5: does implied correlation predict realised correlation?", (
        r"^(?P<verdict>[^.]+)\.",
        r"COR3M gives a slope of (?P<slope>[\d.]+) \(Newey-West se [\d.]+\), N = (?P<n>\d+) days",
        r"R² is (?P<r2>[\d.]+)"),
        "{verdict}. Regressing next quarter's realised sector correlation on COR3M gives a slope of {slope} and an "
        "R² of {r2} (N = {n} days)."),
    Finding("6", "Question 6: how does hedged P&L split, and what does hedging frequency change?", (
        r"median explained share is (?P<live>[\d.]+) \(N = (?P<n>\d+) position moves",
        r"\(k = 1\) leaves an error sd of (?P<gbm>[\d.]+) under GBM",
        r"The same hedge leaves (?P<heston>[\d.]+) under Heston"),
        "The Greeks explain a median {live} of each live ^SPX straddle move (N = {n} moves). Hedging every step "
        "leaves an error sd of {gbm} under GBM but {heston} under Heston, because the delta hedge is blind to vol "
        "moves."),
)


def _per_event(answers: pd.DataFrame) -> pd.Series:
    """The answer rows that give 1 event each, with its ratio."""
    return (answers["source_table"] == "events.csv") & (answers["source_column"] == "ratio")


def answer_text(answers: pd.DataFrame, question: str, summary: bool = False) -> str:
    """The answer rows of `question` as 1 paragraph; with `summary`, without the per-event rows (instruction 13)."""
    keep = answers["question"] == question
    if summary:
        keep &= ~_per_event(answers)
    return " ".join(answers.loc[keep, "answer"]).replace(" -", f" {MINUS}")


def findings(answers: pd.DataFrame) -> list[tuple[str, str]]:
    """The (question, paragraph) pairs of "What it found", 1 per research question."""
    events = {"below": str(int((pd.to_numeric(answers.loc[_per_event(answers), "value"]) < 1).sum()))}
    out = []
    for finding in FINDINGS:
        text = answer_text(answers, finding.question)
        values = dict(events)
        for pattern in finding.patterns:
            match = re.search(pattern, text)
            if match is None:
                raise ValueError(f"question {finding.question}: {pattern!r} is not in answers.csv")
            values.update(match.groupdict())
        out.append((finding.heading, finding.text.format(**values)))
    return out


def findings_markdown(answers: pd.DataFrame) -> str:
    return "\n\n".join(f"**{heading}** {text}" for heading, text in findings(answers))


def _cell(text: str, column: Column) -> str:
    if column.places is None or text == "":
        return text
    if column.exp:
        return f"{float(text) * column.scale:.{column.places}e}".replace("-", MINUS)
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
            question, _, part = key.removeprefix("answers:").partition(":")
            return answer_text(answers, question, summary=part == "summary")
        if key == "findings":
            return findings_markdown(answers)
        return values[key]

    return re.sub(r"\{\{([\w:]+)\}\}", fill, template)
