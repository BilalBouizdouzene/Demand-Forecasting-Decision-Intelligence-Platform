"""HTTP routes for the local forecast and monitoring artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException

from .schemas import ForecastRequest, ForecastResponse, HealthResponse


class ArtifactStore:
    def __init__(self, root: str | Path = "results") -> None:
        self.root = Path(root)
        self.forecasts_path = self.root / "forecasts" / "latest_forecasts.csv"
        self.decisions_path = self.root / "decisions" / "decisions.csv"
        self.anomalies_path = self.root / "anomalies" / "anomalies.csv"
        self.metrics_path = self.root / "metrics" / "model_benchmark.csv"
        self.model_info_path = self.root / "forecasts" / "model_info.json"

    @property
    def data_available(self) -> bool:
        return self.forecasts_path.exists()

    @property
    def model_version(self) -> str:
        if self.model_info_path.exists():
            return str(
                json.loads(self.model_info_path.read_text(encoding="utf-8")).get(
                    "model_version", "unknown"
                )
            )
        return "unavailable"

    def read(self, path: Path) -> pd.DataFrame:
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Artifact not available: {path}")
        return pd.read_csv(path)

    def forecast(self, request: ForecastRequest) -> ForecastResponse:
        if not self.forecasts_path.exists():
            raise HTTPException(
                status_code=503,
                detail="No forecast file is available. Run the data and model pipeline first.",
            )
        frame = pd.read_csv(self.forecasts_path)
        subset = frame[
            (frame["store_id"].astype(str) == request.store_id)
            & (frame["item_id"].astype(str) == request.item_id)
        ].head(request.horizon)
        if subset.empty:
            raise HTTPException(
                status_code=404,
                detail="Store/item is not present in the forecast file",
            )

        def values(column: str, fallback: float | None = None) -> list[float]:
            if column in subset:
                return subset[column].astype(float).tolist()
            return [float(value if fallback is None else fallback) for value in subset["forecast"]]

        decision = None
        if self.decisions_path.exists():
            decisions = pd.read_csv(self.decisions_path)
            match = decisions[
                (decisions["store_id"].astype(str) == request.store_id)
                & (decisions["item_id"].astype(str) == request.item_id)
            ]
            decision = match.iloc[0].to_dict() if not match.empty else None
        return ForecastResponse(
            store_id=request.store_id,
            item_id=request.item_id,
            horizon=len(subset),
            forecast=values("forecast"),
            lower_bound=values("lower_bound", 0.0),
            upper_bound=values("upper_bound"),
            stockout_risk=str((decision or {}).get("stockout_risk", "UNKNOWN")),
            recommended_order_qty=int((decision or {}).get("recommended_order_qty", 0)),
            model_version=self.model_version,
        )

    def overview(self) -> dict:
        forecasts = self.read(self.forecasts_path)
        decisions = (
            self.read(self.decisions_path) if self.decisions_path.exists() else pd.DataFrame()
        )
        metrics = self.read(self.metrics_path) if self.metrics_path.exists() else pd.DataFrame()
        anomalies = (
            self.read(self.anomalies_path) if self.anomalies_path.exists() else pd.DataFrame()
        )

        horizon = pd.to_numeric(forecasts.get("horizon", 0), errors="coerce")
        next_7d = float(forecasts.loc[horizon.le(7), "forecast"].sum())
        risk_count = 0
        if not decisions.empty and "stockout_risk" in decisions:
            risk_count = int(decisions["stockout_risk"].isin(["HIGH", "CRITICAL"]).sum())
        anomaly_count = 0
        if not anomalies.empty and "anomaly_flag" in anomalies:
            anomaly_count = int(anomalies["anomaly_flag"].astype(bool).sum())
        avg_wape = None
        if not metrics.empty and "wape" in metrics:
            operational = metrics[
                metrics.get("model", pd.Series(dtype=str)).astype(str).str.lower().eq("ridge")
            ]
            source = operational if not operational.empty else metrics
            avg_wape = float(pd.to_numeric(source["wape"], errors="coerce").mean())

        return {
            "forecast_units_next_7d": round(next_7d, 2),
            "forecast_series": int(forecasts[["store_id", "item_id"]].drop_duplicates().shape[0]),
            "high_risk_series": risk_count,
            "anomaly_flags": anomaly_count,
            "avg_wape": round(avg_wape, 4) if avg_wape is not None else None,
            "forecast_date": str(forecasts["date"].max()) if "date" in forecasts else None,
            "model_version": self.model_version,
            "forecast_curve": forecasts.groupby("horizon", as_index=False)["forecast"]
            .sum()
            .sort_values("horizon")
            .to_dict(orient="records"),
        }

    def catalog(self) -> dict:
        forecasts = self.read(self.forecasts_path)
        series = (
            forecasts[["store_id", "item_id"]]
            .drop_duplicates()
            .sort_values(["store_id", "item_id"])
        )
        return {
            "stores": sorted(series["store_id"].astype(str).unique().tolist()),
            "series": series.astype(str).to_dict(orient="records"),
        }

    def monitoring(self) -> dict:
        summary_path = self.root / "reports" / "monitoring_summary.json"
        drift_path = self.root / "reports" / "drift_report.csv"
        performance_path = self.root / "reports" / "performance_drift.csv"
        summary = (
            json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
        )
        drift = pd.read_csv(drift_path).to_dict(orient="records") if drift_path.exists() else []
        performance = (
            pd.read_csv(performance_path).to_dict(orient="records")
            if performance_path.exists()
            else []
        )
        return {"summary": summary, "drift": drift, "performance": performance}


def build_router(store: ArtifactStore | None = None) -> APIRouter:
    store = store or ArtifactStore()
    router = APIRouter()

    @router.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            data_available=store.data_available,
            model_available=store.model_version != "unavailable",
            model_version=store.model_version,
        )

    @router.get("/model/info")
    def model_info() -> dict:
        if not store.model_info_path.exists():
            return {"model_version": "unavailable", "status": "model file not found"}
        return json.loads(store.model_info_path.read_text(encoding="utf-8"))

    @router.get("/overview")
    def overview() -> dict:
        return store.overview()

    @router.get("/catalog")
    def catalog() -> dict:
        return store.catalog()

    @router.get("/monitoring")
    def monitoring() -> dict:
        return store.monitoring()

    @router.post("/forecast", response_model=ForecastResponse)
    def forecast(request: ForecastRequest) -> ForecastResponse:
        return store.forecast(request)

    @router.post("/forecast/batch")
    def forecast_batch(requests: list[ForecastRequest]) -> list[ForecastResponse]:
        return [store.forecast(request) for request in requests]

    @router.get("/forecast/{store_id}/{item_id}", response_model=ForecastResponse)
    def forecast_by_id(store_id: str, item_id: str, horizon: int = 7) -> ForecastResponse:
        return store.forecast(ForecastRequest(store_id=store_id, item_id=item_id, horizon=horizon))

    @router.get("/decisions")
    def decisions() -> list[dict]:
        return store.read(store.decisions_path).to_dict(orient="records")

    @router.get("/anomalies")
    def anomalies() -> list[dict]:
        return store.read(store.anomalies_path).to_dict(orient="records")

    @router.get("/metrics")
    def metrics() -> list[dict]:
        return store.read(store.metrics_path).to_dict(orient="records")

    return router
