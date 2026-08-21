import numpy as np

from demand_intelligence.evaluation.metrics import mae, mape, rmsse, smape, wape


def test_zero_safe_metrics():
    assert mae([0, 2], [0, 1]) == 0.5
    assert wape([0, 2], [0, 1]) == 0.5
    assert mape([0, 2], [0, 1]) == 0.5
    assert smape([0, 0], [0, 1]) == 1.0
    assert np.isfinite(rmsse([1, 2], [1, 3], [1, 2, 3]))
