"""Feature importance extraction that works for tree models and linear models."""

from __future__ import annotations

import pandas as pd


def extract_feature_importance(model) -> pd.DataFrame:
    estimator = getattr(model, "estimator", model)
    preprocessor = getattr(model, "preprocessor", None)
    if hasattr(estimator, "feature_importances_"):
        values = estimator.feature_importances_
    elif hasattr(estimator, "coef_"):
        import numpy as np

        values = np.abs(estimator.coef_)
    else:
        return pd.DataFrame(columns=["feature", "importance"])
    if preprocessor is not None:
        try:
            names = preprocessor.get_feature_names_out()
        except (AttributeError, ValueError):
            names = [f"feature_{i}" for i in range(len(values))]
    else:
        names = getattr(model, "feature_columns", [f"feature_{i}" for i in range(len(values))])
    return (
        pd.DataFrame({"feature": names, "importance": values})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )
