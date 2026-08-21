"""Representative, configurable series selection for constrained local runs."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from .loaders import ID_COLUMNS, read_sales_header

LOGGER = logging.getLogger(__name__)


def select_representative_series(
    sales_path: str | Path,
    max_items: int = 100,
    max_stores: int = 10,
    chunksize: int = 2048,
    seed: int = 42,
    metadata_path: str | Path | None = None,
) -> tuple[set[tuple[str, str]], pd.DataFrame]:
    """Select stores and products spanning categories and demand-volume segments.

    Selection is based on observed historical sales, not arbitrary first rows. The
    result is deterministic for a fixed seed and is persisted by the preparation script.
    """
    np.random.default_rng(seed)
    day_columns = [c for c in read_sales_header(sales_path) if c.startswith("d_")]
    usecols = ID_COLUMNS + day_columns
    summary_parts: list[pd.DataFrame] = []
    for chunk in pd.read_csv(sales_path, usecols=usecols, chunksize=chunksize, low_memory=False):
        chunk["total_sales"] = chunk[day_columns].sum(axis=1).astype("float64")
        chunk["zero_rate"] = (chunk[day_columns] == 0).mean(axis=1).astype("float32")
        summary_parts.append(chunk[ID_COLUMNS + ["total_sales", "zero_rate"]])
    summary = pd.concat(summary_parts, ignore_index=True)
    store_table = summary.groupby(["state_id", "store_id"], as_index=False)["total_sales"].sum()
    store_table = store_table.sort_values(["state_id", "store_id"])
    if max_stores < len(store_table):
        # Round-robin across states, then use deterministic seeded order for ties.
        chosen_stores: list[str] = []
        for _, group in store_table.groupby("state_id", sort=True):
            chosen_stores.extend(group["store_id"].tolist())
        chosen_stores = chosen_stores[:max_stores]
    else:
        chosen_stores = store_table["store_id"].tolist()
    scoped = summary[summary["store_id"].isin(chosen_stores)].copy()
    item_summary = scoped.groupby(["item_id", "cat_id", "dept_id"], as_index=False).agg(
        total_sales=("total_sales", "sum"),
        zero_rate=("zero_rate", "mean"),
    )
    item_summary["volume_segment"] = pd.qcut(
        item_summary["total_sales"].rank(method="first"),
        q=3,
        labels=["low", "medium", "high"],
    )
    candidate_items: list[str] = []
    for _, group in item_summary.groupby("cat_id", sort=True):
        for segment in ["low", "medium", "high"]:
            segment_rows = group[group["volume_segment"].astype(str) == segment]
            if not segment_rows.empty:
                candidate_items.append(
                    segment_rows.sort_values("total_sales").iloc[len(segment_rows) // 2]["item_id"]
                )
    remaining = item_summary[~item_summary["item_id"].isin(candidate_items)].sort_values(
        "total_sales"
    )
    candidate_items.extend(remaining["item_id"].tolist())
    candidate_items = list(dict.fromkeys(candidate_items))[:max_items]
    selected = scoped[scoped["item_id"].isin(candidate_items)].copy()
    selected = selected[selected["store_id"].isin(chosen_stores)]
    selected["selected"] = True
    selected["selection_reason"] = selected.apply(
        lambda row: (
            f"category={row['cat_id']};volume={item_summary.loc[item_summary['item_id'].eq(row['item_id']), 'volume_segment'].iloc[0]}"
        ),
        axis=1,
    )
    selected = selected.sort_values(["store_id", "item_id"])
    selected["selection_seed"] = seed
    selected["selection_method"] = "category-balanced-volume-segments"
    if metadata_path:
        output = Path(metadata_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        selected.to_csv(output, index=False)
        output.with_suffix(".json").write_text(
            json.dumps(
                {
                    "max_items": max_items,
                    "max_stores": max_stores,
                    "seed": seed,
                    "series_count": len(selected),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    LOGGER.info(
        "Selected %d item-store series across %d stores and %d items",
        len(selected),
        selected["store_id"].nunique(),
        selected["item_id"].nunique(),
    )
    pairs = set(
        zip(selected["item_id"].astype(str), selected["store_id"].astype(str), strict=False)
    )
    return pairs, selected
