# Review: Section 1

## Section

Section 1: Long history data and the snapshot loader (`PLAN.md` steps 1.0 to 1.4, with instruction 01). Per instruction 01, everything that needs the 2026-10-28 capture (the fixture in 1.2, the fixture-day CLEAN_LOG and the real capture health table in 1.4) moves to instruction 01b.

## Steps completed

- 1.0  494de82  step 1.0: upload only when better (reached `origin/main` at 2026-10-28 12:40:06 UTC)
- 1.1  ff312dd  step 1.1: long history pull
- 1.2  892c547  step 1.2: snapshot download (fixture deferred to 01b)
- 1.3  2557f5b  step 1.3: loader and cleaning
- 1.4  b1be0ec  step 1.4: capture health
- part B  fcf3ad4  section 1: review decisions recorded (`decisions/section_1_review.md`, `decisions/OPEN.md`)

## Evidence

### D1. Step 1.0: the 4 new tests and the forced Actions run

`.venv/Scripts/pytest -p socket --disable-socket -v tests/test_snapshots.py -k should_upload`:

```
tests/test_snapshots.py::test_should_upload_no_existing_asset PASSED     [ 25%]
tests/test_snapshots.py::test_should_upload_more_tickers_ok PASSED       [ 50%]
tests/test_snapshots.py::test_should_upload_tie_keeps_existing PASSED    [ 75%]
tests/test_snapshots.py::test_should_upload_fewer_tickers_ok PASSED      [100%]
================= 4 passed, 6 deselected, 1 warning in 2.38s ==================
```

The push of 494de82 started snapshot run 40689704608 (event `push`, so `--force` with `--upload better`; conclusion **success**, 6m41s). Last 3 lines of its Capture step log:

```
2026-10-28T12:46:41.7765788Z ABNB   ok      rows=   653 expiries= 12 failed=0    9.8s
2026-10-28T12:46:41.9857945Z 2026-10-28T12:46:41.981653+00:00 done ok=32 partial=0 error=0 rows=70424
2026-10-28T12:46:44.2902231Z uploaded 4 files to release snapshots-test
```

It uploaded because `snapshots-test` had no `test_snaplog_2026-10-28.json` yet (`existing_n_ok = None`). The release now holds (`gh release view snapshots-test --json assets`: name, size, updatedAt):

```
test_chains_2026-10-27.parquet	2371196	2026-10-28T00:08:28Z
test_chains_2026-10-28.parquet	2054673	2026-10-28T12:46:44Z
test_earnings_2026-10-27.csv	39457	2026-10-28T00:08:28Z
test_earnings_2026-10-28.csv	39457	2026-10-28T12:46:43Z
test_snaplog_2026-10-27.json	11865	2026-10-28T00:08:28Z
test_snaplog_2026-10-28.json	11868	2026-10-28T12:46:43Z
test_underlying_2026-10-27.csv	2952	2026-10-28T00:08:28Z
test_underlying_2026-10-28.csv	2952	2026-10-28T12:46:43Z
```

The other branches of `upload(..., "better", ...)` were exercised against a fake `gh` before the commit (a scratch check, not committed). Its output, one line per case (case, return value, whether `gh release upload` was called):

```
missing  uploaded 2 files to release t   uploaded=True
tie      skipped: existing n_ok=31 >= new n_ok=31   uploaded=False
better   uploaded 2 files to release t   uploaded=True
worse    skipped: existing n_ok=32 >= new n_ok=10   uploaded=False
dlfail   RAISED gh release download snaplog_d.json failed: HTTP 502   uploaded=False
```

A raised error in `upload` becomes `upload failed: ...` in the log and exit code 2 in `main`, with the files kept, as before.

### D2. `MANIFEST.json` and the first and last 3 rows of every committed raw file

#### `data/raw/MANIFEST.json`

