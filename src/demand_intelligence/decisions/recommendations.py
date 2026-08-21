"""Replenishment rules built from forecasts and simulated stock levels."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .inventory import recommended_order_quantity, reorder_point, safety_stock_from_interval
from .overstock import overstock_risk
from .stockout import stockout_risk


def decision_priority(
    stockout: str,
    uncertainty: float,
    demand_value: float,
    anomaly: bool,
    weights: dict[str, float] | None = None,
) -> float:
    weights = weights or {
        "stockout": 0.45,
        "uncertainty": 0.25,
        "demand_value": 0.20,
        "anomaly": 0.10,
    }
    stockout_component = {"LOW": 0.0, "MEDIUM": 0.4, "HIGH": 0.8, "CRITICAL": 1.0}.get(
        stockout, 0.0
    )
    return float(
        weights.get("stockout", 0.45) * stockout_component
        + weights.get("uncertainty", 0.25) * min(1.0, max(0.0, uncertainty))
        + weights.get("demand_value", 0.20) * min(1.0, max(0.0, demand_value))
        + weights.get("anomaly", 0.10) * float(anomaly)
    )


def build_decision_row(
    row: dict[str, Any],
    lead_time_days: int = 7,
    service_level: float = 0.95,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    point_7d = float(row.get("forecast_7d", row.get("forecast", 0.0)))
    upper_7d = float(row.get("upper_90_7d", point_7d))
    current_stock = float(row.get("simulated_stock", 0.0))
    safety = safety_stock_from_interval(upper_7d, point_7d)
    rop = reorder_point(point_7d * lead_time_days / 7, safety)
    order_qty = recommended_order_quantity(
        point_7d, current_stock, safety, float(row.get("incoming_stock", 0.0))
    )
    risk = stockout_risk(current_stock, upper_7d, rop)
    overstock = overstock_risk(current_stock, point_7d)
    uncertainty_ratio = (upper_7d - point_7d) / max(1.0, point_7d)
    output = dict(row)
    output.update(
        {
            "safety_stock": round(safety, 2),
            "reorder_point": round(rop, 2),
            "recommended_order_qty": int(order_qty),
            "stockout_risk": risk,
            "overstock_risk": overstock,
            "priority_score": decision_priority(
                risk,
                uncertainty_ratio,
                min(1.0, point_7d / 100),
                bool(row.get("anomaly_flag", False)),
                weights,
            ),
            "inventory_source": "simulated decision layer; M5 contains no inventory snapshots",
            "service_level": service_level,
        }
    )
    return output


def build_decisions(frame: pd.DataFrame, **kwargs) -> pd.DataFrame:
    return pd.DataFrame(
        [build_decision_row(row, **kwargs) for row in frame.to_dict(orient="records")]
    )
