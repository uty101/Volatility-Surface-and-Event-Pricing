"""Sample book, shock grid and limits (PLAN 10.1, kickoff 5.11, instruction 10 step 10.1).

Each contract is revalued on the pricer the project uses for it: Black-76 on the day's parity F and D for `^SPX`, CRR
American at `n_prod` on the day's r and q for the others. The Greeks for the limits come from the same pricers.

Each contract's vol is its own expiry's accepted SVI slice at its strike, for the reason Section 4 moved the daily
metrics off SSVI: 1 rho cannot fit the wings. SSVI is the fallback only when that expiry has no accepted slice
(instruction 11 step 11.0); `vol_source` says which one a position used.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
from scipy.stats import norm

from volsurf.data import SPX
from volsurf.greeks import greeks
from volsurf.pricing import black76, crr
from volsurf.ssvi import ssvi_w, theta_at
from volsurf.svi import svi_w

BOOK_COLUMNS = ["day", "position", "contract", "underlying", "side", "kind", "contracts", "target_delta", "target_days",
                "expiry", "days", "strike", "T", "S", "F", "D", "r", "q", "select_delta", "status"]
RISK_COLUMNS = [*BOOK_COLUMNS[:-1], "vol", "vol_source", "price", "delta", "gamma", "vega", "dollar_delta", "dollar_gamma",
                "vega_pt", "status"]
GRID_COLUMNS = ["day", "position", "contract", "spot_shock", "vol_shock_pts", "pnl", "status", "left_out"]
BREACH_COLUMNS = ["day", "underlying", "measure", "value", "limit", "breach", "status", "left_out"]
MEASURES = {"dollar_delta": "dollar_delta", "dollar_gamma": "dollar_gamma_1pct", "vega_pt": "vega_per_point"}
BOOK_LABEL = "book"  # the grid's total rows, position 0
OK, NO_SURFACE = "ok", "no_surface"
SVI, SSVI = "svi", "ssvi"  # vol_source, instruction 11 part A status 5
MULTIPLIER = 100  # contract multiplier, instruction 10 step 10.1
VOL_POINT = 100  # vol points per 1.00 of vol, Convention 4.10


def day_surface(ssvi: pd.Series, thetas: pd.DataFrame, slices: dict[str, tuple] | None = None) -> dict:
    """1 underlying's surface on a day: a SURFACE_DAILY row, its accepted expiries' T and theta_used, sorted by T, and
    `slices`, each accepted expiry's raw SVI parameters (a, b, rho, m, s)."""
    return {"rho": ssvi["ssvi_rho"], "eta": ssvi["ssvi_eta"], "gamma": ssvi["ssvi_gamma"],
            "thetas": thetas.sort_values("T"), "slices": slices or {}}


def vol_source(s: dict, expiry: str | None) -> str:
    """`svi` when the expiry has an accepted slice, else `ssvi`."""
    return SVI if expiry in s["slices"] else SSVI


def contract_vol(K: float, F: float, T: float, s: dict, expiry: str | None = None) -> float:
    """The contract's vol: sqrt(w(ln(K / F)) / T) on its expiry's accepted SVI slice, else on SSVI with theta(T) by
    Convention 4.12, nan outside that range."""
    if vol_source(s, expiry) == SVI:
        return float(np.sqrt(svi_w(np.log(K / F), *s["slices"][expiry]) / T))
    theta = theta_at(T, s["thetas"])
    if not np.isfinite(theta):
        return np.nan
    return float(np.sqrt(ssvi_w(np.log(K / F), theta, s["rho"], s["eta"], s["gamma"]) / T))


def _label(underlying: str, kind: str, expiry: str | None = None, strike: float | None = None) -> str:
    return f"{underlying} {kind}" if expiry is None else f"{underlying} {expiry} {kind} {strike:g}"