```
{
  "stages": {
    "cboe": {
      "pulled_utc": "2026-10-28T12:44:27.952058+00:00",
      "versions": {
        "python": "3.12.13",
        "yfinance": "1.7.0",
        "pandas": "3.1.0",
        "numpy": "2.5.4",
        "pyarrow": "26.0.0",
        "openpyxl": "3.1.5",
        "requests": "2.34.2",
        "curl_cffi": "0.17.0"
      }
    },
    "fred": {
      "pulled_utc": "2026-10-28T12:44:35.693989+00:00",
      "versions": {
        "python": "3.12.13",
        "yfinance": "1.7.0",
        "pandas": "3.1.0",
        "numpy": "2.5.4",
        "pyarrow": "26.0.0",
        "openpyxl": "3.1.5",
        "requests": "2.34.2",
        "curl_cffi": "0.17.0"
      }
    },
    "prices": {
      "pulled_utc": "2026-10-28T12:44:47.167681+00:00",
      "versions": {
        "python": "3.12.13",
        "yfinance": "1.7.0",
        "pandas": "3.1.0",
        "numpy": "2.5.4",
        "pyarrow": "26.0.0",
        "openpyxl": "3.1.5",
        "requests": "2.34.2",
        "curl_cffi": "0.17.0"
      }
    },
    "ssga": {
      "pulled_utc": "2026-10-28T12:44:41.430717+00:00",
      "versions": {
        "python": "3.12.13",
        "yfinance": "1.7.0",
        "pandas": "3.1.0",
        "numpy": "2.5.4",
        "pyarrow": "26.0.0",
        "openpyxl": "3.1.5",
        "requests": "2.34.2",
        "curl_cffi": "0.17.0"
      }
    }
  },
  "files": {
    "cboe/BXM.csv": {
      "stage": "cboe",
      "url": "https://cdn-api.cboe.com/api/global/delayed_quotes/charts/historical/_BXM.json",
      "pulled_utc": "2026-10-28T12:44:27.952058+00:00",
      "rows": 6187,
      "first_date": "2002-03-22",
      "last_date": "2026-10-27",
      "sha256": "43282fc1632590be68d7abb138606dd07bee45b41b3c90c19c35fac73a2042fa"
    },
    "cboe/COR3M.csv": {
      "stage": "cboe",
      "url": "https://cdn-api.cboe.com/api/global/delayed_quotes/charts/historical/_COR3M.json",
      "pulled_utc": "2026-10-28T12:44:27.952058+00:00",
      "rows": 5222,
      "first_date": "2006-01-03",
      "last_date": "2026-10-27",
      "sha256": "55ed15be9d8a3bcb56b7888f9d73e5b92f0345355bd440b380f3e18c7cde26dd"
    },
    "cboe/PUT.csv": {
      "stage": "cboe",
      "url": "https://cdn-api.cboe.com/api/global/delayed_quotes/charts/historical/_PUT.json",
      "pulled_utc": "2026-10-28T12:44:27.952058+00:00",
      "rows": 4993,
      "first_date": "1991-03-04",
      "last_date": "2026-10-27",
      "sha256": "d98edca5a804a45adca627599606d2f671bff54fe2c2c3f1f566b7aca5835a39"
    },
    "cboe/VIX.csv": {
      "stage": "cboe",
      "url": "https://cdn-api.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv",
      "pulled_utc": "2026-10-28T12:44:27.952058+00:00",
      "rows": 9303,
      "first_date": "1990-01-02",
      "last_date": "2026-10-27",
      "sha256": "6da7f149324ec456c80f6d7e96c90b5d3bcaa3d0f6a4274f7840542db9809265"
    },
    "cboe/VIX3M.csv": {
      "stage": "cboe",
      "url": "https://cdn-api.cboe.com/api/global/us_indices/daily_prices/VIX3M_History.csv",
      "pulled_utc": "2026-10-28T12:44:27.952058+00:00",
      "rows": 4303,
      "first_date": "2009-09-18",
      "last_date": "2026-10-27",
      "sha256": "b670475f9250d54f36b820ecab5c1d0c141d45287ad77e6be4cca9ea70114469"
    },
    "cboe/VIX6M.csv": {
      "stage": "cboe",
      "url": "https://cdn-api.cboe.com/api/global/us_indices/daily_prices/VIX6M_History.csv",
      "pulled_utc": "2026-10-28T12:44:27.952058+00:00",
      "rows": 4735,
      "first_date": "2008-01-02",
      "last_date": "2026-10-27",
      "sha256": "53b9583bcc7bc49c9584fa91bc2f8201c2624170fe39cd605b17db53b06e74de"
    },
    "cboe/VIX9D.csv": {
      "stage": "cboe",
      "url": "https://cdn-api.cboe.com/api/global/us_indices/daily_prices/VIX9D_History.csv",
      "pulled_utc": "2026-10-28T12:44:27.952058+00:00",
      "rows": 3977,
      "first_date": "2011-01-04",
      "last_date": "2026-10-27",
      "sha256": "1d730a489e704a9d85b049de5d33ee8b2978c1d77525e0f567e0bf3d1427201f"
    },
    "fred/DGS1.csv": {
      "stage": "fred",
      "url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS1",
      "pulled_utc": "2026-10-28T12:44:35.693989+00:00",
      "rows": 16910,
      "first_date": "1962-01-02",
      "last_date": "2026-10-26",
      "sha256": "42d24ef4c26af3e4921091374442e60c27c8cce167718604c6f5ed3432048046"
    },
    "fred/DGS1MO.csv": {
      "stage": "fred",
      "url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS1MO",
      "pulled_utc": "2026-10-28T12:44:35.693989+00:00",
      "rows": 6585,
      "first_date": "2001-07-31",
      "last_date": "2026-10-26",
      "sha256": "bc20f03a3b1bdb3b1638c9187a7ccf477819ec72d583a85293512c0c0bb09c6d"
    },
    "fred/DGS3MO.csv": {
      "stage": "fred",
      "url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS3MO",
      "pulled_utc": "2026-10-28T12:44:35.693989+00:00",
      "rows": 11780,
      "first_date": "1981-09-01",
      "last_date": "2026-10-26",
      "sha256": "bb51057fbbc393f6ec082162142129e46191376dc153dd1173cee5e6fdaf9fab"
    },
    "fred/DGS6MO.csv": {
      "stage": "fred",
      "url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS6MO",
      "pulled_utc": "2026-10-28T12:44:35.693989+00:00",
      "rows": 11780,
      "first_date": "1981-09-01",
      "last_date": "2026-10-26",
      "sha256": "274a1c7c904ce86f371ae05c684abdf90ac0a60f6e1e224813fcf087733a2b92"
    },
    "fred/DTB3.csv": {
      "stage": "fred",
      "url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTB3",
      "pulled_utc": "2026-10-28T12:44:35.693989+00:00",
      "rows": 18996,
      "first_date": "1954-01-04",
      "last_date": "2026-10-26",
      "sha256": "ea83d928c3d15fbd7376ba76b87423b1a536e465846ca64e2f4d57f6a3577e0f"
    },
    "prices/close.parquet": {
      "stage": "prices",
      "url": "yfinance Ticker(t).history(start=1989-12-01, end=2026-10-29, auto_adjust=False, actions=True)",
      "pulled_utc": "2026-10-28T12:44:47.167681+00:00",
      "rows": 9293,
      "first_date": "1989-12-01",
      "last_date": "2026-10-27",
      "sha256": "1a86d3b1f6aca7d9416b6b72c449763943c49b9848df7f7e96ffcc9438df23e6"
    },
    "prices/dividends.csv": {
      "stage": "prices",
      "url": "yfinance Ticker(t).history(start=1989-12-01, end=2026-10-29, auto_adjust=False, actions=True)",
      "pulled_utc": "2026-10-28T12:44:47.167681+00:00",
      "rows": 2181,
      "first_date": "1989-12-05",
      "last_date": "2026-10-09",
      "sha256": "e6be77d5f5a59e2fae5afe95f0f851de1b215630ea82566370a54cc0f3fd2ea1"
    },
    "prices/index.parquet": {
      "stage": "prices",
      "url": "yfinance Ticker(t).history(start=1989-12-01, end=2026-10-29, auto_adjust=False, actions=True)",
      "pulled_utc": "2026-10-28T12:44:47.167681+00:00",
      "rows": 9293,
      "first_date": "1989-12-01",
      "last_date": "2026-10-27",
      "sha256": "0be7e5e7de69456bb8fb7ac79219e5c7a5d1fb2922f3d1df6e159d5b693f09e0"
    },
    "prices/sectors.parquet": {
      "stage": "prices",
      "url": "yfinance Ticker(t).history(start=1989-12-01, end=2026-10-29, auto_adjust=False, actions=True)",
      "pulled_utc": "2026-10-28T12:44:47.167681+00:00",
      "rows": 7004,
      "first_date": "1998-12-22",
      "last_date": "2026-10-27",
      "sha256": "7eddf4f226fedcc7ee9974e0bbb7826ae92750fa1b77917a825c2efc91fa7b18"
    },
    "ssga/xlk_holdings_2026-10-28.csv": {
      "stage": "ssga",
      "url": "https://www.ssga.com/us/en/intermediary/library-content/products/fund-data/etfs/us/holdings-daily-us-en-xlk.xlsx",
      "pulled_utc": "2026-10-28T12:44:41.430717+00:00",
      "rows": 76,
      "first_date": "2026-10-27",
      "last_date": "2026-10-27",
      "sha256": "f911bdede086dbb8c07321934fc20ee1db04ee2241c97548378911cd66914dd8"
    },
    "ssga/xlk_holdings_2026-10-28.xlsx": {
      "stage": "ssga",
      "url": "https://www.ssga.com/us/en/intermediary/library-content/products/fund-data/etfs/us/holdings-daily-us-en-xlk.xlsx",
      "pulled_utc": "2026-10-28T12:44:41.430717+00:00",
      "rows": 181,
      "first_date": null,
      "last_date": null,
      "sha256": "a991b135e66a27c4b5e8ac224a7c3a3c7e3a1c47f322bd1b3152c216e15acdef"
    }
  }
}
```

#### `cboe/BXM.csv` (6187 rows): first and last 3

```
            date    close
0     2002-03-22    584.3
1     2002-03-25   578.48
2     2002-03-26   581.43
6184  2026-10-23  2550.53
6185  2026-10-26  2563.55
6186  2026-10-27  2573.02
```

#### `cboe/COR3M.csv` (5222 rows): first and last 3

```
            date  close
0     2006-01-03  31.34
1     2006-01-04  31.12
2     2006-01-05  30.92
5219  2026-10-23     15
5220  2026-10-26  13.95
5221  2026-10-27  13.49
```

#### `cboe/PUT.csv` (4993 rows): first and last 3

```
            date    close
0     1991-03-04    153.5
1     1991-08-07   163.67
2     1994-09-27   234.31
4990  2026-10-23  3686.47
4991  2026-10-26  3706.24
4992  2026-10-27  3718.37
```

#### `cboe/VIX.csv` (9303 rows): first and last 3

```
            DATE       OPEN       HIGH        LOW      CLOSE
0     01/02/1990  17.240000  17.240000  17.240000  17.240000
1     01/03/1990  18.190000  18.190000  18.190000  18.190000
2     01/04/1990  19.220000  19.220000  19.220000  19.220000
9300  10/23/2026  19.180000  20.660000  18.870000  19.450000
9301  10/26/2026  19.660000  19.840000  17.790000  18.390000
9302  10/27/2026  18.430000  18.550000  17.430000  17.520000
```

#### `cboe/VIX3M.csv` (4303 rows): first and last 3

```
            DATE       OPEN       HIGH        LOW      CLOSE
0     09/18/2009  25.910000  26.660000  25.910000  26.540000
1     09/21/2009  26.960000  27.240000  26.170000  26.230000
2     09/22/2009  25.970000  26.210000  25.650000  25.690000
4300  10/23/2026  20.940000  21.380000  20.270000  20.480000
4301  10/26/2026  20.100000  20.220000  19.550000  19.940000
4302  10/27/2026  19.650000  19.870000  19.440000  19.570000
```

#### `cboe/VIX6M.csv` (4735 rows): first and last 3

```
            DATE       OPEN       HIGH        LOW      CLOSE
0     01/02/2008  24.360000  24.360000  24.360000  24.360000
1     01/03/2008  23.750000  23.750000  23.750000  23.750000
2     01/04/2008  24.500000  24.500000  24.500000  24.500000
4732  10/23/2026  22.260000  22.560000  21.780000  21.960000
4733  10/26/2026  21.740000  21.860000  21.350000  21.630000
4734  10/27/2026  21.440000  21.640000  21.290000  21.420000
```

#### `cboe/VIX9D.csv` (3977 rows): first and last 3

```
            DATE       OPEN       HIGH        LOW      CLOSE
0     01/04/2011  16.060000  16.060000  16.060000  16.060000
1     01/05/2011  15.570000  15.570000  15.570000  15.570000
2     01/06/2011  15.710000  15.710000  15.710000  15.710000
3974  10/23/2026  20.120000  20.710000  18.530000  18.700000
3975  10/26/2026  19.040000  19.290000  17.380000  17.920000
3976  10/27/2026  17.290000  17.690000  16.600000  16.650000
```

#### `fred/DGS1.csv` (16910 rows): first and last 3

```
      observation_date  DGS1
0           1962-01-02  3.22
1           1962-01-03  3.24
2           1962-01-04  3.24
16907       2026-10-22  4.41
16908       2026-10-23  4.44
16909       2026-10-26  4.47
```

