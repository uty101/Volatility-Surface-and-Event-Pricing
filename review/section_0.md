# Review: Section 0

## Section

Section 0: plan, scaffolding and capture (kickoff Section 9, steps 0.0 to 0.2).

## Steps completed

- 0.0  a079d2a  step 0.0: plan and scaffolding
- 0.1  01c1dcd  step 0.1: snapshot capture
- 0.2  6a8de21  step 0.2: capture schedule (pushed to `main` at 2026-10-28 00:02 UTC; this push triggered the forced Actions run)

Step 0.2 item 4b (registering the local scheduled task) was refused by the permission system on the first attempt and registered on the owner's instruction afterwards: see Evidence, live check b.

## Evidence

All tables below are printed with `DataFrame.to_string()` from the files the runs wrote.

### Live check a: forced local run

Command, run on the owner's Windows machine at 2026-10-28 00:01 UTC (2026-10-27 20:01 New York, after the close):

```
.venv/Scripts/python scripts/snapshot.py --force --runner local --out data/local_capture --upload never
```

Script output (per-ticker lines and exit code; pandas deprecation warnings raised inside yfinance removed):

```
2026-10-28T00:01:35.531194+00:00 start runner=local ny=2026-10-27 20:01:35 forced=True tickers=32
^SPX   ok      rows= 12182 expiries= 46 failed=0   31.6s 
SPY    ok      rows=  7722 expiries= 26 failed=0   17.4s 
QQQ    ok      rows=  6671 expiries= 23 failed=0   16.7s 
XLK    ok      rows=  1461 expiries= 12 failed=0    8.4s 
XLE    ok      rows=  1331 expiries= 18 failed=0   11.9s 
XLF    ok      rows=   939 expiries= 18 failed=0   11.5s 
NVDA   ok      rows=  2808 expiries= 17 failed=0   12.5s 
AAPL   ok      rows=  1942 expiries= 15 failed=0   11.2s 
MSFT   ok      rows=  2342 expiries= 15 failed=0   11.2s 
AVGO   ok      rows=  2135 expiries= 17 failed=0   12.0s 
ORCL   ok      rows=  1486 expiries= 14 failed=0   10.6s 
AMD    ok      rows=  3890 expiries= 16 failed=0   12.8s 
CSCO   ok      rows=   816 expiries= 12 failed=0    9.9s 
CRM    ok      rows=  1065 expiries= 13 failed=0   10.0s 
IBM    ok      rows=  1192 expiries= 14 failed=0   10.7s 
PLTR   ok      rows=  1680 expiries= 14 failed=0   11.3s 
AMZN   ok      rows=  1613 expiries= 17 failed=0   13.0s 
META   ok      rows=  4393 expiries= 17 failed=0   13.8s 
GOOGL  ok      rows=  2397 expiries= 15 failed=0   11.3s 
TSLA   ok      rows=  3118 expiries= 16 failed=0   12.7s 
NFLX   ok      rows=  2631 expiries= 11 failed=0    9.0s 
JPM    ok      rows=   952 expiries= 11 failed=0    8.9s 
BAC    ok      rows=   726 expiries= 15 failed=0   11.0s 
XOM    ok      rows=   729 expiries= 13 failed=0   10.0s 
CVX    ok      rows=   643 expiries= 11 failed=0    9.3s 
UNH    ok      rows=  1117 expiries= 11 failed=0    8.8s 
WMT    ok      rows=   760 expiries= 11 failed=0    8.8s 
HD     ok      rows=  1030 expiries= 13 failed=0   10.2s 
DIS    ok      rows=   610 expiries= 12 failed=0    9.1s 
UBER   ok      rows=   660 expiries= 11 failed=0    8.7s 
SHOP   ok      rows=   916 expiries= 12 failed=0    9.6s 
ABNB   ok      rows=   653 expiries= 12 failed=0    9.7s 
2026-10-28T00:07:50.466810+00:00 done ok=32 partial=0 error=0 rows=72610
exit=0
```

UNDERLYING table, `data/local_capture/test_underlying_2026-10-27.csv`:

