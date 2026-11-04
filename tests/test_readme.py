import re
from pathlib import Path

import pytest
from pypdf import PdfReader

from tests.test_report import _build
from volsurf.answers import read_table, select_rows
from volsurf.readme import MINUS, TABLES, capture_window, render_table

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "tables"
# PLAN 11.3 names test_readme_tables_match_csvs on the committed outputs, and PLAN beats rule 7 (rule 13)
README = (ROOT / "README.md").read_text(encoding="utf-8")
METHODS = (ROOT / "docs" / "METHODS.md").read_text(encoding="utf-8")
BANNED = ["robust", "resilient", "rigorous", "leveraging", "grounded"]
DASHES = ["\N{EM DASH}", "\N{EN DASH}"]


def _report_text(tmp_path):
    built = " ".join(p.extract_text() for p in PdfReader(_build(tmp_path / "r.pdf")).pages)
    committed = [" ".join(p.extract_text() for p in PdfReader(f).pages) for f in (ROOT / "outputs" / "reports").glob("*.pdf")]
    return " ".join([built, *committed])


def _markdown_rows(spec):
    """The README rows of the table with `spec`'s header, each as a list of cells."""
    header = "| " + " | ".join(c.header for c in spec.columns) + " |"
    lines = README.split("\n")
    start = lines.index(header) + 2
    rows = []
    for line in lines[start:]:
        if not line.startswith("|"):
            break
        rows.append([c.strip() for c in line.strip("|").split("|")])
    return rows


@pytest.mark.parametrize("name", TABLES)
def test_readme_tables_match_csvs(name):
    spec = TABLES[name]
    wanted = select_rows(read_table(OUT / spec.file), spec.row)
    shown = _markdown_rows(spec)
    assert len(shown) == len(wanted)
    for cells, (_, row) in zip(shown, wanted.iterrows(), strict=True):
        for cell, column in zip(cells, spec.columns, strict=True):
            if column.places is None:
                assert cell == row[column.name]
            elif row[column.name] == "":
                assert cell == ""
            else:
                got = float(cell.replace(MINUS, "-"))
                assert got == pytest.approx(float(row[column.name]) * column.scale, abs=0.51 * 10**-column.places)


@pytest.mark.parametrize("name", TABLES)
def test_readme_holds_the_generated_table(name):
    assert render_table(TABLES[name], OUT) in README


@pytest.mark.parametrize("word", BANNED)
def test_no_banned_words(word, tmp_path):
    for text in (README, METHODS, _report_text(tmp_path)):
        assert not re.search(rf"\b{word}\b", text, re.IGNORECASE)


def test_no_dashes_and_no_hyphen_joining_sentences(tmp_path):
    for text in (README, METHODS, _report_text(tmp_path)):
        for dash in DASHES:
            assert dash not in text
    for text in (README, METHODS):
        prose = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        assert not re.search(r"\w - \w", prose)


def test_readme_under_15_kb():
    assert (ROOT / "README.md").stat().st_size < 15 * 1024


def test_status_line_under_the_intro():
    line = next(x for x in README.split("\n") if x.startswith("Results are in"))
    assert "(outputs/)" in line
    assert "actions/workflows/ci.yml/badge.svg" in line
    assert re.search(r"[\d,]+ tests\.", line)
    assert README.index(line) < README.index("## Run it")


def test_capture_window_from_the_data():
    w = capture_window(OUT)
    assert f"{w['first_day']} to {w['last_day']}, {w['n_days']} days, {w['missed']} missed" in README
    assert w["missed"] == "2026-11-02"


def test_limits_section():
    section = README[README.index("## What this does not do"):]
    for text in ("live window is a few weeks", "Yahoo's delayed quotes at 15:30 New York", "sector proxy",
                 "1 specification of a family", "risk book is a sample"):
        assert text in section


def test_every_figure_exists_with_a_callout_before_it():
    lines = README.split("\n")
    figures = [i for i, line in enumerate(lines) if line.startswith("![")]
    assert len(figures) >= 7
    for i in figures:
        path = re.search(r"\((outputs/figures/[^)]+)\)", lines[i]).group(1)
        assert (ROOT / path).exists()
        assert lines[i - 1] == "" and lines[i - 2] and not lines[i - 2].startswith(("!", "|", "#"))


def test_nothing_left_to_fill():
    assert "{{" not in README
