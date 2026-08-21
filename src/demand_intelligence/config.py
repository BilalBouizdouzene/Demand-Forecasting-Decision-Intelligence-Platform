"""Configuration helpers shared by scripts, API, and dashboard."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_config(name: str) -> dict[str, Any]:
    return load_yaml(PROJECT_ROOT / "configs" / name)


def ensure_dirs() -> None:
    for relative in (
        "data/raw",
        "data/interim",
        "data/processed",
        "data/external",
        "results/metrics",
        "results/forecasts",
        "results/figures",
        "results/explainability",
        "results/anomalies",
        "results/decisions",
        "results/reports",
    ):
        (PROJECT_ROOT / relative).mkdir(parents=True, exist_ok=True)
