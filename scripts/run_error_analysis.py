"""Generate actual validation error segments for the operational model."""

import sys
from pathlib import Path

import joblib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from demand_intelligence.config import PROJECT_ROOT
from demand_intelligence.data.loaders import load_processed
from demand_intelligence.evaluation.backtesting import chronological_split
from demand_intelligence.evaluation.error_analysis import summarize_errors
from demand_intelligence.features.pipeline import make_supervised

if __name__ == "__main__":
    frame = load_processed(PROJECT_ROOT / "data/processed/m5_features.parquet")
    bundle = joblib.load(PROJECT_ROOT / "results/forecasts/model.joblib")
    supervised, target = make_supervised(frame, 1)
    _, validation, _ = chronological_split(supervised, validation_days=28, test_days=28)
    model = bundle["models"][1]
    evidence = validation[["date", "store_id", "item_id", "cat_id", "sales", "has_event"]].copy()
    evidence["actual"] = evidence.pop("sales")
    evidence["forecast"] = model.predict(validation)
    evidence["event_flag"] = evidence.pop("has_event")
    evidence["demand_segment"] = evidence["actual"].map(
        lambda value: (
            "intermittent"
            if value == 0
            else "high_volume"
            if value >= evidence["actual"].quantile(0.9)
            else "regular"
        )
    )
    summarize_errors(evidence, PROJECT_ROOT / "results/reports/error_analysis.md")
    print("Wrote results/reports/error_analysis.md")
