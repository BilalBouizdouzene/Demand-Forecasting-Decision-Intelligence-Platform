import pandas as pd

from demand_intelligence.features.pipeline import build_features, make_supervised


def fixture_frame():
    dates = pd.date_range("2024-01-01", periods=70)
    return pd.DataFrame(
        {
            "date": list(dates) * 2,
            "item_id": ["ITEM_1"] * 70 + ["ITEM_2"] * 70,
            "store_id": ["STORE_1"] * 140,
            "dept_id": ["D_1"] * 140,
            "cat_id": ["C_1"] * 140,
            "state_id": ["S_1"] * 140,
            "series_id": ["STORE_1__ITEM_1"] * 70 + ["STORE_1__ITEM_2"] * 70,
            "sales": list(range(70)) + list(range(70, 140)),
            "sell_price": [10.0] * 140,
            "event_name_1": [None] * 140,
            "event_type_1": [None] * 140,
            "event_name_2": [None] * 140,
            "event_type_2": [None] * 140,
            "snap_CA": [0] * 140,
        }
    )


def test_lag_and_rolling_are_past_only():
    result = build_features(
        fixture_frame(),
        {"lags": [1, 7], "rolling_windows": [7], "rolling_stats": ["mean"], "ewm_spans": []},
    )
    first = result.sort_values(["store_id", "item_id", "date"]).iloc[0]
    assert pd.isna(first["lag_1"])
    assert pd.isna(first["rolling_mean_7"])
    later = result[(result["item_id"] == "ITEM_1") & (result["date"] == "2024-01-08")].iloc[0]
    assert later["lag_1"] == 6
    assert later["lag_7"] == 0
    assert later["rolling_mean_7"] == 3


def test_supervised_target_is_future_and_feature_row_unchanged():
    built = build_features(
        fixture_frame(),
        {"lags": [1], "rolling_windows": [7], "rolling_stats": ["mean"], "ewm_spans": []},
    )
    supervised, target = make_supervised(built, 7)
    row = supervised[
        (supervised["item_id"] == "ITEM_1") & (supervised["date"] == "2024-01-01")
    ].iloc[0]
    assert row[target] == 7
    assert pd.isna(row["lag_1"])
