"""Generate compact, question-driven EDA figures from the prepared M5 subset."""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from demand_intelligence.config import PROJECT_ROOT
from demand_intelligence.data.loaders import load_processed

if __name__ == "__main__":
    frame = load_processed(PROJECT_ROOT / "data/processed/m5_subset.parquet")
    output = PROJECT_ROOT / "results/figures"
    output.mkdir(parents=True, exist_ok=True)
    daily = frame.groupby("date", as_index=False)["sales"].sum()
    plt.figure(figsize=(12, 4))
    sns.lineplot(data=daily, x="date", y="sales")
    plt.title("Question: how does aggregate demand evolve over time?")
    plt.tight_layout()
    plt.savefig(output / "aggregate_demand_over_time.png", dpi=140)
    plt.close()
    store = (
        frame.groupby("store_id", as_index=False)["sales"]
        .sum()
        .sort_values("sales", ascending=False)
    )
    plt.figure(figsize=(8, 4))
    sns.barplot(data=store, x="store_id", y="sales")
    plt.title("Question: which stores contribute the most demand?")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output / "sales_by_store.png", dpi=140)
    plt.close()
    category = (
        frame.groupby("cat_id", as_index=False)["sales"].sum().sort_values("sales", ascending=False)
    )
    plt.figure(figsize=(8, 4))
    sns.barplot(data=category, x="cat_id", y="sales")
    plt.title("Question: how is demand distributed by category?")
    plt.tight_layout()
    plt.savefig(output / "sales_by_category.png", dpi=140)
    plt.close()
    weekday = (
        frame.assign(day_of_week=pd.to_datetime(frame["date"]).dt.day_name())
        .groupby("day_of_week", as_index=False)["sales"]
        .mean()
    )
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    plt.figure(figsize=(9, 4))
    sns.barplot(data=weekday, x="day_of_week", y="sales", order=order)
    plt.title("Question: is demand different by weekday?")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(output / "weekday_effect.png", dpi=140)
    plt.close()
    print(f"Wrote EDA figures to {output}")
