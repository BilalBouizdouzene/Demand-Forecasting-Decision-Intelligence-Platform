"""SHAP wrappers with a graceful optional-dependency fallback."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .feature_importance import extract_feature_importance


def explain_model(
    model, frame: pd.DataFrame, output_dir: str | Path, max_rows: int = 500
) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    sample = frame.head(max_rows)
    result: dict[str, object] = {"method": "feature_importance_fallback"}
    try:
        import shap

        transformed = model.preprocessor.transform(sample[model.feature_columns])
        explainer = shap.Explainer(model.estimator, transformed)
        values = explainer(transformed)
        feature_names = model.preprocessor.get_feature_names_out()
        importance = pd.DataFrame(
            {"feature": feature_names, "mean_abs_shap": abs(values.values).mean(axis=0)}
        ).sort_values("mean_abs_shap", ascending=False)
        importance.to_csv(output / "shap_global_importance.csv", index=False)
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        shap.summary_plot(
            values, transformed, feature_names=feature_names, show=False, max_display=20
        )
        plt.tight_layout()
        plt.savefig(output / "shap_summary.png", dpi=140, bbox_inches="tight")
        plt.close()
        local = pd.DataFrame(
            {"feature": feature_names, "shap_value": values.values[0]}
        ).sort_values("shap_value", key=lambda series: series.abs(), ascending=False)
        local.head(20).to_csv(output / "shap_local_example.csv", index=False)
        result["method"] = "shap"
        result["top_features"] = importance.head(20)["feature"].tolist()
    except Exception as exc:  # pragma: no cover - optional runtime behavior
        importance = extract_feature_importance(model)
        importance.to_csv(output / "feature_importance_fallback.csv", index=False)
        result["fallback_reason"] = str(exc)
        result["top_features"] = importance.head(20)["feature"].tolist()
    return result
