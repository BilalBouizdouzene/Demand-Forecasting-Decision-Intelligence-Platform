# CV project summary

## Demand Forecasting & Decision Intelligence Platform

Time Series · XGBoost · SHAP · Probabilistic Forecasting · FastAPI · Web Application · MLOps

- Developed a multi-horizon retail forecasting pipeline across 1,000 M5 store-item series (1.913M rows, 100 products, 10 stores) using calendar, price, event, lag, rolling, and hierarchy features with chronological validation and explicit leakage checks.

- Benchmarked statistical baselines and CPU-friendly machine-learning models using MAE, RMSE, WAPE, sMAPE, RMSSE, and runtime; Ridge reached 1.0896 WAPE at 28 days on the chronological holdout, while LightGBM reached 1.2226 WAPE at 7 days.

- Built decision support for conformal-style uncertainty, 2,876 residual anomaly flags across 28,000 validation rows, simulated stockout/overstock risk, and 1,000 replenishment recommendations, exposed through FastAPI and a responsive Demand Intelligence Control Center web application.

### Key measured results

Measured subset results are stored in `results/metrics/model_benchmark.csv`; the strongest operational 28-day result is Ridge WAPE 1.089612.

### Interview talking points

Temporal validation, shifted rolling features, zero-safe metrics, conformal calibration, SHAP limitations, simulated inventory assumptions, and runtime/accuracy trade-offs are documented in `docs/INTERVIEW_GUIDE.md`.
