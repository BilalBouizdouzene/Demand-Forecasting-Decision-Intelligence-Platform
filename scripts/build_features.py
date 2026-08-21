"""Build leakage-safe features once and cache them as Parquet."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from demand_intelligence.config import PROJECT_ROOT, ensure_dirs, load_config
from demand_intelligence.data.loaders import load_processed
from demand_intelligence.features.pipeline import build_features

if __name__ == "__main__":
    ensure_dirs()
    data_cfg = load_config("data.yaml")["data"]
    feature_cfg = load_config("features.yaml")["features"]
    source = PROJECT_ROOT / data_cfg["processed_dir"] / data_cfg["processed_filename"]
    output = PROJECT_ROOT / "data/processed/m5_features.parquet"
    if output.exists():
        frame = load_processed(output)
    else:
        frame = build_features(load_processed(source), feature_cfg)
        frame.to_parquet(output, index=False)
    print(f"Feature table: {len(frame):,} rows x {len(frame.columns)} columns at {output}")
