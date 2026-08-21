# Interview guide

## Why time-based split instead of random split?

Demand forecasting predicts future dates. A random split can let training observe patterns from after the forecast origin and produce optimistic results. Chronological holdouts and rolling-origin folds mirror deployment.

## What is target leakage?

Leakage is information unavailable at forecast time entering a feature. Here, lags are shifted and rolling windows are shifted before aggregation; future targets are separate columns.

## Why lag features?

Retail demand has autocorrelation and weekly repetition. Past demand at one, seven, fourteen, twenty-eight, and fifty-six days captures recent level and seasonality.

## Why rolling features?

Rolling means and dispersion summarize level and volatility. Shifting before rolling ensures the current target is not included.

## Why does MAPE fail with zero sales?

Division by zero makes it undefined or unstable. This project reports zero-safe MAPE but prefers WAPE and RMSSE for aggregate comparison.

## Why WAPE?

WAPE weights errors by actual demand and is interpretable for portfolio-level planning. It can still be dominated by high-volume series, so segmentation matters.

## What is RMSSE?

RMSSE scales forecast error by the in-sample naive-difference error, helping compare series with different units and demand levels. The implementation returns NaN when the training scale is zero.

## Why XGBoost for forecasting?

With causal tabular features, boosted trees model nonlinear interactions among calendar, price, hierarchy, and demand history while remaining practical on CPU. It must still beat strong seasonal baselines in time-aware evaluation.

## Why can tree models outperform LSTM?

On moderate CPU-sized retail panels, engineered lag/calendar features and tree ensembles can be strong without sequence-training overhead. A neural model is not automatically better.

## Recursive vs direct forecasting?

Recursive models reuse a one-step model and can accumulate error. Direct models optimize each horizon separately and avoid that propagation, at the cost of more models and potentially inconsistent paths.

## How do prediction intervals work?

The project calibrates an absolute residual radius on chronological validation predictions and adds/subtracts it from point forecasts. Coverage and width are evaluated, not assumed.

## Why use conformal prediction?

It provides a model-agnostic finite-sample calibration idea and is easy to explain. Series-specific and conditional coverage would be a future improvement.

## What does SHAP explain?

SHAP decomposes a fitted model output relative to a background expectation. It explains model behavior, not the real-world causal effect of a promotion or price.

## How did you evaluate by horizon?

Targets are shifted separately for one, seven, and twenty-eight days. Metrics are reported separately so longer-horizon degradation is visible.

## How do you handle intermittent demand?

The subset selection includes low-volume/zero-heavy segments, and metrics are segmented. A production version could add Croston-style models, zero-inflated distributions, and series-specific calibration.

## What causes forecast drift?

Assortment changes, price/promotion regimes, events, store behavior, data pipeline changes, or demand shocks can alter feature and error distributions. PSI/KS and MAE/WAPE monitoring distinguish data drift from performance degradation.

## How would you retrain?

Use a monitored recommendation threshold, review candidate metrics and stability, retrain in a separate artifact/version, compare with the incumbent, and promote only after approval. This repository does not silently overwrite a production model.

## How does stockout risk work?

It compares simulated current stock with point/upper forecast demand and a reorder point. Thresholds are transparent and configurable.

## Why is inventory simulated?

M5 provides sales, calendar, and price data, not on-hand or incoming inventory. Simulated stock is clearly labeled and used only to demonstrate decision logic.

## How would this move to production?

Add real inventory and lead-time feeds, a model registry, scheduled data quality checks, feature-store contracts, authenticated API, monitoring storage, human approvals, hierarchical reconciliation, and deployment-specific load tests.
