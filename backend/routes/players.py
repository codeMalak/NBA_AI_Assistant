from flask import Blueprint, jsonify, request
from services.data_loader import load_games

players_bp = Blueprint("players", __name__)


@players_bp.get("/players")
def players():
    team = request.args.get("team")
    df = load_games()

    if team:
        if "team_abbr" not in df.columns:
            return jsonify({"error": "team_abbr column not available in dataset"}), 500

        team_series = df["team_abbr"].fillna("").astype(str).str.strip().str.upper()
        df = df[team_series == team.upper().strip()]

    player_names = sorted(df["player_name"].dropna().astype(str).unique().tolist())

    return jsonify({
        "team": team,
        "players": [{"player_name": name} for name in player_names]
    })