```
   ticker                          snap_utc        price             price_time_utc  n_expiries_listed  n_expiries_kept  n_rows  n_spx_am_dropped  error
0    ^SPX  2026-10-28 00:01:36.098839+00:00  7722.979980  2026-10-27 19:59:00+00:00                 53               46   12182              5356    NaN
1     SPY  2026-10-28 00:02:07.675955+00:00   769.719971  2026-10-27 19:59:00+00:00                 31               26    7722                 0    NaN
2     QQQ  2026-10-28 00:02:25.122507+00:00   721.239990  2026-10-27 19:59:00+00:00                 28               23    6671                 0    NaN
3     XLK  2026-10-28 00:02:41.779453+00:00   189.490005  2026-10-27 19:59:00+00:00                 17               12    1461                 0    NaN
4     XLE  2026-10-28 00:02:50.191972+00:00    68.230003  2026-10-27 19:59:00+00:00                 22               18    1331                 0    NaN
5     XLF  2026-10-28 00:03:02.069984+00:00    55.880001  2026-10-27 19:59:00+00:00                 22               18     939                 0    NaN
6    NVDA  2026-10-28 00:03:13.614028+00:00   217.919998  2026-10-27 19:59:00+00:00                 23               17    2808                 0    NaN
7    AAPL  2026-10-28 00:03:26.104933+00:00   347.079987  2026-10-27 19:59:00+00:00                 21               15    1942                 0    NaN
8    MSFT  2026-10-28 00:03:37.301420+00:00   531.599976  2026-10-27 19:59:00+00:00                 20               15    2342                 0    NaN
9    AVGO  2026-10-28 00:03:48.497474+00:00   342.450012  2026-10-27 19:59:00+00:00                 22               17    2135                 0    NaN
10   ORCL  2026-10-28 00:04:00.505013+00:00   130.559998  2026-10-27 19:59:00+00:00                 19               14    1486                 0    NaN
11    AMD  2026-10-28 00:04:11.139040+00:00   560.450012  2026-10-27 19:59:00+00:00                 21               16    3890                 0    NaN
12   CSCO  2026-10-28 00:04:23.950017+00:00   111.348999  2026-10-27 19:59:00+00:00                 17               12     816                 0    NaN
13    CRM  2026-10-28 00:04:33.821311+00:00   240.869995  2026-10-27 19:59:00+00:00                 17               13    1065                 0    NaN
14    IBM  2026-10-28 00:04:43.775702+00:00   250.240005  2026-10-27 19:59:00+00:00                 19               14    1192                 0    NaN
15   PLTR  2026-10-28 00:04:54.429213+00:00   198.750000  2026-10-27 19:59:00+00:00                 19               14    1680                 0    NaN
16   AMZN  2026-10-28 00:05:05.695631+00:00   253.149994  2026-10-27 19:59:00+00:00                 22               17    1613                 0    NaN
17   META  2026-10-28 00:05:18.741933+00:00   620.119995  2026-10-27 19:59:00+00:00                 22               17    4393                 0    NaN
18  GOOGL  2026-10-28 00:05:32.547406+00:00   320.559998  2026-10-27 19:59:00+00:00                 20               15    2397                 0    NaN
19   TSLA  2026-10-28 00:05:43.875046+00:00   407.459992  2026-10-27 19:59:00+00:00                 21               16    3118                 0    NaN
20   NFLX  2026-10-28 00:05:56.562011+00:00    62.520000  2026-10-27 19:59:00+00:00                 16               11    2631                 0    NaN
21    JPM  2026-10-28 00:06:05.597799+00:00   335.790008  2026-10-27 19:59:00+00:00                 15               11     952                 0    NaN
22    BAC  2026-10-28 00:06:14.509985+00:00    50.680000  2026-10-27 19:59:00+00:00                 19               15     726                 0    NaN
23    XOM  2026-10-28 00:06:25.490315+00:00   179.889999  2026-10-27 19:59:00+00:00                 17               13     729                 0    NaN
24    CVX  2026-10-28 00:06:35.444220+00:00   228.309998  2026-10-27 19:59:00+00:00                 14               11     643                 0    NaN
25    UNH  2026-10-28 00:06:44.783837+00:00   410.609985  2026-10-27 19:59:00+00:00                 15               11    1117                 0    NaN
26    WMT  2026-10-28 00:06:53.618803+00:00   119.300003  2026-10-27 19:59:00+00:00                 15               11     760                 0    NaN
27     HD  2026-10-28 00:07:02.424414+00:00   318.540008  2026-10-27 19:59:00+00:00                 18               13    1030                 0    NaN
28    DIS  2026-10-28 00:07:12.640297+00:00   110.239998  2026-10-27 19:59:00+00:00                 15               12     610                 0    NaN
29   UBER  2026-10-28 00:07:21.772715+00:00    65.779999  2026-10-27 19:59:00+00:00                 16               11     660                 0    NaN
30   SHOP  2026-10-28 00:07:30.487206+00:00   165.850006  2026-10-27 19:59:00+00:00                 16               12     916                 0    NaN
31   ABNB  2026-10-28 00:07:40.105241+00:00   168.820007  2026-10-27 19:59:00+00:00                 15               12     653                 0    NaN
```

