# Status: session 5c (`instructions/05c_section_5_finish.md`)

## Outcome

Complete. Section 5 is finished. Step 5c.1 is `d25abb1`, step 5.1 is `558b5cf` and step 5.2 is `68e173a`. Evidence is in `review/section_5.md` under `## Session 5c`.

## Last step reached

Step 5.2. Then the review section, this file, the fresh-clone check and CI.

## What changed

- **Step 5c.1.**
  - A fit counts on any route, the first included, only with w ≥ 1e-12 on the 200,001-point acceptance grid and with `_violation` = 0. A first fit that fails goes to the refit route.
  - O-37 (a) is applied to `test_nonnegative_when_butterfly_passes`, and the restated line is in `CLAUDE.md` under Amendments.
  - New test: `test_negative_w_slices_never_accepted`, with CSCO and SHOP quote fixtures.
- **Against session 5b, only CSCO 2026-11-13 and SHOP 2026-11-20 on 2026-10-29 changed.** Both are now `ok_refit`, with smallest w 1.0e-3 and 7.8e-8. Neither is `density_fail` any more. The fixture day is unchanged: 74 of 74 accepted, with the same routes.
- **The 2026-10-30 capture is the third day.** It was in the `snapshots` release when the session started, so it is included as the instruction 05c status 8 decision says. The scheduled run had landed at 19:55 UTC on 2026-10-30, and the work began on 2026-11-02.
- **Step 5.1.**
  - 1,013 accepted slices over the 3 days.
  - Largest |integral − 1|: 2.5e-9.
  - Largest `tail_mass`: 2.6e-3 (MU 2027).
  - 2 `density_fail` slices: MU 2027-08-20 and 2027-09-17 on 2026-10-30. Their mean misses `int_tol` (1.1e-3 and 1.7e-3) by exactly the mean mass beyond k = +10, which the mean leaves out by design (instruction 05b part B).
- **Step 5.2.**
  - Tail tables for the 1,011 slices with an `ok` density.
  - On 2026-10-30, the 30-day `^SPX` slice (2026-11-30) gives P(S_T < 0.9 F) = 0.0438 and P(S_T > 1.1 F) = 0.0036.
  - PIT: `^SPX` 2026-10-29 u = 0.4112 and SPY 2026-10-29 u = 0.4120, from 2026-10-28 slices and the 2026-10-29 closes. The price files end on 2026-10-29, so no later expiry is covered.

## Questions and blockers for the reviewer

1. **O-38: the finite-difference bound on every slice.** The 5e-3 × peak bound passes as the fixture test, with a largest gap of 1.05e-3. Measured on every accepted slice, 109 of 1,013 exceed it; the largest is 0.856 (CRM 2027-05-21).
   - 97 of the 109 have s at the 1e-4 floor. The density has a spike at k = m that the step `bl_dk` × F cannot resolve.
   - The analytic density is not at fault: on the 4 slices tried, the gap shrinks with the step, for example CRM 0.856, 0.237 and 3.7e-3 at 1, 1/10 and 1/100 of the step.
   - Sessions 5 and 5b measured the fixture only, so this is newly seen, not new: 54 of the 109 are on 2026-10-29.
   - I asked the owner in session whether to stop under rule 4 or finish and report. The owner chose to finish.
   - (a) The bound is the fixture test only. (b) The bound holds on every slice, by scaling the step or by rejecting unresolvable slices in Section 4.
2. **O-39: the CSV rounds the parameters.** `svi_fits.csv` is written at `%.10g`, and steps 5.1 and 5.2 read the parameters back from it.
   - From the rounded parameters, 37 accepted slices have g below −1e-10 on the acceptance grid; the smallest is −4.8e-10.
   - From the fit's full-precision parameters, none does; the smallest is −9.5e-11.
   - (a) Write the parameters at full precision. (b) Keep `%.10g`.
3. **Daily accepted shares below 0.75.** These are reported only, like XLE and NFLX in session 5b:
   - 2026-10-30: XLK 0.545, PANW 0.583, MU 0.588, CSCO 0.636, XLE 0.643, NFLX 0.700 and TSLA 0.714.
   - 2026-10-29: NFLX 0.700, XLE 0.714 and AMD 0.733.

   On 2026-10-30, MU and PANW are `no_bracket` in SURFACE_DAILY, and SHOP is `delta_outside_quotes`.
4. **Runtime.**
   - The surface stage over 3 days takes 173 min.
   - The IV stage for one new day takes 20 min.
   - The density and tails stages take 3 min and 1 min.
5. **`spx_smiles_2026-10-29.png`** stays from session 5b, unchanged. Only the first and last days are drawn, and 2026-10-29 is no longer the last.
6. **Clones on disk:** `C:\vs4`, `C:\vs4b`, `C:\vs5`, `C:\vs5b`, and `C:\vs5c` from this session. All are safe to delete.

## Tests

`.venv\Scripts\python -m pytest -p socket --disable-socket -q` on Windows at `68e173a` (30 min 54 s): `4523 passed`. `ruff check .`: `All checks passed!` Fresh clone and CI: added in the commit `session 5c: fresh-clone check and CI`.

## `git log origin/main --oneline -3` (before this commit)

```
824752e Add session 5c instructions
543f8f4 session 5b: fresh-clone check and CI
79b9976 session 5b: stopped after step 5b.1, review and status
```
