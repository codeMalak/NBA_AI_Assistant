from __future__ import annotations

import pandas as pd

from services.data_loader import load_training_data


def safe_float(value, default: float = 0.0) -> float:
    """
    Safely convert values like pd.NA, None, NaN, strings, etc. to float.
    """
    if pd.isna(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_mean(series: pd.Series, default: float = 0.0) -> float:
    """
    Safely compute a numeric mean from a Series that may contain mixed values.
    """
    numeric = pd.to_numeric(series, errors="coerce")
    mean_value = numeric.mean()
    return safe_float(mean_value, default=default)


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
    player_df = df[df["player_name"].astype(str).str.lower() == player_name.lower()].copy()

    if player_df.empty:
        return None

    if stat not in player_df.columns:
        raise ValueError(f"Stat '{stat}' not found in dataset")

    player_df = player_df.sort_values("game_date")
    last_5 = player_df.tail(5)

    # Convert the stat column safely
    stat_series = pd.to_numeric(player_df[stat], errors="coerce")
    last_5_series = pd.to_numeric(last_5[stat], errors="coerce")

    recent_values = [safe_float(v) for v in last_5_series.tolist()]
    last_5_avg = round(safe_mean(last_5_series), 2)
    season_avg = round(safe_mean(stat_series), 2)

    return {
        "player_name": player_name,
        "stat": stat,
        "threshold": safe_float(threshold),
        "predicted_value": round(safe_float(predicted_value), 2),
        "probability_percent": round(safe_float(probability) * 100, 1),
        "last_5_avg": last_5_avg,
        "season_avg": season_avg,
        "recent_values": recent_values,
        "game_id": game_id,
        "game_date": game_date,
        "team_abbr": team_abbr,
        "opponent_abbr": opponent_abbr,
    }