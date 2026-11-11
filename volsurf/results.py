"""outputs/results.html (instruction 13 step 13.1): every chart and headline table on 1 self-contained page.

The sections follow the README's 6 questions and its risk report section. Each holds the question's "What it found"
paragraph, its headline tables rendered from the CSVs with the README's column specs, and its charts as base64 PNG.
CSS is inline and the only URL is the footer's link to the repo, so the page makes no request. Nothing on it depends on
the time it is built, so 2 builds give the same bytes.
"""

from __future__ import annotations

import base64
import html
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from volsurf.answers import read_table, select_rows
from volsurf.readme import TABLES, Column, Spec, _cell, capture_window, findings
from volsurf.report import INK, MUTED, RULE, THOUSAND, _shock, heat_colour
from volsurf.risk import BOOK_LABEL

REPO = "https://github.com/uty101/Volatility-Surface-and-Event-Pricing"
TITLE = "Volatility Surface and Event Pricing: results"
DAY = re.compile(r"\d{4}-\d{2}-\d{2}")

PRICER = Spec("pricer_check.csv", "all", (
    Column("check", "check"), Column("n_cases", "cases", 0), Column("largest_gap", "largest gap", 1, exp=True),
    Column("bound", "bound", 0, exp=True), Column("passed", "passed")))
BREACHES = Spec("limit_breaches.csv", "breach=True", (
    Column("underlying", "underlying"), Column("measure", "measure"), Column("value", "value", 0),
    Column("limit", "limit", 0)))


@dataclass(frozen=True)
class Section:
    """A README section: its heading, the research question whose finding opens it, its tables and its charts. Each
    chart is a glob under outputs/figures/ with a caption, `{day}` standing for the date in the file name; a file
    an earlier glob already placed is not repeated."""

    heading: str
    question: str
    tables: tuple[Spec, ...]
    figures: tuple[tuple[str, str], ...]


SECTIONS = (
    Section("1. Does the pricer match QuantLib?", "1", (PRICER,), ()),
    Section("2. The S&P 500 surface", "2", (TABLES["surface"],), (
        ("spx_smiles_{last_day}.png", "^SPX smiles on {day}, 1 line per accepted expiry"),
        ("spx_metrics.png", "^SPX ATM vol, risk reversal, butterfly and term slope on each capture day"),
        ("spx_density_last.png", "^SPX density on the last day, the quoted strike range shaded"),
        ("spx_surface_last.png", "^SPX SSVI implied vol surface on the last day"),
        ("spx_smile_fits_*.png", "^SPX SVI fits against market implied vols on {day}"),
        ("spx_smiles_*.png", "^SPX smiles on {day}"))),
    Section("3. Earnings events", "3", (TABLES["events"],), (
        ("event_scatter.png", "Realised against implied move, 1 point per completed event"),
        ("event_term_structures.png", "ATM total variance against T before the 4 largest priced moves"))),
    Section("4. The volatility risk premium", "4", (TABLES["strategies"],), (
        ("vrp_vix2_vs_rv.png", "VIX squared against the variance that followed"),
        ("vrp_cumulative.png", "Cumulative excess return"),
        ("vrp_drawdowns.png", "Drawdowns"))),
    Section("5. Correlation", "5", (TABLES["cor3m"], TABLES["implied_corr"]), (
        ("cor3m_vs_realised.png", "COR3M against the realised sector correlation that followed"),)),
    Section("6. P&L attribution and hedging", "6", (TABLES["hedging"],), ()),
)

def _hex(colour) -> str:
    return colour.hexval().replace("0x", "#")


CSS = f"""
body {{ font-family: Helvetica, Arial, sans-serif; color: {_hex(INK)}; background: #ffffff;
  max-width: 1000px; margin: 2em auto; padding: 0 16px; font-size: 15px; line-height: 1.45; }}
h1 {{ font-size: 1.6em; margin-bottom: 0.3em; }}
h2 {{ font-size: 1.2em; margin-top: 2.2em; padding-bottom: 4px; border-bottom: 1px solid {_hex(RULE)}; }}
h3 {{ font-size: 1em; margin-top: 1.6em; }}
.note, figcaption {{ color: {_hex(MUTED)}; font-size: 0.9em; }}
.scroll {{ overflow-x: auto; }}
table {{ border-collapse: collapse; font-size: 12px; margin: 1em 0; font-variant-numeric: tabular-nums; }}
th {{ text-align: right; padding: 4px 8px; border-bottom: 1.2px solid {_hex(INK)}; white-space: nowrap; }}
td {{ text-align: right; padding: 4px 8px; border-bottom: 0.5px solid {_hex(RULE)}; white-space: nowrap; }}
th.t, td.t {{ text-align: left; }}
table.grid th, table.grid td {{ text-align: center; border: 2px solid #ffffff; padding: 6px 12px; }}
table.grid th:first-child, table.grid td:first-child {{ font-weight: bold; }}
figure {{ margin: 1.4em 0; }}
img {{ max-width: 100%; height: auto; display: block; }}
footer {{ margin-top: 3em; padding-top: 1em; border-top: 1px solid {_hex(RULE)}; }}
"""