#### `fred/DGS1MO.csv` (6585 rows): first and last 3

```
     observation_date DGS1MO
0          2001-07-31   3.67
1          2001-08-01   3.65
2          2001-08-02   3.65
6582       2026-10-22   4.11
6583       2026-10-23   4.11
6584       2026-10-26   4.11
```

#### `fred/DGS3MO.csv` (11780 rows): first and last 3

```
      observation_date DGS3MO
0           1981-09-01  17.01
1           1981-09-02  16.65
2           1981-09-03  16.96
11777       2026-10-22   4.22
11778       2026-10-23   4.22
11779       2026-10-26   4.22
```

#### `fred/DGS6MO.csv` (11780 rows): first and last 3

```
      observation_date DGS6MO
0           1981-09-01  17.17
1           1981-09-02  17.32
2           1981-09-03  17.42
11777       2026-10-22   4.29
11778       2026-10-23   4.30
11779       2026-10-26   4.35
```

#### `fred/DTB3.csv` (18996 rows): first and last 3

```
      observation_date  DTB3
0           1954-01-04  1.33
1           1954-01-05  1.28
2           1954-01-06  1.28
18993       2026-10-22  4.04
18994       2026-10-23  4.04
18995       2026-10-26  4.05
```

#### `prices/dividends.csv` (2181 rows): first and last 3

```
            date ticker dividend
0     1993-03-19    SPY    0.213
1     1993-06-18    SPY    0.318
2     1993-09-17    SPY    0.286
2178  2025-06-24    DIS      0.5
2179  2025-12-15    DIS     0.75
2180  2026-06-30    DIS     0.75
```

#### `ssga/xlk_holdings_2026-10-28.csv` (76 rows): first and last 3

```
   ticker                     name      weight    shares  as_of_date
0    NVDA              NVIDIA CORP   0.1521906  87345399  2026-10-27
1    AAPL                APPLE INC  0.14617395  52674995  2026-10-27
2    MSFT           MICROSOFT CORP  0.11384873  26801123  2026-10-27
73   GDDY    GODADDY INC   CLASS A   0.0007859    925529  2026-10-27
74    GEN          GEN DIGITAL INC  0.00076328   3936985  2026-10-27
75  IXTZ6  XAK TECHNOLOGY    DEC26    3.31e-06     21200  2026-10-27
```

#### `prices/close.parquet` (9293 rows x 31 columns): first and last 3

```
                   SPY         QQQ         XLK        XLE        XLF        NVDA        AAPL        MSFT        AVGO        ORCL         AMD        CSCO         CRM         IBM        PLTR        AMZN        META       GOOGL        TSLA       NFLX         JPM        BAC         XOM         CVX         UNH         WMT          HD         DIS       UBER        SHOP        ABNB
date                                                                                                                                                                                                                                                                                                                                                                                     
1989-12-01         NaN         NaN         NaN        NaN        NaN         NaN    0.392857    0.590278         NaN    0.601852    3.812500         NaN         NaN   23.213432         NaN         NaN         NaN         NaN         NaN        NaN   10.666667  11.593750   12.093750   17.593750    0.386719    1.859375    1.845679   10.687083        NaN         NaN         NaN
1989-12-04         NaN         NaN         NaN        NaN        NaN         NaN    0.404018    0.598958         NaN    0.614198    3.812500         NaN         NaN   23.721319         NaN         NaN         NaN         NaN         NaN        NaN   10.916667  11.437500   12.031250   17.718750    0.382813    1.859375    1.808642   10.594599        NaN         NaN         NaN
1989-12-05         NaN         NaN         NaN        NaN        NaN         NaN    0.401786    0.602431         NaN    0.614198    3.750000         NaN         NaN   23.810946         NaN         NaN         NaN         NaN         NaN        NaN   10.666667  11.218750   11.968750   17.687500    0.382813    1.843750    1.796296   10.666531        NaN         NaN         NaN
2026-10-23  759.969971  704.400024  183.229996  69.330002  55.900002  210.960007  347.730011  524.510010  321.679993  126.160004  516.789978  106.500000  248.570007  253.559998  196.750000  248.000000  642.619995  320.209991  372.220001  65.849998  331.579987  50.560001  183.210007  233.210007  418.089996  119.889999  319.829987  112.519997  66.699997  168.679993  172.009995
2026-10-26  765.369995  712.200012  186.320007  69.639999  56.020000  216.000000  343.910004  532.599976  329.170013  126.059998  531.280029  110.239998  247.610001  253.440002  198.839996  249.089996  630.559998  316.799988  391.619995  63.900002  334.040009  50.520000  184.539993  232.009995  410.700012  120.290001  319.380005  110.400002  66.129997  168.179993  171.050003
2026-10-27  769.659973  721.250000  189.490005  68.209999  55.880001  217.940002  347.100006  531.330017  342.329987  130.529999  560.260010  111.379997  240.889999  250.250000  198.729996  253.100006  620.190002  320.579987  407.459991  62.520000  335.790009  50.680000  179.910004  228.229996  410.390015  119.320000  318.500000  110.230003  65.779999  165.809998  168.820007
```

#### `prices/index.parquet` (9293 rows x 2 columns): first and last 3

```
                  ^GSPC      ^SP500TR
date                                 
1989-12-01   350.630005    375.519989
1989-12-04   351.410004    376.519989
1989-12-05   349.579987    374.619995
2026-10-23  7623.680176  17107.060547
2026-10-26  7676.770020  17226.599609
2026-10-27  7722.600098  17329.470703
```

#### `prices/sectors.parquet` (7004 rows x 9 columns): first and last 3

```
                  XLB        XLE        XLF         XLI         XLK        XLP        XLU         XLV         XLY
date                                                                                                             
1998-12-22   5.670646   5.661901  11.085254   14.358088   11.895225  13.798895   5.752996   16.652407    9.340212
1998-12-23   5.730201   5.779774  11.248709   14.608631   12.179412  14.132482   5.728889   17.026617    9.380323
1998-12-24   5.862076   5.749357  11.323007   14.801355   12.133008  14.108074   5.834364   17.130573    9.552230
2026-10-23  51.310001  69.330002  55.900002  164.619995  183.229996  88.260002  42.560001  179.279999  113.099998
2026-10-26  51.380001  69.639999  56.020000  166.960007  186.320007  87.959999  42.549999  179.279999  114.260002
2026-10-27  51.779999  68.209999  55.880001  167.919998  189.490005  87.150002  42.849998  179.179993  115.449997
```

#### `ssga/xlk_holdings_2026-10-28.xlsx` (first sheet, 181 rows, first 8 columns): first 6 rows (header block and first holding) and the last 3 holding lines (2 cash lines, 1 futures line)

```
                                0                                                 1           2        3         4       5            6               7
0                      Fund Name:  State Street® Technology Select Sector SPDR® ETF         NaN      NaN      None     NaN         None             NaN
1                  Ticker Symbol:                                               XLK         NaN      NaN      None     NaN         None             NaN
2                       Holdings:                                 As of 27-Oct-2026         NaN      NaN      None     NaN         None             NaN
3                             NaN                                               NaN         NaN      NaN      None     NaN         None             NaN
4                            Name                                            Ticker  Identifier    SEDOL    Weight  Sector  Shares Held  Local Currency
5                     NVIDIA CORP                                              NVDA   67066G104  2379504  15.21906       -   87345399.0             USD
80  SSI US GOV MONEY MARKET CLASS                                                 -   924QSGII3        -  0.043534       -  54452330.46             USD
81                      US DOLLAR                                                 -   999USDZ92        -  0.006035       -   7548598.49             USD
82        XAK TECHNOLOGY    DEC26                                             IXTZ6   ADI394XN3        -  0.000331       -      21200.0             USD
```

### D2b. PUT history is sparse before 2007

The first-date gate passes (PUT 1991-03-04), but the Cboe chart JSON holds only 7 PUT values before 2007-01-03 and is daily from then on. BXM starts on 2002-03-22 and is daily throughout. First 9 rows of `data/raw/cboe/PUT.csv`, with the gap in calendar days:

```
        date   close  gap_days
0 1991-03-04  153.50       NaN
1 1991-08-07  163.67     156.0
2 1994-09-27  234.31    1147.0
3 1997-02-03  343.44     860.0
4 1997-11-18  406.31     288.0
5 2001-01-12  697.96    1151.0
6 2004-03-16  694.53    1159.0
7 2007-01-03  923.60    1023.0
8 2007-01-04  925.10       1.0
```

### D3. Parsed XLK holdings and weight sum

#### `data/raw/ssga/xlk_holdings_2026-10-28.csv` in full

