"""Build replenishment recommendations from the forecast artifact."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from demand_intelligence.config import PROJECT_ROOT, load_config
from demand_intelligence.data.loaders import load_processed
from demand_intelligence.decisions.recommendations import build_decisions

if __name__ == "__main__":
    forecasts = pd.read_csv(PROJECT_ROOT / "results/forecasts/latest_forecasts.csv")
    history = load_processed(PROJECT_ROOT / "data/processed/m5_subset.parquet")
    rows = []
    for (store, item), group in forecasts.groupby(["store_id", "item_id"], observed=True):
        group = group.sort_values("date")
        recent = (
            history[(history["store_id"] == store) & (history["item_id"] == item)]
            .sort_values("date")
            .tail(28)
        )
        simulated_stock = float(recent["sales"].mean() * 7 * 1.2) if not recent.empty else 0.0
        first_7 = group.head(7)
        rows.append(
            {
                "store_id": store,
                "item_id": item,
                "forecast_7d": first_7["forecast"].sum(),
                "forecast_28d": group["forecast"].sum(),
                "lower_90_7d": first_7["lower_bound"].sum(),
                "upper_90_7d": first_7["upper_bound"].sum(),
                "simulated_stock": simulated_stock,
                "anomaly_flag": False,
            }
        )
    cfg = load_config("app.yaml")["app"]
    decisions = build_decisions(
        pd.DataFrame(rows),
        lead_time_days=cfg["default_lead_time_days"],
        service_level=cfg["default_service_level"],
        weights=cfg["decision_weights"],
    )
    decisions.sort_values("priority_score", ascending=False).to_csv(
        PROJECT_ROOT / "results/decisions/decisions.csv", index=False
    )
    print(f"Wrote {len(decisions):,} simulated-inventory decisions.")
