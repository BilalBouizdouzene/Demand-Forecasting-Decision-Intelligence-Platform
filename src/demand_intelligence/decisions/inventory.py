"""Explainable reorder point and order quantity calculations."""

from __future__ import annotations

import math


def reorder_point(expected_demand_during_lead_time: float, safety_stock: float) -> float:
    return max(0.0, float(expected_demand_during_lead_time) + float(safety_stock))


def safety_stock_from_interval(upper_forecast: float, point_forecast: float) -> float:
    return max(0.0, float(upper_forecast) - float(point_forecast))


def recommended_order_quantity(
    planning_demand: float, current_stock: float, safety_stock: float, incoming: float = 0.0
) -> int:
    return max(
        0,
        math.ceil(
            float(planning_demand) + float(safety_stock) - float(current_stock) - float(incoming)
        ),
    )
