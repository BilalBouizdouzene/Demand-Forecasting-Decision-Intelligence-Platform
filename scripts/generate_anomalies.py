"""Flag unusual residuals on a chronological validation window."""

import sys
from pathlib import Path

import joblib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from demand_intelligence.anomalies.detector import detect_anomalies
from demand_intelligence.config import PROJECT_ROOT
from demand_intelligence.data.loaders import load_processed
from demand_intelligence.evaluation.backtesting import chronological_split
from demand_intelligence.features.pipeline import make_supervised
from demand_intelligence.forecasting.intervals import make_interval

if __name__ == "__main__":
    frame = load_processed(PROJECT_ROOT / "data/processed/m5_features.parquet")
    bundle = joblib.load(PROJECT_ROOT / "results/forecasts/model.joblib")
    supervised, target = make_supervised(frame, 1)
    train, validation, _ = chronological_split(supervised, validation_days=28, test_days=28)
    model = bundle["models"][1]
    prediction = model.predict(validation)
    lower, upper = make_interval(prediction, float(bundle["interval_radii"].get(1, 0.0)))
    evidence = validation[["date", "store_id", "item_id", "cat_id", "sales"]].copy()
    evidence = evidence.rename(columns={"sales": "actual"})
    evidence["forecast"] = prediction
    evidence["lower"] = lower
    evidence["upper"] = upper
    anomalies = detect_anomalies(evidence, lower_column="lower", upper_column="upper")
    output = PROJECT_ROOT / "results/anomalies"
    output.mkdir(parents=True, exist_ok=True)
    anomalies.to_csv(output / "anomalies.csv", index=False)
    summary = anomalies[anomalies["anomaly_flag"]].groupby("anomaly_type").size().to_dict()
    (PROJECT_ROOT / "results/reports/anomaly_summary.json").write_text(
        __import__("json").dumps(
            {
                "validation_rows": len(anomalies),
                "anomaly_rows": int(anomalies["anomaly_flag"].sum()),
                "types": summary,
                "interpretation": "unusual residual deviation from expected demand; not a fraud or incident conclusion",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        f"Generated {int(anomalies['anomaly_flag'].sum()):,} anomaly flags from {len(anomalies):,} validation rows."
    )
