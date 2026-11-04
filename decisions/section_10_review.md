# Decisions from the Section 10 review (instruction 11, part A)

Section 10 is approved, with the vol change in step 11.0. The reviewer read it from a fresh clone at `7118cf5`, including the page render.

- **Dollar gamma.** The `^SPX` figure checks by hand: Γ of about 0.0008 gives roughly 0.46m per leg and about 0.9m for the 2 legs. The table's −1,008,798 is the sum of −381,876 and −626,921.
- **The breach.** The book's config produces it: short 20 `^SPX` wings against a 250,000 limit. The book stays as it is, and the breach is a result the report is meant to show.
- **O-47** (a).
- **O-48** (a).
- **O-49** (a). `build_risk_report` takes a 6th argument, `n_days`, a change from the kickoff signature `build_risk_report(day, grid, greeks, breaches, out_path)`: the page has to state the N of capture days and nothing else passed in holds it.
- **Status 4 (small-shock MEASURE).** The `^SPX` positions are bound at 0.5% of delta × dS. The tree positions stay report-only, with the piecewise-linear reason written in the test.
- **Status 5 (SSVI misprices the wings).** Changed. Each contract's vol is its own expiry's accepted SVI slice at its strike. SSVI is the fallback only when that expiry has no accepted slice, with a `vol_source` column (`svi` or `ssvi`). Step 11.0 builds this.
- **Status 6.** Accepted.
- **Status 7.** The owner may delete `C:\vs4` to `C:\vs10`. Claude Code does not.
