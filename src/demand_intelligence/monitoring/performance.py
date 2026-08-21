"""Performance degradation checks and retraining recommendations."""

from __future__ import annotations

import pandas as pd


def performance_drift(
    frame: pd.DataFrame, date_column: str = "date", error_column: str = "absolute_error"
) -> pd.DataFrame:
    result = frame.copy()
    result[date_column] = pd.to_datetime(result[date_column])
    return (
        result.groupby(result[date_column].dt.to_period("W"))
        .agg(mae=(error_column, "mean"), rows=(error_column, "size"))
        .reset_index()
        .assign(period=lambda x: x[date_column].astype(str))
        .drop(columns=[date_column])
    )


def retraining_recommendation(
    recent_mae: float, reference_mae: float, degradation_threshold: float = 0.20
) -> dict[str, object]:
    ratio = (recent_mae - reference_mae) / reference_mae if reference_mae else float("inf")
    return {
        "retraining_recommended": bool(ratio > degradation_threshold),
        "degradation_ratio": float(ratio),
        "threshold": degradation_threshold,
        "action": "review and retrain candidate; do not overwrite production automatically"
        if ratio > degradation_threshold
        else "continue monitoring",
    }
