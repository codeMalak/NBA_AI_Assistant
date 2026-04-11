# API Contract

## GET /api/health
Response:
```json
{ "status": "ok" }
```

## POST /api/predict
Request:
```json
{
  "player_name": "Stephen Curry",
  "stat": "points",
  "threshold": 28.5
}
```

Response:
```json
{
  "player_name": "Stephen Curry",
  "stat": "points",
  "threshold": 28.5,
  "predicted_value": 30.1,
  "probability_over_threshold": 0.64,
  "model_residual_std": 5.9,
  "latest_context_date": "2025-11-28"
}
```

## POST /api/explain
Same request as `/api/predict`.

Response includes prediction + retrieval context + explanation text.