```
   ticker                          name    weight    shares  as_of_date
0    NVDA                   NVIDIA CORP  0.152191  87345399  2026-10-27
1    AAPL                     APPLE INC  0.146174  52674995  2026-10-27
2    MSFT                MICROSOFT CORP  0.113849  26801123  2026-10-27
3     AMD        ADVANCED MICRO DEVICES  0.047776  10666166  2026-10-27
4    AVGO                  BROADCOM INC  0.046997  17171582  2026-10-27
5      MU         MICRON TECHNOLOGY INC  0.040155   5407911  2026-10-27
6    INTC                    INTEL CORP  0.027214  36312975  2026-10-27
7    PLTR   PALANTIR TECHNOLOGIES INC A  0.026714  16813570  2026-10-27
8    CSCO             CISCO SYSTEMS INC  0.025649  28803958  2026-10-27
9    PANW        PALO ALTO NETWORKS INC  0.019128   5956038  2026-10-27
10   AMAT         APPLIED MATERIALS INC  0.018367   5802262  2026-10-27
11   LRCX             LAM RESEARCH CORP  0.017609   9144662  2026-10-27
12    TXN         TEXAS INSTRUMENTS INC  0.016483   6674014  2026-10-27
13   CRWD  CROWDSTRIKE HOLDINGS INC   A  0.015946   7441899  2026-10-27
14    IBM   INTL BUSINESS MACHINES CORP  0.013775   6885102  2026-10-27
15   ORCL                   ORACLE CORP  0.013181  12630252  2026-10-27
16   MRVL        MARVELL TECHNOLOGY INC  0.012463   6400123  2026-10-27
17    ADI            ANALOG DEVICES INC  0.012105   3559630  2026-10-27
18   KLAC                      KLA CORP  0.011730   9548232  2026-10-27
19    CRM                SALESFORCE INC  0.011527   5985243  2026-10-27
20   QCOM                  QUALCOMM INC  0.011493   7805369  2026-10-27
21   ANET           ARISTA NETWORKS INC  0.011437   7650081  2026-10-27
22    APH            AMPHENOL CORP CL A  0.011268  18021261  2026-10-27
23   SNDK                  SANDISK CORP  0.011131   1066961  2026-10-27
24    NOW                SERVICENOW INC  0.009350   7555497  2026-10-27
25   DELL          DELL TECHNOLOGIES  C  0.008866   2209165  2026-10-27
26    STX   SEAGATE TECHNOLOGY HOLDINGS  0.008844   1656315  2026-10-27
27    ACN            ACCENTURE PLC CL A  0.008408   4472053  2026-10-27
28    WDC          WESTERN DIGITAL CORP  0.008023   2634814  2026-10-27
29   FTNT                  FORTINET INC  0.006662   4504081  2026-10-27
30    GLW                   CORNING INC  0.005848   5791428  2026-10-27
31   ADBE                     ADOBE INC  0.005768   2904937  2026-10-27
32   CDNS        CADENCE DESIGN SYS INC  0.005520   2012593  2026-10-27
33   DDOG         DATADOG INC   CLASS A  0.005495   2447488  2026-10-27
34   SNPS                  SYNOPSYS INC  0.005307   1399316  2026-10-27
35   INTU                    INTUIT INC  0.005249   1999017  2026-10-27
36    HPE    HEWLETT PACKARD ENTERPRISE  0.004707   9677266  2026-10-27
37    MSI        MOTOROLA SOLUTIONS INC  0.004676   1209430  2026-10-27
38   LITE         LUMENTUM HOLDINGS INC  0.004484    647498  2026-10-27
39    TEL           TE CONNECTIVITY PLC  0.003812   2115714  2026-10-27
40   NXPI         NXP SEMICONDUCTORS NV  0.003735   1842776  2026-10-27
41   MPWR  MONOLITHIC POWER SYSTEMS INC  0.003480    359138  2026-10-27
42   KEYS      KEYSIGHT TECHNOLOGIES IN  0.003356   1248904  2026-10-27
43   ADSK                  AUTODESK INC  0.002985   1542016  2026-10-27
44    TER                  TERADYNE INC  0.002957   1142551  2026-10-27
45   CIEN                    CIENA CORP  0.002904   1034479  2026-10-27
46   COHR                 COHERENT CORP  0.002698   1431121  2026-10-27
47      P                EVERPURE INC A  0.002694   2429188  2026-10-27
48   NTAP                    NETAPP INC  0.002609   1434032  2026-10-27
49   MCHP      MICROCHIP TECHNOLOGY INC  0.002543   3968267  2026-10-27
50    ROP        ROPER TECHNOLOGIES INC  0.002511    722767  2026-10-27
51   WDAY           WORKDAY INC CLASS A  0.002413   1468861  2026-10-27
52   FLEX                      FLEX LTD  0.001799   2699572  2026-10-27
53    HPQ                        HP INC  0.001794   6683319  2026-10-27
54     ON              ON SEMICONDUCTOR  0.001789   2845131  2026-10-27
55    TDY     TELEDYNE TECHNOLOGIES INC  0.001774    338758  2026-10-27
56   CTSH    COGNIZANT TECH SOLUTIONS A  0.001743   3291839  2026-10-27
57    JBL                     JABIL INC  0.001734    765778  2026-10-27
58   TWLO                TWILIO INC   A  0.001533    753135  2026-10-27
59   FFIV                        F5 INC  0.001520    413805  2026-10-27
60      Q         QNITY ELECTRONICS INC  0.001452   1528924  2026-10-27
61   VRSN                  VERISIGN INC  0.001444    593952  2026-10-27
62    PTC                       PTC INC  0.001234    792948  2026-10-27
63    CDW                   CDW CORP/DE  0.001179    913622  2026-10-27
64   SMCI      SUPER MICRO COMPUTER INC  0.001154   4112521  2026-10-27
65   SWKS        SKYWORKS SOLUTIONS INC  0.001139   1667001  2026-10-27
66   FSLR               FIRST SOLAR INC  0.001104    785372  2026-10-27
67   ZBRA  ZEBRA TECHNOLOGIES CORP CL A  0.001055    345708  2026-10-27
68   FICO               FAIR ISAAC CORP  0.000873    157838  2026-10-27
69   TRMB                   TRIMBLE INC  0.000860   1704075  2026-10-27
70    TYL        TYLER TECHNOLOGIES INC  0.000843    278342  2026-10-27
71   AKAM       AKAMAI TECHNOLOGIES INC  0.000836   1050287  2026-10-27
72     IT                   GARTNER INC  0.000815    461488  2026-10-27
73   GDDY         GODADDY INC   CLASS A  0.000786    925529  2026-10-27
74    GEN               GEN DIGITAL INC  0.000763   3936985  2026-10-27
75  IXTZ6       XAK TECHNOLOGY    DEC26  0.000003     21200  2026-10-27
```

#### Weight sum

```
   n_rows  weight_sum
0      76    0.999488
```

#### The 10 `[universe] xlk_holdings` names in the holdings CSV

```
   ticker                         name    weight    shares  as_of_date
0    NVDA                  NVIDIA CORP  0.152191  87345399  2026-10-27
1    AAPL                    APPLE INC  0.146174  52674995  2026-10-27
2    MSFT               MICROSOFT CORP  0.113849  26801123  2026-10-27
3     AMD       ADVANCED MICRO DEVICES  0.047776  10666166  2026-10-27
4    AVGO                 BROADCOM INC  0.046997  17171582  2026-10-27
7    PLTR  PALANTIR TECHNOLOGIES INC A  0.026714  16813570  2026-10-27
8    CSCO            CISCO SYSTEMS INC  0.025649  28803958  2026-10-27
14    IBM  INTL BUSINESS MACHINES CORP  0.013775   6885102  2026-10-27
15   ORCL                  ORACLE CORP  0.013181  12630252  2026-10-27
19    CRM               SALESFORCE INC  0.011527   5985243  2026-10-27
```

The kept rows include 1 futures line, `IXTZ6` (XAK TECHNOLOGY DEC26, weight 0.00000331), because its ticker is neither blank nor `-`. The 2 cash lines (`SSI US GOV MONEY MARKET CLASS` and `US DOLLAR`, ticker `-`) and every footer line (blank ticker) are dropped.

### D4. `data/raw/snapshot_manifest.csv`

The `snapshots` release does not exist yet (`gh release view snapshots` returns `release not found`). `python scripts/pull_snapshots.py` printed `release snapshots does not exist; wrote header-only snapshot_manifest.csv` and exited 0.

#### `data/raw/snapshot_manifest.csv` in full

```
asset,size,sha256,downloaded_utc
```

### D5. Synthetic capture health test

`.venv/Scripts/pytest -p socket --disable-socket -v tests/test_capture_health.py`:

