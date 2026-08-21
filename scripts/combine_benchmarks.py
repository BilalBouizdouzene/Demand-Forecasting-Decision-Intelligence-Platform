"""Combine baseline and machine-learning benchmark files into one table."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from demand_intelligence.config import PROJECT_ROOT, ensure_dirs
from demand_intelligence.evaluation.comparison import summarize_benchmark, write_model_selection

if __name__ == "__main__":
    ensure_dirs()
    metrics_dir = PROJECT_ROOT / "results/metrics"
    paths = [
        metrics_dir / "baseline_benchmark.csv",
        metrics_dir / "model_benchmark_ridge.csv",
        metrics_dir / "model_benchmark_random_forest.csv",
        metrics_dir / "model_benchmark_xgboost.csv",
        metrics_dir / "model_benchmark.csv",
    ]
    frames = []
    for path in paths:
        if path.exists():
            frame = pd.read_csv(path)
            frame["benchmark_type"] = "baseline" if "baseline" in path.name else "ml"
            frames.append(frame)
    if not frames:
        raise FileNotFoundError("No benchmark artifacts found")
    output = pd.concat(frames, ignore_index=True).drop_duplicates(
        subset=["model", "horizon", "benchmark_type"], keep="last"
    )
    output.to_csv(metrics_dir / "model_benchmark.csv", index=False)
    output.to_json(metrics_dir / "model_benchmark.json", orient="records", indent=2)
    summary = summarize_benchmark(output)
    summary.to_csv(metrics_dir / "model_benchmark_summary.csv", index=False)
    write_model_selection(summary, PROJECT_ROOT / "results/reports/model_selection.md")
    print(summary.to_string(index=False))
