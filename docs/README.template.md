# Volatility Surface and Event Pricing

[![ci](https://github.com/uty101/Volatility-Surface-and-Event-Pricing/actions/workflows/ci.yml/badge.svg)](https://github.com/uty101/Volatility-Surface-and-Event-Pricing/actions/workflows/ci.yml) {{n_tests}} tests

Prices listed options and their Greeks, solves implied volatility, and fits an arbitrage-free SVI and SSVI surface per underlying.
Reads the risk-neutral distribution off the surface and measures the move options price around earnings and macro events.
Tests the volatility risk premium on S&P 500 history from 1990 and implied against realised correlation from Cboe COR3M.
Splits delta-hedged option P&L into Greeks and builds a 1-page daily risk report.
Option chains are captured daily from 2026-10-28, so every live result is a method demonstration with its N stated.

Every table, chart and the risk report are committed in [`outputs/`](outputs/), and [`outputs/results.html`](outputs/results.html) shows them on 1 page, so nothing needs to be run to see the results.

**Capture window:** {{first_day}} to {{last_day}}, {{n_days}} days, {{missed}} missed. The first day holds `^SPX`, SPY and AAPL only, from an in-session test capture. The others hold all 37 underlyings.

## What it found

{{findings}}

## 1. Does the pricer match QuantLib?

{{answers:1}}

## 2. The S&P 500 surface

{{answers:2}}

{{table:surface}}

The smile on the last day shows the skew the slices hold: the 30-day 25-delta risk reversal is {{rr_last}} vol points.

![^SPX smiles](outputs/figures/spx_smiles_{{last_day}}.png)

ATM vol jumped on 2026-10-30, fell back on 2026-11-04 and jumped again on 2026-11-05, ending at {{atm_last}}% with the term slope negative.

![^SPX metrics](outputs/figures/spx_metrics.png)

The density comes straight from each slice, and the shaded band marks where quotes exist. Tail probabilities outside it are labelled extrapolated.

![^SPX density](outputs/figures/spx_density_last.png)

## 3. Earnings events

{{answers:3:summary}}

{{table:events}}

Points above the line moved more than the options priced. {{n_events}} points say nothing about the average.

![Implied against realised](outputs/figures/event_scatter.png)

## 4. The volatility risk premium

{{answers:4}}

{{table:strategies}}

`bxm_long` is BXM alone over its longer window. VIX squared sat above the variance that followed in {{vrp_above}} of {{vrp_months}} months.

![VIX squared against realised](outputs/figures/vrp_vix2_vs_rv.png)

The timed line ends highest of the option strategies, with a Sharpe of {{timed_sharpe}} against PUT's {{put_sharpe}}. That is 1 specification of 5, so read it with the deflated Sharpes above.

![Cumulative excess return](outputs/figures/vrp_cumulative.png)

Its worst drawdown is {{timed_dd}}% against PUT's {{put_dd}}%, because it was out of the market for part of the falls.

![Drawdowns](outputs/figures/vrp_drawdowns.png)

## 5. Correlation

{{answers:5}}

{{table:cor3m}}

{{table:implied_corr}}

Implied and realised move together, with a slope of {{cor3m_slope}} and an R² of {{cor3m_r2}}. The shaded gap is the sector proxy, not a premium.

![COR3M against realised](outputs/figures/cor3m_vs_realised.png)

## 6. P&L attribution and hedging

{{answers:6}}

{{table:hedging}}

## Risk report

[`outputs/reports/risk_{{last_day}}.pdf`](outputs/reports/risk_{{last_day}}.pdf) is the 1-page report for {{last_day}} (N = {{n_days}} capture days). Each vol is the contract's own SVI slice at its strike.

{{table:risk_book}}

The worst cell of the grid loses {{grid_worst}} thousand dollars, at spot {{grid_spot}}% and vol +{{grid_vol}} points. {{n_breaches}} of 9 limits is breached: {{breach_underlying}} dollar gamma of {{breach_value}} against a limit of {{breach_limit}}, which the short wings produce and the report is meant to show.

## Run it

```bash
uv venv --python 3.12
uv pip install -r requirements-lock.txt
uv pip install -e . --no-deps
python scripts/run_all.py                  # every stage, in section order
pytest -p socket --disable-socket -q
```

`run_all.py` needs an authenticated `gh` to download the chains from the `snapshots` release. Long history is committed in `data/raw/`. Fitted surfaces are cached in `data/processed/surface/`, so only new days are fitted. Methods are in [`docs/METHODS.md`](docs/METHODS.md).

## What this does not do

- The live window is a few weeks, so nothing built on captured chains is a statistical result.
- Option prices are Yahoo's delayed quotes at 15:30 New York, not exchange data.
- The COR3M comparison is a sector proxy, because COR3M covers single stocks and the realised side uses sector ETFs.
- The timed PUT result is 1 specification of a family of 5, and its gain over PUT does not survive the deflation.
- The risk book is a sample, not a real portfolio.

## Repo map

| Path | What is in it |
|---|---|
| `volsurf/` | The package |
| `scripts/` | Daily capture, data pulls and `run_all.py` |
| `tests/` | Offline tests and fixtures |
| `data/raw/` | Prices, yields, Cboe series and XLK holdings |
| `data/manual/` | Earnings timing overrides and the macro calendar |
| `outputs/tables/` | Every table, `answers.csv` among them |
| `outputs/figures/` | Every chart |
| `outputs/reports/` | The last day's risk report |
| `docs/` | Methods, conventions, README template |
| `decisions/` | Design and review decisions |
| `instructions/`, `review/` | Session instructions, status and reviews |
| `.github/workflows/` | CI and the daily capture |
| `config.toml` | Every parameter |
| `project_outline/` | The original brief |

## Licence

MIT, see [LICENSE](LICENSE).
