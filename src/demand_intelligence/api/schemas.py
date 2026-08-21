"""Pydantic request/response contracts."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    store_id: str
    item_id: str
    horizon: int = Field(default=7, ge=1, le=28)


class ForecastResponse(BaseModel):
    store_id: str
    item_id: str
    horizon: int
    forecast: list[float]
    lower_bound: list[float]
    upper_bound: list[float]
    stockout_risk: str = "UNKNOWN"
    recommended_order_qty: int = 0
    model_version: str = "unavailable"


class HealthResponse(BaseModel):
    status: str
    data_available: bool
    model_available: bool
    model_version: str


class RuntimeBundle(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    metadata: dict[str, Any] = {}
