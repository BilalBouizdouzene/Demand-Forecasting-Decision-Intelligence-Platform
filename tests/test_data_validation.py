import pandas as pd
import pytest

from demand_intelligence.data.validation import validate_long_frame


def test_validation_accepts_clean_frame():
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01"]),
            "item_id": ["I"],
            "store_id": ["S"],
            "sales": [1],
            "sell_price": [2.0],
        }
    )
    assert validate_long_frame(frame)["valid"]


def test_validation_rejects_duplicates():
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-01"]),
            "item_id": ["I", "I"],
            "store_id": ["S", "S"],
            "sales": [1, 2],
        }
    )
    with pytest.raises(ValueError):
        validate_long_frame(frame)
