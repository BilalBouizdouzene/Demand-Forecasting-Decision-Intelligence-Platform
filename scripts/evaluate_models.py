"""Print the current benchmark and model-selection artifacts."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from demand_intelligence.config import PROJECT_ROOT

if __name__ == "__main__":
    path = PROJECT_ROOT / "results/metrics/model_benchmark.csv"
    if not path.exists():
        raise FileNotFoundError("Run scripts/run_backtest.py first")
    print(pd.read_csv(path).to_string(index=False))
