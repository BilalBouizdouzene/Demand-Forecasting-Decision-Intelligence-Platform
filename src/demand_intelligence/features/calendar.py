"""Calendar and cyclical features derived from observed calendar columns."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_calendar_features(frame: pd.DataFrame, cyclical: bool = True) -> pd.DataFrame:
    result = frame.copy()
    dates = pd.to_datetime(result["date"])
    result["day_of_week"] = dates.dt.dayofweek.astype("int8")
    result["day_of_month"] = dates.dt.day.astype("int8")
    result["week_of_year"] = dates.dt.isocalendar().week.astype("int16")
    result["month_num"] = dates.dt.month.astype("int8")
    result["quarter"] = dates.dt.quarter.astype("int8")
    result["year_num"] = dates.dt.year.astype("int16")
    result["is_weekend"] = (result["day_of_week"] >= 5).astype("int8")
    result["is_month_start"] = dates.dt.is_month_start.astype("int8")
    result["is_month_end"] = dates.dt.is_month_end.astype("int8")
    if cyclical:
        result["dow_sin"] = np.sin(2 * np.pi * result["day_of_week"] / 7).astype("float32")
        result["dow_cos"] = np.cos(2 * np.pi * result["day_of_week"] / 7).astype("float32")
        result["month_sin"] = np.sin(2 * np.pi * result["month_num"] / 12).astype("float32")
        result["month_cos"] = np.cos(2 * np.pi * result["month_num"] / 12).astype("float32")
    return result
