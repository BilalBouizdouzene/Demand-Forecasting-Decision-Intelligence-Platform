"""Memory-conscious readers and M5 wide-to-long transformation."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

import pandas as pd

LOGGER = logging.getLogger(__name__)
ID_COLUMNS = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"]


def file_signature(path: str | Path) -> str:
    path = Path(path)
    stat = path.stat()
    return hashlib.sha256(
        f"{path.resolve()}:{stat.st_size}:{stat.st_mtime_ns}".encode()
    ).hexdigest()[:16]


def read_sales_header(path: str | Path) -> list[str]:
    return list(pd.read_csv(path, nrows=0).columns)


def read_sales_metadata(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path, usecols=ID_COLUMNS, dtype="string")


def read_calendar(path: str | Path) -> pd.DataFrame:
    calendar = pd.read_csv(path, low_memory=False)
    calendar["date"] = pd.to_datetime(calendar["date"], errors="raise")
    return calendar


def read_prices(path: str | Path) -> pd.DataFrame:
    prices = pd.read_csv(
        path, dtype={"store_id": "string", "item_id": "string", "wm_yr_wk": "int32"}
    )
    prices["sell_price"] = pd.to_numeric(prices["sell_price"], errors="coerce").astype("float32")
    return prices


def read_sales_rows(
    path: str | Path, pairs: set[tuple[str, str]] | None = None, chunksize: int = 2048
) -> pd.DataFrame:
    """Read selected sales rows in chunks; the full matrix is never required for subset runs."""
    day_columns = [column for column in read_sales_header(path) if column.startswith("d_")]
    usecols = ID_COLUMNS + day_columns
    chunks: list[pd.DataFrame] = []
    for chunk in pd.read_csv(path, usecols=usecols, chunksize=chunksize, low_memory=False):
        if pairs is not None:
            key = list(
                zip(chunk["item_id"].astype(str), chunk["store_id"].astype(str), strict=False)
            )
            chunk = chunk[[pair in pairs for pair in key]]
        if not chunk.empty:
            chunks.append(chunk)
    if not chunks:
        return pd.DataFrame(columns=usecols)
    result = pd.concat(chunks, ignore_index=True)
    for column in day_columns:
        result[column] = pd.to_numeric(result[column], errors="coerce").fillna(0).astype("float32")
    return result


def _downcast_ids(frame: pd.DataFrame) -> pd.DataFrame:
    for column in [
        "item_id",
        "dept_id",
        "cat_id",
        "store_id",
        "state_id",
        "event_name_1",
        "event_type_1",
        "event_name_2",
        "event_type_2",
        "weekday",
    ]:
        if column in frame:
            frame[column] = frame[column].astype("category")
    return frame


def wide_to_long(
    sales: pd.DataFrame,
    calendar: pd.DataFrame,
    prices: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Convert M5 sales to one row per date/store/item and join calendar/prices."""
    day_columns = [column for column in sales.columns if column.startswith("d_")]
    long = sales.melt(id_vars=ID_COLUMNS, value_vars=day_columns, var_name="d", value_name="sales")
    long["sales"] = pd.to_numeric(long["sales"], errors="coerce").fillna(0).astype("float32")
    calendar_columns = [column for column in calendar.columns if column not in {"date", "d"}]
    long = long.merge(
        calendar[["d", "date", *calendar_columns]], on="d", how="left", validate="many_to_one"
    )
    if prices is not None and "wm_yr_wk" in long.columns:
        long = long.merge(
            prices[["store_id", "item_id", "wm_yr_wk", "sell_price"]],
            on=["store_id", "item_id", "wm_yr_wk"],
            how="left",
            validate="many_to_one",
        )
    long["series_id"] = long["store_id"].astype(str) + "__" + long["item_id"].astype(str)
    long = long.sort_values(["series_id", "date"], kind="stable").reset_index(drop=True)
    return _downcast_ids(long)


def load_processed(path: str | Path) -> pd.DataFrame:
    return pd.read_parquet(path)
