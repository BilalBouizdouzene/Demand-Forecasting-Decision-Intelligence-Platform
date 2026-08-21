"""Strong, transparent seasonal baselines."""

from __future__ import annotations

import numpy as np
import pandas as pd


def forecast_from_history(
    history: pd.Series | np.ndarray, horizon: int, method: str = "seasonal_naive_7"
) -> np.ndarray:
    values = pd.to_numeric(pd.Series(history), errors="coerce").fillna(0).to_numpy(dtype=float)
    if len(values) == 0:
        return np.zeros(horizon)
    if method == "naive_last":
        return np.repeat(values[-1], horizon)
    if method == "rolling_mean_7":
        return np.repeat(values[-min(7, len(values)) :].mean(), horizon)
    if method == "rolling_mean_28":
        return np.repeat(values[-min(28, len(values)) :].mean(), horizon)
    season = 7 if method == "seasonal_naive_7" else 28
    if len(values) < season:
        return np.repeat(values[-1], horizon)
    return np.resize(values[-season:], horizon).astype(float)


def baseline_forecast(
    frame: pd.DataFrame,
    horizon: int,
    method: str = "seasonal_naive_7",
    group: tuple[str, str] | None = None,
) -> np.ndarray:
    """Forecast one series; for a full panel use ``panel_baseline_forecast``."""
    if group is None:
        group = (str(frame["store_id"].iloc[0]), str(frame["item_id"].iloc[0]))
    store, item = group
    values = frame[
        (frame["store_id"].astype(str) == str(store)) & (frame["item_id"].astype(str) == str(item))
    ].sort_values("date")["sales"]
    return forecast_from_history(values, horizon, method)


def panel_baseline_forecast(frame: pd.DataFrame, horizon: int, method: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (store, item), group in frame.groupby(["store_id", "item_id"], observed=True):
        dates = pd.date_range(
            pd.to_datetime(group["date"]).max() + pd.Timedelta(days=1), periods=horizon, freq="D"
        )
        values = baseline_forecast(frame, horizon, method, (str(store), str(item)))
        rows.extend(
            {"store_id": store, "item_id": item, "date": date, "forecast": float(value)}
            for date, value in zip(dates, values, strict=False)
        )
    return pd.DataFrame(rows)
