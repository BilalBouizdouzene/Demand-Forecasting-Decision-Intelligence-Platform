"""Log the benchmark results and saved artifacts to a local MLflow store."""

import json
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from demand_intelligence.config import PROJECT_ROOT

if __name__ == "__main__":
    os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"
    import mlflow

    mlflow.set_tracking_uri(f"file:{PROJECT_ROOT / 'mlruns'}")
    mlflow.set_experiment("m5-demand-intelligence")
    benchmark = pd.read_csv(PROJECT_ROOT / "results/metrics/model_benchmark.csv")
    operational = benchmark[(benchmark["model"] == "ridge") & (benchmark["horizon"] == 28)].iloc[0]
    with mlflow.start_run(run_name="real-m5-subset-benchmark") as run:
        mlflow.log_params(
            {
                "dataset": "M5 Forecasting - Accuracy",
                "subset_series": 1000,
                "operational_model": "ridge",
                "training_cap_rows": 100000,
                "horizons": "1,7,28",
            }
        )
        mlflow.log_metrics(
            {
                "wape_h28_ridge": float(operational["wape"]),
                "rmse_h28_ridge": float(operational["rmse"]),
                "mae_h28_ridge": float(operational["mae"]),
            }
        )
        for path in [
            PROJECT_ROOT / "results/metrics/model_benchmark.csv",
            PROJECT_ROOT / "results/forecasts/model_info.json",
            PROJECT_ROOT / "results/explainability/shap_global_importance.csv",
            PROJECT_ROOT / "results/anomalies/anomalies.csv",
        ]:
            if path.exists():
                mlflow.log_artifact(str(path))
        (PROJECT_ROOT / "results/reports/mlflow_run.json").write_text(
            json.dumps(
                {
                    "run_id": run.info.run_id,
                    "experiment": "m5-demand-intelligence",
                    "tracking_uri": "file:./mlruns",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    print(f"Logged MLflow run {run.info.run_id}")
