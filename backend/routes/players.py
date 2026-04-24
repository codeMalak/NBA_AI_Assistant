from flask import Blueprint, jsonify, request
from services.data_loader import load_games

players_bp = Blueprint("players", __name__)


@players_bp.get("/players")
def players():
    team = request.args.get("team")
    game_id = request.args.get("game_id")

    df = load_games()

    # First filter by team
    if team and "team_abbr" in df.columns:
        df = df[df["team_abbr"].fillna("").astype(str).str.upper() == team.upper()]

    # Only use game_id filter if it actually finds players
    if game_id and "game_id" in df.columns:
        game_df = df[df["game_id"].astype(str) == str(game_id)]

        if not game_df.empty:
            df = game_df

    player_names = (
        df["player_name"]
        .dropna()
        .astype(str)
        .str.strip()
    )
    player_names = player_names[player_names != ""]

    return jsonify({
        "team": team,
        "game_id": game_id,
        "players": [{"player_name": name} for name in sorted(player_names.unique())]
    })