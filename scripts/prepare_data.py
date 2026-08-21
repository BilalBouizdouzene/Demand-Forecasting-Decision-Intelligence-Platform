"""Create the cached representative M5 parquet dataset."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from demand_intelligence.config import PROJECT_ROOT, ensure_dirs, load_config
from demand_intelligence.data.download import validate_raw_files
from demand_intelligence.data.preprocessing import prepare_m5_subset, profile_dataset
from demand_intelligence.logging_utils import configure_logging

if __name__ == "__main__":
    configure_logging()
    ensure_dirs()
    data_cfg = load_config("data.yaml")["data"]
    raw_dir = PROJECT_ROOT / data_cfg["raw_dir"]
    validate_raw_files(raw_dir)
    processed = PROJECT_ROOT / data_cfg["processed_dir"] / data_cfg["processed_filename"]
    frame = prepare_m5_subset(
        raw_dir,
        processed,
        PROJECT_ROOT / "data/interim/subset_metadata.csv",
        max_items=data_cfg["max_items"],
        max_stores=data_cfg["max_stores"],
        chunksize=data_cfg["sales_chunk_rows"],
        seed=data_cfg["seed"],
    )
    profile_dataset(
        frame,
        PROJECT_ROOT / "results/reports/data_profile.json",
        PROJECT_ROOT / "results/reports/data_profile.md",
    )
    print(
        f"Prepared {len(frame):,} rows across {frame['series_id'].nunique():,} series at {processed}."
    )
