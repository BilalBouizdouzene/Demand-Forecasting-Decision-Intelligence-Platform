import pandas as pd

from demand_intelligence.models.naive import baseline_forecast


def test_seasonal_naive_7():
    frame = pd.DataFrame(
        {
            "store_id": ["S"] * 14,
            "item_id": ["I"] * 14,
            "date": pd.date_range("2024-01-01", periods=14),
            "sales": list(range(14)),
        }
    )
    assert baseline_forecast(frame, 3, "seasonal_naive_7", ("S", "I")).tolist() == [7.0, 8.0, 9.0]
