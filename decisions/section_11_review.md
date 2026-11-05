# Decisions from the Section 11 review (instruction 12, part A)

Section 11 is approved, and with it the project's 11 sections. The reviewer read the README, `answers.csv` and the status from a fresh clone at `90be1cd`. CI is green with 4,729 tests.

- **O-50 to O-55** All (a).
- **Status 1.** Accepted. The fix comes with a test.
- **Status 2 (NVDA slice 1.05 points from its mid).** Accepted. The slice passed the RMSE gate, and a 45-day single-name put 1 vol point off is within that gate. The slice stays the source.
- **Status 4 (question 4 blank).** Changed. This is the reviewer's gap: a deflated Sharpe needs the family of specifications that was tried, and the project tried only 1. Step 12.1 adds a small family, fixed before any result was seen.
- **Status 5 and 6.** Step 12.2 refreshes prices and runs the newer capture days.
- **Status 9 and 10.** Accepted. The owner may delete `C:\vs4` to `C:\vs11`, `C:\vs11pre`, `data/processed/surface_s10_backup` and `data/processed/surface_cold1`. Claude Code does not.
- **README risk section.** The breach sentence keeps the sign that the table shows: "dollar gamma of −1,003,799 against a limit of 250,000".
