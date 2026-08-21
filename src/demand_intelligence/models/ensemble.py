"""Simple non-negative weighted forecast ensemble."""

from __future__ import annotations

import numpy as np


def weighted_average(
    predictions: dict[str, np.ndarray], weights: dict[str, float] | None = None
) -> np.ndarray:
    if not predictions:
        return np.array([])
    weights = weights or {name: 1.0 for name in predictions}
    total = sum(max(0.0, float(weights.get(name, 0.0))) for name in predictions)
    if total == 0:
        return np.mean(list(predictions.values()), axis=0)
    return (
        np.sum(
            [predictions[name] * max(0.0, float(weights.get(name, 0.0))) for name in predictions],
            axis=0,
        )
        / total
    )
