from __future__ import annotations

from math import erf, sqrt

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from services.data_loader import load_games
from services.feature_engineering import add_features, get_feature_columns

MODEL_PATH = "models/points_model.joblib"


def _normal_cdf(x: float, mean: float, std: float) -> float:
    if std <= 0:
        return 1.0 if x >= mean else 0.0
    z = (x - mean) / (std * sqrt(2))
    return 0.5 * (1 + erf(z))


def train_or_load_model():
    try:
        return joblib.load(MODEL_PATH)
    except FileNotFoundError:
        df = load_games()
        df = add_features(df)

        feature_columns = get_feature_columns(df)
        X = df[feature_columns]
        y = df["points"]

        model = RandomForestRegressor(
            n_estimators=200,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X, y)

        joblib.dump(model, MODEL_PATH)
        return model


def predict_stat_threshold(player_name: str, stat: str, threshold: float) -> dict:
    if stat != "points":
        raise ValueError("This version currently supports only points predictions.")

    df = load_games()
    df = add_features(df)

    player_df = df[df["player_name"].str.lower() == player_name.lower()].copy()
    if player_df.empty:
        raise ValueError(f"No data found for player '{player_name}'")

    latest_row = player_df.sort_values("game_date").iloc[-1:]
    feature_columns = get_feature_columns(df)

    model = train_or_load_model()
    predicted_value = float(model.predict(latest_row[feature_columns])[0])

    # Use player's historical scoring std as uncertainty estimate
    historical_std = float(player_df["points"].std())
    if pd.isna(historical_std) or historical_std <= 0:
        historical_std = 5.0

    probability_over_threshold = 1.0 - _normal_cdf(
        threshold,
        mean=predicted_value,
        std=historical_std,
    )

    probability_over_threshold = max(0.0, min(1.0, probability_over_threshold))

    return {
        "player_name": player_name,
        "stat": stat,
        "threshold": threshold,
        "predicted_value": round(predicted_value, 2),
        "probability_over_threshold": round(probability_over_threshold, 4),
        "feature_columns_used": feature_columns,
    }