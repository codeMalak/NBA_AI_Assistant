from __future__ import annotations

import pandas as pd

ROLLING_WINDOW = 5


def _validate_columns(df: pd.DataFrame) -> None:
    required = ["player_name", "game_date", "points", "team_abbr", "opponent_abbr"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for feature engineering: {missing}")


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    _validate_columns(df)

    data = df.copy()
    data["game_date"] = pd.to_datetime(data["game_date"], errors="coerce")
    data = data.dropna(subset=["player_name", "game_date", "points"])
    data = data.sort_values(["player_name", "game_date"]).reset_index(drop=True)

    grouped_player = data.groupby("player_name", group_keys=False)

    data["points_last_5"] = grouped_player["points"].transform(
        lambda s: s.shift(1).rolling(ROLLING_WINDOW, min_periods=1).mean()
    )

    data["points_season_avg"] = grouped_player["points"].transform(
        lambda s: s.shift(1).expanding(min_periods=1).mean()
    )

    data["points_last_5_std"] = grouped_player["points"].transform(
        lambda s: s.shift(1).rolling(ROLLING_WINDOW, min_periods=2).std()
    ).fillna(0)

    data["games_played_prior"] = grouped_player.cumcount()

    if "minutes" in data.columns:
        data["minutes_last_5"] = grouped_player["minutes"].transform(
            lambda s: s.shift(1).rolling(ROLLING_WINDOW, min_periods=1).mean()
        )

    if "rebounds" in data.columns:
        data["rebounds_last_5"] = grouped_player["rebounds"].transform(
            lambda s: s.shift(1).rolling(ROLLING_WINDOW, min_periods=1).mean()
        )

    if "assists" in data.columns:
        data["assists_last_5"] = grouped_player["assists"].transform(
            lambda s: s.shift(1).rolling(ROLLING_WINDOW, min_periods=1).mean()
        )

    # Player vs opponent team history
    data = data.sort_values(["player_name", "opponent_abbr", "game_date"]).reset_index(drop=True)
    grouped_vs_team = data.groupby(["player_name", "opponent_abbr"], group_keys=False)

    data["vs_team_points_avg"] = grouped_vs_team["points"].transform(
        lambda s: s.shift(1).expanding(min_periods=1).mean()
    )

    data["vs_team_points_last_5"] = grouped_vs_team["points"].transform(
        lambda s: s.shift(1).rolling(ROLLING_WINDOW, min_periods=1).mean()
    )

    data["vs_team_games_count"] = grouped_vs_team.cumcount()

    # Opponent defense: points allowed
    # Since each row is a player performance against an opponent,
    # grouping by opponent_abbr gives us points allowed by that team.
    data = data.sort_values(["opponent_abbr", "game_date"]).reset_index(drop=True)
    grouped_opponent = data.groupby("opponent_abbr", group_keys=False)

    data["opponent_points_allowed_last_5"] = grouped_opponent["points"].transform(
        lambda s: s.shift(1).rolling(ROLLING_WINDOW, min_periods=1).mean()
    )

    data["opponent_points_allowed_season"] = grouped_opponent["points"].transform(
        lambda s: s.shift(1).expanding(min_periods=1).mean()
    )

    # Restore consistent ordering
    data = data.sort_values(["player_name", "game_date"]).reset_index(drop=True)

    # Drop rows with no prior context at all
    data = data.dropna(subset=["points_last_5", "points_season_avg"])

    return data.reset_index(drop=True)


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    candidate_columns = [
        "points_last_5",
        "points_season_avg",
        "points_last_5_std",
        "games_played_prior",
        "minutes_last_5",
        "rebounds_last_5",
        "assists_last_5",
        "vs_team_points_avg",
        "vs_team_points_last_5",
        "vs_team_games_count",
        "opponent_points_allowed_last_5",
        "opponent_points_allowed_season",
        "home_flag",
    ]

    return [col for col in candidate_columns if col in df.columns]