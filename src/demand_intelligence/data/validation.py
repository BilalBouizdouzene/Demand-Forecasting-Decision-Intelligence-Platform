"""Data quality checks that fail on severe structural issues and report expected gaps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def validate_long_frame(
    frame: pd.DataFrame, report_path: str | Path | None = None
) -> dict[str, Any]:
    required = {"date", "item_id", "store_id", "sales"}
    missing_columns = sorted(required - set(frame.columns))
    errors: list[str] = []
    warnings: list[str] = []
    if missing_columns:
        errors.append(f"Missing required columns: {missing_columns}")
    duplicates = (
        int(frame.duplicated(["date", "store_id", "item_id"]).sum()) if not missing_columns else 0
    )
    if duplicates:
        errors.append(f"Duplicate date/store/item rows: {duplicates}")
    negative_sales = int(
        (pd.to_numeric(frame.get("sales", pd.Series(dtype=float)), errors="coerce") < 0).sum()
    )
    if negative_sales:
        errors.append(f"Negative sales values: {negative_sales}")
    missing_ids = (
        int(frame[[c for c in ["item_id", "store_id"] if c in frame]].isna().any(axis=1).sum())
        if not missing_columns
        else 0
    )
    if missing_ids:
        errors.append(f"Rows with missing IDs: {missing_ids}")
    if "sell_price" in frame:
        invalid_prices = int((pd.to_numeric(frame["sell_price"], errors="coerce") < 0).sum())
        if invalid_prices:
            errors.append(f"Negative prices: {invalid_prices}")
        if frame["sell_price"].isna().mean() > 0:
            warnings.append("M5 price coverage is not complete for every date/item/store row.")
    if "date" in frame:
        dates = pd.to_datetime(frame["date"], errors="coerce")
        if dates.isna().any():
            errors.append("Unparseable dates detected")
        if (dates.dt.month < 1).any() or (dates.dt.month > 12).any():
            errors.append("Impossible calendar month values detected")
    series_counts = (
        frame.groupby(["item_id", "store_id"], observed=True).size()
        if not missing_columns
        else pd.Series(dtype=int)
    )
    report: dict[str, Any] = {
        "row_count": int(len(frame)),
        "series_count": int(len(series_counts)),
        "date_min": str(pd.to_datetime(frame["date"]).min())
        if "date" in frame and len(frame)
        else None,
        "date_max": str(pd.to_datetime(frame["date"]).max())
        if "date" in frame and len(frame)
        else None,
        "duplicate_series_date_rows": duplicates,
        "negative_sales": negative_sales,
        "missing_id_rows": missing_ids,
        "missingness": {
            str(k): float(v)
            for k, v in frame.isna().mean().sort_values(ascending=False).head(30).items()
        },
        "warnings": warnings,
        "errors": errors,
        "valid": not errors,
    }
    if report_path:
        path = Path(report_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    if errors:
        raise ValueError("Long-format validation failed: " + "; ".join(errors))
    return report
