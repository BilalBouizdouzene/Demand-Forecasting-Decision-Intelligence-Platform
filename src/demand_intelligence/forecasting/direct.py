"""Direct multi-horizon training utilities."""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd

from ..features.pipeline import make_supervised


def fit_direct_models(
    frame: pd.DataFrame,
    horizons: list[int],
    model_factory: Callable[[], object],
    features: list[str],
) -> dict[int, object]:
    models = {}
    for horizon in horizons:
        supervised, target = make_supervised(frame, horizon)
        model = model_factory()
        model.fit(supervised, target, features)
        models[horizon] = model
    return models
