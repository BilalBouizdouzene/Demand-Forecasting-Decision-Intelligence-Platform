"""Run chronological ML benchmarks for 1/7/28 day direct targets."""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from demand_intelligence.config import PROJECT_ROOT, ensure_dirs, load_config
from demand_intelligence.data.loaders import load_processed
from demand_intelligence.evaluation.backtesting import chronological_split
from demand_intelligence.evaluation.comparison import summarize_benchmark, write_model_selection
from demand_intelligence.evaluation.metrics import metric_dict
from demand_intelligence.features.pipeline import feature_columns, make_supervised
from demand_intelligence.models.lightgbm_model import make_lightgbm
from demand_intelligence.models.linear import make_ridge
from demand_intelligence.models.random_forest import make_random_forest
from demand_intelligence.models.xgboost_model import make_xgboost


def factories(model_cfg: dict):
    output = {
        "ridge": lambda: make_ridge(model_cfg.get("ridge_alpha", 1.0)),
        "random_forest": lambda: make_random_forest(**model_cfg.get("random_forest", {})),
    }
    for name, factory in [
        ("xgboost", lambda: make_xgboost(**model_cfg.get("xgboost", {}))),
        ("lightgbm", lambda: make_lightgbm(**model_cfg.get("lightgbm", {}))),
    ]:
        try:
            factory()
            output[name] = factory
        except ImportError:
            print(f"Skipping optional {name}: dependency unavailable")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--models",
        default="ridge,random_forest,xgboost,lightgbm",
        help="Comma-separated model names",
    )
    parser.add_argument("--output", default="results/metrics/model_benchmark.csv")
    args = parser.parse_args()
    ensure_dirs()
    frame = load_processed(PROJECT_ROOT / "data/processed/m5_features.parquet")
    model_cfg = load_config("models.yaml")["models"]
    backtest_cfg = load_config("backtesting.yaml")["backtesting"]
    rows = []
    for horizon in backtest_cfg["horizons"]:
        supervised, target = make_supervised(frame, horizon)
        train, validation, _ = chronological_split(
            supervised,
            validation_days=backtest_cfg["validation_days"],
            test_days=backtest_cfg["validation_days"],
        )
        train = train.tail(backtest_cfg["max_training_rows"])
        cols = feature_columns(supervised, target)
        available = factories(model_cfg)
        requested = [name.strip() for name in args.models.split(",") if name.strip()]
        for name in requested:
            if name not in available:
                print(f"Skipping unavailable model {name}", flush=True)
                continue
            factory = available[name]
            model = factory()
            print(f"training model={name} horizon={horizon} rows={len(train):,}", flush=True)
            model.fit(train, target, cols)
            prediction = model.predict(validation)
            rows.append(
                {
                    "model": name,
                    "horizon": horizon,
                    "training_seconds": model.training_seconds,
                    **metric_dict(validation[target], prediction, train["sales"]),
                }
            )
            print(f"finished model={name} horizon={horizon}", flush=True)
    output = pd.DataFrame(rows)
    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(output_path, index=False)
    output.to_json(output_path.with_suffix(".json"), orient="records", indent=2)
    summary = summarize_benchmark(output)
    summary.to_csv(PROJECT_ROOT / "results/metrics/model_benchmark_summary.csv", index=False)
    write_model_selection(summary, PROJECT_ROOT / "results/reports/model_selection.md")
    print(summary.to_string(index=False))
