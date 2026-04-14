from flask import Blueprint, jsonify, request
from services.model_service import predict_stat_threshold

predict_bp = Blueprint("predict", __name__)


@predict_bp.post("/predict")
def predict():
    payload = request.get_json(silent=True) or {}
    player_name = payload.get("player_name", "").strip()
    stat = payload.get("stat", "points").strip().lower()
    threshold = payload.get("threshold")
    model_type = payload.get("model_type", "baseline").strip().lower()

    if not player_name:
        return jsonify({"error": "player_name is required"}), 400

    if threshold is None:
        return jsonify({"error": "threshold is required"}), 400

    try:
        threshold = float(threshold)
    except (TypeError, ValueError):
        return jsonify({"error": "threshold must be numeric"}), 400

    if model_type not in {"baseline", "enriched"}:
        return jsonify({"error": "model_type must be 'baseline' or 'enriched'"}), 400

    try:
        result = predict_stat_threshold(
            player_name=player_name,
            stat=stat,
            threshold=threshold,
            model_type=model_type,
        )
        return jsonify(result)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception as exc:
        return jsonify({"error": f"Prediction failed: {exc}"}), 500