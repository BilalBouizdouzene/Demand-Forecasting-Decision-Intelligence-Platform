"""Optional XGBoost adapter; imports lazily so baselines remain usable."""

from .base import TabularForecastModel


def make_xgboost(**kwargs) -> TabularForecastModel:
    try:
        from xgboost import XGBRegressor
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError("Install the optional 'ml' extra to use XGBoost") from exc
    params = {"objective": "reg:squarederror", "random_state": 42, "tree_method": "hist", **kwargs}
    return TabularForecastModel(XGBRegressor(**params), "xgboost")
