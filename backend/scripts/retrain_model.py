from __future__ import annotations

from pathlib import Path
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

DATA_PATH = Path("data/processed/training_features.csv")
MODEL_PATH = Path("models/latest_points_model.joblib")


def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Training data not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")
    df = df.dropna(subset=["player_name", "game_date", "points"])
    return df


def choose_features(df: pd.DataFrame) -> tuple[list[str], str]:
    target = "points"

    candidate_features = [
        "home",
        "days_rest",
        "minutes_last_3",
        "minutes_last_5",
        "minutes_last_10",
        "points_last_3",
        "points_last_5",
        "points_last_10",
        "rebounds_last_3",
        "rebounds_last_5",
        "assists_last_3",
        "assists_last_5",
        "team_injury_count",
        "opponent_injury_count",
        "general_base_gp",
        "general_base_pts",
        "general_base_reb",
        "general_base_ast",
        "general_advanced_pace",
        "general_advanced_off_rating",
        "general_advanced_def_rating",
        "team_ctx_team_general_base_pts",
        "team_ctx_team_general_advanced_pace",
        "opp_ctx_team_general_base_pts",
        "opp_ctx_team_general_advanced_defense_rating",
    ]

    features = [col for col in candidate_features if col in df.columns]
    if not features:
        raise ValueError("No candidate features were found in training_features.csv")

    return features, target


def main():
    df = load_data()
    features, target = choose_features(df)

    # Chronological split is better than random for sports data
    df = df.sort_values("game_date").reset_index(drop=True)
    split_idx = int(len(df) * 0.8)

    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()

    X_train = train_df[features]
    y_train = train_df[target]
    X_test = test_df[features]
    y_test = test_df[target]

    numeric_features = features

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                    ]
                ),
                numeric_features,
            )
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", RandomForestRegressor(
                n_estimators=200,
                max_depth=12,
                random_state=42,
                n_jobs=-1,
            )),
        ]
    )

    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    mae = mean_absolute_error(y_test, preds)
    mse = mean_squared_error(y_test, preds)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "features": features,
            "target": target,
        },
        MODEL_PATH,
    )

    print(f"Saved model to: {MODEL_PATH}")
    print(f"Train rows: {len(train_df)}")
    print(f"Test rows: {len(test_df)}")
    print(f"Features used: {features}")
    print(f"MAE: {mae:.4f}")
    print(f"MSE: {mse:.4f}")


if __name__ == "__main__":
    main()