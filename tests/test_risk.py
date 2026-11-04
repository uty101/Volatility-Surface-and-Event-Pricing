import dataclasses
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from volsurf.config import load_config
from volsurf.greeks import greeks
from volsurf.pricing import bsm, crr
from volsurf.risk import (
    BOOK_COLUMNS,
    BOOK_LABEL,
    BREACH_COLUMNS,
    GRID_COLUMNS,
    NO_SURFACE,
    OK,
    RISK_COLUMNS,
    SSVI,
    SVI,
    black76_greeks,
    book_risk,
    contract_vol,
    crr_greeks,
    day_surface,
    limit_breaches,
    position_value,
    select_book,
    shock_grid,
    vol_source,
)
from volsurf.ssvi import ssvi_w
from volsurf.svi import svi_w

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "config.toml")
DAY = date(2026, 11, 3)
SPX_INPUTS = {"S": 7700.0, "r": 0.037, "q": 0.012}
AAPL_INPUTS = {"S": 270.0, "r": 0.037, "q": 0.004}
THETAS = pd.DataFrame({"T": [0.01, 0.5], "theta_used": [0.0004, 0.02]})
SLICE = (0.002, 0.05, -0.6, 0.01, 0.08)  # a, b, rho, m, s


def _surface(*tickers, slices=None):
    row = pd.Series({"ssvi_rho": -0.5, "ssvi_eta": 1.0, "ssvi_gamma": 0.45})
    return {t: day_surface(row, THETAS, slices) for t in tickers}


def _iv(ticker, inputs, expiries, kind, strikes):
    rows = []
    for expiry in expiries:
        T = (date.fromisoformat(expiry) - DAY).days / 365
        F = inputs["S"] * np.exp((inputs["r"] - inputs["q"]) * T)
        rows += [{"ticker": ticker, "expiry": expiry, "kind": kind, "strike": K, "T": T, "F": F, "iv": 0.2, **inputs}
                 for K in strikes]
    return pd.DataFrame(rows)


def _position(underlying="^SPX", side=-1, kind="P", target_delta=-0.25, target_days=30, contracts=10):
    return SimpleNamespace(underlying=underlying, side=side, kind=kind, target_delta=target_delta,
                           target_days=target_days, contracts=contracts)


SPX_CHAIN = _iv("^SPX", SPX_INPUTS, ["2026-12-03"], "P", np.arange(6800.0, 7700.0, 25.0))
AAPL_CHAIN = _iv("AAPL", AAPL_INPUTS, ["2026-12-18", "2027-01-15"], "C", np.arange(250.0, 330.0, 5.0))
SPX_BOOK = select_book(DAY, [_position()], SPX_CHAIN, _surface("^SPX"))
AAPL_POSITION = _position("AAPL", 1, "C", 0.5, 60, 20)
AAPL_BOOK = select_book(DAY, [AAPL_POSITION], AAPL_CHAIN, _surface("AAPL"))
BOOKS = {"^SPX": SPX_BOOK, "AAPL": AAPL_BOOK}


def _shocks(spot, vol=(0.0,)):
    return dataclasses.replace(CFG, risk=dataclasses.replace(CFG.risk, spot_shocks=spot, vol_shocks_pts=vol))


def test_select_nearest_days_then_nearest_delta():
    book = AAPL_BOOK.iloc[0]
    assert list(AAPL_BOOK.columns) == BOOK_COLUMNS
    assert book["expiry"] == "2027-01-15"  # 73 days is 13 from 60, 45 days is 15
    assert book["days"] == 73
    strikes = np.sort(AAPL_CHAIN["strike"].unique())
    s = _surface("AAPL")["AAPL"]
    vols = np.array([contract_vol(K, book["F"], book["T"], s) for K in strikes])
    deltas = greeks(book["S"], strikes, book["T"], book["r"], book["q"], vols, "C")["delta"]
    assert book["strike"] == strikes[np.argmin(np.abs(deltas - 0.5))]
    assert book["select_delta"] == pytest.approx(deltas[strikes == book["strike"]][0])


def test_select_expiry_tie_goes_to_the_shorter():
    chain = _iv("AAPL", AAPL_INPUTS, ["2026-12-18", "2027-01-15"], "C", [280.0, 285.0])
    book = select_book(DAY, [_position("AAPL", 1, "C", 0.5, 59, 20)], chain, _surface("AAPL"))
    assert book["expiry"].iloc[0] == "2026-12-18"  # 45 and 73 days are both 14 from 59