Per ticker: CHAINS rows, rows with bid > 0, earliest and latest expiry, and distinct expiries in CHAINS, from `data/local_capture/test_chains_2026-10-27.parquet`:

```
         rows  bid_gt_0 earliest_expiry latest_expiry  n_expiries
ticker                                                           
^SPX    12182       620      2026-10-28    2027-09-30          38
SPY      7722      7067      2026-10-28    2027-09-30          26
QQQ      6671      6261      2026-10-28    2027-09-30          23
XLK      1461      1044      2026-10-30    2027-09-17          12
XLE      1331       774      2026-10-28    2027-09-30          18
XLF       939       724      2026-10-28    2027-09-30          18
NVDA     2808      2443      2026-10-28    2027-09-17          17
AAPL     1942      1609      2026-10-28    2027-09-17          15
MSFT     2342      2218      2026-10-30    2027-09-17          15
AVGO     2135      1902      2026-10-28    2027-09-17          17
ORCL     1486      1429      2026-10-30    2027-10-15          14
AMD      3890      3432      2026-10-28    2027-09-17          16
CSCO      816       666      2026-10-30    2027-09-17          12
CRM      1065       864      2026-10-30    2027-09-17          13
IBM      1192       990      2026-10-30    2027-09-17          14
PLTR     1680      1547      2026-10-30    2027-09-17          14
AMZN     1613      1524      2026-10-28    2027-09-17          17
META     4393      3753      2026-10-28    2027-09-17          17
GOOGL    2397      2148      2026-10-30    2027-09-17          15
TSLA     3118      2824      2026-10-28    2027-09-17          16
NFLX     2631      2021      2026-10-30    2027-09-17          11
JPM       952       703      2026-10-30    2027-09-17          11
BAC       726       573      2026-10-30    2027-09-17          15
XOM       729       574      2026-10-30    2027-09-17          13
CVX       643       494      2026-10-30    2027-09-17          11
UNH      1117       878      2026-10-30    2027-09-17          11
WMT       760       593      2026-10-30    2027-09-17          11
HD       1030       801      2026-10-30    2027-09-17          13
DIS       610       488      2026-10-30    2027-09-17          12
UBER      660       576      2026-10-30    2027-09-17          11
SHOP      916       794      2026-10-30    2027-09-17          12
ABNB      653       499      2026-10-30    2027-09-17          12
```

CHAINS columns and dtypes:

```
columns: ['snap_utc', 'ticker', 'expiry', 'kind', 'contract_symbol', 'strike', 'last_price', 'bid', 'ask', 'change', 'pct_change', 'volume', 'open_interest', 'yahoo_iv', 'in_the_money', 'last_trade_utc', 'contract_size', 'currency']
snap_utc           datetime64[us, UTC]
ticker                             str
expiry                             str
kind                               str
contract_symbol                    str
strike                         float64
last_price                     float64
bid                            float64
ask                            float64
change                         float64
pct_change                     float64
volume                         float64
open_interest                  float64
yahoo_iv                       float64
in_the_money                      bool
last_trade_utc     datetime64[us, UTC]
contract_size                      str
currency                           str
```

