# Issue 006: Predictive Strategy Analytics

## Summary
Implement the predictive analytics capability outlined in [Implementation Plan §Predictive Strategy Analytics](../IMPLEMENTATION_PLAN.md#predictive-strategy-analytics).

## Current State
- Forecast API returns random values without real time-series models or data pipelines.【F:packages/api/src/stratmaster_api/services.py†L726-L788】
- No ML training workflow or feature store exists for strategy metrics.

## Proposed Solution
1. Build data ingestion and feature engineering pipeline for historical strategy metrics.
2. Implement forecasting models (Prophet/NeuralProphet) with MLflow tracking.
3. Deploy inference service and update API/UX to consume real forecasts behind `ENABLE_PREDICTIVE_ANALYTICS`.

## Feature Flag
- `ENABLE_PREDICTIVE_ANALYTICS` (default `false`).

## Acceptance Criteria
- Historical data ingested into analytics store with reproducible transformations.
- Forecast service produces validated metrics (MAPE, RMSE) above defined thresholds and exposes model lineage.
- API/UI display real forecasts when flag enabled and fall back to legacy behavior otherwise.
- Documentation covers operations, model governance, and troubleshooting.

## Dependencies
- Data warehouse or analytics database for historical metrics.
- ML tooling (Prophet, MLflow) and compute resources for training.

## Testing Plan
- Unit tests for feature engineering and model evaluation utilities.
- Contract tests for forecast API schema and fallback logic.
- Integration tests training lightweight models on sample data during CI.

## Rollout & Monitoring
- Pilot with internal tenants, then expand. Monitor forecast accuracy and drift via dashboards.
