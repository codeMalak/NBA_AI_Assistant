from flask import Blueprint, jsonify, request
from services.data_loader import load_players

players_bp = Blueprint("players", __name__)


@players_bp.get("/players")
def players():
    team = request.args.get("team")
    df = load_players()

    if team:
        team_value = team.strip().upper()

        if "team.abbreviation" in df.columns:
            team_series = df["team.abbreviation"].fillna("").astype(str).str.strip().str.upper()
            df = df[team_series == team_value]

        elif "team_name" in df.columns:
            team_series = df["team_name"].fillna("").astype(str).str.strip().str.upper()
            df = df[team_series == team_value]

        elif "team_id" in df.columns and team_value.isdigit():
            df = df[df["team_id"] == int(team_value)]

        # Do not hard fail if no team filter column exists

    # player_names = (
    #     df["player_name"]
    #     .dropna()
    #     .astype(str)
    #     .str.strip()
    # )
    # player_names = player_names[player_names != ""]

    # print(f"Players for team {team}:")
    player_names = []
    for player in df.itertuples():
        if type(player.first_name) is not str or type(player.last_name) is not str:
            # Some players have missing fields for their name: Nene
            print(f"\t\tERROR: NAME NOT STR: {player.first_name} {player.last_name}")
        name = player.first_name + " " + player.last_name
        name = name.strip()
        # print(name)
        player_names.append(name)

    return jsonify({
        "team": team,
        "players": [{"player_name": name} for name in sorted(player_names)]
    })