```
snap_utc range: 2026-10-28 00:01:37.574846+00:00 2026-10-28 00:07:47.913368+00:00
```

What these rows show:

- 32 of 32 underlyings have status ok; 72,610 CHAINS rows in total; exit code 0.
- `^SPX`: only 620 of 12,182 rows have bid > 0. The run was at 20:01 New York, after the close, which is the zero-bid problem Correction 5 describes. The other underlyings keep most of their bids after the close. Scheduled runs are at 15:30 New York.
- `^SPX`: `filter_expiries` kept 46 expiries, but only 38 appear in CHAINS. After `keep_spxw` the other 8 had only AM-settled `SPX` contracts; 5,356 rows were dropped and counted in `n_spx_am_dropped`. Every `^SPX` contract symbol in CHAINS starts with `SPXW`.

EARNINGS timing counts, `data/local_capture/test_earnings_2026-10-27.csv` (26 single names):

```
timing
AMC        397
BMO        236
unknown     16
    snap_date ticker                event_ts_ny   timing  eps_estimate  reported_eps  surprise_pct
0  2026-10-27   NVDA  2026-11-17 15:00:00-05:00  unknown          2.47           NaN           NaN
1  2026-10-27   NVDA  2026-08-26 16:00:00-04:00      AMC          2.09          2.22          6.16
2  2026-10-27   NVDA  2026-05-20 16:00:00-04:00      AMC          1.77          1.87          5.54
3  2026-10-27   NVDA  2026-02-25 16:00:00-05:00      AMC          1.54          1.62          5.32
4  2026-10-27   NVDA  2025-11-19 16:00:00-05:00      AMC          1.26          1.30          3.46
5  2026-10-27   NVDA  2025-08-27 16:00:00-04:00      AMC          1.01          1.05          4.10
```

Every row classified `unknown`:

```
      snap_date ticker                event_ts_ny   timing  eps_estimate  reported_eps  surprise_pct
0    2026-10-27   NVDA  2026-11-17 15:00:00-05:00  unknown          2.47           NaN           NaN
25   2026-10-27   AAPL  2026-11-02 15:00:00-05:00  unknown          1.98           NaN           NaN
75   2026-10-27   AVGO  2026-12-09 15:00:00-05:00  unknown          3.84           NaN           NaN
100  2026-10-27   ORCL  2026-12-14 15:00:00-05:00  unknown          1.89           NaN           NaN
125  2026-10-27    AMD  2026-11-03 15:00:00-05:00  unknown          1.93           NaN           NaN
150  2026-10-27   CSCO  2026-11-12 15:00:00-05:00  unknown          1.32           NaN           NaN
175  2026-10-27    CRM  2026-12-02 15:00:00-05:00  unknown          3.45           NaN           NaN
200  2026-10-27    IBM  2027-01-27 15:00:00-05:00  unknown          4.63           NaN           NaN
225  2026-10-27   PLTR  2026-11-02 15:00:00-05:00  unknown          0.41           NaN           NaN
259  2026-10-27   AMZN  2024-08-01 12:00:00-04:00  unknown          1.02          1.26         23.76
275  2026-10-27   META  2027-01-27 15:00:00-05:00  unknown          8.34           NaN           NaN
325  2026-10-27   TSLA  2027-01-27 15:00:00-05:00  unknown          0.50           NaN           NaN
346  2026-10-27   TSLA  2021-10-20 15:00:00-04:00  unknown          0.54          0.62         15.22
350  2026-10-27   NFLX  2027-01-19 15:00:00-05:00  unknown          0.68           NaN           NaN
423  2026-10-27    BAC  2021-04-15 12:00:00-04:00  unknown          0.65          0.86         32.86
625  2026-10-27   ABNB  2026-11-05 15:00:00-05:00  unknown          2.85           NaN           NaN
```

Every upcoming (not yet reported) event is served with time 15:00 New York, which `classify_timing` maps to `unknown` under Convention 4.11. It looks like Yahoo's placeholder for an unconfirmed time. Until an override or a later snapshot shows a confirmed time, the event study cannot classify these events. This bears on O-12.

