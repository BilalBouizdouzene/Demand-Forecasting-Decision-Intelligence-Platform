"""Chronological splits and rolling-origin evaluation."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import pandas as pd

from .metrics import metric_dict


def chronological_split(
    frame: pd.DataFrame, validation_days: int = 28, test_days: int = 28
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dates = sorted(pd.to_datetime(frame["date"]).unique())
    if len(dates) <= validation_days + test_days:
        raise ValueError("Not enough dates for requested chronological split")
    train_end = dates[-(validation_days + test_days)]
    validation_end = dates[-test_days]
    train = frame[pd.to_datetime(frame["date"]) < train_end].copy()
    validation = frame[
        (pd.to_datetime(frame["date"]) >= train_end)
        & (pd.to_datetime(frame["date"]) < validation_end)
    ].copy()
    test = frame[pd.to_datetime(frame["date"]) >= validation_end].copy()
    return train, validation, test


def rolling_origin_folds(
    frame: pd.DataFrame, horizon: int = 28, folds: int = 3, min_train_days: int = 365
) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
    dates = pd.Series(pd.to_datetime(frame["date"]).drop_duplicates().sort_values().tolist())
    if len(dates) < min_train_days + horizon * folds:
        raise ValueError("Not enough dates for requested rolling-origin folds")
    result = []
    for fold in range(folds, 0, -1):
        train_end_index = len(dates) - horizon * fold
        train_end = dates.iloc[train_end_index - 1]
        validation_dates = dates.iloc[train_end_index : train_end_index + horizon]
        train = frame[pd.to_datetime(frame["date"]) <= train_end].copy()
        validation = frame[pd.to_datetime(frame["date"]).isin(validation_dates)].copy()
        if train["date"].nunique() >= min_train_days:
            result.append((train, validation))
    return result


def evaluate_predictions(
    actual: pd.Series, forecast: pd.Series, training_history: pd.Series | None = None
) -> dict[str, float]:
    return metric_dict(
        actual.to_numpy(),
        forecast.to_numpy(),
        None if training_history is None else training_history.to_numpy(),
    )


def run_backtest(
    frame: pd.DataFrame,
    model_factories: dict[str, Callable[[], Any]],
    feature_columns: list[str],
    target: str,
    horizon: int = 28,
    folds: int = 3,
    min_train_days: int = 365,
    max_training_rows: int | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for fold_number, (train, validation) in enumerate(
        rolling_origin_folds(frame, horizon, folds, min_train_days), start=1
    ):
        train_fit = train.tail(max_training_rows) if max_training_rows else train
        for model_name, factory in model_factories.items():
            model = factory()
            started = time.perf_counter()
            model.fit(train_fit, target, feature_columns)
            predictions = model.predict(validation)
            inference_time = time.perf_counter() - started - (model.training_seconds or 0)
            metrics = metric_dict(
                validation[target].to_numpy(), predictions, train_fit["sales"].to_numpy()
            )
            rows.append(
                {
                    "model": model_name,
                    "fold": fold_number,
                    "horizon": horizon,
                    "training_seconds": model.training_seconds,
                    "inference_seconds": max(0.0, inference_time),
                    **metrics,
                }
            )
    return pd.DataFrame(rows)
