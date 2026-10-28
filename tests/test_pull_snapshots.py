import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from scripts.pull_snapshots import COLUMNS, pull

NOW = datetime(2026, 10, 28, 21, 0, tzinfo=UTC)


class FakeGh:
    """Stands in for the gh CLI: a release listing and the bytes each asset downloads as."""

    def __init__(self, contents: dict[str, bytes] | None):
        self.contents, self.downloads = contents, []

    def __call__(self, args: list[str]) -> subprocess.CompletedProcess:
        if args[:2] == ["release", "view"]:
            if self.contents is None:
                return subprocess.CompletedProcess(args, 1, "", "release not found\n")
            assets = [{"name": n, "size": len(b), "digest": "sha256:" + hashlib.sha256(b).hexdigest()}
                      for n, b in self.contents.items()]
            return subprocess.CompletedProcess(args, 0, json.dumps({"assets": assets}), "")
        if args[:2] == ["release", "download"]:
            name, out = args[args.index("--pattern") + 1], Path(args[args.index("--dir") + 1])
            (out / name).write_bytes(self.contents[name])
            self.downloads.append(name)
            return subprocess.CompletedProcess(args, 0, "", "")
        raise AssertionError(args)


def _run(tmp_path, fake):
    manifest = tmp_path / "raw" / "snapshot_manifest.csv"
    msg = pull("snapshots", tmp_path / "snapshots", manifest, runner=fake, now=lambda: NOW)
    return msg, pd.read_csv(manifest)


def test_manifest_header_only_when_release_missing(tmp_path):
    msg, manifest = _run(tmp_path, FakeGh(None))
    assert list(manifest.columns) == COLUMNS and manifest.empty
    assert "does not exist" in msg


def test_manifest_header_only_when_no_assets(tmp_path):
    msg, manifest = _run(tmp_path, FakeGh({}))
    assert list(manifest.columns) == COLUMNS and manifest.empty
    assert "no assets" in msg


def test_manifest_rows_match_release_listing(tmp_path):
    contents = {"underlying_2026-10-28.csv": b"ticker\nSPY\n", "chains_2026-10-28.parquet": b"PAR1 chains"}
    snaps = tmp_path / "snapshots"
    snaps.mkdir()
    (snaps / "chains_2026-10-28.parquet").write_bytes(contents["chains_2026-10-28.parquet"])  # matching sha256
    (snaps / "underlying_2026-10-28.csv").write_bytes(b"stale bytes")  # wrong sha256
    fake = FakeGh(contents)
    _, manifest = _run(tmp_path, fake)
    assert fake.downloads == ["underlying_2026-10-28.csv"]
    assert manifest["asset"].tolist() == ["chains_2026-10-28.parquet", "underlying_2026-10-28.csv"]
    for row in manifest.itertuples():
        body = contents[row.asset]
        assert row.size == len(body)
        assert row.sha256 == hashlib.sha256(body).hexdigest()
        assert (snaps / row.asset).read_bytes() == body
    assert (manifest["downloaded_utc"] == NOW.isoformat()).all()
