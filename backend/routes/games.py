from flask import Blueprint, jsonify, request
import requests
from services.live_nba_service import get_games_for_date

games_bp = Blueprint("games", __name__)

@games_bp.get("/games")
def games():
    target_date = request.args.get("date")
    if not target_date:
        return jsonify({"error": "date is required in YYYY-MM-DD format"}), 400

    try:
        games = get_games_for_date(target_date)
        return jsonify({"date": target_date, "games": games})
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else 500
        if status == 429:
            return jsonify({
                "error": "Rate limit reached on BALLDONTLIE. Wait a minute and try again."
            }), 429
        return jsonify({"error": f"Failed to fetch games: {exc}"}), status
    except Exception as exc:
        return jsonify({"error": f"Failed to fetch games: {exc}"}), 500