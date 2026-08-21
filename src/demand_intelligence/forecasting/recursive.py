"""Recursive forecasting contract used by lightweight deployments."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np


def recursive_forecast(
    last_values: list[float],
    horizon: int,
    one_step_predictor: Callable[[list[float]], float],
    max_history: int = 56,
) -> np.ndarray:
    history = list(map(float, last_values))
    forecasts: list[float] = []
    for _ in range(horizon):
        prediction = max(0.0, float(one_step_predictor(history)))
        forecasts.append(prediction)
        history = (history + [prediction])[-max_history:]
    return np.asarray(forecasts)
