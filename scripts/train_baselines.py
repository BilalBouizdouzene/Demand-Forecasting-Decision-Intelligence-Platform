"""Evaluate transparent baselines on the final chronological holdout."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from demand_intelligence.config import PROJECT_ROOT, ensure_dirs, load_config
from demand_intelligence.data.loaders import load_processed
from demand_intelligence.evaluation.metrics import metric_dict
from demand_intelligence.models.naive import forecast_from_history


def evaluate(frame: pd.DataFrame, horizon: int, method: str) -> dict[str, object]:
    dates = sorted(pd.to_datetime(frame["date"]).unique())
    cutoff = dates[-horizon]
    train = frame[pd.to_datetime(frame["date"]) < cutoff]
    test = frame[pd.to_datetime(frame["date"]) >= cutoff].sort_values(
        ["store_id", "item_id", "date"]
    )
    actuals, predictions, histories = [], [], []
    train_groups = {
        (str(key[0]), str(key[1])): group
        for key, group in train.groupby(["store_id", "item_id"], observed=True)
    }
    for key, group in test.groupby(["store_id", "item_id"], observed=True):
        train_group = train_groups.get((str(key[0]), str(key[1])))
        if train_group is None or train_group.empty:
            continue
        actual = group.sort_values("date")["sales"].astype(float).to_numpy()
        pred = forecast_from_history(train_group.sort_values("date")["sales"], len(actual), method)
        actuals.extend(actual)
        predictions.extend(pred)
        histories.extend(train_group.sort_values("date")["sales"].astype(float).to_numpy())
    metrics = metric_dict(np.asarray(actuals), np.asarray(predictions), np.asarray(histories))
    return {"model": method, "horizon": horizon, **metrics}


if __name__ == "__main__":
    ensure_dirs()
    cfg = load_config("data.yaml")["data"]
    frame = load_processed(PROJECT_ROOT / cfg["processed_dir"] / cfg["processed_filename"])
    rows = [
        evaluate(frame, horizon, method)
        for horizon in [1, 7, 28]
        for method in [
            "naive_last",
            "seasonal_naive_7",
            "seasonal_naive_28",
            "rolling_mean_7",
            "rolling_mean_28",
        ]
    ]
    output = PROJECT_ROOT / "results/metrics/baseline_benchmark.csv"
    pd.DataFrame(rows).to_csv(output, index=False)
    print(pd.DataFrame(rows).to_string(index=False))