### Live check b: local scheduled task

`gh auth status` on this machine:

```
github.com
  ✓ Logged in to github.com account uty101 (keyring)
  - Active account: true
  - Git operations protocol: https
  - Token scopes: 'gist', 'read:org', 'repo', 'workflow'
```

`gh` is installed (2.101.0) and authenticated, so the kickoff says to register the task. The first attempt to run `scripts/windows/register_snapshot_task.ps1` was refused by Claude Code's permission system and was not worked around. The owner then told Claude Code to register it, and the second run succeeded. The machine's time zone is `GMT Standard Time` (London), which the script checks before registering.

```
Registered volsurf-snapshot at 19:30, 20:30 London, Monday to Friday, in C:\Utkarsh\10. Quant Projects\7) Volatility Surface and Event Pricing\Volatility-Surface-and-Event-Pricing
```

`Get-ScheduledTask volsurf-snapshot | Format-List`:

```
Actions            : {MSFT_TaskExecAction}
Description        : Backup daily option chain capture for Volatility-Surface-and-Event-Pricing
Principal          : MSFT_TaskPrincipal2
Settings           : MSFT_TaskSettings3
State              : Ready
TaskName           : volsurf-snapshot
TaskPath           : \
Triggers           : {MSFT_TaskWeeklyTrigger, MSFT_TaskWeeklyTrigger}
URI                : \volsurf-snapshot
```

`Get-ScheduledTaskInfo volsurf-snapshot`, then triggers, action, settings and principal:

```
NextRunTime    : 28/10/2026 19:30:00
LastRunTime    : 30/11/1999 00:00:00
LastTaskResult : 267011

StartBoundary             DaysOfWeek Enabled
-------------             ---------- -------
2026-10-28T19:30:00+00:00         62    True
2026-10-28T20:30:00+00:00         62    True

Execute          : "C:\Utkarsh\10. Quant Projects\7) Volatility Surface and Event Pricing\Volatility-Surface-and-Event-Pricing\.venv\Scripts\python.exe"
Arguments        : scripts\snapshot.py --runner local --out data\local_capture --upload if-missing
WorkingDirectory : C:\Utkarsh\10. Quant Projects\7) Volatility Surface and Event Pricing\Volatility-Surface-and-Event-Pricing

StartWhenAvailable         : True
DisallowStartIfOnBatteries : False
StopIfGoingOnBatteries     : False

UserId    : astha
LogonType : Interactive
```

DaysOfWeek 62 is the bitmask for Monday to Friday. `LastTaskResult` 267011 means the task has not run yet. Both StartBoundary values carry a `+00:00` offset, so Task Scheduler pins the triggers to UTC, not to London wall-clock time. These are the same instants as the Actions crons (19:30 and 20:30 UTC), so 1 of them falls at 15:30 New York on both sides of the US clock change. When the UK moves to BST on 2027-03-28 they will fire at 20:30 and 21:30 London time, not at the configured `local_task_times_london`. This is reported, not changed (rule 15).

### Live check c: Actions run triggered by the push

`gh run list` showed run 40606139956 (workflow `snapshot`, event `push`, commit `step 0.2: capture schedule`). Conclusion: **success** in 6m11s. The `ci` run on the same push (40606139930) also succeeded, in 14s (ruff and 7 tests on ubuntu-latest).

Per-ticker status lines from the run's `Capture` step:

