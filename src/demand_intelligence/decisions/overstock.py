"""Overstock risk based on cover relative to a planning forecast."""

from __future__ import annotations


def overstock_risk(current_stock: float, planning_demand: float) -> str:
    if planning_demand <= 0 and current_stock > 0:
        return "HIGH"
    cover_ratio = current_stock / planning_demand if planning_demand else 0.0
    if cover_ratio >= 2.5:
        return "HIGH"
    if cover_ratio >= 1.5:
        return "MEDIUM"
    return "LOW"
