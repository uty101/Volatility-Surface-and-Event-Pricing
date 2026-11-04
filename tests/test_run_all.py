import re
from fnmatch import fnmatch
from pathlib import Path

from scripts import run_all

ROOT = Path(__file__).resolve().parents[1]


def _produced() -> list[str]:
    return [path.replace("{day}", "*") for paths in run_all.STAGE_OUTPUTS.values() for path in paths]


def test_run_all_stages_listed():
    plan = (ROOT / "PLAN.md").read_text(encoding="utf-8")
    named = set(re.findall(r"`((?:outputs/[^`]+)|data/raw/snapshot_manifest\.csv)`", plan))
    assert len(named) > 30
    patterns = _produced()
    missing = [n for n in named if not any(fnmatch(n.replace("{day}", "2026-11-03"), p) for p in patterns)]
    assert missing == []


def test_every_stage_declares_its_outputs():
    assert list(run_all.STAGE_OUTPUTS) == list(run_all.STAGES)


def test_stages_run_in_section_order():
    stages = list(run_all.STAGES)
    assert stages[0] == "snapshots"  # the days are every capture day in the release when it runs
    assert stages[-2:] == ["answers", "readme"]
    order = ["capture_health", "eep", "iv", "surface", "density", "tails", "events", "cor3m", "live_corr", "vrp",
             "strategies", "attribution", "risk", "report"]
    assert [s for s in stages if s in order] == order


def test_no_stage_argument_runs_every_stage(monkeypatch):
    ran = []
    fake = {name: (lambda cfg, name=name, **kw: ran.append(name) or name) for name in run_all.STAGES}
    monkeypatch.setattr(run_all, "STAGES", fake)
    assert run_all.main([]) == 0
    assert ran == list(fake)


def test_snapshots_stage_prints_the_day_count(monkeypatch, tmp_path, capsys):
    from types import SimpleNamespace

    from scripts import pull_snapshots

    (tmp_path / "chains_2026-10-29.parquet").touch()
    (tmp_path / "chains_2026-11-03.parquet").touch()
    monkeypatch.setattr(pull_snapshots, "pull", lambda tag, snap, manifest: f"pulled {tag}")
    monkeypatch.setattr(run_all, "SNAPSHOTS", tmp_path)
    run_all.stage_snapshots(SimpleNamespace(snapshot=SimpleNamespace(release_tag="snapshots")))
    out = capsys.readouterr().out
    assert "pulled snapshots" in out
    assert "capture days: 3, 2026-10-28 to 2026-11-03" in out
