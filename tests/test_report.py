from datetime import date
from pathlib import Path

import pandas as pd
import pytest
from pypdf import PdfReader

from volsurf.config import load_config
from volsurf.report import GAIN, LOSS, NEUTRAL, build_risk_report, heat_colour
from volsurf.risk import BOOK_LABEL, GRID_COLUMNS, RISK_COLUMNS

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "config.toml")
DAY = date(2026, 11, 3)
NUMERIC = ["price", "vol", "dollar_delta", "dollar_gamma", "vega_pt"]


def _greeks(status="ok"):
    row = dict.fromkeys(RISK_COLUMNS)
    row.update(day=str(DAY), position=1, contract="^SPX 2026-12-03 P 7275", underlying="^SPX", side=-1, kind="P",
               contracts=10, status=status)
    if status == "ok":
        row.update(price=70.05, vol=0.2165, dollar_delta=1845800.0, dollar_gamma=-381876.0, vega_pt=-6801.0)
    return pd.DataFrame([row] * 4).astype(dict.fromkeys(NUMERIC, float))


def _grid(left_out=0):
    rows = [{"day": str(DAY), "position": 0, "contract": BOOK_LABEL, "spot_shock": s, "vol_shock_pts": v,
             "pnl": 1000.0 * (s * 100 + v), "status": "ok", "left_out": left_out}
            for s in CFG.risk.spot_shocks for v in CFG.risk.vol_shocks_pts]
    return pd.DataFrame(rows, columns=GRID_COLUMNS)


def _breaches(breach=True):
    return pd.DataFrame([{"day": str(DAY), "underlying": "^SPX", "measure": "dollar_gamma", "value": -1008798.0,
                          "limit": 250000, "breach": breach, "status": "ok", "left_out": 0}])


def _build(path, grid=None, greeks=None, breaches=None):
    return build_risk_report(DAY, _grid() if grid is None else grid, _greeks() if greeks is None else greeks,
                             _breaches() if breaches is None else breaches, path, 4)


def _text(path):
    return " ".join(page.extract_text() for page in PdfReader(path).pages)


def test_two_builds_byte_identical(tmp_path):
    assert _build(tmp_path / "a.pdf").read_bytes() == _build(tmp_path / "b.pdf").read_bytes()


def test_one_page(tmp_path):
    assert len(PdfReader(_build(tmp_path / "a.pdf")).pages) == 1


def test_a4_helvetica(tmp_path):
    page = PdfReader(_build(tmp_path / "a.pdf")).pages[0]
    assert [round(float(x)) for x in page.mediabox[2:]] == [595, 842]
    fonts = {f.get_object()["/BaseFont"].lstrip("/") for f in page["/Resources"]["/Font"].values()}
    assert fonts <= {"Helvetica", "Helvetica-Bold"}


def test_page_holds_what_the_instruction_lists(tmp_path):
    text = _text(_build(tmp_path / "a.pdf"))
    for want in ("2026-11-03", "Yahoo", "N = 4 capture days", "^SPX 2026-12-03 P 7275", "short", "70.05", "21.6",
                 "1,845,800", "-381,876", "-6,801", "1 of 1 limits breached", "-1,008,798", "250,000",
                 "Positions left out of the total: 0"):
        assert want in text
    assert "-15.0" in text  # the -10%, -5 pts corner is -15,000 dollars, shown in thousands


def test_no_breach_says_so(tmp_path):
    text = _text(_build(tmp_path / "a.pdf", breaches=_breaches(False)))
    assert "0 of 1 limits breached" in text
    assert "Measure" not in text


def test_missing_position_is_shown(tmp_path):
    text = _text(_build(tmp_path / "a.pdf", grid=_grid(left_out=1), greeks=_greeks("no_surface"),
                        breaches=_breaches().assign(breach=pd.NA, status="no_surface", value=float("nan"))))
    assert "no_surface" in text
    assert "Positions left out of the total: 1" in text
    assert "Not checked, no surface: ^SPX" in text


@pytest.mark.parametrize("value,want", [(0.0, NEUTRAL), (10.0, GAIN), (-10.0, LOSS)])
def test_heat_colour_runs_from_the_neutral_to_each_pole(value, want):
    assert heat_colour(value, 10.0).rgb() == pytest.approx(want.rgb())
