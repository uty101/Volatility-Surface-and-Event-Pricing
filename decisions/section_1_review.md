# Decisions from the Section 0 review (instruction 01, part B)

One line per OPEN item: the option chosen and the reviewer's reason. Options are as written in `decisions/OPEN.md`.

- **O-1** (a). One entry point keeps `run_all.py` the single rebuild path.
- **O-2** (a), every proposed name. They are clear and already in PLAN.md.
- **O-3** (a). `^GSPC` and `^SPX` are the same index; `^GSPC` has the long daily history.
- **O-4** (a) 2026-10-28. The first real capture; fixed so tests never move.
- **O-5** (b). A day is a snapshot day if any non-test chains asset exists; each ticker is used only if its status is `ok`. One bad ticker should not cost the other 31.
- **O-6** (a). Details in instruction 01 step 1.1 (header row is the first whose first cell is `Name`; weight percent stored as decimal; blank and `-` tickers dropped; `as_of_date` from the `Holdings:` line; weights gate 0.97 to 1.01).
- **O-7** (a). Each tenor uses its own latest valid observation dated ≤ t − 1.
- **O-8** (a). Log-moneyness bins apply to calls and puts alike and need no vol.
- **O-9** (a). No reason given.
- **O-10** (a). No reason given.
- **O-11** (a). No reason given.
- **O-12** (b), with a rule. Use the row from the latest earnings asset that lists the event; if that row's time is 15:00 New York, the timing is `unknown` whatever `classify_timing` says, because 15:00 is Yahoo's placeholder for unconfirmed dates; `unknown` events need an override to enter the study.
- **O-13** (a). No reason given.
- **O-14** (a). No reason given.
- **O-15** (a). No reason given.
- **O-16** (b), restated. The T-bill return for month m+1 is the DTB3 value on the last session of month m, divided by 1200 (the rate known at the decision); the first position counts as a switch.
- **O-17** (a). No reason given.
- **O-18** (a), changed for Heston. T = 21 / 252 (a 21-trading-day straddle), step 1 / (252 × `steps_per_day`), Heston by full-truncation Euler; the straddle is sold at its model price (BSM at σ for GBM; QuantLib `AnalyticHestonEngine` once at t = 0 for Heston); hedge delta is BSM delta at σ for GBM and at √v_t for Heston; hedging error as in (a).
- **O-19** (a). No reason given.
- **O-20** (a). Γ × S² × 0.01 × 100 × contracts × side is the standard desk measure.
- **O-21** (a). No reason given.
- **O-22** (a) on items 1 to 9, plus the `better` upload change of instruction 01 step 1.0. No reason given.
- **O-23** (b). Rule e is skipped for `^SPX` in Section 1, logged as `rows_dropped = 0` with the note `deferred to section 3`.
- **O-24** (a). No reason given.

Also decided in instruction 01 part A: status question 1 of session 0 (local task triggers pinned to UTC) is (a), keep the UTC triggers, since they fire at the same instants as the Actions crons. The owner re-registers the task by hand after step 1.0.
