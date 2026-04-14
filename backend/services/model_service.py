from __future__ import annotations

from math import erf, sqrt
from pathlib import Path

import joblib
import pandas as pd

from services.data_loader import load_training_data

BASELINE_MODEL_PATH = Path("models/baseline_points_model.joblib")
ENRICHED_MODEL_PATH = Path("models/enriched_points_model.joblib")


def safe_float(value, default: float = 0.0) -> float:
    if pd.isna(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normal_cdf(x: float, mean: float, std: float) -> float:
    if std <= 0:
        return 1.0 if x >= mean else 0.0
    z = (x - mean) / (std * sqrt(2))
    return 0.5 * (1 + erf(z))


def load_model_bundle(model_type: str = "baseline") -> dict:
    if model_type == "enriched":
        model_path = ENRICHED_MODEL_PATH
    else:
        model_path = BASELINE_MODEL_PATH

    if not model_path.exists():
        raise FileNotFoundError(
            f"{model_type.capitalize()} model not found at: {model_path}. "
            f"Run the corresponding retraining script first."
        )

    bundle = joblib.load(model_path)

    if not isinstance(bundle, dict) or "model" not in bundle or "features" not in bundle:
        raise ValueError(
            f"Model file at {model_path} is not in the expected bundle format."
        )

    return bundle


def _prepare_dataframe() -> pd.DataFrame:
    """
    Load the training/enriched dataset used for prediction.
    """
    df = load_training_data().copy()

    if "game_date" in df.columns:
        df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")

    return df


def _build_prediction_row(latest_row: pd.DataFrame, feature_columns: list[str]) -> pd.DataFrame:
    row = latest_row.copy()

    for col in feature_columns:
        if col not in row.columns:
            row[col] = pd.NA

    return row[feature_columns].copy()


def predict_stat_threshold(
    player_name: str,
    stat: str,
    threshold: float,
    model_type: str = "baseline",
) -> dict:
    if stat != "points":
        raise ValueError("This version currently supports only points predictions.")

    df = _prepare_dataframe()

    if "player_name" not in df.columns:
        raise ValueError("Dataset is missing required column: player_name")

    player_df = df[df["player_name"].astype(str).str.lower() == player_name.lower()].copy()
    if player_df.empty:
        raise ValueError(f"No data found for player '{player_name}'")

    player_df = player_df.sort_values("game_date")
    latest_row = player_df.iloc[-1:].copy()

    bundle = load_model_bundle(model_type=model_type)
    model = bundle["model"]
    feature_columns = bundle["features"]

    X_pred = _build_prediction_row(latest_row, feature_columns)
    predicted_raw = model.predict(X_pred)[0]
    predicted_value = safe_float(predicted_raw, default=0.0)

    # Safely compute player's scoring std
    points_series = pd.to_numeric(player_df["points"], errors="coerce")
    historical_std = safe_float(points_series.std(), default=5.0)
    if historical_std <= 0:
        historical_std = 5.0

    threshold_value = safe_float(threshold, default=0.0)

    probability_over_threshold = 1.0 - _normal_cdf(
        threshold_value,
        mean=predicted_value,
        std=historical_std,
    )
    probability_over_threshold = max(0.0, min(1.0, probability_over_threshold))

    return {
        "player_name": player_name,
        "stat": stat,
        "threshold": threshold_value,
        "predicted_value": round(predicted_value, 2),
        "probability_over_threshold": round(probability_over_threshold, 4),
        "model_type": model_type,
        "feature_columns_used": feature_columns,
    }