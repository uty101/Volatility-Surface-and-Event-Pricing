import pytest
import QuantLib as ql

QL_TODAY = ql.Date(28, 10, 2026)


def _ql_option(S, K, days, r, q, sigma, kind, american=False, steps=None):
    """QuantLib vanilla option per instruction 02 Section B: dates today + days, Actual365Fixed, flat
    continuous r and q. European options get AnalyticEuropeanEngine; American get BinomialVanillaEngine("crr")."""
    ql.Settings.instance().evaluationDate = QL_TODAY
    dc = ql.Actual365Fixed()
    expiry = QL_TODAY + days
    process = ql.BlackScholesMertonProcess(
        ql.QuoteHandle(ql.SimpleQuote(S)),
        ql.YieldTermStructureHandle(ql.FlatForward(QL_TODAY, q, dc)),
        ql.YieldTermStructureHandle(ql.FlatForward(QL_TODAY, r, dc)),
        ql.BlackVolTermStructureHandle(ql.BlackConstantVol(QL_TODAY, ql.NullCalendar(), sigma, dc)),
    )
    payoff = ql.PlainVanillaPayoff(ql.Option.Call if kind == "C" else ql.Option.Put, K)
    if american:
        option = ql.VanillaOption(payoff, ql.AmericanExercise(QL_TODAY, expiry))
        option.setPricingEngine(ql.BinomialVanillaEngine(process, "crr", steps))
    else:
        option = ql.VanillaOption(payoff, ql.EuropeanExercise(expiry))
        option.setPricingEngine(ql.AnalyticEuropeanEngine(process))
    return option


@pytest.fixture
def ql_option():
    return _ql_option
