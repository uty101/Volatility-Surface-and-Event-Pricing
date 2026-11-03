# instructions/07_section_7.md: Session 7 (Section 6 correction, surface cache, then Section 7: correlation and relative value)

Read `CLAUDE.md`, `PLAN.md` and every earlier instruction file first. This file beats them where they differ (rule 13). Build step 7.0, then every step of Section 7, in one session.

---

## A. Approval of Section 6

Section 6 is approved, with the correction in step 7.0. The reviewer checked it from a fresh clone at `31c8874`.

- **INTC.** The realised move matches the captured spot prices. The 2026-10-29 snapshot has INTC at 91.85, and the 2026-10-30 snapshot has it at 64.94 at 15:53 New York. The close-to-close move of 0.337 is real.
- **CVX hand check.** With n1 = 1 and n2 = 6 from 2026-10-29, v_d = (0.002457 − 0.000862) / 5 = 0.000319. Then v_e = θ1 − v_d × 0 = 0.000862, and M_t = √(2/π) × √0.000862 = 0.02343. That matches `ts_move`.

| Item | Decision |
|---|---|
| Status 1 (98 kinks, not 99) | Accepted. The stated rule decides, and CVX 2026-11-06 stays `ok`. |
| Status 2 (AMZN E1 is a `kink` slice) | Accepted. θ is w(0), and the kink sits at m, away from 0. |
| Status 3 (INTC) | Checked above. |
| Status 4 (pre-event snapshot) | **Corrected.** Convention 4.11 says the pre-event snapshot is the **last** snapshot on a session strictly before the window's end close and no later than the window's start session. It does not have to fall on the start session. So AAPL and PLTR (AMC 2026-11-02) and SHOP (BMO 2026-11-03) take the 2026-10-30 snapshot, with n1 and n2 counted from 2026-10-30. `pre_snap_date` already shows how old the snapshot is. Add a column `pre_snap_age`, the sessions between `pre_snap_date` and the window's start session, so a stale snapshot is visible in the table. |
| Status 5 (run 41622958662) | Print its log and say whether the 2026-11-03 assets landed. |
| Status 6 (155 min surface stage) | Step 7.0 adds a per-day cache, so only new days are fitted. |
| Status 7 | The owner may delete `C:\vs4` to `C:\vs6`. Claude Code does not. |

Record these in `decisions/section_6_review.md`.

---

## B. Steps

### Step 7.0 (commit `step 7.0: last pre-event snapshot, surface cache, new capture days`)

1. **Pre-event snapshot.** Apply the status 4 correction and add `pre_snap_age` to EVENTS, after `pre_snap_date`. Add a test: an AMC event on 2026-11-02 with snapshots on 2026-10-29 and 2026-10-30 takes 2026-10-30, with `pre_snap_age` = 1.
2. **Surface cache.** The surface stage writes each day's fits to `data/processed/surface/{day}.parquet`, stamped with a key. The key is the sha256 of `volsurf/svi.py`, `volsurf/ssvi.py`, the `[svi]` and `[surface]` config tables, and that day's IV file. A day whose key matches is read, not refitted. `--force` refits everything.
   - **Test:** a second run with nothing changed refits 0 days.
   - **Test:** editing the `[svi]` table refits all days.
3. **New days.** Run `pull_snapshots.py`. Then run the IV, surface, density and tails stages for every new capture day (2026-11-03 if it has landed, and any later day). Rebuild EVENTS and the summary, refreshing the prices first.
4. **Print:**
   - the EVENTS status counts against session 6;
   - every row whose status changed;
   - the surface stage runtime with the cache.

### Step 7.1: COR3M study

As in PLAN 7.1 and kickoff 5.8. The returns are daily log returns of the 9 sector SPDRs from `sectors.parquet` (adjusted closes). Day t is a COR3M date with sessions t+1 to t+63 all in the sector data.

The reviewer ran this regression independently on the committed data, with statsmodels OLS and HAC covariance (maxlags 63):

| n | first t | last t | intercept (NW se) | slope (NW se) | R² | mean gap (implied − realised) |
|---|---|---|---|---|---|---|
| 5,163 | 2006-01-03 | 2026-08-04 | 0.2862 (0.0371) | 0.7115 (0.0740) | 0.4373 | −0.1672 |

The section's numbers should match to 3 decimals. If they do not, print both and explain the difference. That is reported, not a stop.

**A note for the write-up.** The mean gap is negative, so implied sits below realised. That is the proxy, not a negative correlation risk premium. COR3M is the implied correlation of the 50 largest S&P 500 stocks. Sector ETFs are already diversified baskets, so they correlate with each other more than single stocks do. The tables and the write-up must say this next to the gap, and must not call the gap a correlation risk premium. The slope and R² are the usable result: how much of the next quarter's correlation the index options anticipate.

### Step 7.2: live implied correlation and RV screens

As in PLAN 7.2 and kickoff 5.8, with O-15 (a).

- **Implied side.** σ is each name's `atm_30` from SURFACE_DAILY. A name with a blank `atm_30` that day is left out and its weight is renormalised away. `covered_weight` reports what is left.
- **Weights.** They come from `data/raw/ssga/xlk_holdings_2026-10-28.csv`. Holdings are not refreshed in this session.
- **Realised side.** A day whose next 21 sessions are not all in the price data keeps its row with status `pending`. That is every day so far.
- **RV screen.** The z-score is blank, with status `below_min_days`, until a name has `rv_min_days` = 20 snapshot days. The group-median column fills from day 1.

---

## C. Review evidence (in `review/section_7.md`)

1. **Step 7.0:**
   - the test output;
   - the EVENTS status counts and every changed row;
   - the new days added, with their capture status;
   - runtime with the cache.
2. **Step 7.1:**
   - the regression row against the reviewer's;
   - a figure `outputs/figures/cor3m_vs_realised.png`, with implied and forward realised over time and the gap shaded.
3. **Step 7.2:**
   - `implied_corr_live.csv` in full;
   - the top and bottom 5 RV screen rows on the last day, by vol minus group median.
4. **Wrap-up:**
   - every figure, listed by path;
   - the fresh-clone check;
   - CI status.

Status file: `instructions/07_section_7.status.md`.