def test_select_strike_tie_goes_to_the_lower(monkeypatch):
    chain = _iv("AAPL", AAPL_INPUTS, ["2026-12-18"], "C", [280.0, 285.0])
    monkeypatch.setattr("volsurf.risk.greeks", lambda *a: {"delta": np.array([0.45, 0.55])})
    book = select_book(DAY, [_position("AAPL", 1, "C", 0.5, 45, 20)], chain, _surface("AAPL"))
    assert book["strike"].iloc[0] == 280.0


def test_vol_is_the_ssvi_vol_at_the_strike():
    pos = SPX_BOOK.iloc[0]
    theta = float(np.interp(pos["T"], THETAS["T"], THETAS["theta_used"]))
    w = ssvi_w(np.log(pos["strike"] / pos["F"]), theta, -0.5, 1.0, 0.45)
    assert contract_vol(pos["strike"], pos["F"], pos["T"], _surface("^SPX")["^SPX"]) == pytest.approx(
        float(np.sqrt(w / pos["T"])), rel=1e-14)


def test_vol_is_the_expiry_svi_slice_at_the_strike():
    pos = SPX_BOOK.iloc[0]
    s = _surface("^SPX", slices={"2026-12-03": SLICE})["^SPX"]
    want = np.sqrt(svi_w(np.log(pos["strike"] / pos["F"]), *SLICE) / pos["T"])
    assert contract_vol(pos["strike"], pos["F"], pos["T"], s, "2026-12-03") == pytest.approx(float(want), rel=1e-14)
    assert vol_source(s, "2026-12-03") == SVI


def test_ssvi_is_the_fallback_when_the_expiry_has_no_slice():
    pos = SPX_BOOK.iloc[0]
    s = _surface("^SPX", slices={"2026-12-18": SLICE})["^SPX"]  # another expiry's slice is not used
    want = contract_vol(pos["strike"], pos["F"], pos["T"], _surface("^SPX")["^SPX"])
    assert contract_vol(pos["strike"], pos["F"], pos["T"], s, "2026-12-03") == want
    assert vol_source(s, "2026-12-03") == SSVI


def test_vol_source_column():
    surface = _surface("^SPX", slices={"2026-12-03": SLICE})
    assert book_risk(select_book(DAY, [_position()], SPX_CHAIN, surface), surface, CFG)["vol_source"].iloc[0] == SVI
    assert book_risk(SPX_BOOK, _surface("^SPX"), CFG)["vol_source"].iloc[0] == SSVI


def test_selection_and_shocks_run_on_the_slice_vol():
    surface = _surface("^SPX", slices={"2026-12-03": SLICE})
    book = select_book(DAY, [_position()], SPX_CHAIN, surface)
    pos = book.iloc[0]
    s = surface["^SPX"]
    strikes = np.sort(SPX_CHAIN["strike"].unique())
    vols = np.array([contract_vol(K, pos["F"], pos["T"], s, "2026-12-03") for K in strikes])
    deltas = greeks(pos["S"], strikes, pos["T"], pos["r"], pos["q"], vols, "P")["delta"]
    assert pos["strike"] == strikes[np.argmin(np.abs(deltas + 0.25))]
    vol = contract_vol(pos["strike"], pos["F"], pos["T"], s, "2026-12-03")
    grid = shock_grid(book, surface, _shocks((-0.05,), (2.5,)))
    want = (position_value(pos, -0.05, vol + 0.025, CFG) - position_value(pos, 0.0, vol, CFG)) * 100 * 10 * -1
    assert grid["pnl"].iloc[0] == pytest.approx(want, rel=1e-12)


@pytest.mark.parametrize("name", ["^SPX", "AAPL"])
def test_zero_shock_zero_pnl(name):
    grid = shock_grid(BOOKS[name], _surface(name), CFG)
    assert list(grid.columns) == GRID_COLUMNS
    zero = grid[(grid["spot_shock"] == 0) & (grid["vol_shock_pts"] == 0)]
    assert len(zero) == 2  # the position and the book
    assert (zero["pnl"] == 0).all()


def test_grid_has_every_cell_and_the_book_is_the_sum():
    book = pd.concat([SPX_BOOK, AAPL_BOOK.assign(position=2)], ignore_index=True)
    grid = shock_grid(book, _surface("^SPX", "AAPL"), CFG)
    cells = len(CFG.risk.spot_shocks) * len(CFG.risk.vol_shocks_pts)
    assert cells == 45
    assert len(grid) == 3 * cells
    total = grid[grid["contract"] == BOOK_LABEL].set_index(["spot_shock", "vol_shock_pts"])["pnl"]
    parts = grid[grid["position"] > 0].groupby(["spot_shock", "vol_shock_pts"])["pnl"].sum()
    assert total.sort_index().to_numpy() == pytest.approx(parts.sort_index().to_numpy(), rel=1e-12)


