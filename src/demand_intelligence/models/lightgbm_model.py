"""Optional LightGBM adapter."""

from .base import TabularForecastModel


def make_lightgbm(**kwargs) -> TabularForecastModel:
    try:
        from lightgbm import LGBMRegressor
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError("Install the optional 'ml' extra to use LightGBM") from exc
    return TabularForecastModel(LGBMRegressor(random_state=42, verbosity=-1, **kwargs), "lightgbm")
