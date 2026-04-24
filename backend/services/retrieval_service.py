from __future__ import annotations

import pandas as pd

from services.data_loader import load_training_data


def safe_float(value, default: float = 0.0) -> float:
    if pd.isna(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_mean(series: pd.Series, default: float = 0.0) -> float:
    numeric = pd.to_numeric(series, errors="coerce")
    mean_value = numeric.mean()
    return safe_float(mean_value, default=default)


def safe_get(row: pd.Series, column: str, default=None):
    if column not in row.index:
        return default
    value = row[column]
    if pd.isna(value):
        return default
    return value


def build_player_context(
    player_name,
    stat,
    threshold,
    predicted_value,
    probability,
    game_id=None,
    game_date=None,
    team_abbr=None,
    opponent_abbr=None,
):
    df = load_training_data()
    df["player_name"] = df["player_name"].astype(str)

    player_df = df[df["player_name"].str.lower() == player_name.lower()].copy()

    if player_df.empty:
        return None

    if stat not in player_df.columns:
        raise ValueError(f"Stat '{stat}' not found in dataset")

    player_df = player_df.sort_values("game_date").copy()

    player_df["game_date"] = pd.to_datetime(player_df["game_date"], errors="coerce")

    if game_date:
        target_date = pd.to_datetime(game_date, errors="coerce")
        if pd.notna(target_date):
            player_df = player_df[player_df["game_date"] < target_date].copy()

    if player_df.empty:
        return None

    player_df = player_df.sort_values("game_date")
    latest_row = player_df.iloc[-1]
    last_5 = player_df.tail(5)
    last_10 = player_df.tail(10)

    # Main stat series
    stat_series = pd.to_numeric(player_df[stat], errors="coerce")
    last_5_series = pd.to_numeric(last_5[stat], errors="coerce")
    last_10_series = pd.to_numeric(last_10[stat], errors="coerce")

    recent_values = [safe_float(v) for v in last_5_series.tolist()]
    last_5_avg = round(safe_mean(last_5_series), 2)
    last_10_avg = round(safe_mean(last_10_series), 2)
    season_avg = round(safe_mean(stat_series), 2)

    # Home / away splits
    home_avg = None
    away_avg = None
    if "home" in player_df.columns:
        home_series = pd.to_numeric(player_df[player_df["home"] == 1][stat], errors="coerce")
        away_series = pd.to_numeric(player_df[player_df["home"] == 0][stat], errors="coerce")

        if len(home_series.dropna()) > 0:
            home_avg = round(safe_mean(home_series), 2)
        if len(away_series.dropna()) > 0:
            away_avg = round(safe_mean(away_series), 2)

    # Opponent-specific history
    vs_team_points_avg = None
    vs_team_points_last_5 = None
    career_vs_team_avg = None

    if "opponent_id" in player_df.columns and "opponent_id" in latest_row.index:
        opponent_id = safe_get(latest_row, "opponent_id")
        if opponent_id is not None:
            vs_team_df = player_df[player_df["opponent_id"] == opponent_id].copy()
            if not vs_team_df.empty:
                vs_team_series = pd.to_numeric(vs_team_df[stat], errors="coerce")
                vs_team_points_avg = round(safe_mean(vs_team_series), 2)
                career_vs_team_avg = round(safe_mean(vs_team_series), 2)

                vs_team_last_5_series = pd.to_numeric(vs_team_df.tail(5)[stat], errors="coerce")
                if len(vs_team_last_5_series.dropna()) > 0:
                    vs_team_points_last_5 = round(safe_mean(vs_team_last_5_series), 2)

    # Playoff context
    is_playoff_game = None
    career_playoff_avg = None
    recent_playoff_avg = None
    playoff_minutes_avg = None

    if "postseason" in player_df.columns:
        is_playoff_game = bool(safe_get(latest_row, "postseason", False))

        playoff_df = player_df[player_df["postseason"] == True].copy()
        if not playoff_df.empty:
            playoff_stat_series = pd.to_numeric(playoff_df[stat], errors="coerce")
            career_playoff_avg = round(safe_mean(playoff_stat_series), 2)

            recent_playoff_series = pd.to_numeric(playoff_df.tail(5)[stat], errors="coerce")
            if len(recent_playoff_series.dropna()) > 0:
                recent_playoff_avg = round(safe_mean(recent_playoff_series), 2)

            if "minutes" in playoff_df.columns:
                playoff_minutes_series = pd.to_numeric(playoff_df["minutes"], errors="coerce")
                playoff_minutes_avg = round(safe_mean(playoff_minutes_series), 2)

    # Context features from enriched dataset
    team_injury_count = safe_float(safe_get(latest_row, "team_injury_count"), default=0.0)
    opponent_injury_count = safe_float(safe_get(latest_row, "opponent_injury_count"), default=0.0)
    days_rest = safe_float(safe_get(latest_row, "days_rest"), default=0.0)
    minutes_last_5 = safe_float(safe_get(latest_row, "minutes_last_5"), default=0.0)

    # Opponent defense context
    opponent_points_allowed_last_5 = safe_get(latest_row, "opp_ctx_team_general_base_pts", None)
    opponent_points_allowed_season = safe_get(latest_row, "opp_ctx_team_general_base_pts", None)
    opponent_pace = safe_get(latest_row, "opp_ctx_team_general_advanced_pace", None)
    opponent_def_rating = safe_get(latest_row, "opp_ctx_team_general_advanced_def_rating", None)

    # Team context
    team_pace = safe_get(latest_row, "team_ctx_team_general_advanced_pace", None)

    # Home / away label
    home_away = None
    if "home" in latest_row.index:
        home_val = safe_get(latest_row, "home")
        if home_val == 1:
            home_away = "Home"
        elif home_val == 0:
            home_away = "Away"

    # Usage trend placeholder
    usage_trend = None
    if "points_last_5" in latest_row.index and "points_last_10" in latest_row.index:
        p5 = safe_float(safe_get(latest_row, "points_last_5"), default=0.0)
        p10 = safe_float(safe_get(latest_row, "points_last_10"), default=0.0)
        usage_trend = round(p5 - p10, 2)

    return {
        "player_name": player_name,
        "stat": stat,
        "threshold": safe_float(threshold),
        "predicted_value": round(safe_float(predicted_value), 2),
        "probability_percent": round(safe_float(probability) * 100, 1),

        "last_5_avg": last_5_avg,
        "last_10_avg": last_10_avg,
        "season_avg": season_avg,
        "recent_values": recent_values,

        "home_split_avg": home_avg,
        "away_split_avg": away_avg,
        "home_away": home_away,
        "days_rest": days_rest,
        "minutes_last_5": minutes_last_5,
        "usage_trend": usage_trend,

        "vs_team_points_avg": vs_team_points_avg,
        "vs_team_points_last_5": vs_team_points_last_5,
        "career_vs_team_avg": career_vs_team_avg,

        "is_playoff_game": is_playoff_game,
        "career_playoff_avg": career_playoff_avg,
        "recent_playoff_avg": recent_playoff_avg,
        "playoff_minutes_avg": playoff_minutes_avg,

        "team_injury_count": team_injury_count,
        "opponent_injury_count": opponent_injury_count,

        "opponent_points_allowed_last_5": opponent_points_allowed_last_5,
        "opponent_points_allowed_season": opponent_points_allowed_season,
        "opponent_pace": opponent_pace,
        "opponent_def_rating": opponent_def_rating,
        "team_pace": team_pace,

        # These are placeholders for future upgrades
        "player_height": safe_get(latest_row, "player_height", None),
        "primary_defender": None,
        "primary_defender_height": None,
        "height_difference": None,
        "vs_defender_avg": None,
        "vs_defender_last_5": None,

        "game_id": game_id,
        "game_date": game_date,
        "team_abbr": team_abbr,
        "opponent_abbr": opponent_abbr,

        "starter_flag": safe_float(safe_get(latest_row, "starter_flag"), 0),
        "bench_flag": safe_float(safe_get(latest_row, "bench_flag"), 0),
        "team_injured_count": safe_float(safe_get(latest_row, "team_injured_count"), 0),
        "team_starter_injured_count": safe_float(safe_get(latest_row, "team_starter_injured_count"), 0),
        "team_injured_minutes_lost": safe_float(safe_get(latest_row, "team_injured_minutes_lost"), 0),
        "team_injured_points_lost": safe_float(safe_get(latest_row, "team_injured_points_lost"), 0),
        "opponent_injured_count": safe_float(safe_get(latest_row, "opponent_injured_count"), 0),
        "opponent_starter_injured_count": safe_float(safe_get(latest_row, "opponent_starter_injured_count"), 0),
        "role_boost_flag": safe_float(safe_get(latest_row, "role_boost_flag"), 0),
        "role_boost_score": safe_float(safe_get(latest_row, "role_boost_score"), 0),
    }