def test_spx_cell_is_black76_on_the_shocked_forward():
    pos = SPX_BOOK.iloc[0]
    vol = contract_vol(pos["strike"], pos["F"], pos["T"], _surface("^SPX")["^SPX"])
    grid = shock_grid(SPX_BOOK, _surface("^SPX"), _shocks((-0.05,), (2.5,)))
    # S e^(-qT) = D F makes BSM on the shocked spot the same as Black-76 on the shocked forward
    want = bsm(pos["S"] * 0.95, pos["strike"], pos["T"], pos["r"], pos["q"], vol + 0.025, "P") - bsm(
        pos["S"], pos["strike"], pos["T"], pos["r"], pos["q"], vol, "P")
    assert grid["pnl"].iloc[0] == pytest.approx(float(want) * 100 * 10 * -1, rel=1e-9)


def test_aapl_cell_is_the_american_tree():
    pos = AAPL_BOOK.iloc[0]
    vol = contract_vol(pos["strike"], pos["F"], pos["T"], _surface("AAPL")["AAPL"])
    n = CFG.pricing.n_prod
    grid = shock_grid(AAPL_BOOK, _surface("AAPL"), _shocks((0.05,), (-2.5,)))
    args = (pos["strike"], pos["T"], pos["r"], pos["q"])
    want = crr(pos["S"] * 1.05, *args, vol - 0.025, "C", n, True) - crr(pos["S"], *args, vol, "C", n, True)
    assert grid["pnl"].iloc[0] == pytest.approx(want * 100 * 20, rel=1e-12)


def test_vol_shock_floored_at_iv_lo():
    cfg = dataclasses.replace(CFG, iv=dataclasses.replace(CFG.iv, iv_lo=0.15))
    pos = SPX_BOOK.iloc[0]
    vol = contract_vol(pos["strike"], pos["F"], pos["T"], _surface("^SPX")["^SPX"])
    grid = shock_grid(SPX_BOOK, _surface("^SPX"), dataclasses.replace(cfg, risk=_shocks((0.0,), (-50.0,)).risk))
    want = (position_value(pos, 0.0, 0.15, cfg) - position_value(pos, 0.0, vol, cfg)) * 100 * 10 * -1
    assert grid["pnl"].iloc[0] == pytest.approx(want, rel=1e-12)


@pytest.mark.parametrize("name", ["^SPX", "AAPL"])
def test_small_shock_matches_delta_measure(name):
    # Instruction 11 part A status 4: the ^SPX positions are bound at 0.5% of delta x dS. The tree positions are
    # report-only: the tree's value is piecewise linear in S between terminal nodes, so its P&L over a small shock is
    # the slope of 1 segment and does not converge to the node delta as the shock shrinks
    h = CFG.tolerances.fd_h_spot_rel
    risk = book_risk(BOOKS[name], _surface(name), CFG).iloc[0]
    pnl = shock_grid(BOOKS[name], _surface(name), _shocks((h,)))["pnl"].iloc[0]
    want = risk["dollar_delta"] * h
    gap = abs(pnl - want) / abs(want)
    print(f"{name} shock {h:g}: P&L {pnl:.6f}, delta x dS {want:.6f}, relative gap {gap:.6g}")
    assert np.isfinite(gap)
    if name == "^SPX":
        assert gap <= 0.005


def test_black76_greeks_match_bsm():
    S, K, T, r, q, vol = 7700.0, 7400.0, 0.08, 0.037, 0.012, 0.18
    g = black76_greeks(S, S * np.exp((r - q) * T), K, T, np.exp(-r * T), vol, "P")
    b = greeks(S, K, T, r, q, vol, "P")
    for name in ("delta", "gamma", "vega"):
        assert g[name] == pytest.approx(float(b[name]), rel=1e-12)


def test_crr_greeks_read_the_nodes_of_the_tree():
    S, K, T, r, q, vol, n = 270.0, 275.0, 0.2, 0.037, 0.0, 0.27, 200
    # with q = 0 the American call is the European one, so the root is the discounted mean of its 2 children
    dt = T / n
    u = np.exp(vol * np.sqrt(dt))
    p = (np.exp(r * dt) - 1 / u) / (u - 1 / u)
    up, down = (crr(S * x, K, T - dt, r, q, vol, "C", n - 1, True) for x in (u, 1 / u))
    assert np.exp(-r * dt) * (p * up + (1 - p) * down) == pytest.approx(crr(S, K, T, r, q, vol, "C", n, True), rel=1e-12)


