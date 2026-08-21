"""Ridge forecasting adapter."""

from sklearn.linear_model import Ridge

from .base import TabularForecastModel


def make_ridge(alpha: float = 1.0) -> TabularForecastModel:
    return TabularForecastModel(Ridge(alpha=alpha, solver="lsqr"), "ridge")