```
2026-10-28T00:02:30.275473+00:00 start runner=actions ny=2026-10-27 20:02:30 forced=True tickers=32
^SPX   ok      rows= 11906 expiries= 45 failed=0   29.0s 
SPY    ok      rows=  7720 expiries= 25 failed=0   16.3s 
QQQ    ok      rows=  6669 expiries= 23 failed=0   14.9s 
XLK    ok      rows=  1461 expiries= 12 failed=0    8.2s 
XLE    ok      rows=  1331 expiries= 18 failed=0   11.6s 
XLF    ok      rows=   939 expiries= 18 failed=0   11.5s 
NVDA   ok      rows=  2808 expiries= 17 failed=0   12.3s 
AAPL   ok      rows=  1942 expiries= 15 failed=0   10.9s 
MSFT   ok      rows=  2342 expiries= 15 failed=0   10.9s 
AVGO   ok      rows=  2135 expiries= 17 failed=0   11.9s 
ORCL   ok      rows=  1486 expiries= 14 failed=0   10.3s 
AMD    ok      rows=  3844 expiries= 16 failed=0   11.7s 
CSCO   ok      rows=   813 expiries= 12 failed=0    9.2s 
CRM    ok      rows=  1065 expiries= 13 failed=0    9.6s 
IBM    ok      rows=  1192 expiries= 14 failed=0   10.4s 
PLTR   ok      rows=  1680 expiries= 14 failed=0   10.4s 
AMZN   ok      rows=  1613 expiries= 17 failed=0   11.8s 
META   ok      rows=  4393 expiries= 17 failed=0   12.4s 
GOOGL  ok      rows=  2384 expiries= 15 failed=0   11.0s 
TSLA   ok      rows=  3110 expiries= 16 failed=0   11.6s 
NFLX   ok      rows=  2638 expiries= 11 failed=0    9.0s 
JPM    ok      rows=   951 expiries= 11 failed=0    8.6s 
BAC    ok      rows=   726 expiries= 15 failed=0   10.8s 
XOM    ok      rows=   717 expiries= 13 failed=0    9.8s 
CVX    ok      rows=   643 expiries= 11 failed=0    8.6s 
UNH    ok      rows=  1103 expiries= 11 failed=0    8.8s 
WMT    ok      rows=   760 expiries= 11 failed=0    8.6s 
HD     ok      rows=  1030 expiries= 13 failed=0    9.8s 
DIS    ok      rows=   608 expiries= 12 failed=0    9.2s 
UBER   ok      rows=   660 expiries= 11 failed=0    8.6s 
SHOP   ok      rows=   916 expiries= 12 failed=0    9.0s 
ABNB   ok      rows=   653 expiries= 12 failed=0    9.1s 
2026-10-28T00:08:26.476115+00:00 done ok=32 partial=0 error=0 rows=72238
uploaded 4 files to release snapshots-test
```

Yahoo did not refuse requests from Actions: 32 of 32 ok, 72,238 rows.

Assets of release `snapshots-test` (`gh release view snapshots-test --json assets`):

```
test_chains_2026-10-27.parquet	2371196
test_earnings_2026-10-27.csv	39457
test_snaplog_2026-10-27.json	11865
test_underlying_2026-10-27.csv	2952
```

Workflow artifact: `snap-40606139956`, 1,990,580 bytes, expires 2026-11-04T00:08:29Z. The release `snapshots` does not exist yet (`gh release view snapshots` returns `release not found`); the first scheduled run creates it.

Expiry listings differed between the local and Actions runs, which started 55 seconds apart:

```
^SPX: local only ['2026-12-10'], actions only []

SPY: local only ['2027-04-30'], actions only []
```

`^SPX` listed 53 expiries locally against 52 on Actions, and SPY 31 against 30. Yahoo's `options` list is not stable from one request to the next. On a scheduled day only one run's assets are kept, so an expiry can be missing from a day's capture without any error being logged.

## Tests run

```
.venv/Scripts/pytest -p socket --disable-socket -q
```

```
.......                                                                  [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:894
  C:\Utkarsh\10. Quant Projects\7) Volatility Surface and Event Pricing\Volatility-Surface-and-Event-Pricing\.venv\Lib\site-packages\_pytest\config\__init__.py:894: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

tests/test_snapshots.py::test_is_session
tests/test_snapshots.py::test_is_session
tests/test_snapshots.py::test_is_session
tests/test_snapshots.py::test_is_session
  C:\Utkarsh\10. Quant Projects\7) Volatility Surface and Event Pricing\Volatility-Surface-and-Event-Pricing\.venv\Lib\site-packages\pandas\core\series.py:848: Pandas4Warning: Series.values returning an ndarray that drops timezone information for DatetimeTZDtype is deprecated. In a future version, this will return the underlying DatetimeArray instead. Use 'Series.dt.tz_convert(None).to_numpy()' to get a NumPy array of UTC values, or 'Series.array' to get the ExtensionArray.
  See https://pandas.pydata.org/docs/dev/whatsnew/v3.1.0.html#whatsnew-310-deprecations-values for more details.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
7 passed, 5 warnings in 1.10s
exit=0
```