@pytest.mark.parametrize("K,kind", [(250.0, "P"), (270.0, "P"), (275.0, "C"), (300.0, "C")])
def test_crr_greeks_converge_to_the_fine_tree(K, kind):
    # gamma is not the 0 a small bump of S returns. Measured gaps at n_prod: delta 3e-4, gamma 0.4%, and vega 4.1%,
    # from the sawtooth of the tree in sigma as nodes cross K; the bound on vega covers that and no more
    S, T, r, q, vol, h = 270.0, 0.2, 0.037, 0.004, 0.27, CFG.tolerances.fd_h_vol
    g = crr_greeks(S, K, T, r, q, vol, kind, CFG.pricing.n_prod, h)
    fine = crr_greeks(S, K, T, r, q, vol, kind, CFG.pricing.n_validate, h)
    assert g["delta"] == pytest.approx(fine["delta"], abs=1e-3)
    assert g["gamma"] == pytest.approx(fine["gamma"], rel=1e-2)
    assert g["vega"] == pytest.approx(fine["vega"], rel=0.05)


def test_limit_measures():
    risk = book_risk(SPX_BOOK, _surface("^SPX"), CFG)
    assert list(risk.columns) == RISK_COLUMNS
    r = risk.iloc[0]
    assert r["dollar_delta"] == pytest.approx(r["delta"] * r["S"] * 100 * 10 * -1, rel=1e-14)
    assert r["dollar_gamma"] == pytest.approx(r["gamma"] * r["S"]**2 * 0.01 * 100 * 10 * -1, rel=1e-14)
    assert r["vega_pt"] == pytest.approx(r["vega"] / 100 * 100 * 10 * -1, rel=1e-14)
    assert r["dollar_delta"] > 0  # short a put is long delta
    assert r["dollar_gamma"] < 0 and r["vega_pt"] < 0


def _limits(**kw):
    return dataclasses.replace(CFG, limits=dataclasses.replace(CFG.limits, **kw))


def test_breach_flagged():
    risk = book_risk(SPX_BOOK, _surface("^SPX"), CFG)
    gamma = abs(risk["dollar_gamma"].iloc[0])
    table = limit_breaches(risk, _limits(dollar_gamma_1pct=gamma / 2, dollar_delta=1e12, vega_per_point=1e12))
    assert list(table.columns) == BREACH_COLUMNS
    assert table.set_index("measure")["breach"].to_dict() == {"dollar_delta": False, "dollar_gamma": True,
                                                              "vega_pt": False}


def test_breach_uses_the_size_and_a_value_at_the_limit_passes():
    risk = book_risk(SPX_BOOK, _surface("^SPX"), CFG)
    gamma = abs(risk["dollar_gamma"].iloc[0])  # the position's gamma is negative
    table = limit_breaches(risk, _limits(dollar_gamma_1pct=gamma))
    assert not table.set_index("measure")["breach"]["dollar_gamma"]


def test_limits_apply_per_underlying_on_the_net():
    risk = book_risk(pd.concat([SPX_BOOK, SPX_BOOK.assign(position=2, side=1)], ignore_index=True),
                     _surface("^SPX"), CFG)
    table = limit_breaches(risk, _limits(dollar_gamma_1pct=1.0, dollar_delta=1.0, vega_per_point=1.0))
    assert table["value"].to_numpy() == pytest.approx(0, abs=1e-6)
    assert not table["breach"].any()


def test_missing_surface_keeps_its_row_and_the_book_counts_it():
    positions = [_position(), AAPL_POSITION]
    chain = pd.concat([SPX_CHAIN, AAPL_CHAIN], ignore_index=True)
    surface = _surface("^SPX")  # AAPL has no accepted surface
    book = select_book(DAY, positions, chain, surface)
    assert book["status"].to_list() == [OK, NO_SURFACE]
    risk = book_risk(book, surface, CFG)
    assert risk.loc[1, ["vol", "price", "dollar_delta", "strike"]].isna().all()
    grid = shock_grid(book, surface, CFG)
    assert grid.loc[grid["position"] == 2, "pnl"].isna().all()
    assert (grid.loc[grid["position"] == 2, "status"] == NO_SURFACE).all()
    total = grid[grid["contract"] == BOOK_LABEL]
    assert (total["left_out"] == 1).all()
    assert total["pnl"].notna().all()
    table = limit_breaches(risk, CFG).set_index("underlying")
    assert (table.loc["AAPL", "status"] == NO_SURFACE).all()
    assert table.loc["AAPL", "value"].isna().all()
    assert table.loc["AAPL", "breach"].isna().all()


def test_every_position_missing_leaves_the_book_blank():
    book = select_book(DAY, [_position()], SPX_CHAIN, {})
    grid = shock_grid(book, {}, CFG)
    total = grid[grid["contract"] == BOOK_LABEL]
    assert total["pnl"].isna().all()
    assert (total["status"] == NO_SURFACE).all()
