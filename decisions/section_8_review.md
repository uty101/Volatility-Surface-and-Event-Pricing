# Decisions from the Section 8 review (instruction 09, part A)

Section 8 is approved. The reviewer checked it from a fresh clone at `d39fa33`.

- **Status 1 (signal share).** The session is right and the reviewer was wrong. The reviewer's 90.7% came from 2 errors in the reviewer's own run: VIX was looked up on exact dates, so 1997-01-31 and 1999-12-31 got no IV, and the incomplete month 2026-11-02 was counted. 362 of 395 (91.6%) stands.
- **Status 2 (mean VRP).** VRP_t = IV − RV does not need the GARCH forecast, so the headline is over every row with IV and RV: 0.01037 over 441 months. The GARCH-era mean (0.00970, 394 months) is reported beside it, labelled.
- **The 3 numbers that miss at 2 decimals.** Accepted, as explained: October 2026 now ends on the 10-30 close after the Cboe refresh.
- **O-43** (a).
- **O-44** (a).
- **`kurt_pearson`.** Accepted. `deflated_sharpe(sr, n_obs, skew, kurt_pearson, sr_trials)` departs from the kickoff signature, which names the argument `kurt`. The argument takes the non-excess (Pearson) kurtosis, and the name says so (instruction 08 point 3).
- **Status 5.** Noted.
- **Status 6.** The owner may delete `C:\vs4` to `C:\vs8`. Claude Code does not.
- **Capture.** The 2026-11-03 capture landed through the chained run (37 of 37 ok). The capture fix works.
