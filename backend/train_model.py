from __future__ import annotations

import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from services.data_loader import load_training_data


from services.feature_engineering import add_features, get_feature_columns

MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "points_model.joblib")


def main():
    df = load_training_data()
    df = add_features(df)

    if df.empty:
        raise ValueError("No training data available after feature engineering.")

    # Time-based split
    df = df.sort_values("game_date").reset_index(drop=True)
    split_idx = int(len(df) * 0.8)

    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()

    feature_columns = get_feature_columns(train_df)

    X_train = train_df[feature_columns]
    y_train = train_df["points"]

    X_test = test_df[feature_columns]
    y_test = test_df["points"]

    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    mae = mean_absolute_error(y_test, preds)
    mse = mean_squared_error(y_test, preds)

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    print(f"Saved model to: {MODEL_PATH}")
    print(f"Feature columns used: {feature_columns}")
    print(f"Train rows: {len(train_df)}")
    print(f"Test rows: {len(test_df)}")
    print(f"MAE: {mae:.4f}")
    print(f"MSE: {mse:.4f}")


if __name__ == "__main__":
    main()