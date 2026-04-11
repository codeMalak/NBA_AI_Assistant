from flask import Blueprint, jsonify, request
from services.model_service import predict_stat_threshold

predict_bp = Blueprint("predict", __name__)


@predict_bp.post("/predict")
def predict():
    payload = request.get_json(silent=True) or {}
    player_name = payload.get("player_name", "").strip()
    stat = payload.get("stat", "points").strip().lower()
    threshold = payload.get("threshold")

    if not player_name:
        return jsonify({"error": "player_name is required"}), 400

    if threshold is None:
        return jsonify({"error": "threshold is required"}), 400

    try:
        threshold = float(threshold)
    except (TypeError, ValueError):
        return jsonify({"error": "threshold must be numeric"}), 400

    try:
        result = predict_stat_threshold(player_name=player_name, stat=stat, threshold=threshold)
        return jsonify(result)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception as exc:
        return jsonify({"error": f"Prediction failed: {exc}"}), 500