```
tests/test_capture_health.py::test_health_rows_one_per_session PASSED    [ 33%]
tests/test_capture_health.py::test_gap_flagged PASSED                    [ 66%]
tests/test_capture_health.py::test_empty_snapshot_dir_gives_header_only PASSED [100%]
======================== 3 passed, 5 warnings in 3.30s ========================
```

#### Synthetic files written (the `test_` pair must be ignored)

```
                             file
0       chains_2026-10-28.parquet
1       chains_2026-10-30.parquet
2         snaplog_2026-10-28.json
3         snaplog_2026-10-30.json
4  test_chains_2026-10-29.parquet
5    test_snaplog_2026-10-29.json
```

#### Synthetic `snaplog_2026-10-28.json`

```
{"runner": "actions", "ny_start": "2026-10-28T15:31:10-04:00", "n_ok": 32, "n_error": 0}
```

#### Synthetic `snaplog_2026-10-30.json`

```
{"runner": "local", "ny_start": "2026-10-30T16:02:00-04:00", "n_ok": 30, "n_error": 2}
```

#### Capture health table built from them

```
      session   runner  start_ny                   ny_start  minutes_after_1530  tickers_ok  rows  after_close_rows    gap
0  2026-10-28  actions  15:31:10  2026-10-28T15:31:10-04:00            1.166667        32.0   3.0               1.0  False
1  2026-10-29      NaN       NaN                        NaN                 NaN         NaN   NaN               NaN   True
2  2026-10-30    local  16:02:00  2026-10-30T16:02:00-04:00           32.000000        30.0   2.0               2.0  False
```

#### `outputs/tables/capture_health.csv` from the real `data/snapshots/` (empty today)

```
Empty DataFrame
Columns: [session, runner, start_ny, ny_start, minutes_after_1530, tickers_ok, rows, after_close_rows, gap]
Index: []
```

### D6. Cleaning rules a to e on synthetic chains

Every case is a test in `tests/test_data.py`, and the frames below are built from the same rows. `dropped` is True for rows absent from the clean output. S is the UNDERLYING price.

#### Rule a (bid <= 0): synthetic input rows

```
  ticker contract_symbol kind  strike  bid  ask   mid      S  dropped
0   AAPL             ok1    C   100.0  2.0  2.2  2.10  100.0    False
1   AAPL             ok2    P   100.0  1.9  2.1  2.00  100.0    False
2   AAPL              a1    C   100.0  0.0  1.0  0.50  100.0     True
3   AAPL              a2    P   100.0 -0.1  1.0  0.45  100.0     True
```

#### Rule a (bid <= 0): CLEAN_LOG

```
          day ticker rule  rows_before  rows_dropped note
0  2026-10-28   AAPL    a            4             2     
1  2026-10-28   AAPL    b            2             0     
2  2026-10-28   AAPL    c            2             0     
3  2026-10-28   AAPL    d            2             0     
4  2026-10-28   AAPL    e            2             0     
```

#### Rule b (ask <= bid): synthetic input rows

```
  ticker contract_symbol kind  strike  bid  ask   mid      S  dropped
0   AAPL             ok1    C   100.0  2.0  2.2  2.10  100.0    False
1   AAPL             ok2    P   100.0  1.9  2.1  2.00  100.0    False
2   AAPL              b1    C   100.0  2.0  2.0  2.00  100.0     True
3   AAPL              b2    P   100.0  2.0  1.9  1.95  100.0     True
```

#### Rule b (ask <= bid): CLEAN_LOG

```
          day ticker rule  rows_before  rows_dropped note
0  2026-10-28   AAPL    a            4             0     
1  2026-10-28   AAPL    b            4             2     
2  2026-10-28   AAPL    c            2             0     
3  2026-10-28   AAPL    d            2             0     
4  2026-10-28   AAPL    e            2             0     
```

#### Rule c (mid < min_mid 0.05): synthetic input rows

```
  ticker contract_symbol kind  strike   bid   ask   mid      S  dropped
0   AAPL             ok1    C   100.0  2.00  2.20  2.10  100.0    False
1   AAPL             ok2    P   100.0  1.90  2.10  2.00  100.0    False
2   AAPL              c1    C   150.0  0.02  0.04  0.03  100.0     True
```

#### Rule c (mid < min_mid 0.05): CLEAN_LOG

```
          day ticker rule  rows_before  rows_dropped note
0  2026-10-28   AAPL    a            3             0     
1  2026-10-28   AAPL    b            3             0     
2  2026-10-28   AAPL    c            3             1     
3  2026-10-28   AAPL    d            2             0     
4  2026-10-28   AAPL    e            2             0     
```

#### Rule d ((ask - bid) / mid > max_rel_spread 0.5): synthetic input rows

```
  ticker contract_symbol kind  strike  bid  ask  mid      S  dropped
0   AAPL             ok1    C   100.0  2.0  2.2  2.1  100.0    False
1   AAPL             ok2    P   100.0  1.9  2.1  2.0  100.0    False
2   AAPL              d1    C   100.0  1.0  2.0  1.5  100.0     True
```

#### Rule d ((ask - bid) / mid > max_rel_spread 0.5): CLEAN_LOG

```
          day ticker rule  rows_before  rows_dropped note
0  2026-10-28   AAPL    a            3             0     
1  2026-10-28   AAPL    b            3             0     
2  2026-10-28   AAPL    c            3             0     
3  2026-10-28   AAPL    d            3             1     
4  2026-10-28   AAPL    e            2             0     
```

#### Rule e (American bounds, S = 100): synthetic input rows

```
  ticker contract_symbol kind  strike    bid    ask     mid      S  dropped
0   AAPL             ok1    C   100.0    2.0    2.2    2.10  100.0    False
1   AAPL             ok2    P   100.0    1.9    2.1    2.00  100.0    False
2   AAPL              e1    C    80.0   14.9   15.1   15.00  100.0     True
3   AAPL              e2    C     1.0  100.0  100.1  100.05  100.0     True
4   AAPL              e3    P    10.0   10.0   10.1   10.05  100.0     True
5   AAPL              e4    P   130.0   29.0   29.2   29.10  100.0     True
```

#### Rule e (American bounds, S = 100): CLEAN_LOG

```
          day ticker rule  rows_before  rows_dropped note
0  2026-10-28   AAPL    a            6             0     
1  2026-10-28   AAPL    b            6             0     
2  2026-10-28   AAPL    c            6             0     
3  2026-10-28   AAPL    d            6             0     
4  2026-10-28   AAPL    e            6             4     
```

#### Rule e for ^SPX (deferred, O-23 (b)): synthetic input rows

```
  ticker contract_symbol kind  strike   bid   ask   mid      S  dropped
0   ^SPX             ok1    C   100.0   2.0   2.2   2.1  100.0    False
1   ^SPX             ok2    P   100.0   1.9   2.1   2.0  100.0    False
2   ^SPX              s1    C    80.0  14.9  15.1  15.0  100.0    False
```

#### Rule e for ^SPX (deferred, O-23 (b)): CLEAN_LOG

```
          day ticker rule  rows_before  rows_dropped                   note
0  2026-10-28   ^SPX    a            3             0                       
1  2026-10-28   ^SPX    b            3             0                       
2  2026-10-28   ^SPX    c            3             0                       
3  2026-10-28   ^SPX    d            3             0                       
4  2026-10-28   ^SPX    e            3             0  deferred to section 3
```

#### Rule order (a and d on one row): synthetic input rows

```
  ticker contract_symbol kind  strike  bid  ask  mid      S  dropped
0   AAPL             ok1    C   100.0  2.0  2.2  2.1  100.0    False
1   AAPL             ok2    P   100.0  1.9  2.1  2.0  100.0    False
2   AAPL              ad    C   100.0  0.0  1.0  0.5  100.0     True
```

#### Rule order (a and d on one row): CLEAN_LOG

```
          day ticker rule  rows_before  rows_dropped note
0  2026-10-28   AAPL    a            3             1     
1  2026-10-28   AAPL    b            2             0     
2  2026-10-28   AAPL    c            2             0     
3  2026-10-28   AAPL    d            2             0     
4  2026-10-28   AAPL    e            2             0     
```

### D7. Fresh clone, CI and the step 1.0 push time

Push times from `gh api repos/uty101/Volatility-Surface-and-Event-Pricing/activity?ref=refs/heads/main`:

```
2026-10-28T12:51:37Z	fcf3ad4	push
2026-10-28T12:40:06Z	494de82	push      <- step 1.0
2026-10-28T12:32:57Z	b31d701	push
```

CI runs (`gh run list`): workflow, head, event, status, conclusion, created:

