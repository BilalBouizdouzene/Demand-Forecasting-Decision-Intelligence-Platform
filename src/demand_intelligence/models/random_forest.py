"""CPU-friendly random forest adapter."""

from sklearn.ensemble import RandomForestRegressor

from .base import TabularForecastModel


def make_random_forest(**kwargs) -> TabularForecastModel:
    return TabularForecastModel(RandomForestRegressor(random_state=42, **kwargs), "random_forest")