def html_table(spec: Spec, tables: Path) -> str:
    """The rows `spec` selects, formatted as in the README, with text columns left-aligned."""
    rows = select_rows(read_table(tables / spec.file), spec.row)

    def cls(c: Column) -> str:
        return ' class="t"' if c.places is None else ""

    head = "".join(f"<th{cls(c)}>{html.escape(c.header)}</th>" for c in spec.columns)
    body = "".join("<tr>" + "".join(f"<td{cls(c)}>{html.escape(_cell(r[c.name], c))}</td>" for c in spec.columns)
                   + "</tr>\n" for _, r in rows.iterrows())
    return f'<div class="scroll"><table>\n<thead><tr>{head}</tr></thead>\n<tbody>\n{body}</tbody></table></div>'


def grid_table(tables: Path) -> str:
    """The book's shock grid in thousands of dollars, coloured as in the risk report."""
    grid = pd.read_csv(tables / "risk_grid.csv")
    cells = grid[grid["contract"] == BOOK_LABEL].pivot(index="spot_shock", columns="vol_shock_pts", values="pnl")
    cells = cells.sort_index().sort_index(axis=1)
    largest = float(cells.abs().max().max())
    head = "".join(f"<th>{html.escape(_shock(v, '{:+.1f} pts'))}</th>" for v in cells.columns)
    rows = []
    for spot, line in cells.iterrows():
        tds = "".join(f'<td style="background: {_hex(heat_colour(v, largest))}">'
                      f'{"" if pd.isna(v) else f"{v / THOUSAND:,.1f}".replace("-", chr(0x2212))}</td>' for v in line)
        rows.append(f"<tr><td>{html.escape(_shock(spot * 100, '{:+.1f}%'))}</td>{tds}</tr>\n")
    return (f'<div class="scroll"><table class="grid">\n<thead><tr><th>Spot / Vol</th>{head}</tr></thead>\n<tbody>\n'
            f'{"".join(rows)}</tbody></table></div>')


def section_figures(section: Section, figures: Path, last_day: str) -> list[tuple[Path, str]]:
    """The section's charts in order, each with its caption."""
    placed: list[tuple[Path, str]] = []
    for pattern, caption in section.figures:
        for path in sorted(figures.glob(pattern.format(last_day=last_day))):
            if path not in [p for p, _ in placed]:
                day = DAY.search(path.name)
                placed.append((path, caption.format(day=day.group(0) if day else last_day)))
    return placed


def figure(path: Path, caption: str) -> str:
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return (f'<figure><img src="data:image/png;base64,{data}" alt="{html.escape(caption)}">'
            f"<figcaption>{html.escape(caption)}</figcaption></figure>")


def build_results(tables: Path, figures: Path, n_tests: int) -> str:
    """The page, from the committed tables and figures; `n_tests` is the README's test count."""
    window = capture_window(tables)
    found = dict(zip([s.question for s in SECTIONS], findings(read_table(tables / "answers.csv")), strict=True))
    parts = [f"<h1>{html.escape(TITLE)}</h1>",
             (f"<p><strong>Capture window:</strong> {window['first_day']} to {window['last_day']}, {window['n_days']} "
             f"days, {window['missed']} missed. {n_tests:,} tests.</p>"),
             ('<p class="note">Built by <code>scripts/run_all.py --stage results</code> from the committed tables and '
             "charts in <code>outputs/</code>. Every live result is a method demonstration with its N stated.</p>")]
    for section in SECTIONS:
        heading, text = found[section.question]
        parts.append(f"<h2>{html.escape(section.heading)}</h2>")
        parts.append(f"<p><strong>{html.escape(heading)}</strong> {html.escape(text)}</p>")
        parts += [html_table(spec, tables) for spec in section.tables]
        parts += [figure(p, c) for p, c in section_figures(section, figures, window["last_day"])]
    report = f"reports/risk_{window['last_day']}.pdf"
    parts += ["<h2>Risk report</h2>",
              (f'<p>The 1-page report for {window["last_day"]} is <a href="{report}">{report}</a> '
              f"(N = {window['n_days']} capture days). Each vol is the contract's own SVI slice at its strike.</p>"),
              "<h3>Book</h3>", html_table(TABLES["risk_book"], tables),
              "<h3>Book P&amp;L under shocks, thousands of dollars</h3>",
              '<p class="note">Full revaluation, sticky strike. Blue is a gain, red a loss.</p>', grid_table(tables),
              "<h3>Limit breaches</h3>", html_table(BREACHES, tables),
              f'<footer><a href="{REPO}">The repository on GitHub</a></footer>']
    body = "\n".join(parts)
    return (f'<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>{html.escape(TITLE)}</title>\n'
            f"<style>{CSS}</style></head>\n<body>\n{body}\n</body></html>\n")
