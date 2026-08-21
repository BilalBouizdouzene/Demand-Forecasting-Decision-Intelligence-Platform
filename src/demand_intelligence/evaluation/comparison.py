"""Benchmark aggregation and model selection report."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def summarize_benchmark(raw_results: pd.DataFrame) -> pd.DataFrame:
    numeric = [
        c
        for c in [
            "mae",
            "rmse",
            "wape",
            "mape",
            "smape",
            "rmsse",
            "training_seconds",
            "inference_seconds",
        ]
        if c in raw_results
    ]
    return (
        raw_results.groupby(["model", "horizon"], as_index=False)[numeric]
        .mean()
        .sort_values(["horizon", "wape"])
    )


def write_model_selection(summary: pd.DataFrame, path: str | Path) -> None:
    best = summary.sort_values(["horizon", "wape"]).groupby("horizon", as_index=False).first()
    lines = [
        "# Model selection",
        "",
        "Models are ranked mainly by WAPE, then reviewed for stability across folds and runtime. The table below comes from the backtest run.",
        "",
    ]
    if best.empty:
        lines.append(
            "No benchmark results are available yet. Run `python scripts/run_backtest.py` after preparing data."
        )
    else:
        lines.append("```text")
        lines.append(best.to_string(index=False))
        lines.append("```")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
