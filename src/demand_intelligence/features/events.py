"""Event and SNAP encodings from the M5 calendar."""

from __future__ import annotations

import pandas as pd


def add_event_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    event_columns = [
        c for c in ["event_name_1", "event_type_1", "event_name_2", "event_type_2"] if c in result
    ]
    result["has_event"] = (
        result[event_columns].notna().any(axis=1).astype("int8") if event_columns else 0
    )
    for column in event_columns:
        values = result[column].astype("string").fillna("NONE")
        result[f"{column}_code"] = values.astype("category").cat.codes.astype("int16")
    snap_columns = [c for c in ["snap_CA", "snap_TX", "snap_WI"] if c in result]
    if snap_columns:
        result["snap_active"] = result[snap_columns].fillna(0).max(axis=1).astype("int8")
    return result
