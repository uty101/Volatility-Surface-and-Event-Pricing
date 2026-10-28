# instructions/01d_section_1_complete.md: Session 1d (finish Section 1 now)

Read `CLAUDE.md` and instructions `01`, `01b` and `01c` first. This file beats all of them where they differ (rule 13). **It replaces `01c` in full: there is no gate and nothing in this session waits for the 19:30 UTC capture.** Build every step below in one go. Rule 4 still applies to genuine failures (a broken earlier test, a data pull that fails, a check that misses its threshold).

---

## A. Why the gate is gone

The fixture does not need the scheduled capture. The forced run 40711619617 (`snapshots-test`, `test_*_2026-10-28`) started at 11:00:58 New York, inside the session, with 37 of 37 tickers ok. The reviewer checked it on Linux:

| ticker | rows | bid > 0, all rows | bid > 0, abs(ln(K/S)) ≤ 0.10 |
|---|---|---|---|
| `^SPX` | 11,557 | 94.5% | 98.2% |
| SPY | 7,466 | 91.4% | 98.1% |
| AAPL | 1,856 | 85.2% | 99.1% |

The after-close run on 2026-10-27 had only 4.4% of `^SPX` rows with a live bid. This in-session capture is the evidence that timing matters, so it is the right fixture. The 01c rule against `test_` assets is lifted for this one file set only.

---

## B. Decisions

| Item | Decision |
|---|---|
| Fixture source (replaces O-4) | `snapshots-test` assets `test_chains_2026-10-28.parquet`, `test_underlying_2026-10-28.csv`, `test_earnings_2026-10-28.csv`, `test_snaplog_2026-10-28.json` from run 40711619617. Fixture day 2026-10-28. |
| O-27 | (b), as in 01c step 1c.3. |
| O-28 | (a), as in 01c. |
| 01c snap_utc window test | Dropped. The 15:25 to 16:30 window is a property of scheduled runs and is already tested in `test_snapshots.py`; a fixture taken at 11:00 New York does not need it. |

Record these in `decisions/section_1_review.md` under `## Session 1d` and mark O-4, O-27 and O-28 decided in `decisions/OPEN.md`.

---

## C. Steps

### Step 1d.1: fixture (commit `step 1d.1: fixture from the in-session 2026-10-28 capture`)

1. Download the 4 test assets above with `gh release download snapshots-test --pattern <name>` into a temp folder. Check each sha256 against `test_snaplog_2026-10-28.json` and print the comparison.
2. Build `tests/fixtures/chains_sample.parquet` (rows for `^SPX`, SPY and AAPL), `tests/fixtures/underlying_sample.csv` (same 3 tickers) and `tests/fixtures/earnings_sample.csv` (AAPL rows). Copy rows exactly as served.
3. Add `tests/fixtures/README.md` with 4 lines: source release and run ID, New York start time, the 3 tickers, and the sha256 of each source asset.
4. Tests in `tests/test_fixture.py`: every `^SPX` `contract_symbol` starts with `SPXW`; among `^SPX` rows with abs(ln(K / S)) ≤ 0.10 (S from the fixture UNDERLYING), more than 90% have bid > 0; CHAINS column order equals the schema.

### Step 1d.2: cleaning on the fixture (commit `step 1d.2: cleaning on the fixture`)

1. Run `clean_chain` on the fixture for all 3 tickers and commit `outputs/tables/clean_log_fixture.csv`.
2. Add a test that `clean_chain` on the committed fixture reproduces that file exactly.
3. Run `scripts/pull_snapshots.py` and the capture health builder. If the `snapshots` release does not exist yet, the manifest stays header-only and the health table has headers only; that is expected and is not a stop. The real health table is rebuilt in Section 2 once captures exist.

### Step 1d.3: last completed session (commit `step 1d.3: histories end at the last completed session`)

Exactly as 01c step 1c.3, items 1 to 4.

---

## D. Review evidence (append to `review/section_1.md` under `## Session 1d`)

1. The sha256 comparison from step 1d.1.
2. Fixture row counts per ticker and the timing check numbers for all 3 tickers.
3. `clean_log_fixture.csv` in full with the share of rows surviving per ticker.
4. Output of the 4 `last_completed_session` tests.
5. Full test output, the fresh-clone check, and CI status of the final commit.

Status file: `instructions/01d_section_1_complete.status.md`.
