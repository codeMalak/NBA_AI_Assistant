from __future__ import annotations

from pathlib import Path
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error

DATA_PATH = Path("data/processed/training_features.csv")
MODEL_PATH = Path("models/enriched_points_model.joblib")


def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Training data not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH, low_memory=False)
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
    ]

    features = [col for col in candidate_features if col in df.columns]
    if not features:
        raise ValueError("No enriched features found in training_features.csv")

    return features, target


def coerce_feature_types(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    df = df.copy()
    for col in features:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def filter_to_enriched_rows(df: pd.DataFrame) -> pd.DataFrame:
    required_context_cols = [
        "home",
        "team_ctx_team_general_base_pts",
        "opp_ctx_team_general_base_pts",
    ]

    existing_required = [col for col in required_context_cols if col in df.columns]
    if not existing_required:
        raise ValueError("Required enriched context columns are missing from dataset.")

    enriched_df = df.dropna(subset=existing_required).copy()

    if enriched_df.empty:
        raise ValueError("No enriched rows found after filtering.")

    print(f"[INFO] Using enriched rows only: {len(enriched_df)} / {len(df)}")
    return enriched_df


def drop_fully_empty_features(df: pd.DataFrame, features: list[str]) -> list[str]:
    usable = [col for col in features if df[col].notna().sum() > 0]

    dropped = [col for col in features if col not in usable]
    if dropped:
        print(f"[INFO] Dropping fully empty enriched features: {dropped}")

    if not usable:
        raise ValueError("All enriched features are empty after filtering.")

    return usable


def main():
    df = load_data()
    features, target = choose_features(df)
    df = coerce_feature_types(df, features)

    df = filter_to_enriched_rows(df)
    features = drop_fully_empty_features(df, features)

    df = df.sort_values("game_date").reset_index(drop=True)

    split_idx = int(len(df) * 0.8)
    if split_idx <= 0 or split_idx >= len(df):
        raise ValueError(f"Not enough enriched rows to split. Rows available: {len(df)}")

    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()

    X_train = train_df[features]
    y_train = train_df[target]
    X_test = test_df[features]
    y_test = test_df[target]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                    ]
                ),
                features,
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
            "model_type": "enriched",
        },
        MODEL_PATH,
    )

    print(f"Saved enriched model to: {MODEL_PATH}")
    print(f"Rows used: {len(df)}")
    print(f"Train rows: {len(train_df)}")
    print(f"Test rows: {len(test_df)}")
    print(f"Features used: {features}")
    print(f"Enriched MAE: {mae:.4f}")
    print(f"Enriched MSE: {mse:.4f}")


if __name__ == "__main__":
    main()