"""Generate offline data-drift and performance-monitoring artifacts."""

import json
import sys
from pathlib import Path

import joblib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from demand_intelligence.config import PROJECT_ROOT
from demand_intelligence.data.loaders import load_processed
from demand_intelligence.evaluation.backtesting import chronological_split
from demand_intelligence.evaluation.error_analysis import add_error_columns
from demand_intelligence.features.pipeline import make_supervised
from demand_intelligence.monitoring.drift import drift_report
from demand_intelligence.monitoring.performance import performance_drift, retraining_recommendation

if __name__ == "__main__":
    frame = load_processed(PROJECT_ROOT / "data/processed/m5_features.parquet")
    bundle = joblib.load(PROJECT_ROOT / "results/forecasts/model.joblib")
    supervised, target = make_supervised(frame, 1)
    train, validation, _ = chronological_split(supervised, validation_days=28, test_days=28)
    model = bundle["models"][1]
    validation_error = validation[["date", "store_id", "item_id", "sales"]].copy()
    validation_error["actual"] = validation_error.pop("sales")
    validation_error["forecast"] = model.predict(validation)
    validation_error = add_error_columns(validation_error)
    drift = drift_report(
        train, validation, ["sales", "sell_price", "lag_1", "lag_7", "rolling_mean_7"]
    )
    drift.to_csv(PROJECT_ROOT / "results/reports/drift_report.csv", index=False)
    performance = performance_drift(validation_error)
    performance.to_csv(PROJECT_ROOT / "results/reports/performance_drift.csv", index=False)
    validation_error = validation_error.sort_values("date")
    midpoint = max(1, len(validation_error) // 2)
    reference_mae = float(validation_error.head(midpoint)["absolute_error"].mean())
    recent_mae = float(validation_error.tail(midpoint)["absolute_error"].mean())
    recommendation = retraining_recommendation(recent_mae, reference_mae)
    (PROJECT_ROOT / "results/reports/monitoring_summary.json").write_text(
        json.dumps(
            {
                "data_drift_rows": len(drift),
                "performance_periods": len(performance),
                **recommendation,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print("Wrote drift, performance, and retraining reports.")
