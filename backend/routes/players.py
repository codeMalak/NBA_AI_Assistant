from flask import Blueprint, jsonify, request
from services.data_loader import load_players

players_bp = Blueprint("players", __name__)


@players_bp.get("/players")
def players():
    team = request.args.get("team")
    game_id = request.args.get("game_id")

    df = load_players()

    if team and "team_abbr" in df.columns:
        df = df[df["team_abbr"].fillna("").astype(str).str.upper() == team.upper()]

    if game_id and "game_id" in df.columns:
        game_df = df[df["game_id"].astype(str) == str(game_id)]
        if not game_df.empty:
            df = game_df

    if "player_name" in df.columns:
        names = df["player_name"].fillna("").astype(str).str.strip()
    elif {"first_name", "last_name"}.issubset(df.columns):
        names = (
            df["first_name"].fillna("").astype(str).str.strip()
            + " "
            + df["last_name"].fillna("").astype(str).str.strip()
        ).str.strip()
    else:
        return jsonify({"error": "No player name columns available"}), 500

    names = names[names != ""]
    names = sorted(names.unique().tolist())

    return jsonify({
        "team": team,
        "game_id": game_id,
        "players": [{"player_name": name} for name in names]
    })