def select_book(day: date, positions, iv: pd.DataFrame, surface: dict[str, dict]) -> pd.DataFrame:
    """O-21 (a): for each `[book]` position, the expiry with calendar days nearest `target_days` (ties to the shorter),
    then the strike on it whose BSM delta at the contract's vol is nearest `target_delta` (ties to the lower strike).

    `iv` is the day's IV table and `surface` maps each underlying with an accepted surface to `day_surface`. Candidates
    are the IV table's contracts of that kind with a solved vol (O-47 (a)). A position with no candidate, no surface or
    no vol keeps its row with status `no_surface` and blank values. 1 row per position (BOOK_COLUMNS)."""
    rows = []
    for number, p in enumerate(positions, start=1):
        row = {"day": str(day), "position": number, "contract": _label(p.underlying, p.kind),
               "underlying": p.underlying, "side": p.side, "kind": p.kind, "contracts": p.contracts,
               "target_delta": p.target_delta, "target_days": p.target_days, "status": NO_SURFACE}
        rows.append(row)
        chain = iv[(iv["ticker"] == p.underlying) & (iv["kind"] == p.kind) & iv["iv"].notna()]
        if p.underlying not in surface or chain.empty:
            continue
        expiries = sorted(chain["expiry"].astype(str).unique())
        days = np.array([(date.fromisoformat(e) - day).days for e in expiries])
        expiry = expiries[int(np.argmin(np.abs(days - p.target_days)))]  # argmin: first, the shorter
        block = chain[chain["expiry"].astype(str) == expiry].sort_values("strike")
        T, S, F, r, q = (float(block[c].iloc[0]) for c in ("T", "S", "F", "r", "q"))
        strikes = block["strike"].to_numpy(dtype=float)
        vols = np.array([contract_vol(K, F, T, surface[p.underlying], expiry) for K in strikes])
        if not np.isfinite(vols).all():
            continue
        deltas = greeks(S, strikes, T, r, q, vols, p.kind)["delta"]
        best = int(np.argmin(np.abs(deltas - p.target_delta)))  # argmin: first, the lower strike
        row.update(contract=_label(p.underlying, p.kind, expiry, strikes[best]), expiry=expiry,
                   days=(date.fromisoformat(expiry) - day).days, strike=strikes[best], T=T, S=S, F=F,
                   D=float(np.exp(-r * T)), r=r, q=q, select_delta=float(deltas[best]), status=OK)
    return pd.DataFrame(rows, columns=BOOK_COLUMNS)


def black76_greeks(S: float, F: float, K: float, T: float, D: float, sigma: float, kind: str) -> dict:
    """Delta and gamma in spot by the chain rule with F / S held fixed, as `volsurf.attribution.straddle_greeks`, and
    vega per 1.00 of vol (Convention 4.10)."""
    sd = sigma * np.sqrt(T)
    d1 = (np.log(F / K) + sd**2 / 2) / sd
    fs, pdf = F / S, norm.pdf(d1)
    forward_delta = norm.cdf(d1) if kind == "C" else norm.cdf(d1) - 1
    return {"delta": float(D * fs * forward_delta), "gamma": float(fs**2 * D * pdf / (F * sd)),
            "vega": float(D * F * pdf * np.sqrt(T))}


def crr_greeks(S: float, K: float, T: float, r: float, q: float, sigma: float, kind: str, n: int, h_vol: float) -> dict:
    """Greeks of the American CRR tree. Delta and gamma come from the nodes of steps 1 and 2, not from bumping S: the
    tree's value is piecewise linear in S between terminal nodes, so a second difference over a bump smaller than their
    spacing is 0 or a spike. The subtree at a node is `crr` from that node's spot with the same dt, so its value is
    the node's. Vega is a central difference in sigma of width `h_vol`, which is smooth on the tree."""
    dt = T / n
    u = np.exp(sigma * np.sqrt(dt))
    up, down = (crr(S * x, K, T - dt, r, q, sigma, kind, n - 1, True) for x in (u, 1 / u))
    uu, ud, dd = (crr(S * x, K, T - 2 * dt, r, q, sigma, kind, n - 2, True) for x in (u**2, 1.0, u**-2))
    gamma = ((uu - ud) / (S * (u**2 - 1)) - (ud - dd) / (S * (1 - u**-2))) / (S * (u**2 - u**-2) / 2)
    vega = (crr(S, K, T, r, q, sigma + h_vol, kind, n, True) - crr(S, K, T, r, q, sigma - h_vol, kind, n, True))
    return {"delta": (up - down) / (S * (u - 1 / u)), "gamma": gamma, "vega": vega / (2 * h_vol)}


def position_value(pos: pd.Series, spot_shock: float, vol: float, cfg) -> float:
    """Value per share at a shocked spot and a given vol. A spot shock moves S and F together; D, r, q and T stay."""
    if pos["underlying"] == SPX:
        return float(black76(pos["F"] * (1 + spot_shock), pos["strike"], pos["T"], pos["D"], vol, pos["kind"]))
    return crr(pos["S"] * (1 + spot_shock), pos["strike"], pos["T"], pos["r"], pos["q"], vol, pos["kind"],
               cfg.pricing.n_prod, True)


