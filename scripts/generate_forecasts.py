"""Generate recursive forecasts in batches across the selected panel."""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from demand_intelligence.config import PROJECT_ROOT
from demand_intelligence.forecasting.intervals import make_interval


def _m5_wday(date: pd.Timestamp) -> int:
    return {5: 1, 6: 2, 0: 3, 1: 4, 2: 5, 3: 6, 4: 7}[date.dayofweek]


def _future_row(last: dict, sales: list[float], date: pd.Timestamp) -> dict:
    row = dict(last)
    row["sales"] = np.nan
    row["date"] = date
    row["weekday"] = date.day_name()
    row["wday"] = _m5_wday(date)
    row["month"] = date.month
    row["year"] = date.year
    row["day_of_week"] = date.dayofweek
    row["day_of_month"] = date.day
    row["week_of_year"] = date.isocalendar().week
    row["month_num"] = date.month
    row["quarter"] = date.quarter
    row["year_num"] = date.year
    row["is_weekend"] = int(date.dayofweek >= 5)
    row["is_month_start"] = int(date.is_month_start)
    row["is_month_end"] = int(date.is_month_end)
    row["dow_sin"] = float(np.sin(2 * np.pi * date.dayofweek / 7))
    row["dow_cos"] = float(np.cos(2 * np.pi * date.dayofweek / 7))
    row["month_sin"] = float(np.sin(2 * np.pi * date.month / 12))
    row["month_cos"] = float(np.cos(2 * np.pi * date.month / 12))
    for lag in [1, 7, 14, 28, 56]:
        row[f"lag_{lag}"] = sales[-lag] if len(sales) >= lag else np.nan
    for window in [7, 14, 28]:
        values = np.asarray(sales[-window:], dtype=float)
        row[f"rolling_mean_{window}"] = float(values.mean()) if len(values) else np.nan
        row[f"rolling_std_{window}"] = float(values.std(ddof=1)) if len(values) > 1 else np.nan
        row[f"rolling_min_{window}"] = float(values.min()) if len(values) else np.nan
        row[f"rolling_max_{window}"] = float(values.max()) if len(values) else np.nan
    for span in [7, 28]:
        row[f"ewm_mean_{span}"] = (
            float(pd.Series(sales).ewm(span=span, adjust=False).mean().iloc[-1])
            if sales
            else np.nan
        )
    if "sell_price" in row:
        row["price_lag_1"] = row["sell_price"]
        row["price_change"] = 0.0
        row["price_change_pct"] = 0.0
        row["price_vs_rolling_mean"] = 1.0
    row["has_event"] = 0
    row["snap_active"] = max(
        float(row.get("snap_CA", 0) or 0),
        float(row.get("snap_TX", 0) or 0),
        float(row.get("snap_WI", 0) or 0),
    )
    return row


def recursive_panel(frame: pd.DataFrame, model, horizon: int = 28) -> pd.DataFrame:
    states = {}
    for key, group in frame.groupby(["store_id", "item_id"], observed=True):
        group = group.sort_values("date")
        states[key] = {
            "last": group.iloc[-1].to_dict(),
            "sales": group["sales"].astype(float).tolist(),
            "last_date": pd.Timestamp(group["date"].max()),
        }
    rows: list[dict] = []
    for step in range(1, horizon + 1):
        future_rows = []
        keys = []
        for key, state in states.items():
            future_rows.append(
                _future_row(
                    state["last"], state["sales"], state["last_date"] + pd.Timedelta(step, unit="D")
                )
            )
            keys.append(key)
        current = pd.DataFrame(future_rows)
        for column in model.feature_columns:
            if column not in current:
                current[column] = 0
        predictions = model.predict(current)
        for key, row, prediction in zip(keys, future_rows, predictions, strict=True):
            value = float(prediction)
            states[key]["sales"].append(value)
            states[key]["last"] = row
            rows.append(
                {
                    "store_id": key[0],
                    "item_id": key[1],
                    "date": row["date"],
                    "forecast": value,
                    "horizon": step,
                }
            )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    bundle = joblib.load(PROJECT_ROOT / "results/forecasts/model.joblib")
    frame = pd.read_parquet(PROJECT_ROOT / "data/processed/m5_features.parquet")
    forecasts = recursive_panel(frame, bundle["models"][1], 28)
    radius = float(bundle["interval_radii"].get(1, 0.0))
    forecasts["lower_bound"], forecasts["upper_bound"] = make_interval(
        forecasts["forecast"], radius
    )
    forecasts.to_csv(PROJECT_ROOT / "results/forecasts/latest_forecasts.csv", index=False)
    print(
        f"Wrote {len(forecasts):,} forecast rows across {forecasts[['store_id', 'item_id']].drop_duplicates().shape[0]:,} series."
    )
