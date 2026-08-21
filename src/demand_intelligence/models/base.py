"""Common model interface and feature encoding."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


class ForecastModel(ABC):
    name = "base"

    @abstractmethod
    def fit(self, frame: pd.DataFrame, target: str, feature_columns: list[str]) -> ForecastModel:
        raise NotImplementedError

    @abstractmethod
    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        raise NotImplementedError


def make_preprocessor(frame: pd.DataFrame, feature_columns: list[str]) -> ColumnTransformer:
    categorical = [
        c for c in feature_columns if str(frame[c].dtype) in {"object", "string", "category"}
    ]
    numeric = [c for c in feature_columns if c not in categorical]
    return ColumnTransformer(
        transformers=[
            ("numeric", Pipeline([("impute", SimpleImputer(strategy="median"))]), numeric),
            (
                "categorical",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical,
            ),
        ],
        remainder="drop",
    )


class TabularForecastModel(ForecastModel):
    estimator: Any

    def __init__(self, estimator: Any, name: str) -> None:
        self.estimator = estimator
        self.name = name
        self.feature_columns: list[str] = []
        self.preprocessor: ColumnTransformer | None = None
        self.training_seconds: float | None = None

    def fit(
        self, frame: pd.DataFrame, target: str, feature_columns: list[str]
    ) -> TabularForecastModel:
        started = time.perf_counter()
        self.feature_columns = feature_columns
        self.preprocessor = make_preprocessor(frame, feature_columns)
        X = self.preprocessor.fit_transform(frame[feature_columns])
        y = pd.to_numeric(frame[target], errors="raise").to_numpy()
        self.estimator.fit(X, y)
        self.training_seconds = time.perf_counter() - started
        return self

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        if self.preprocessor is None:
            raise RuntimeError("Model has not been fitted")
        return np.maximum(
            0.0,
            np.asarray(
                self.estimator.predict(self.preprocessor.transform(frame[self.feature_columns]))
            ),
        )

    def save(self, path: str) -> None:
        import joblib

        joblib.dump(self, path)

    @classmethod
    def load(cls, path: str) -> TabularForecastModel:
        import joblib

        return joblib.load(path)
