"""Transparent stockout risk categories."""

from __future__ import annotations


def stockout_risk(current_stock: float, upper_demand: float, reorder_point: float) -> str:
    if current_stock <= 0 or current_stock < upper_demand * 0.5:
        return "CRITICAL"
    if current_stock < reorder_point:
        return "HIGH"
    if current_stock < upper_demand:
        return "MEDIUM"
    return "LOW"
