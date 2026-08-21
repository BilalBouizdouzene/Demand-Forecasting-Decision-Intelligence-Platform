"""Past-only price movement features."""

from __future__ import annotations

import pandas as pd


def add_price_features(frame: pd.DataFrame, group_columns: list[str] | None = None) -> pd.DataFrame:
    result = frame.sort_values([*(group_columns or ["store_id", "item_id"]), "date"]).copy()
    groups = group_columns or ["store_id", "item_id"]
    if "sell_price" not in result:
        result["sell_price"] = pd.NA
    price = pd.to_numeric(result["sell_price"], errors="coerce").astype("float32")
    result["price_lag_1"] = price.groupby([result[c] for c in groups], observed=True).shift(1)
    result["price_change"] = price - result["price_lag_1"]
    result["price_change_pct"] = result["price_change"] / result["price_lag_1"].replace(0, pd.NA)
    result["price_vs_rolling_mean"] = price / price.groupby(
        [result[c] for c in groups], observed=True
    ).transform(lambda x: x.shift(1).rolling(28, min_periods=1).mean())
    return result
