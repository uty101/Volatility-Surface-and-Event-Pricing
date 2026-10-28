"""Snapshot download (PLAN 1.2, instruction 01 step 1.2).

Lists every asset of the `snapshots` release, downloads each into data/snapshots/ (gitignored), skipping
files already present whose sha256 matches the release's digest, and writes data/raw/snapshot_manifest.csv
(asset, size, sha256, downloaded_utc), one row per asset sorted by name. A missing release or a release
with no assets gives a header-only manifest and exit 0. Every gh call goes through `runner`, so tests
drive the script with a fake.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tomllib
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = ["asset", "size", "sha256", "downloaded_utc"]


def gh(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args], cwd=ROOT, capture_output=True, text=True, check=False)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def list_assets(tag: str, runner) -> list[dict] | None:
    """Release assets as dicts with name, size, digest; None when the release does not exist."""
    res = runner(["release", "view", tag, "--json", "assets"])
    if res.returncode != 0:
        if "release not found" in (res.stderr or "").lower():
            return None
        raise RuntimeError(f"gh release view {tag} failed: {(res.stderr or '').strip()}")
    return json.loads(res.stdout)["assets"]


def pull(tag: str, snap_dir: Path, manifest_path: Path, runner=gh, now=lambda: datetime.now(UTC)) -> str:
    snap_dir.mkdir(parents=True, exist_ok=True)
    previous = {}
    if manifest_path.exists():
        prev = pd.read_csv(manifest_path, dtype=str)
        previous = dict(zip(prev["asset"], prev["downloaded_utc"], strict=True))
    assets = list_assets(tag, runner)
    rows, downloaded, skipped = [], 0, 0
    for a in sorted(assets or [], key=lambda a: a["name"]):
        name, digest = a["name"], a["digest"].removeprefix("sha256:")
        local = snap_dir / name
        if local.exists() and sha256(local) == digest:
            skipped += 1
            when = previous.get(name) or now().isoformat()
        else:
            res = runner(["release", "download", tag, "--pattern", name, "--dir", str(snap_dir), "--clobber"])
            if res.returncode != 0:
                raise RuntimeError(f"gh release download {name} failed: {(res.stderr or '').strip()}")
            if sha256(local) != digest:
                raise RuntimeError(f"{name}: downloaded sha256 {sha256(local)} != release digest {digest}")
            downloaded += 1
            when = now().isoformat()
        rows.append({"asset": name, "size": int(a["size"]), "sha256": digest, "downloaded_utc": when})
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=COLUMNS).to_csv(manifest_path, index=False, lineterminator="\n", encoding="utf-8")
    if assets is None:
        return f"release {tag} does not exist; wrote header-only {manifest_path.name}"
    if not assets:
        return f"release {tag} has no assets; wrote header-only {manifest_path.name}"
    return f"{len(rows)} assets in {tag}: {downloaded} downloaded, {skipped} already present"


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    with open(ROOT / "config.toml", "rb") as fh:
        tag = tomllib.load(fh)["snapshot"]["release_tag"]
    print(pull(tag, ROOT / "data" / "snapshots", ROOT / "data" / "raw" / "snapshot_manifest.csv"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