def book_risk(book: pd.DataFrame, surface: dict[str, dict], cfg) -> pd.DataFrame:
    """Price, vol, its source and Greeks per position, with the limit measures of instruction 10 step 10.1 and O-20 (a):
    dollar delta = delta S 100 contracts side, dollar gamma = gamma S^2 0.01 100 contracts side, vega per vol point =
    vega / 100 x 100 contracts side. `no_surface` rows stay blank. 1 row per position (RISK_COLUMNS)."""
    rows = []
    for _, pos in book.iterrows():
        row = pos.to_dict()
        if pos["status"] == OK:
            s = surface[pos["underlying"]]
            vol = contract_vol(pos["strike"], pos["F"], pos["T"], s, pos["expiry"])
            if pos["underlying"] == SPX:
                g = black76_greeks(pos["S"], pos["F"], pos["strike"], pos["T"], pos["D"], vol, pos["kind"])
            else:
                g = crr_greeks(pos["S"], pos["strike"], pos["T"], pos["r"], pos["q"], vol, pos["kind"],
                               cfg.pricing.n_prod, cfg.tolerances.fd_h_vol)
            size = MULTIPLIER * pos["contracts"] * pos["side"]
            row.update(vol=vol, vol_source=vol_source(s, pos["expiry"]), price=position_value(pos, 0.0, vol, cfg), **g,
                       dollar_delta=g["delta"] * pos["S"] * size,
                       dollar_gamma=g["gamma"] * pos["S"]**2 * 0.01 * size,  # 1% move, O-20 (a)
                       vega_pt=g["vega"] / VOL_POINT * size)
        rows.append(row)
    return pd.DataFrame(rows, columns=RISK_COLUMNS)


def shock_grid(book: pd.DataFrame, surface: dict[str, dict], cfg) -> pd.DataFrame:
    """Kickoff 5.11, sticky strike with full revaluation: each contract keeps its own vol at its strike. A spot
    shock moves S and F but not the vol; a vol shock adds its points to that vol, floored at `iv_lo`. P&L in dollars is
    value change x 100 x contracts x side. 1 row per position and cell, then 1 `book` row per cell summing them, whose
    `left_out` counts the `no_surface` positions (GRID_COLUMNS). A `no_surface` position's rows have blank P&L."""
    rows = []
    left_out = int((book["status"] != OK).sum())
    for _, pos in book.iterrows():
        ok = pos["status"] == OK
        vol = contract_vol(pos["strike"], pos["F"], pos["T"], surface[pos["underlying"]], pos["expiry"]) if ok else np.nan
        base = position_value(pos, 0.0, vol, cfg) if ok else np.nan
        for spot in cfg.risk.spot_shocks:
            for points in cfg.risk.vol_shocks_pts:
                pnl = np.nan
                if ok:
                    shocked = position_value(pos, spot, max(vol + points / VOL_POINT, cfg.iv.iv_lo), cfg)
                    pnl = (shocked - base) * MULTIPLIER * pos["contracts"] * pos["side"]
                rows.append({"day": pos["day"], "position": pos["position"], "contract": pos["contract"],
                             "spot_shock": spot, "vol_shock_pts": points, "pnl": pnl, "status": pos["status"]})
    frame = pd.DataFrame(rows)
    total = frame.groupby(["day", "spot_shock", "vol_shock_pts"], sort=False, as_index=False)["pnl"].sum(min_count=1)
    total = total.assign(position=0, contract=BOOK_LABEL, left_out=left_out,
                         status=np.where(total["pnl"].notna(), OK, NO_SURFACE))
    return pd.concat([frame, total], ignore_index=True).reindex(columns=GRID_COLUMNS)


def limit_breaches(book_greeks: pd.DataFrame, cfg) -> pd.DataFrame:
    """O-19 (a): the `[limits]` values apply to every underlying alike. Per underlying and measure, the net of the
    book's positions against the limit, `breach` when its size is above it (BREACH_COLUMNS). `left_out` counts that
    underlying's `no_surface` positions; an underlying with none priced keeps its rows with status `no_surface`."""
    rows = []
    for underlying, block in book_greeks.groupby("underlying", sort=False):
        priced = block[block["status"] == OK]
        for measure, key in MEASURES.items():
            limit = getattr(cfg.limits, key)
            row = {"day": block["day"].iloc[0], "underlying": underlying, "measure": measure, "limit": limit,
                   "left_out": len(block) - len(priced), "status": NO_SURFACE, "value": np.nan, "breach": pd.NA}
            if not priced.empty:
                value = float(priced[measure].sum())
                row.update(value=value, breach=abs(value) > limit, status=OK)
            rows.append(row)
    return pd.DataFrame(rows, columns=BREACH_COLUMNS)