```
ci	fcf3ad4	push	completed	success	2026-10-28T12:51:39Z
snapshot	494de82	push	completed	success	2026-10-28T12:40:08Z
ci	494de82	push	completed	success	2026-10-28T12:40:08Z
```

fcf3ad4 holds every step of this section. The commit that adds this review and the status file changes no code, so its CI result cannot be printed inside it.

## Tests run

`.venv/Scripts/pytest -p socket --disable-socket -q` on Windows, at b1be0ec:

```
........................................                                 [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:894
  C:\Utkarsh\10. Quant Projects\7) Volatility Surface and Event Pricing\Volatility-Surface-and-Event-Pricing\.venv\Lib\site-packages\_pytest\config\__init__.py:894: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
  C:\Utkarsh\10. Quant Projects\7) Volatility Surface and Event Pricing\Volatility-Surface-and-Event-Pricing\.venv\Lib\site-packages\pandas\core\series.py:848: Pandas4Warning: Series.values returning an ndarray that drops timezone information for DatetimeTZDtype is deprecated. In a future version, this will return the underlying DatetimeArray instead. Use 'Series.dt.tz_convert(None).to_numpy()' to get a NumPy array of UTC values, or 'Series.array' to get the ExtensionArray.
  See https://pandas.pydata.org/docs/dev/whatsnew/v3.1.0.html#whatsnew-310-deprecations-values for more details.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
40 passed, 5 warnings in 5.70s
```

`.venv/Scripts/ruff check .`:

```
All checks passed!
```

## Fresh-clone check

Cloned into `C:\Users\astha\AppData\Local\Temp\vs1` from GitHub after the push of fcf3ad4:

```
$ git clone https://github.com/uty101/Volatility-Surface-and-Event-Pricing vs1
$ git log --oneline -1
fcf3ad4 section 1: review decisions recorded
$ uv venv --python 3.12
$ uv pip install -r requirements-lock.txt
$ uv pip install -e . --no-deps
$ .venv/Scripts/pytest -p socket --disable-socket -q
........................................                                 [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:894
  C:\Users\astha\AppData\Local\Temp\vs1\.venv\Lib\site-packages\_pytest\config\__init__.py:894: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
  C:\Users\astha\AppData\Local\Temp\vs1\.venv\Lib\site-packages\pandas\core\series.py:848: Pandas4Warning: Series.values returning an ndarray that drops timezone information for DatetimeTZDtype is deprecated. In a future version, this will return the underlying DatetimeArray instead. Use 'Series.dt.tz_convert(None).to_numpy()' to get a NumPy array of UTC values, or 'Series.array' to get the ExtensionArray.
  See https://pandas.pydata.org/docs/dev/whatsnew/v3.1.0.html#whatsnew-310-deprecations-values for more details.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
40 passed, 5 warnings in 32.93s
exit=0
```

## Runtime per step

- 1.0: forced Actions capture 6m41s (run 40689704608); the 4 tests about 1 s.
- 1.1: `pull_data.py` stages, from the `pulled_utc` stamps in the manifest: cboe about 8 s, fred about 6 s, ssga about 6 s, prices about 24 s (31 + 2 + 9 yfinance histories).
- 1.2: `pull_snapshots.py` under 2 s (release missing).
- 1.3 and 1.4: code and tests only. The full suite runs in 3 to 6 s locally and 33 s in the fresh clone.

## Deviations from PLAN.md

1. **Fixture deferred (instruction 01).** `tests/fixtures/*_sample.*`, `test_fixture_schema` (1.2) and `outputs/tables/clean_log_fixture.csv` (1.4) are not built; instruction 01b builds them after the 2026-10-28 capture.
2. **CLEAN_LOG has a trailing `note` column** after the 5 schema columns, so the `^SPX` rule e row can carry `deferred to section 3`. OPEN O-25.
3. **Capture health has 2 more columns** than PLAN 1.4, `ny_start` and `minutes_after_1530` (instruction 01), placed after `start_ny`. OPEN O-26 covers the overlap between `start_ny` and `ny_start`.
4. **`volsurf/config.py`** (`Config`, `load_config`, CLAUDE.md Section 6.1) is built here, because `clean_chain` and `capture_health` take a `cfg`; the kickoff left it to Section 1. Each TOML table becomes a frozen dataclass and lists become tuples.
5. **`scripts/run_all.py`** exists with 1 stage, `capture_health` (O-1 (a)); Section 11.1 completes it.
6. **Tests beyond the PLAN names:** `test_close_has_every_captured_ticker_but_spx`, `test_xlk_weights_sum`, `test_xlk_names_in_holdings`, `test_manifest_header_only_when_release_missing`, `test_manifest_header_only_when_no_assets`, `test_rule_e_spx_deferred`, `test_rate_missing_t_minus_1_uses_t_minus_2` and `test_load_snapshot_missing_chains_names_asset` (all asked for by instruction 01); `test_clean_log_one_row_per_ticker_and_rule`, `test_load_snapshot_reads_four_assets` and `test_empty_snapshot_dir_gives_header_only` (added).
7. **Pushes.** Step 1.0 was pushed on its own (instruction 01). Steps 1.1 to 1.4 and the decisions were pushed before the fresh-clone check, which clones the pushed repo (rule 12). This review and the status file are the last push.

## Not verified

- The `better` skip branch has not yet run against the real `snapshots` release. Tonight's 19:30 UTC run creates the release, and the 20:30 UTC run or the local task is the first that can skip.
- The local task still runs `--upload if-missing` until the owner re-registers it with the edited `register_snapshot_task.ps1` (instruction 01 part A). The script was not run.
- Interpretations made while building, each small, for the reviewer to confirm:
  - `better`: whether the release already has the snaplog is read from `gh release view <tag> --json assets` before `gh release download`, so a missing asset is told apart from a failed download.
  - Rules a to d keep a row only when the inequality holds, so a missing (NaN) bid or ask is dropped under the first rule it touches.
  - Rule e (American): a row is kept when max(S − K, 0) ≤ mid < S for calls and max(K − S, 0) ≤ mid < K for puts. A ticker with no UNDERLYING price loses every row under rule e.
  - `stale` is `sessions_between(last trade New York date, snapshot New York date) > stale_sessions`; `after_close` is a snapshot New York time strictly after 16:00.
  - CLEAN_LOG `day` is the New York date of the ticker's first `snap_utc`.
  - The pull date in 1.1 is the New York date when the script runs. Today's pull ran before the open, so no partial bar is in the files (last date 2026-10-27 everywhere).
  - In the manifest, an `.xlsx` row count is the worksheet's `max_row` (181), with blank dates.
  - `snapshot_manifest.csv` keeps the earlier `downloaded_utc` for an asset that is skipped because it is already present.
  - `load_snapshot` returns `snaplog` as the per-ticker rows of the JSON, with the run fields (runner, ny_start, n_ok and so on) in `DataFrame.attrs`.
  - `sessions_between(t, e)` returns 0 when e ≤ t.
- The first FRED request timed out because `pull_data.py` sent the header `User-Agent: Mozilla/5.0`, which FRED does not answer (`curl`, and `requests` with its default agent, answer in 0.2 s). The header was removed and every stage was rerun. It was a fault in the client code, not a failed pull.

## Open questions

- **O-25** CLEAN_LOG note: (a) trailing `note` column (implemented); (b) the note written into `rule` as `e (deferred to section 3)`.
- **O-26** capture health `start_ny` and `ny_start`: (a) keep both, wall time and full timestamp (implemented); (b) keep one.
- **PUT and BXM history (D2b).** Not an OPEN item, because no choice in this section depends on it. The Cboe chart JSON gives PUT daily only from 2007-01-03 (7 values before) and BXM from 2002-03-22, while question 4 and Section 8 assume monthly PUT and BXM returns from 1990. Section 8 will need a decision on the start month or another source.

## Files changed

- `volsurf/snapshots.py`, `scripts/snapshot.py`, `.github/workflows/snapshot.yml`, `scripts/windows/register_snapshot_task.ps1`, `tests/test_snapshots.py` (1.0)
- `volsurf/config.py`, `scripts/pull_data.py`, `tests/test_pull_data.py`, `data/raw/MANIFEST.json`, `data/raw/cboe/*.csv` (7), `data/raw/fred/*.csv` (5), `data/raw/prices/close.parquet`, `index.parquet`, `sectors.parquet`, `dividends.csv`, `data/raw/ssga/xlk_holdings_2026-10-28.xlsx` and `.csv` (1.1)
- `scripts/pull_snapshots.py`, `tests/test_pull_snapshots.py`, `data/raw/snapshot_manifest.csv` (1.2)
- `volsurf/data.py`, `tests/test_data.py` (1.3)
- `volsurf/data.py` (capture health), `scripts/run_all.py`, `tests/test_capture_health.py`, `outputs/tables/capture_health.csv` (1.4)
- `decisions/section_1_review.md`, `decisions/OPEN.md` (part B, O-25, O-26)
- `review/section_1.md`, `instructions/01_section_1.status.md`

