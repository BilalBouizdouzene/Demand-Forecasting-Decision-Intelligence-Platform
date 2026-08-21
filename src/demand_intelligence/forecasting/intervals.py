"""Conformal-style residual intervals with transparent finite-sample calibration."""

from __future__ import annotations

import numpy as np

from ..evaluation.metrics import interval_coverage, interval_width


def conformal_radius(actual, forecast, alpha: float = 0.10) -> float:
    residuals = np.abs(np.asarray(actual, dtype=float) - np.asarray(forecast, dtype=float))
    if residuals.size == 0:
        return 0.0
    quantile = min(1.0, max(0.0, (1 - alpha) * (1 + 1 / residuals.size)))
    return float(np.quantile(residuals, quantile, method="higher"))


def make_interval(forecast, radius: float) -> tuple[np.ndarray, np.ndarray]:
    point = np.maximum(0.0, np.asarray(forecast, dtype=float))
    return np.maximum(0.0, point - radius), point + radius


def evaluate_interval(actual, lower, upper) -> dict[str, float]:
    return {
        "coverage": interval_coverage(actual, lower, upper),
        "average_width": interval_width(lower, upper),
    }