The 7 tests are `tests/test_placeholder.py::test_package_imports` and the 6 tests in `tests/test_snapshots.py` named in step 0.1. `ruff check .` prints `All checks passed!` (ruff 0.17.3 from the lock).

## Fresh-clone check

Not required for Section 0 (rule 12 starts at Section 1). The `ci` workflow on the pushed commit does the equivalent: it builds a clean venv from `requirements-lock.txt`, runs `pip install -e . --no-deps`, `ruff check .` and `pytest -p socket --disable-socket -q`, and it passed (run 40606139930).

## Runtime per step

- 0.0: lock compile and venv build about 1 minute.
- 0.1: test suite 1 to 5 seconds.
- 0.2: local forced capture 6m15s (00:01:35 to 00:07:50 UTC); Actions snapshot job 6m11s; Actions ci job 14s.

## Deviations from PLAN.md

- `tests/test_placeholder.py` was added in step 0.0. Kickoff step 0.0 does not list it, but WORKFLOW.md Stage C asks for a placeholder test, and without one the CI job has no tests to run.
- O-22 records 9 capture interpretations: window bounds, CHAINS `snap_utc`, ticker status, retries, the skip log, the upload failure exit code, UNDERLYING `snap_utc`, earnings failures and the task's power settings. Option (a) of each is what runs now. They were implemented, not left open, because capture had to start on 2026-10-28, and rule 15 means only an instruction file can change them.
- `CLAUDE.md` holds Sections 0, 4 and 6 verbatim and an empty `## Amendments` heading, with no title line above them.

## Not verified

- The local task has not fired yet. Its first run is 2026-10-28 19:30 UTC, at the same instant as the first Actions cron.
- No scheduled (non-forced) run has happened yet. The first is due at 2026-10-28 19:30 UTC (15:30 New York). The 20:30 UTC cron that day falls at 16:30 New York; by the time the runner reaches the window check it should be past 16:30:00 and log a skip.
- The `--upload if-missing` path has not been run.
- The share of `^SPX` rows with bid > 0 inside the session is not yet known; this run was after the close.

## Open questions

All are in `decisions/OPEN.md` with 2 options each: O-1 to O-21, O-23 and O-24 from writing PLAN.md, and O-22 (capture interpretations, 9 parts) from steps 0.1 and 0.2. Two observations from the live runs bear on open items:

- O-12: upcoming earnings rows carry a 15:00 placeholder time and classify as `unknown` (rows above).
- O-5: Yahoo's expiry listing changes between requests (rows above), so an accepted day can be missing an expiry.

## Files changed

PLAN.md, CLAUDE.md, config.toml, README.md, pyproject.toml, requirements-lock.txt, .gitattributes, .gitignore, .github/workflows/ci.yml, .github/workflows/snapshot.yml, review/TEMPLATE.md, review/section_0.md, decisions/OPEN.md, decisions/data_and_history.md, decisions/american_options.md, decisions/capture.md, decisions/dropped_scope.md, docs/CONVENTIONS_RESOLVED.md, volsurf/__init__.py, volsurf/snapshots.py, scripts/snapshot.py, scripts/windows/register_snapshot_task.ps1, scripts/windows/unregister_snapshot_task.ps1, tests/test_placeholder.py, tests/test_snapshots.py, data/manual/earnings_overrides.csv, data/manual/macro_events.csv, instructions/00_kickoff.status.md, and `.gitkeep` in data/raw, outputs/tables, outputs/figures, outputs/reports, review and tests/fixtures.

## Reviewer reads

1. `instructions/00_kickoff.status.md`
2. This file: Evidence and Not verified
3. `decisions/OPEN.md`
4. `scripts/snapshot.py` and `volsurf/snapshots.py`
5. `.github/workflows/snapshot.yml`
6. `PLAN.md`
7. Release `snapshots-test` assets