## Reviewer reads

1. `instructions/01_section_1.status.md`
2. This file: D1, D2b, D3, D6, Not verified, Open questions
3. `git show 494de82` (step 1.0, the capture change)
4. `volsurf/data.py`
5. `scripts/pull_data.py`
6. `decisions/OPEN.md` O-25 and O-26

## Session 1b

Instruction `instructions/01b_section_1_capture_fixes.md`. Commits: `980bf69` step 1b.1, `9a24030` step 1b.2, `c43e2e6` step 1b.3, `5c013e5` decisions record (`decisions/section_1_review.md`, `## Session 1b`).

### 1b-D1. Step 1b.1, XLK top holdings

**1. The new `[universe]` table** (`config.toml` at `980bf69`). `[snapshot] min_tickers_ok` is now 33.

```toml
[universe]
index = ["^SPX"]
etfs = ["SPY", "QQQ", "XLK", "XLE", "XLF"]
xlk_holdings = ["NVDA", "AAPL", "MSFT", "AMD", "AVGO", "MU", "INTC", "PLTR", "CSCO", "PANW", "AMAT", "LRCX", "ORCL", "CRM", "IBM"]
singles = ["AMZN", "META", "GOOGL", "TSLA", "NFLX", "JPM", "BAC", "XOM", "CVX", "UNH", "WMT", "HD", "DIS", "UBER", "SHOP", "ABNB"]
max_days_to_expiry = 400
sector_spdrs = ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"]
```

**2. Coverage from the committed holdings CSV** (`data/raw/ssga/xlk_holdings_2026-10-28.csv`). Rank is the name's rank by weight among all XLK holdings. The 15 names cover **0.720304** of XLK; `test_xlk_names_cover_70_percent` asserts at least 0.70.

**3. The first and last 3 rows of `close.parquet` for the 5 new columns**, with each column's first non-missing date (PANW listed on 2012-07-20).

```
 rank ticker   weight
  1.0   NVDA 0.152191
  2.0   AAPL 0.146174
  3.0   MSFT 0.113849
  4.0    AMD 0.047776
  5.0   AVGO 0.046997
  6.0     MU 0.040155
  7.0   INTC 0.027214
  8.0   PLTR 0.026714
  9.0   CSCO 0.025649
 10.0   PANW 0.019128
 11.0   AMAT 0.018367
 12.0   LRCX 0.017609
 15.0    IBM 0.013775
 16.0   ORCL 0.013181
 20.0    CRM 0.011527
coverage of 15 names: 0.720304
first non-missing dates:
MU      1989-12-01
INTC    1989-12-01
PANW    2012-07-20
AMAT    1989-12-01
LRCX    1989-12-01
                MU      INTC  PANW      AMAT      LRCX
date                                                  
1989-12-01  0.9625  1.101563   NaN  0.425781  0.116667
1989-12-04  1.0000  1.117188   NaN  0.429688  0.119444
1989-12-05  1.0125  1.109375   NaN  0.421875  0.113889
                    MU       INTC        PANW        AMAT        LRCX
date                                                                 
2026-10-23  877.549988  86.959999  380.549988  377.239990  230.100006
2026-10-26  903.700012  90.470001  390.459991  387.589996  237.500000
2026-10-27  928.760010  93.739998  401.700012  395.929993  240.850006
close.parquet shape (9293, 36)
```

**4. How the prices stage was rerun (O-27).** At 14:56 UTC yfinance already returned a live 2026-10-28 row (MU 967.06 at 10:56 New York), and `pull_data.py` ends the history at the New York pull date + 1, so the plain `--stage prices` command would have stored an intraday price as the 2026-10-28 close. The stage function was called with the pull date pinned to 2026-10-27:

```python
pull_data.stage_prices(yf.Ticker, date(2026, 10, 27), load_config())
```

```
prices prices/close.parquet                 rows=9293 1989-12-01 .. 2026-10-27
prices prices/index.parquet                 rows=9293 1989-12-01 .. 2026-10-27
prices prices/sectors.parquet               rows=7004 1998-12-22 .. 2026-10-27
prices prices/dividends.csv                 rows=2479 1989-12-05 .. 2026-10-14
```

Checks against the session 1 files: the 31 old `close.parquet` columns are identical (`DataFrame.equals`), the 2,181 old dividend rows are identical (outer merge on date and ticker, max difference 0), and `index.parquet` came back byte-identical. `sectors.parquet`'s adjusted closes moved by at most 7.6e-5 (XLV), Yahoo recomputing its adjustment factors, so the session 1 file was kept with its manifest entries, under "Nothing else in `data/raw/` changes". Only `close.parquet`, `dividends.csv`, their 2 manifest entries and the prices stage's `pulled_utc` changed:

```diff
diff --git a/data/raw/MANIFEST.json b/data/raw/MANIFEST.json
index a514ee3..48dd025 100644
--- a/data/raw/MANIFEST.json
+++ b/data/raw/MANIFEST.json
@@ -27,7 +27,7 @@
       }
     },
     "prices": {
-      "pulled_utc": "2026-10-28T12:44:47.167681+00:00",
+      "pulled_utc": "2026-10-28T14:56:50.962009+00:00",
       "versions": {
         "python": "3.12.13",
         "yfinance": "1.7.0",
@@ -164,21 +164,21 @@
     },
     "prices/close.parquet": {
       "stage": "prices",
-      "url": "yfinance Ticker(t).history(start=1989-12-01, end=2026-10-29, auto_adjust=False, actions=True)",
-      "pulled_utc": "2026-10-28T12:44:47.167681+00:00",
+      "url": "yfinance Ticker(t).history(start=1989-12-01, end=2026-10-28, auto_adjust=False, actions=True)",
+      "pulled_utc": "2026-10-28T14:56:50.962009+00:00",
       "rows": 9293,
       "first_date": "1989-12-01",
       "last_date": "2026-10-27",
-      "sha256": "1a86d3b1f6aca7d9416b6b72c449763943c49b9848df7f7e96ffcc9438df23e6"
+      "sha256": "7d1a6c0d0b32018017d1a94fe26cdc1bbad198b0d29843e863f9675e20aee665"
     },
     "prices/dividends.csv": {
       "stage": "prices",
-      "url": "yfinance Ticker(t).history(start=1989-12-01, end=2026-10-29, auto_adjust=False, actions=True)",
-      "pulled_utc": "2026-10-28T12:44:47.167681+00:00",
-      "rows": 2181,
+      "url": "yfinance Ticker(t).history(start=1989-12-01, end=2026-10-28, auto_adjust=False, actions=True)",
+      "pulled_utc": "2026-10-28T14:56:50.962009+00:00",
+      "rows": 2479,
       "first_date": "1989-12-05",
-      "last_date": "2026-10-09",
-      "sha256": "e6be77d5f5a59e2fae5afe95f0f851de1b215630ea82566370a54cc0f3fd2ea1"
+      "last_date": "2026-10-14",
+      "sha256": "4f0eee3ba5a81ff07a6c8ed872510d1a5bcf906e9ef1422efd64cfc264628262"
     },
     "prices/index.parquet": {
       "stage": "prices",
```

**5. Tests that count tickers.** `test_pull_uses_fake_session` now expects 36 close columns and 36 dividend rows (31 before). `test_close_has_every_captured_ticker_but_spx` and `test_xlk_names_in_holdings` read the config, so they now cover all 15 names without a change.

### 1b-D2. Step 1b.2, the diff of `register_snapshot_task.ps1`

