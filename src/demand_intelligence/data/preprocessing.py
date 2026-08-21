"""M5 preparation orchestration and compact data profiling."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .loaders import read_calendar, read_prices, read_sales_rows, wide_to_long
from .sampling import select_representative_series
from .validation import validate_long_frame


def prepare_m5_subset(
    raw_dir: str | Path,
    processed_path: str | Path,
    metadata_path: str | Path,
    max_items: int = 100,
    max_stores: int = 10,
    chunksize: int = 2048,
    seed: int = 42,
    force: bool = False,
) -> pd.DataFrame:
    processed = Path(processed_path)
    if processed.exists() and not force:
        return pd.read_parquet(processed)
    raw = Path(raw_dir)
    pairs, _ = select_representative_series(
        raw / "sales_train_validation.csv",
        max_items=max_items,
        max_stores=max_stores,
        chunksize=chunksize,
        seed=seed,
        metadata_path=metadata_path,
    )
    sales = read_sales_rows(raw / "sales_train_validation.csv", pairs=pairs, chunksize=chunksize)
    calendar = read_calendar(raw / "calendar.csv")
    prices = read_prices(raw / "sell_prices.csv")
    long = wide_to_long(sales, calendar, prices)
    validate_long_frame(
        long, processed.parent.parent.parent / "results" / "reports" / "validation_report.json"
    )
    processed.parent.mkdir(parents=True, exist_ok=True)
    long.to_parquet(processed, index=False)
    return long


def profile_dataset(
    frame: pd.DataFrame, output_json: str | Path, output_md: str | Path
) -> dict[str, Any]:
    sales = pd.to_numeric(frame["sales"], errors="coerce")
    profile: dict[str, Any] = {
        "rows": int(len(frame)),
        "series": int(frame[["item_id", "store_id"]].drop_duplicates().shape[0]),
        "items": int(frame["item_id"].nunique()),
        "stores": int(frame["store_id"].nunique()),
        "states": int(frame["state_id"].nunique()) if "state_id" in frame else None,
        "departments": int(frame["dept_id"].nunique()) if "dept_id" in frame else None,
        "categories": int(frame["cat_id"].nunique()) if "cat_id" in frame else None,
        "date_min": str(pd.to_datetime(frame["date"]).min()),
        "date_max": str(pd.to_datetime(frame["date"]).max()),
        "total_sales": float(sales.sum()),
        "mean_daily_sales_per_row": float(sales.mean()),
        "sales_quantiles": {str(q): float(sales.quantile(q)) for q in [0, 0.5, 0.9, 0.99, 1]},
        "zero_sales_proportion": float((sales == 0).mean()),
        "missingness": {
            str(k): float(v)
            for k, v in frame.isna().mean().sort_values(ascending=False).head(30).items()
        },
        "price_coverage": float(frame["sell_price"].notna().mean())
        if "sell_price" in frame
        else None,
        "event_days": int(
            frame[[c for c in ["event_name_1", "event_name_2"] if c in frame]]
            .notna()
            .any(axis=1)
            .sum()
        )
        if any(c in frame for c in ["event_name_1", "event_name_2"])
        else 0,
    }
    json_path, md_path = Path(output_json), Path(output_md)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    lines = [
        "# M5 data profile",
        "",
        "This profile is calculated from the selected local M5 subset.",
        "",
    ]
    for key, value in profile.items():
        lines.append(f"- **{key}**: `{value}`")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return profile
