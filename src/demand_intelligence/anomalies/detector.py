"""Residual z-score and interval breach detector."""

from __future__ import annotations

import numpy as np
import pandas as pd


def detect_anomalies(
    frame: pd.DataFrame,
    actual_column: str = "actual",
    forecast_column: str = "forecast",
    lower_column: str | None = "lower",
    upper_column: str | None = "upper",
    threshold: float = 3.0,
    rolling_window: int = 28,
) -> pd.DataFrame:
    result = frame.copy().sort_values([c for c in ["store_id", "item_id", "date"] if c in frame])
    result["residual"] = result[actual_column].astype(float) - result[forecast_column].astype(float)
    groups = [result[c] for c in ["store_id", "item_id"] if c in result]
    mean = result.groupby(groups, observed=True)["residual"].transform(
        lambda s: s.shift(1).rolling(rolling_window, min_periods=7).mean()
    )
    std = result.groupby(groups, observed=True)["residual"].transform(
        lambda s: s.shift(1).rolling(rolling_window, min_periods=7).std()
    )
    result["anomaly_score"] = (
        ((result["residual"] - mean) / std.replace(0, np.nan)).abs().fillna(0.0)
    )
    result["anomaly_flag"] = result["anomaly_score"] >= threshold
    result["anomaly_type"] = np.select(
        [result["residual"] > 0, result["residual"] < 0],
        ["unexpected demand spike", "unexpected demand drop"],
        default="normal",
    )
    if lower_column and upper_column and lower_column in result and upper_column in result:
        breached = (result[actual_column] < result[lower_column]) | (
            result[actual_column] > result[upper_column]
        )
        result["interval_breach"] = breached
        result["anomaly_flag"] = result["anomaly_flag"] | breached
    return result
