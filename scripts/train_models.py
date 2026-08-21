"""Train direct multi-horizon models and persist metadata without silent overwrites."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import joblib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from demand_intelligence.config import PROJECT_ROOT, ensure_dirs, load_config
from demand_intelligence.data.loaders import load_processed
from demand_intelligence.evaluation.backtesting import chronological_split
from demand_intelligence.evaluation.metrics import metric_dict
from demand_intelligence.features.pipeline import feature_columns, make_supervised
from demand_intelligence.forecasting.intervals import conformal_radius
from demand_intelligence.models.linear import make_ridge
from demand_intelligence.models.random_forest import make_random_forest
from demand_intelligence.models.xgboost_model import make_xgboost


def candidate_factory(name: str, model_cfg: dict):
    if name == "ridge":
        return make_ridge(model_cfg.get("ridge_alpha", 1.0))
    if name == "random_forest":
        return make_random_forest(**model_cfg.get("random_forest", {}))
    if name == "xgboost":
        return make_xgboost(**model_cfg.get("xgboost", {}))
    raise ValueError(name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        default="ridge",
        choices=["ridge", "random_forest", "xgboost"],
        help="Operational model; select from benchmark evidence",
    )
    args = parser.parse_args()
    ensure_dirs()
    data_cfg = load_config("data.yaml")["data"]
    model_cfg = load_config("models.yaml")["models"]
    source = PROJECT_ROOT / "data/processed/m5_features.parquet"
    if not source.exists():
        raise FileNotFoundError("Run scripts/build_features.py first")
    frame = load_processed(source)
    base_features = feature_columns(frame)
    models: dict[int, object] = {}
    radii: dict[int, float] = {}
    selected_name = args.model
    for horizon in [1, 7, 28]:
        supervised, target = make_supervised(frame, horizon)
        train, validation, _ = chronological_split(supervised, validation_days=28, test_days=28)
        try:
            model = candidate_factory(selected_name, model_cfg)
            chosen_name = selected_name
        except ImportError:
            model = candidate_factory("random_forest", model_cfg)
            chosen_name = "random_forest"
        # Keep CPU use bounded on the local default configuration.
        train_fit = train.tail(
            int(load_config("backtesting.yaml")["backtesting"]["max_training_rows"])
        )
        model.fit(train_fit, target, base_features)
        predictions = model.predict(validation)
        radii[horizon] = conformal_radius(validation[target], predictions)
        models[horizon] = model
        if horizon == 1:
            selected_name = chosen_name
        print(
            f"horizon={horizon} model={chosen_name} validation={metric_dict(validation[target], predictions)}"
        )
    version = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output = PROJECT_ROOT / "results/forecasts"
    artifact = output / f"model_{version}.joblib"
    joblib.dump(
        {
            "models": models,
            "interval_radii": radii,
            "feature_columns": base_features,
            "model_name": selected_name,
            "model_version": version,
        },
        artifact,
    )
    joblib.dump(
        {
            "models": models,
            "interval_radii": radii,
            "feature_columns": base_features,
            "model_name": selected_name,
            "model_version": version,
        },
        output / "model.joblib",
    )
    (output / "model_info.json").write_text(
        json.dumps(
            {
                "model_version": version,
                "model_name": selected_name,
                "horizons": [1, 7, 28],
                "feature_count": len(base_features),
                "training_range": [str(frame["date"].min()), str(frame["date"].max())],
                "created_at": version,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Saved model artifact {artifact}")
