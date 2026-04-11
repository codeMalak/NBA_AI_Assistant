from services.data_loader import load_games


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
    df = load_games()
    player_df = df[df["player_name"].str.lower() == player_name.lower()].copy()

    if player_df.empty:
        return None

    if stat not in player_df.columns:
        raise ValueError(f"Stat '{stat}' not found in dataset")

    player_df = player_df.sort_values("game_date")
    last_5 = player_df.tail(5)

    recent_values = last_5[stat].tolist()
    last_5_avg = round(last_5[stat].mean(), 2)
    season_avg = round(player_df[stat].mean(), 2)



    return {
        "player_name": player_name,
        "stat": stat,
        "threshold": float(threshold),
        "predicted_value": round(float(predicted_value), 2),
        "probability_percent": round(float(probability) * 100, 1),
        "last_5_avg": last_5_avg,
        "season_avg": season_avg,
        "recent_values": recent_values,
        "game_id": game_id,
        "game_date": game_date,
        "team_abbr": team_abbr,
        "opponent_abbr": opponent_abbr,
    }