```diff
diff --git a/scripts/windows/register_snapshot_task.ps1 b/scripts/windows/register_snapshot_task.ps1
index 6e16406..e207e86 100644
--- a/scripts/windows/register_snapshot_task.ps1
+++ b/scripts/windows/register_snapshot_task.ps1
@@ -1,5 +1,5 @@
-# Registers the backup capture task volsurf-snapshot (kickoff Section 9, step 0.2).
-# Monday to Friday at each [snapshot] local_task_times_london time, runs the repo venv's Python on
+# Registers the backup capture task volsurf-snapshot (kickoff Section 9, step 0.2; instruction 01b, step 1b.2).
+# Monday to Friday at each [snapshot] local_task_times_utc time, runs the repo venv's Python on
 # scripts/snapshot.py --runner local --out data/local_capture --upload better.
 # Runs only while the user is logged on; starts when available after a missed time.
 $ErrorActionPreference = "Stop"
@@ -9,21 +9,26 @@ $python = Join-Path $repo ".venv\Scripts\python.exe"
 if (-not (Test-Path $python)) {
     throw "No venv Python at $python. Build it: uv venv --python 3.12; uv pip install -r requirements-lock.txt; uv pip install -e . --no-deps"
 }
-# The trigger times are London wall-clock times, and Task Scheduler uses the machine's time zone.
-if ((Get-TimeZone).Id -ne "GMT Standard Time") {
-    throw "Machine time zone is $((Get-TimeZone).Id), not GMT Standard Time (London); the task times would be wrong."
-}
 
 Push-Location $repo
 try {
-    $times = & $python -c "import tomllib; print('\n'.join(tomllib.load(open('config.toml', 'rb'))['snapshot']['local_task_times_london']))"
+    $times = & $python -c "import tomllib; print('\n'.join(tomllib.load(open('config.toml', 'rb'))['snapshot']['local_task_times_utc']))"
 } finally {
     Pop-Location
 }
-if (-not $times) { throw "Could not read [snapshot] local_task_times_london from config.toml" }
+if (-not $times) { throw "Could not read [snapshot] local_task_times_utc from config.toml" }
 
+# The trigger times are UTC instants. Each is built as a UTC DateTime and converted to local time, so
+# New-ScheduledTaskTrigger stores a StartBoundary in UTC and the task fires at the same UTC instant in
+# every time zone and season.
+$today = [DateTime]::UtcNow.ToString("yyyy-MM-dd")
 $days = "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"
-$triggers = @($times | ForEach-Object { New-ScheduledTaskTrigger -Weekly -DaysOfWeek $days -At $_ })
+$triggers = @($times | ForEach-Object {
+    $utc = [DateTime]::SpecifyKind(
+        [DateTime]::ParseExact("$today $_", "yyyy-MM-dd HH:mm", [Globalization.CultureInfo]::InvariantCulture),
+        [DateTimeKind]::Utc)
+    New-ScheduledTaskTrigger -Weekly -DaysOfWeek $days -At $utc.ToLocalTime()
+})
 $action = New-ScheduledTaskAction -Execute "`"$python`"" `
     -Argument "scripts\snapshot.py --runner local --out data\local_capture --upload better" `
     -WorkingDirectory $repo
@@ -33,4 +38,7 @@ $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME"
 Register-ScheduledTask -TaskName "volsurf-snapshot" -Action $action -Trigger $triggers -Settings $settings `
     -Principal $principal -Description "Backup daily option chain capture for Volatility-Surface-and-Event-Pricing" `
     -Force | Out-Null
-Write-Output "Registered volsurf-snapshot at $($times -join ', ') London, Monday to Friday, in $repo"
+Write-Output "Registered volsurf-snapshot at $($times -join ', ') UTC, Monday to Friday, in $repo"
+foreach ($t in (Get-ScheduledTask -TaskName "volsurf-snapshot").Triggers) {
+    Write-Output "StartBoundary $($t.StartBoundary)"
+}
```

The script was not run (step 1b.2 item 3). The trigger construction alone was checked on this machine (time zone `GMT Standard Time`) without registering anything:

```
2026-10-28T19:45:00Z    built from 2026-10-28 19:45 UTC, converted to local
2026-10-28T20:45:00Z    built from 2026-10-28 20:45 UTC, converted to local
2026-07-01T19:45:00Z    a BST date: 19:45 UTC is 20:45 local, stored back as 19:45Z
```

A DateTime without a kind is read as local time: `2026-07-01 19:45` with no kind gave `18:45:00Z`, which is why the script sets the UTC kind before converting.

### 1b-D3. Forced capture run

Run [40711619617](https://github.com/uty101/Volatility-Surface-and-Event-Pricing/actions/runs/40711619617), `gh workflow run snapshot.yml -f force=true`, on `5c013e5`. The push itself started no snapshot run, as expected (it changed no file the `push` trigger watches). Last 5 lines of the Capture step, the script's own output with yfinance's pandas deprecation warnings left out (the job's last raw lines are the artifact upload and a Node.js 20 notice). 37 tickers, 37 ok (at least 33 required); the 2026-10-28 snaplog already in `snapshots-test` had `n_ok` 32, so `better` replaced it:

```
2026-10-28T15:07:30.2447585Z UBER   ok      rows=   660 expiries= 11 failed=0    8.6s 
2026-10-28T15:07:39.5214054Z SHOP   ok      rows=   916 expiries= 12 failed=0    9.3s 
2026-10-28T15:07:48.7919533Z ABNB   ok      rows=   653 expiries= 12 failed=0    9.3s 
2026-10-28T15:07:49.0587582Z 2026-10-28T15:07:49.051393+00:00 done ok=37 partial=0 error=0 rows=84065
2026-10-28T15:07:52.2259741Z uploaded 4 files to release snapshots-test
```

The 5 new names in the same run:

```
2026-10-28T15:03:39.6608666Z MU     ok      rows=  6529 expiries= 18 failed=0   13.3s 
2026-10-28T15:03:49.6307567Z INTC   ok      rows=  1641 expiries= 13 failed=0   10.0s 
2026-10-28T15:04:19.4805201Z PANW   ok      rows=  1879 expiries= 13 failed=0    9.9s 
2026-10-28T15:04:29.3828000Z AMAT   ok      rows=  1925 expiries= 13 failed=0    9.9s 
2026-10-28T15:04:38.9055100Z LRCX   ok      rows=  1667 expiries= 12 failed=0    9.5s 
```

### 1b-D4. Tests, fresh clone, CI, push time

`pytest -p socket --disable-socket -q` on Windows at `5c013e5`:

```
.........................................                                [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:894
  C:\Utkarsh\10. Quant Projects\7) Volatility Surface and Event Pricing\Volatility-Surface-and-Event-Pricing\.venv\Lib\site-packages\_pytest\config\__init__.py:894: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
  C:\Utkarsh\10. Quant Projects\7) Volatility Surface and Event Pricing\Volatility-Surface-and-Event-Pricing\.venv\Lib\site-packages\pandas\core\series.py:848: Pandas4Warning: Series.values returning an ndarray that drops timezone information for DatetimeTZDtype is deprecated. In a future version, this will return the underlying DatetimeArray instead. Use 'Series.dt.tz_convert(None).to_numpy()' to get a NumPy array of UTC values, or 'Series.array' to get the ExtensionArray.
  See https://pandas.pydata.org/docs/dev/whatsnew/v3.1.0.html#whatsnew-310-deprecations-values for more details.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
41 passed, 5 warnings in 4.43s
```

`ruff check .`: `All checks passed!`

Fresh clone of `origin/main` at `5c013e5`:

```
$ git clone https://github.com/uty101/Volatility-Surface-and-Event-Pricing vs1b
$ git log --oneline -1
5c013e5 section 1b: review decisions recorded
$ uv venv --python 3.12
$ uv pip install -r requirements-lock.txt
$ uv pip install -e . --no-deps
$ .venv/Scripts/pytest -p socket --disable-socket -q
.........................................                                [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:894
  C:\Users\astha\AppData\Local\Temp\vs1b\.venv\Lib\site-packages\_pytest\config\__init__.py:894: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
tests/test_capture_health.py::test_health_rows_one_per_session
  C:\Users\astha\AppData\Local\Temp\vs1b\.venv\Lib\site-packages\pandas\core\series.py:848: Pandas4Warning: Series.values returning an ndarray that drops timezone information for DatetimeTZDtype is deprecated. In a future version, this will return the underlying DatetimeArray instead. Use 'Series.dt.tz_convert(None).to_numpy()' to get a NumPy array of UTC values, or 'Series.array' to get the ExtensionArray.
  See https://pandas.pydata.org/docs/dev/whatsnew/v3.1.0.html#whatsnew-310-deprecations-values for more details.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
41 passed, 5 warnings in 23.05s
exit=0
```

CI: success on `5c013e5` (run 40711593427), the commit carrying all 3 steps and the decisions record.

The last step commit reached `origin/main` at **2026-10-28 15:00:34 UTC** (push of `980bf69..5c013e5`), before the 19:15 UTC deadline. Tonight's 19:30 and 20:30 UTC Actions runs use 37 underlyings and `min_tickers_ok = 33`. This review and the status file go in 1 final commit pushed after it; that commit cannot carry its own push time or CI result.

### 1b open questions

- **O-27** How the prices stage was rerun mid-session (above). Implemented as (a).
- **O-28** Where BXM alone from `[vrp] bxm_start` is reported. Nothing built yet; Section 8 needs it.

### 1b owner action

Re-register the local task: `powershell -ExecutionPolicy Bypass -File scripts\windows\register_snapshot_task.ps1`. Until then the registered task still fires at 19:30 and 20:30 UTC with `--upload if-missing`, at the same instants as Actions.
