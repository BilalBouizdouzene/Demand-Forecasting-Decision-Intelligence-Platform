"""Past-only lags."""

from __future__ import annotations

import pandas as pd


def add_lag_features(
    frame: pd.DataFrame, lags: list[int], group_columns: list[str] | None = None
) -> pd.DataFrame:
    result = frame.sort_values([*(group_columns or ["store_id", "item_id"]), "date"]).copy()
    groups = group_columns or ["store_id", "item_id"]
    for lag in lags:
        result[f"lag_{lag}"] = (
            result.groupby(groups, observed=True)["sales"].shift(lag).astype("float32")
        )
    return result
