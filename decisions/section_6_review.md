# Decisions from the Section 6 review (instruction 07, part A)

Section 6 is approved, with the correction in step 7.0. The reviewer checked it from a fresh clone at `31c8874`.

- **INTC.** The realised move matches the captured spot prices: the 2026-10-29 snapshot has INTC at 91.85 and the 2026-10-30 snapshot has it at 64.94 at 15:53 New York, so the close-to-close move of 0.337 is real.
- **CVX hand check.** With n1 = 1 and n2 = 6 from 2026-10-29, v_d = (0.002457 − 0.000862) / 5 = 0.000319, v_e = θ1 − v_d × 0 = 0.000862 and M_t = √(2/π) × √0.000862 = 0.02343, the same as `ts_move`.
- **Status 1 (98 kinks, not 99).** Accepted. The stated rule decides, and CVX 2026-11-06 stays `ok`.
- **Status 2 (AMZN E1 is a `kink` slice).** Accepted. θ is w(0), and the kink sits at m, away from 0.
- **Status 3 (INTC).** Checked, above.
- **Status 4 (pre-event snapshot).** Corrected. Convention 4.11: the pre-event snapshot is the last snapshot on a session strictly before the window's end close and no later than the window's start session; it does not have to fall on the start session. AAPL and PLTR (AMC 2026-11-02) and SHOP (BMO 2026-11-03) take the 2026-10-30 snapshot, with n1 and n2 counted from 2026-10-30. EVENTS gains `pre_snap_age` after `pre_snap_date`: the sessions between `pre_snap_date` and the window's start session, so a stale snapshot is visible in the table.
- **Status 5 (run 41622958662).** Print its log and say whether the 2026-11-03 assets landed.
- **Status 6 (155 min surface stage).** Step 7.0 adds a per-day cache, `data/processed/surface/{day}.parquet`, keyed on the sha256 of `volsurf/svi.py`, `volsurf/ssvi.py`, the `[svi]` and `[surface]` tables and the day's IV file, so only new days are fitted; `--force` refits everything.
- **Status 7.** The owner may delete `C:\vs4` to `C:\vs6`. Claude Code does not.
