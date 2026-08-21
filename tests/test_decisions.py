from demand_intelligence.decisions.inventory import recommended_order_quantity, reorder_point
from demand_intelligence.decisions.recommendations import build_decision_row
from demand_intelligence.decisions.stockout import stockout_risk


def test_inventory_rules():
    assert reorder_point(100, 20) == 120
    assert recommended_order_quantity(100, 50, 20) == 70
    assert stockout_risk(0, 100, 120) == "CRITICAL"


def test_decision_row_labels_simulated_inventory():
    result = build_decision_row(
        {
            "store_id": "S",
            "item_id": "I",
            "forecast_7d": 100,
            "upper_90_7d": 120,
            "simulated_stock": 20,
        }
    )
    assert result["inventory_source"].startswith("simulated")
    assert result["recommended_order_qty"] > 0
