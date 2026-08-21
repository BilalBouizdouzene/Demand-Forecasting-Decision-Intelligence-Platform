"""Residual calculation helpers."""

from __future__ import annotations

import pandas as pd


def add_residuals(
    frame: pd.DataFrame, actual: str = "actual", forecast: str = "forecast"
) -> pd.DataFrame:
    result = frame.copy()
    result["residual"] = result[actual].astype(float) - result[forecast].astype(float)
    return result
