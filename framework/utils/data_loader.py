"""Load test data and JSON schemas from the project's data/ and schemas/ dirs.

Paths may be given absolute, relative to the project root, or as a bare file
name that is resolved against the ``data/`` directory (for ``load_json``) or
``schemas/`` (for ``load_schema``).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _PROJECT_ROOT / "data"
_SCHEMA_DIR = _PROJECT_ROOT / "schemas"


def _resolve(path: str | Path, default_dir: Path) -> Path:
    p = Path(path)
    if p.is_absolute() and p.exists():
        return p
    candidates = [_PROJECT_ROOT / p, default_dir / p, default_dir / p.name]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not locate data file '{path}'. Tried: {candidates}")


def load_json(path: str | Path) -> Any:
    resolved = _resolve(path, _DATA_DIR)
    with resolved.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_yaml(path: str | Path) -> Any:
    resolved = _resolve(path, _DATA_DIR)
    with resolved.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_schema(name: str | Path) -> Any:
    resolved = _resolve(name, _SCHEMA_DIR)
    with resolved.open("r", encoding="utf-8") as handle:
        return json.load(handle)
