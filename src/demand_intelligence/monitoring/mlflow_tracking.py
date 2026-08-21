"""Optional MLflow integration that never blocks local experiments."""

from __future__ import annotations

from typing import Any


def log_experiment(
    name: str, params: dict[str, Any], metrics: dict[str, float], artifacts: list[str] | None = None
) -> str | None:
    try:
        import mlflow
    except ImportError:
        return None
    with mlflow.start_run(run_name=name) as run:
        mlflow.log_params(params)
        mlflow.log_metrics({k: float(v) for k, v in metrics.items() if v == v})
        for artifact in artifacts or []:
            mlflow.log_artifact(artifact)
        return run.info.run_id
