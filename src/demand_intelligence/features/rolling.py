"""Rolling and exponentially weighted features; every window is shifted first."""

from __future__ import annotations

import pandas as pd


def add_rolling_features(
    frame: pd.DataFrame,
    windows: list[int],
    stats: list[str] | None = None,
    ewm_spans: list[int] | None = None,
    group_columns: list[str] | None = None,
) -> pd.DataFrame:
    result = frame.sort_values([*(group_columns or ["store_id", "item_id"]), "date"]).copy()
    groups = group_columns or ["store_id", "item_id"]
    shifted = result.groupby(groups, observed=True)["sales"].shift(1)
    for window in windows:
        rolling = shifted.groupby([result[c] for c in groups], observed=True).rolling(
            window, min_periods=1
        )
        for statistic in stats or ["mean", "std", "min", "max"]:
            values = getattr(rolling, statistic)().reset_index(level=groups, drop=True)
            result[f"rolling_{statistic}_{window}"] = values.astype("float32").to_numpy()
    for span in ewm_spans or []:
        values = (
            shifted.groupby([result[c] for c in groups], observed=True)
            .ewm(span=span, adjust=False, min_periods=1)
            .mean()
        )
        result[f"ewm_mean_{span}"] = (
            values.reset_index(level=groups, drop=True).astype("float32").to_numpy()
        )
    return result
