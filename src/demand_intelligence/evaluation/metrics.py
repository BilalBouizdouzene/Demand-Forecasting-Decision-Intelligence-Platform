"""Forecast metrics with zero-safe definitions."""

from __future__ import annotations

import numpy as np


def _arrays(actual, forecast) -> tuple[np.ndarray, np.ndarray]:
    y = np.asarray(actual, dtype=float)
    p = np.asarray(forecast, dtype=float)
    if y.shape != p.shape:
        raise ValueError(f"Shape mismatch: actual={y.shape}, forecast={p.shape}")
    return y, p


def mae(actual, forecast) -> float:
    y, p = _arrays(actual, forecast)
    return float(np.mean(np.abs(y - p)))


def rmse(actual, forecast) -> float:
    y, p = _arrays(actual, forecast)
    return float(np.sqrt(np.mean((y - p) ** 2)))


def wape(actual, forecast) -> float:
    y, p = _arrays(actual, forecast)
    denominator = np.abs(y).sum()
    return float(np.abs(y - p).sum() / denominator) if denominator else float("nan")


def mape(actual, forecast) -> float:
    y, p = _arrays(actual, forecast)
    mask = y != 0
    return float(np.mean(np.abs((y[mask] - p[mask]) / y[mask]))) if mask.any() else float("nan")


def smape(actual, forecast) -> float:
    y, p = _arrays(actual, forecast)
    denominator = np.abs(y) + np.abs(p)
    terms = np.divide(
        2 * np.abs(y - p), denominator, out=np.zeros_like(denominator), where=denominator != 0
    )
    return float(np.mean(terms))


def rmsse(actual, forecast, training_history) -> float:
    y, p = _arrays(actual, forecast)
    history = np.asarray(training_history, dtype=float)
    scale = np.mean(np.diff(history) ** 2) if len(history) > 1 else 0.0
    return float(np.sqrt(np.mean((y - p) ** 2) / scale)) if scale > 0 else float("nan")


def interval_coverage(actual, lower, upper) -> float:
    y = np.asarray(actual, dtype=float)
    return float(np.mean((y >= np.asarray(lower)) & (y <= np.asarray(upper))))


def interval_width(lower, upper) -> float:
    return float(np.mean(np.asarray(upper, dtype=float) - np.asarray(lower, dtype=float)))


def metric_dict(actual, forecast, training_history=None) -> dict[str, float]:
    result = {
        "mae": mae(actual, forecast),
        "rmse": rmse(actual, forecast),
        "wape": wape(actual, forecast),
        "mape": mape(actual, forecast),
        "smape": smape(actual, forecast),
    }
    if training_history is not None:
        result["rmsse"] = rmsse(actual, forecast, training_history)
    return result
