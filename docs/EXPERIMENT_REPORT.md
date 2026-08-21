# Experiment report

## 1. Business problem

Forecast daily retail unit demand by store and product so planners can anticipate demand, quantify uncertainty, and prioritize simulated replenishment actions.

## 2. Dataset

The project uses the public M5 Forecasting - Accuracy dataset. Raw provenance and local file hashes are captured by `scripts/download_data.py`. The default local run selects a representative subset because the full matrix is large.

## 3. EDA

The selected run contains 1,913,000 rows, 1,000 series, 100 items, 10 stores, 3 states, 7 departments, and 3 categories from 2011-01-29 to 2016-04-24. Zero sales represent 93.3317% of rows and price coverage is 56.1506%. EDA figures are saved in `results/figures/`.

## 4. Temporal validation

All model evaluation is chronological. The final holdout uses the latest dates, while rolling-origin experiments train on earlier dates and validate on the next horizon. No random split is permitted.

## 5. Leakage prevention

Lags use `shift(lag)`. Rolling features use `shift(1)` before aggregation. Future targets are created separately with a negative shift and are excluded from feature columns. The test suite checks these invariants.

## 6. Features

`features/pipeline.py` builds calendar, cyclical, lag, shifted rolling, EWM, price movement, event, SNAP, and hierarchy features.

## 7. Baselines

The project evaluates last-value, seasonal-naive 7/28, and rolling-mean baselines before the machine-learning models. The benchmark table is the reference for model comparisons.

## 8. Model comparison

The measured WAPE table is: Rolling mean 28 = 1.140021 / 1.307565 / 1.296967; Ridge = 1.256954 / 1.238200 / 1.089612; LightGBM = 1.226120 / 1.222643 / 1.224408; XGBoost = 1.302845 / 1.315182 / 1.314153; Random Forest = 1.493239 / 1.406919 / 1.441578 for 1/7/28-day horizons. Full metrics are in `results/metrics/model_benchmark.csv` and `.json`.

## 9. Uncertainty

The direct horizon models calibrate an absolute-residual radius on chronological validation predictions. The interval report should be read with both empirical coverage and average width; a wide interval is not automatically useful.

## 10. Error analysis

`evaluation/error_analysis.py` segments errors by store, category, event context, and demand segment when those columns are present. It also writes largest absolute failures and forecast bias to `results/reports/error_analysis.md`.

## 11. Explainability

SHAP successfully produced `results/explainability/shap_global_importance.csv`, `shap_summary.png`, and `shap_local_example.csv` for the benchmarked LightGBM model. SHAP describes model associations, not causal effects.

## 12. Anomalies

Anomalies are residual-based: actual minus forecast, standardized against prior residual behavior, with optional interval breaches. The validation run flagged 2,876 of 28,000 rows, primarily unexpected demand spikes. They are alerts for unusual deviations, not conclusions about fraud or incidents.

## 13. Decisions

M5 has no inventory snapshots, so current stock and incoming units are simulated. The heuristic combines forecast demand and interval width into safety stock, reorder point, stockout/overstock categories, order quantity, and configurable priority weights.

## 14. Monitoring

Offline monitoring produced five drift-report feature rows. The validation-window performance degradation ratio was 0.0396, below the configured 0.20 threshold, so the current recommendation is to continue monitoring. Data drift (PSI/KS) remains separate from performance degradation (MAE over time), and production model artifacts are never automatically overwritten.

## 15. Limitations

Subset constraints, intermittent demand, simplified intervals, simulated inventory, and non-causal price/event features limit production interpretation.

## 16. Conclusion

The reported numbers come from the locally available M5 files and the saved experiment outputs. If the data or configuration changes, the reports should be regenerated before quoting new results.
