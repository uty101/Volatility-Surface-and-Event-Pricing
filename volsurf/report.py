"""1-page PDF risk report (PLAN 10.2, kickoff 5.11, instruction 10 step 10.2): reportlab, A4, Helvetica, invariant."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from volsurf.risk import BOOK_LABEL

SOURCE = "Yahoo option chains, FRED Treasury yields"
MEASURE_LABELS = {"dollar_delta": "Dollar delta", "dollar_gamma": "Dollar gamma per 1%",
                  "vega_pt": "Vega per vol point"}
INK, MUTED, RULE = colors.HexColor("#1a1a19"), colors.HexColor("#5f5e5a"), colors.HexColor("#d3d1c7")
NEUTRAL, GAIN, LOSS = colors.HexColor("#f0efec"), colors.HexColor("#8ab4e8"), colors.HexColor("#ee9a94")
THOUSAND = 1000  # the grid is shown in thousands of dollars, instruction 10 step 10.2

TITLE = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=INK)
HEAD = ParagraphStyle("head", fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=INK, spaceBefore=11,
                      spaceAfter=4)
BODY = ParagraphStyle("body", fontName="Helvetica", fontSize=8.5, leading=11, textColor=MUTED)
BASE = [("FONTNAME", (0, 0), (-1, -1), "Helvetica"), ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
RULES = [("LINEBELOW", (0, 0), (-1, 0), 0.6, INK), ("LINEBELOW", (0, 1), (-1, -1), 0.25, RULE)]


def _money(x: float) -> str:
    return "" if pd.isna(x) else f"{x:,.0f}"


def book_table(greeks: pd.DataFrame) -> Table:
    """Contract, side, contracts, price, vol, dollar delta, dollar gamma and vega; a `no_surface` row stays blank."""
    rows = [["Contract", "Side", "Contracts", "Price", "Vol %", "Dollar delta", "Dollar gamma 1%", "Vega per pt"]]
    for _, p in greeks.iterrows():
        blank = pd.isna(p["price"])
        rows.append([p["contract"], "short" if p["side"] < 0 else "long", f"{p['contracts']:.0f}",
                     p["status"] if blank else f"{p['price']:.2f}", "" if blank else f"{p['vol'] * 100:.1f}",
                     _money(p["dollar_delta"]), _money(p["dollar_gamma"]), _money(p["vega_pt"])])
    table = Table(rows, colWidths=[52 * mm, 13 * mm, 16 * mm, 16 * mm, 12 * mm, 22 * mm, 25 * mm, 19 * mm])
    table.setStyle(TableStyle([*BASE, *RULES]))
    return table


def heat_colour(value: float, largest: float):
    """Diverging: the neutral at 0, blue for a gain and red for a loss. Strength is the square root of the share of the
    largest size on the grid, so a gain stays visible beside a far larger loss. The number in the cell carries the size."""
    if pd.isna(value) or largest == 0:
        return NEUTRAL
    return colors.linearlyInterpolatedColor(NEUTRAL, GAIN if value > 0 else LOSS, 0, 1, np.sqrt(abs(value) / largest))


def _shock(value: float, text: str) -> str:
    return text.format(0.0).replace("+", "") if value == 0 else text.format(value)


def heat_table(grid: pd.DataFrame) -> Table:
    """The book's 9 x 5 grid in thousands of dollars: spot shocks down, vol shocks across, every cell labelled."""
    cells = grid[grid["contract"] == BOOK_LABEL].pivot(index="spot_shock", columns="vol_shock_pts", values="pnl")
    cells = cells.sort_index().sort_index(axis=1)
    values = cells.to_numpy(dtype=float)
    largest = float(np.nanmax(np.abs(values))) if np.isfinite(values).any() else 0.0
    rows = [["Spot / Vol", *[_shock(v, "{:+.1f} pts") for v in cells.columns]]]
    style = [*BASE, ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
             ("GRID", (1, 1), (-1, -1), 1.5, colors.white)]
    for i, (spot, line) in enumerate(cells.iterrows(), start=1):
        rows.append([_shock(spot * 100, "{:+.1f}%"), *["" if pd.isna(v) else f"{v / THOUSAND:,.1f}" for v in line]])
        style += [("BACKGROUND", (j, i), (j, i), heat_colour(v, largest)) for j, v in enumerate(line, start=1)]
    table = Table(rows, colWidths=[24 * mm] + [26 * mm] * cells.shape[1], rowHeights=[6.5 * mm] * len(rows))
    table.setStyle(TableStyle(style))
    return table


def breach_block(breaches: pd.DataFrame) -> list:
    """The breached limits, with a count that is 0 when there are none, then any underlying that could not be checked."""
    hit = breaches[breaches["breach"].astype("boolean").fillna(False)]
    missing = breaches[breaches["status"] != "ok"]["underlying"].unique()
    block = [Paragraph(f"{len(hit)} of {len(breaches)} limits breached.", BODY), Spacer(1, 2 * mm)]
    if len(hit):
        rows = [["Underlying", "Measure", "Value", "Limit"]]
        rows += [[b["underlying"], MEASURE_LABELS[b["measure"]], _money(b["value"]), _money(b["limit"])]
                 for _, b in hit.iterrows()]
        table = Table(rows, colWidths=[30 * mm, 50 * mm, 30 * mm, 30 * mm], hAlign="LEFT")
        table.setStyle(TableStyle([*BASE, ("ALIGN", (1, 0), (1, -1), "LEFT"), *RULES]))
        block.append(table)
    if len(missing):
        block.append(Paragraph(f"Not checked, no surface: {', '.join(missing)}.", BODY))
    return block


def build_risk_report(day: date, grid: pd.DataFrame, greeks: pd.DataFrame, breaches: pd.DataFrame, out_path: Path,
                      n_days: int) -> Path:
    """The page of instruction 10 step 10.2. `n_days`, the N of capture days, is an argument the kickoff signature
    does not have (O-49): the page has to state it and nothing else passed in holds it."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    left_out = int(grid.loc[grid["contract"] == BOOK_LABEL, "left_out"].iloc[0])
    doc = SimpleDocTemplate(str(out_path), pagesize=A4, invariant=1, title=f"Risk report {day}", author="volsurf",
                            leftMargin=15 * mm, rightMargin=15 * mm, topMargin=15 * mm, bottomMargin=13 * mm)
    doc.build([Paragraph(f"Risk report, {day}", TITLE),
               Paragraph(f"Day {day}. Source: {SOURCE}. N = {n_days} capture days, a method demonstration.", BODY),
               Paragraph("Book", HEAD), book_table(greeks),
               Paragraph("Book P&amp;L under shocks, thousands of dollars", HEAD),
               Paragraph("Full revaluation, sticky strike. Blue is a gain, red a loss. "
                         f"Positions left out of the total: {left_out}.", BODY),
               Spacer(1, 2 * mm), heat_table(grid),
               Paragraph("Limit breaches", HEAD), *breach_block(breaches)])
    return out_path
