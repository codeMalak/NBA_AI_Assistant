from __future__ import annotations

import pandas as pd

ROLLING_WINDOW = 5


BASE_REQUIRED_COLUMNS = [
    "player_name",
    "game_date",
    "points",
]


OPTIONAL_STAT_COLUMNS = [
    "minutes",
    "rebounds",
    "assists",
]


def _validate_columns(df: pd.DataFrame) -> None:
    missing = [col for col in BASE_REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for feature engineering: {missing}")


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    _validate_columns(df)

    data = df.copy()
    data["game_date"] = pd.to_datetime(data["game_date"], errors="coerce")
    data = data.dropna(subset=["player_name", "game_date", "points"])
    data = data.sort_values(["player_name", "game_date"]).reset_index(drop=True)

    grouped = data.groupby("player_name", group_keys=False)

    # Core feature: recent scoring form
    data["points_last_5"] = grouped["points"].transform(
        lambda s: s.shift(1).rolling(ROLLING_WINDOW, min_periods=1).mean()
    )

    # Season-to-date average before current game
    data["points_season_avg"] = grouped["points"].transform(
        lambda s: s.shift(1).expanding(min_periods=1).mean()
    )

    # Recent volatility
    data["points_last_5_std"] = grouped["points"].transform(
        lambda s: s.shift(1).rolling(ROLLING_WINDOW, min_periods=2).std()
    )

    # Number of prior games available before current game
    data["games_played_prior"] = grouped.cumcount()

    # Optional rolling features if the columns exist
    if "minutes" in data.columns:
        data["minutes_last_5"] = grouped["minutes"].transform(
            lambda s: s.shift(1).rolling(ROLLING_WINDOW, min_periods=1).mean()
        )

    if "rebounds" in data.columns:
        data["rebounds_last_5"] = grouped["rebounds"].transform(
            lambda s: s.shift(1).rolling(ROLLING_WINDOW, min_periods=1).mean()
        )

    if "assists" in data.columns:
        data["assists_last_5"] = grouped["assists"].transform(
            lambda s: s.shift(1).rolling(ROLLING_WINDOW, min_periods=1).mean()
        )

    # Optional binary home indicator if available
    if "home_flag" in data.columns:
        data["home_flag"] = data["home_flag"].fillna(0).astype(int)

    # Fill std NaNs for players with too little history
    data["points_last_5_std"] = data["points_last_5_std"].fillna(0)

    # Remove rows with no prior context
    data = data.dropna(subset=["points_last_5", "points_season_avg"])

    return data.reset_index(drop=True)


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    feature_columns = [
        "points_last_5",
        "points_season_avg",
        "points_last_5_std",
        "games_played_prior",
    ]

    optional_features = [
        "minutes_last_5",
        "rebounds_last_5",
        "assists_last_5",
        "home_flag",
    ]

    for col in optional_features:
        if col in df.columns:
            feature_columns.append(col)

    return feature_columns