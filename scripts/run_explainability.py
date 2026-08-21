"""Fit the benchmarked LightGBM model on the validation design and explain it."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from demand_intelligence.config import PROJECT_ROOT, load_config
from demand_intelligence.data.loaders import load_processed
from demand_intelligence.evaluation.backtesting import chronological_split
from demand_intelligence.explainability.shap_analysis import explain_model
from demand_intelligence.features.pipeline import feature_columns, make_supervised
from demand_intelligence.models.lightgbm_model import make_lightgbm

if __name__ == "__main__":
    frame = load_processed(PROJECT_ROOT / "data/processed/m5_features.parquet")
    supervised, target = make_supervised(frame, 1)
    train, _, _ = chronological_split(supervised, validation_days=28, test_days=28)
    train = train.tail(load_config("backtesting.yaml")["backtesting"]["max_training_rows"])
    model = make_lightgbm(**load_config("models.yaml")["models"]["lightgbm"])
    model.fit(train, target, feature_columns(supervised, target))
    result = explain_model(
        model, train.tail(500), PROJECT_ROOT / "results/explainability", max_rows=500
    )
    print(result)
