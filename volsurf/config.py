"""config.toml as nested frozen dataclasses (CLAUDE.md Section 6.1): one dataclass per table."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, make_dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _freeze(value, name: str):
    """Tables become frozen dataclasses, lists become tuples, scalars stay as they are."""
    if isinstance(value, dict):
        fields = [(k, object) for k in value]
        cls = make_dataclass(name.title().replace("_", ""), fields, frozen=True)
        return cls(**{k: _freeze(v, k) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v, name) for v in value)
    return value


@dataclass(frozen=True)
class Config:
    run: object
    universe: object
    snapshot: object
    clean: object
    pricing: object
    eep: object
    iv: object
    forwards: object
    svi: object
    surface: object
    density: object
    events: object
    correlation: object
    vrp: object
    sim: object
    book: object
    limits: object
    risk: object
    tolerances: object


def load_config(path: str | Path = "config.toml") -> Config:
    path = Path(path)
    if not path.is_absolute() and not path.exists():
        path = ROOT / path
    with open(path, "rb") as fh:
        raw = tomllib.load(fh)
    return Config(**{k: _freeze(v, k) for k, v in raw.items()})
