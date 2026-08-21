"""Composable feature pipeline and supervised target construction."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .calendar import add_calendar_features
from .events import add_event_features
from .lags import add_lag_features
from .prices import add_price_features
from .rolling import add_rolling_features


def build_features(frame: pd.DataFrame, config: dict[str, Any] | None = None) -> pd.DataFrame:
    config = config or {}
    result = frame.copy()
    result["date"] = pd.to_datetime(result["date"])
    result = add_calendar_features(result, cyclical=config.get("add_cyclical_features", True))
    result = add_lag_features(result, config.get("lags", [1, 7, 14, 28, 56]))
    result = add_rolling_features(
        result,
        config.get("rolling_windows", [7, 14, 28]),
        config.get("rolling_stats", ["mean", "std", "min", "max"]),
        config.get("ewm_spans", [7, 28]),
    )
    if config.get("add_price_features", True):
        result = add_price_features(result)
    if config.get("add_event_features", True):
        result = add_event_features(result)
    result["series_code"] = (
        pd.factorize(result["series_id"].astype(str))[0].astype("int32")
        if "series_id" in result
        else 0
    )
    result = result.replace([np.inf, -np.inf], np.nan)
    return result


def make_supervised(
    frame: pd.DataFrame, horizon: int, drop_na: bool = True
) -> tuple[pd.DataFrame, str]:
    """Create a future target while preserving feature values at forecast origin."""
    result = frame.sort_values(["store_id", "item_id", "date"]).copy()
    target = f"target_h{horizon}"
    result[target] = result.groupby(["store_id", "item_id"], observed=True)["sales"].shift(-horizon)
    if drop_na:
        result = result.dropna(subset=[target])
    return result, target


def feature_columns(frame: pd.DataFrame, target: str | None = None) -> list[str]:
    excluded = {"sales", "date", "d", "id", "series_id", target or "", "target"}
    return [
        c
        for c in frame.columns
        if c not in excluded and not c.startswith("event_name") and not c.startswith("event_type")
    ]
