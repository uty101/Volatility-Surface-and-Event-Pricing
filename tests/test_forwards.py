from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from volsurf.config import load_config
from volsurf.data import RATE_TENORS, SPX, clean_chain
from volsurf.forwards import FORWARD_COLUMNS, parity_forward, spx_forwards
from volsurf.pricing import black76

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "config.toml")
FW = CFG.forwards
FIXTURE_DAY = date(2026, 10, 28)  # instruction 01d part B


def _chain(F, D, T, strikes, sigma=0.2, noise=None):
    """European calls and puts from Black-76 at known F and D, quoted 0.02 wide around the model price."""
    strikes = np.asarray(strikes, dtype=float)
    c = black76(F, strikes, T, D, sigma, "C")
    p = black76(F, strikes, T, D, sigma, "P")
    if noise is not None:
        c = c + noise
    calls = pd.DataFrame({"strike": strikes, "bid": c - 0.01, "ask": c + 0.01})
    puts = pd.DataFrame({"strike": strikes, "bid": p - 0.01, "ask": p + 0.01})
    return calls, puts


def test_synthetic_recovers_f():
    F, T, r = 100.0, 0.5, 0.04
    D = np.exp(-r * T)
    calls, puts = _chain(F, D, T, np.arange(80, 121, 2.5))
    out = parity_forward(calls, puts, 99.0, T, D, FW.parity_n_strikes, FW.parity_min_pairs, FW.parity_mad_max_bp)
    assert out["status"] == "ok"
    assert out["n_pairs"] == FW.parity_n_strikes
    assert abs(out["F"] - F) <= 1e-10
    assert out["mad_bp"] < 1e-6
    np.testing.assert_allclose(out["r_reg"], r, atol=1e-9)
    np.testing.assert_allclose(out["q_impl"], r - np.log(F / 99.0) / T, atol=1e-12)


def test_gate_rejects_noisy_chain():
    F, T = 100.0, 0.5
    D = np.exp(-0.04 * T)
    strikes = np.arange(90, 111, 2.5)
    noise = np.random.default_rng(CFG.run.seed).normal(0.0, 0.5, len(strikes))  # about 50 bp of F per pair
    calls, puts = _chain(F, D, T, strikes, noise=noise)
    out = parity_forward(calls, puts, F, T, D, FW.parity_n_strikes, FW.parity_min_pairs, FW.parity_mad_max_bp)
    assert out["mad_bp"] > FW.parity_mad_max_bp
    assert out["status"] == "parity_fail"
    assert np.isnan(out["F"]) and np.isnan(out["q_impl"])


def test_gate_rejects_too_few_pairs():
    F, T = 100.0, 0.5
    D = np.exp(-0.04 * T)
    calls, puts = _chain(F, D, T, np.arange(95, 106, 2.5))
    puts = puts.iloc[: FW.parity_min_pairs - 1]  # 1 strike fewer with both mids than the gate needs
    out = parity_forward(calls, puts, F, T, D, FW.parity_n_strikes, FW.parity_min_pairs, FW.parity_mad_max_bp)
    assert out["n_pairs"] < FW.parity_min_pairs
    assert out["status"] == "parity_fail"


def test_nearest_strikes_used():
    # a far strike with a wrong put mid is outside the n nearest and must not move F
    F, T = 100.0, 0.5
    D = np.exp(-0.04 * T)
    calls, puts = _chain(F, D, T, [*np.arange(90, 111, 2.5), 200.0])
    puts.loc[puts["strike"] == 200.0, ["bid", "ask"]] += 50.0
    out = parity_forward(calls, puts, F, T, D, 9, FW.parity_min_pairs, FW.parity_mad_max_bp)
    assert out["n_pairs"] == 9
    assert abs(out["F"] - F) <= 1e-10


def _fixture_forwards():
    chains = pd.read_parquet(ROOT / "tests" / "fixtures" / "chains_sample.parquet")
    underlying = pd.read_csv(ROOT / "tests" / "fixtures" / "underlying_sample.csv")
    fred = {sid: pd.read_csv(ROOT / "data" / "raw" / "fred" / f"{sid}.csv") for sid in RATE_TENORS}
    first, _ = clean_chain(chains, underlying, CFG)
    return first, spx_forwards(first, underlying, fred, FIXTURE_DAY, CFG)


def test_fixture_every_spx_expiry_with_min_pairs_passes_gate():
    first, fw = _fixture_forwards()
    assert list(fw.columns) == FORWARD_COLUMNS
    assert len(fw) == first.loc[first["ticker"] == SPX, "expiry"].nunique()
    eligible = fw[fw["n_pairs"] >= FW.parity_min_pairs]
    assert len(eligible) > 0
    assert (eligible["status"] == "ok").all()
    assert (eligible["mad_bp"] <= FW.parity_mad_max_bp).all()
