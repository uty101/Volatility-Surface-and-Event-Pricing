import hashlib
import json
from datetime import date
from pathlib import Path

import pandas as pd

from scripts import pull_data
from volsurf.config import load_config

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CFG = load_config(ROOT / "config.toml")


def _manifest() -> dict:
    return json.loads((RAW / "MANIFEST.json").read_text(encoding="utf-8"))


def _holdings() -> pd.DataFrame:
    (path,) = sorted((RAW / "ssga").glob("xlk_holdings_*.csv"))[-1:]
    return pd.read_csv(path)


def test_manifest_hashes_match_files():
    files = _manifest()["files"]
    assert files
    for name, entry in files.items():
        assert hashlib.sha256((RAW / name).read_bytes()).hexdigest() == entry["sha256"], name


def test_cboe_first_dates():
    vix = pd.read_csv(RAW / "cboe" / "VIX.csv")
    assert pd.to_datetime(vix["DATE"], format="%m/%d/%Y").min() == pd.Timestamp("1990-01-02")
    assert pd.read_csv(RAW / "cboe" / "PUT.csv")["date"].min() == "1991-03-04"
    assert pd.read_csv(RAW / "cboe" / "COR3M.csv")["date"].min() == "2006-01-03"


def test_close_has_every_captured_ticker_but_spx():
    close = pd.read_parquet(RAW / "prices" / "close.parquet")
    uni = CFG.universe
    captured = list(uni.index) + list(uni.etfs) + list(uni.xlk_holdings) + list(uni.singles)
    for ticker in captured:
        if ticker != "^SPX":
            assert ticker in close.columns, ticker


def test_xlk_weights_sum():
    total = _holdings()["weight"].sum()
    assert 0.97 <= total <= 1.01


def test_xlk_names_in_holdings():
    tickers = set(_holdings()["ticker"])
    for name in CFG.universe.xlk_holdings:
        assert name in tickers, name


def test_xlk_names_cover_70_percent():
    holdings = _holdings()
    assert len(CFG.universe.xlk_holdings) == 15
    assert holdings.loc[holdings["ticker"].isin(CFG.universe.xlk_holdings), "weight"].sum() >= 0.70


class _Resp:
    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self):
        pass


class _FakeSession:
    def __init__(self, pages: dict[str, bytes]):
        self.pages, self.urls = pages, []

    def get(self, url, timeout=None):
        self.urls.append(url)
        return _Resp(self.pages[url])


class _FakeTicker:
    def __init__(self, ticker: str):
        self.ticker = ticker

    def history(self, start, end, auto_adjust, actions):
        assert (start, end, auto_adjust, actions) == ("1989-12-01", "2026-10-29", False, True)
        idx = pd.DatetimeIndex(["2026-10-26", "2026-10-27"]).tz_localize("America/New_York")
        return pd.DataFrame({"Close": [10.0, 11.0], "Adj Close": [9.5, 10.5], "Dividends": [0.0, 0.25]}, index=idx)


def test_pull_uses_fake_session(tmp_path):
    pull = date(2026, 10, 28)
    vix = b"DATE,OPEN,HIGH,LOW,CLOSE\n01/02/1990,17.24,17.24,17.24,17.24\n"
    chart = json.dumps({"data": [{"date": "2006-01-04", "close": "2.5"}, {"date": "2006-01-03", "close": "1.5"}]})
    fred = b"observation_date,DGS1MO\n2026-10-26,3.9\n2026-10-27,\n"
    xlsx = max((RAW / "ssga").glob("xlk_holdings_*.xlsx")).read_bytes()
    pages = {pull_data.CBOE_CSV_URL.format(name=n): vix for n in pull_data.CBOE_CSV}
    pages |= {pull_data.CBOE_JSON_URL.format(name=n): chart.encode() for n in pull_data.CBOE_JSON}
    pages |= {pull_data.FRED_URL.format(id=i): fred for i in pull_data.FRED_IDS}
    pages[pull_data.SSGA_URL] = xlsx
    session = _FakeSession(pages)

    pull_data.stage_cboe(session, pull, tmp_path)
    pull_data.stage_fred(session, pull, tmp_path)
    pull_data.stage_ssga(session, pull, tmp_path)
    pull_data.stage_prices(_FakeTicker, date(2026, 10, 28), CFG, tmp_path)

    assert sorted(session.urls) == sorted(pages)
    assert (tmp_path / "cboe" / "VIX.csv").read_bytes() == vix
    assert (tmp_path / "cboe" / "COR3M.csv").read_text() == "date,close\n2006-01-03,1.5\n2006-01-04,2.5\n"
    assert (tmp_path / "fred" / "DTB3.csv").read_bytes() == fred
    holdings = pd.read_csv(tmp_path / "ssga" / "xlk_holdings_2026-10-28.csv")
    assert list(holdings.columns) == ["ticker", "name", "weight", "shares", "as_of_date"]
    close = pd.read_parquet(tmp_path / "prices" / "close.parquet")
    assert close.index.tolist() == [date(2026, 10, 26), date(2026, 10, 27)] and close.shape[1] == 36
    assert pd.read_parquet(tmp_path / "prices" / "index.parquet").columns.tolist() == ["^GSPC", "^SP500TR"]
    assert pd.read_parquet(tmp_path / "prices" / "sectors.parquet")["XLK"].tolist() == [9.5, 10.5]
    divs = pd.read_csv(tmp_path / "prices" / "dividends.csv")
    assert len(divs) == 36 and (divs["date"] == "2026-10-27").all() and (divs["dividend"] == 0.25).all()
    manifest = json.loads((tmp_path / "MANIFEST.json").read_text())
    assert set(manifest["stages"]) == {"cboe", "fred", "prices", "ssga"}
    assert manifest["stages"]["prices"]["last_session"] == "2026-10-28"
    for name, entry in manifest["files"].items():
        assert hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() == entry["sha256"]
